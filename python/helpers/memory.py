from __future__ import annotations

import asyncio
import json
import logging
import os
import random
from datetime import datetime
from enum import Enum
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
)
from weakref import WeakKeyDictionary

# Import faiss optionally to avoid crashing the UI when faiss is not installed in the
# container. Many dev setups use remote memory (SOMA_ENABLED) and don't require
# local FAISS. We set FAISS_AVAILABLE=False when the module is missing and provide
# a helpful error at the point local index initialization is attempted.
try:
    import faiss

    FAISS_AVAILABLE = True
except Exception:  # pragma: no cover - runtime environment dependent
    faiss = None
    FAISS_AVAILABLE = False
import numpy as np

# LangChain imports (optional in dev). If unavailable, we defer errors until
# local FAISS is actually used. Remote SomaBrain paths stay functional.
LC_AVAILABLE = True
try:
    try:
        # Newer LC: cache class moved under embeddings.cache
        from langchain.embeddings.cache import CacheBackedEmbeddings as LC_CacheBackedEmbeddings
    except Exception:
        from langchain.embeddings import (
            CacheBackedEmbeddings as LC_CacheBackedEmbeddings,  # type: ignore
        )
    from langchain.storage import InMemoryByteStore, LocalFileStore
    from langchain_community.docstore.in_memory import InMemoryDocstore
    from langchain_community.vectorstores import FAISS
    from langchain_community.vectorstores.utils import DistanceStrategy
    from langchain_core.documents import Document
except Exception:
    LC_AVAILABLE = False
    LC_CacheBackedEmbeddings = None
    InMemoryByteStore = None  # type: ignore
    LocalFileStore = None  # type: ignore
    InMemoryDocstore = None  # type: ignore
    FAISS = None  # type: ignore
    DistanceStrategy = None  # type: ignore

        def __init__(self, page_content: str = "", metadata: dict | None = None):
            self.page_content = page_content
            self.metadata = metadata or {}


try:
    from simpleeval import simple_eval  # type: ignore
except Exception:  # pragma: no cover - optional dependency in minimal images

    def simple_eval(expr: str, names: Mapping[str, Any] | None = None) -> bool:

        This avoids a hard dependency on `simpleeval` for environments that only
        use remote SomaBrain memory (SOMA_ENABLED=true). It is not a general
        expression evaluator.
        """
        try:
            if names is None:
                names = {}
            if "==" in expr:
                left, right = expr.split("==", 1)
                key = left.strip()
                val = right.strip().strip("'\"")
                return str(names.get(key)) == val
        except Exception:
            pass
        return False


import models
from agent import Agent
from python.helpers import guids, knowledge_import

# Note: Log imported for type annotations; LogItem used in signatures
from python.helpers.log import LogItem
from python.helpers.print_style import PrintStyle
from python.integrations.somabrain_client import (
    SomaBrainClient,
    SomaClientError,
    SomaMemoryRecord,
)

from . import files

# Raise the log level so WARNING messages aren't shown
logging.getLogger("langchain_core.vectorstores.base").setLevel(logging.ERROR)


def _env_flag(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


SOMA_ENABLED = _env_flag("SOMA_ENABLED", True)
SOMA_CACHE_INCLUDE_WM = _env_flag("SOMA_CACHE_INCLUDE_WM", False)
SOMA_CACHE_WM_LIMIT = int(os.environ.get("SOMA_CACHE_WM_LIMIT", "128"))


class MemoryArea(Enum):
    MAIN = "main"
    FRAGMENTS = "fragments"
    SOLUTIONS = "solutions"
    INSTRUMENTS = "instruments"


if FAISS_AVAILABLE and LC_AVAILABLE and FAISS is not None:

    class MyFaiss(FAISS):
        # override get_by_ids to support faster retrieval from the in-memory docstore
        def get_by_ids(self, ids: Sequence[str], /) -> List[Document]:
            return [
                self.docstore._dict[id]
                for id in (ids if isinstance(ids, list) else [ids])
                if id in self.docstore._dict
            ]  # type: ignore

        async def aget_by_ids(self, ids: Sequence[str], /) -> List[Document]:
            return self.get_by_ids(ids)

else:
    # Minimal placeholder so import-time does not fail when FAISS/LC are missing.
    class MyFaiss:  # type: ignore
        pass

    # override get_by_ids to support faster retrieval from the in-memory docstore
    def get_by_ids(self, ids: Sequence[str], /) -> List[Document]:
        # When using the remote SomaMemory path, this method won't be called.
        # Guard against missing attributes if FAISS is not installed.
        store = getattr(self, "docstore", None)
        backing = getattr(store, "_dict", {}) if store is not None else {}
        return [backing[id] for id in (ids if isinstance(ids, list) else [ids]) if id in backing]  # type: ignore

    async def aget_by_ids(self, ids: Sequence[str], /) -> List[Document]:
        return self.get_by_ids(ids)

    def get_all_docs(self):
        return self.docstore._dict  # type: ignore


class Memory:

    Area = MemoryArea

    index: dict[str, "MyFaiss"] = {}
    _remote_instances: Dict[str, "SomaMemory"] = {}

    @staticmethod
    async def get(agent: Agent):
        if SOMA_ENABLED:
            memory_subdir = agent.config.memory_subdir or "default"
            if memory_subdir not in Memory._remote_instances:
                Memory._remote_instances[memory_subdir] = SomaMemory(
                    agent=agent,
                    memory_subdir=memory_subdir,
                )
            return Memory._remote_instances[memory_subdir]

        memory_subdir = agent.config.memory_subdir or "default"
        if Memory.index.get(memory_subdir) is None:
            log_item = agent.context.log.log(
                type="util",
                heading=f"Initializing VectorDB in '/{memory_subdir}'",
            )
            db, created = Memory.initialize(
                log_item,
                agent.config.embeddings_model,
                memory_subdir,
                False,
            )
            Memory.index[memory_subdir] = db
            wrap = Memory(db, memory_subdir=memory_subdir)
            if agent.config.knowledge_subdirs:
                await wrap.preload_knowledge(
                    log_item, agent.config.knowledge_subdirs, memory_subdir
                )
            return wrap
        else:
            return Memory(
                db=Memory.index[memory_subdir],
                memory_subdir=memory_subdir,
            )

    @staticmethod
    async def get_by_subdir(
        memory_subdir: str,
        log_item: LogItem | None = None,
        preload_knowledge: bool = True,
    ):
        if SOMA_ENABLED:
            if memory_subdir not in Memory._remote_instances:
                Memory._remote_instances[memory_subdir] = SomaMemory(
                    agent=None,
                    memory_subdir=memory_subdir,
                )
            return Memory._remote_instances[memory_subdir]

        if not Memory.index.get(memory_subdir):
            import initialize

            agent_config = initialize.initialize_agent()
            model_config = agent_config.embeddings_model
            db, _created = Memory.initialize(
                log_item=log_item,
                model_config=model_config,
                memory_subdir=memory_subdir,
                in_memory=False,
            )
            wrap = Memory(db, memory_subdir=memory_subdir)
            if preload_knowledge and agent_config.knowledge_subdirs:
                await wrap.preload_knowledge(
                    log_item, agent_config.knowledge_subdirs, memory_subdir
                )
            Memory.index[memory_subdir] = db
        return Memory(db=Memory.index[memory_subdir], memory_subdir=memory_subdir)

    @staticmethod
    async def reload(agent: Agent):
        if SOMA_ENABLED:
            memory_subdir = agent.config.memory_subdir or "default"
            if memory_subdir in Memory._remote_instances:
                await Memory._remote_instances[memory_subdir].refresh()
                return Memory._remote_instances[memory_subdir]
            return await Memory.get(agent)

        memory_subdir = agent.config.memory_subdir or "default"
        if Memory.index.get(memory_subdir):
            del Memory.index[memory_subdir]
        return await Memory.get(agent)

    @staticmethod
    def initialize(
        log_item: LogItem | None,
        model_config: models.ModelConfig,
        memory_subdir: str,
        in_memory=False,
    ) -> tuple[MyFaiss, bool]:

        PrintStyle.standard("Initializing VectorDB...")

        if log_item:
            log_item.stream(progress="\nInitializing VectorDB")

        em_dir = files.get_abs_path("memory/embeddings")  # just caching, no need to parameterize
        db_dir = Memory._abs_db_dir(memory_subdir)

        # make sure embeddings and database directories exist
        os.makedirs(db_dir, exist_ok=True)

        if in_memory:
            if not LC_AVAILABLE or InMemoryByteStore is None:
                raise RuntimeError("LangChain storage not available for in-memory FAISS path")
            store = InMemoryByteStore()
        else:
            os.makedirs(em_dir, exist_ok=True)
            if not LC_AVAILABLE or LocalFileStore is None:
                raise RuntimeError("LangChain storage not available for local FAISS path")
            store = LocalFileStore(em_dir)

        embeddings_model = models.get_embedding_model(
            model_config.provider,
            model_config.name,
            **model_config.build_kwargs(),
        )
        embeddings_model_id = files.safe_file_name(model_config.provider + "_" + model_config.name)

        # here we setup the embeddings model with the chosen cache storage
        if LC_CacheBackedEmbeddings is None:
            raise RuntimeError(
                "or set SOMA_ENABLED=true to use remote SomaBrain memory."
            )
        embedder = LC_CacheBackedEmbeddings.from_bytes_store(  # type: ignore
            embeddings_model, store, namespace=embeddings_model_id
        )

        # initial DB and docs variables
        db: MyFaiss | None = None
        docs: dict[str, Document] | None = None

        created = False

        # if db folder exists and is not empty:
        if os.path.exists(db_dir) and files.exists(db_dir, "index.faiss"):
            db = MyFaiss.load_local(
                folder_path=db_dir,
                embeddings=embedder,
                allow_dangerous_deserialization=True,
                distance_strategy=DistanceStrategy.COSINE,
                # normalize_L2=True,
                relevance_score_fn=Memory._cosine_normalizer,
            )  # type: ignore

            # if there is a mismatch in embeddings used, re-index the whole DB
            emb_ok = False
            emb_set_file = files.get_abs_path(db_dir, "embedding.json")
            if files.exists(emb_set_file):
                embedding_set = json.loads(files.read_file(emb_set_file))
                if (
                    embedding_set["model_provider"] == model_config.provider
                    and embedding_set["model_name"] == model_config.name
                ):
                    # model matches
                    emb_ok = True

            # re-index -  create new DB and insert existing docs
            if db and not emb_ok:
                docs = db.get_all_docs()
                db = None

        # DB not loaded, create one
        if not db:
            if not FAISS_AVAILABLE:
                raise RuntimeError(
                    "Local FAISS library is not installed in the container. "
                    "Install faiss for local vector DB support, or set SOMA_ENABLED=true "
                    "to use remote SomaBrain memory instead."
                )

            index = faiss.IndexFlatIP(len(embedder.embed_query("example")))

            db = MyFaiss(
                embedding_function=embedder,
                index=index,
                docstore=(
                    InMemoryDocstore() if LC_AVAILABLE and InMemoryDocstore is not None else None
                ),
                index_to_docstore_id={},
                distance_strategy=DistanceStrategy.COSINE,
                # normalize_L2=True,
                relevance_score_fn=Memory._cosine_normalizer,
            )

            # insert docs if reindexing

        return db, created

    def __init__(
        self,
        db: MyFaiss,
        memory_subdir: str,
    ):
        self.db = db
        self.memory_subdir = memory_subdir

    async def preload_knowledge(
        self, log_item: LogItem | None, kn_dirs: list[str], memory_subdir: str
    ):
        if log_item:
            log_item.update(heading="Preloading knowledge...")

        # db abs path
        db_dir = Memory._abs_db_dir(memory_subdir)

        # Load the index file if it exists
        index_path = files.get_abs_path(db_dir, "knowledge_import.json")

        # make sure directory exists
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)

        index: dict[str, knowledge_import.KnowledgeImport] = {}
        if os.path.exists(index_path):
            with open(index_path, "r") as f:
                index = json.load(f)

        # preload knowledge folders
        index = self._preload_knowledge_folders(log_item, kn_dirs, index)

        for file in index:
            if index[file]["state"] in ["changed", "removed"] and index[file].get(
                "ids", []
            ):  # for knowledge files that have been changed or removed and have IDs
                await self.delete_documents_by_ids(index[file]["ids"])  # remove original version
            if index[file]["state"] == "changed":
                index[file]["ids"] = await self.insert_documents(
                    index[file]["documents"]
                )  # insert new version

        # remove index where state="removed"
        index = {k: v for k, v in index.items() if v["state"] != "removed"}

        # strip state and documents from index and save it
        for file in index:
            if "documents" in index[file]:
                del index[file]["documents"]  # type: ignore
            if "state" in index[file]:
                del index[file]["state"]  # type: ignore
        with open(index_path, "w") as f:
            json.dump(index, f)

    def _preload_knowledge_folders(
        self,
        log_item: LogItem | None,
        kn_dirs: list[str],
        index: dict[str, knowledge_import.KnowledgeImport],
    ):
        # load knowledge folders, subfolders by area
        for kn_dir in kn_dirs:
            for area in Memory.Area:
                index = knowledge_import.load_knowledge(
                    log_item,
                    files.get_abs_path("knowledge", kn_dir, area.value),
                    index,
                    {"area": area.value},
                )

        # load instruments descriptions
        index = knowledge_import.load_knowledge(
            log_item,
            files.get_abs_path("instruments"),
            index,
            {"area": Memory.Area.INSTRUMENTS.value},
            filename_pattern="**/*.md",
        )

        return index

    def get_document_by_id(self, id: str) -> Document | None:
        return self.db.get_by_ids(id)[0]

    async def search_similarity_threshold(
        self, query: str, limit: int, threshold: float, filter: str = ""
    ):
        comparator = Memory._get_comparator(filter) if filter else None

        return await self.db.asearch(
            query,
            search_type="similarity_score_threshold",
            k=limit,
            score_threshold=threshold,
            filter=comparator,
        )

    async def delete_documents_by_query(self, query: str, threshold: float, filter: str = ""):
        k = 100
        tot = 0
        removed = []

        while True:
            # Perform similarity search with score
            docs = await self.search_similarity_threshold(
                query, limit=k, threshold=threshold, filter=filter
            )
            removed += docs

            # Extract document IDs and filter based on score
            # document_ids = [result[0].metadata["id"] for result in docs if result[1] < score_limit]
            document_ids = [result.metadata["id"] for result in docs]

            # Delete documents with IDs over the threshold score
            if document_ids:
                # fnd = self.db.get(where={"id": {"$in": document_ids}})
                # if fnd["ids"]: self.db.delete(ids=fnd["ids"])
                # tot += len(fnd["ids"])
                await self.db.adelete(ids=document_ids)
                tot += len(document_ids)

            # If fewer than K document IDs, break the loop
            if len(document_ids) < k:
                break

        if tot:
            self._save_db()  # persist
        return removed

    async def delete_documents_by_ids(self, ids: list[str]):
        # aget_by_ids is not yet implemented in faiss, need to do a workaround
        rem_docs = await self.db.aget_by_ids(ids)  # existing docs to remove (prevents error)
        if rem_docs:
            rem_ids = [doc.metadata["id"] for doc in rem_docs]  # ids to remove
            await self.db.adelete(ids=rem_ids)

        if rem_docs:
            self._save_db()  # persist
        return rem_docs

    async def get_all_docs(self) -> dict[str, Document]:
        return self.db.get_all_docs()

    async def get_documents_by_ids(self, ids: Sequence[str]) -> List[Document]:
        return await self.db.aget_by_ids(ids)

    async def delete_by_ids(self, ids: Sequence[str]) -> List[Document]:
        removed = await self.delete_documents_by_ids(list(ids))
        return removed

    async def insert_text(self, text, metadata: dict = {}):
        doc = Document(text, metadata=metadata)
        ids = await self.insert_documents([doc])
        return ids[0]

    async def insert_documents(self, docs: list[Document]):
        ids = [self._generate_doc_id() for _ in range(len(docs))]
        timestamp = self.get_timestamp()

        if ids:
            for doc, id in zip(docs, ids, strict=False):
                doc.metadata["id"] = id  # add ids to documents metadata
                doc.metadata["timestamp"] = timestamp  # add timestamp
                if not doc.metadata.get("area", ""):
                    doc.metadata["area"] = Memory.Area.MAIN.value

            await self.db.aadd_documents(documents=docs, ids=ids)
            self._save_db()  # persist
        return ids

    async def update_documents(self, docs: list[Document]):
        ids = [doc.metadata["id"] for doc in docs]
        await self.db.adelete(ids=ids)  # delete originals
        ins = await self.db.aadd_documents(documents=docs, ids=ids)  # add updated
        self._save_db()  # persist
        return ins

    def _save_db(self):
        Memory._save_db_file(self.db, self.memory_subdir)

    def _generate_doc_id(self):
        while True:
            doc_id = guids.generate_id(10)  # random ID
            if not self.db.get_by_ids(doc_id):  # check if exists
                return doc_id

    @staticmethod
    def _save_db_file(db: MyFaiss, memory_subdir: str):
        abs_dir = Memory._abs_db_dir(memory_subdir)
        db.save_local(folder_path=abs_dir)

    @staticmethod
    def _get_comparator(condition: str):
        def comparator(data: dict[str, Any]):
            try:
                result = simple_eval(condition, names=data)
                return result
            except Exception as e:
                PrintStyle.error(f"Error evaluating condition: {e}")
                return False

        return comparator

    @staticmethod
    def _score_normalizer(val: float) -> float:
        res = 1 - 1 / (1 + np.exp(val))
        return res

    @staticmethod
    def _cosine_normalizer(val: float) -> float:
        res = (1 + val) / 2
        res = max(0, min(1, res))  # float precision can cause values like 1.0000000596046448
        return res

    @staticmethod
    def _abs_db_dir(memory_subdir: str) -> str:
        return files.get_abs_path("memory", memory_subdir)

    @staticmethod
    def format_docs_plain(docs: list[Document]) -> list[str]:
        result = []
        for doc in docs:
            text = ""
            for k, v in doc.metadata.items():
                text += f"{k}: {v}\n"
            text += f"Content: {doc.page_content}"
            result.append(text)
        return result

    @staticmethod
    def get_timestamp():
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class SomaMemory:
    """Remote memory store backed by the SomaBrain API."""

    Area = MemoryArea

    def __init__(self, agent: Optional[Agent], memory_subdir: str) -> None:
        self.agent = agent
        self.memory_subdir = memory_subdir or "default"
        self._client = SomaBrainClient.get()
        self._docstore = _SomaDocStore(self)
        self.db = _SomaDocStoreAdapter(self._docstore)

    @property
    def context(self):
        if self.agent and getattr(self.agent, "context", None):
            return self.agent.context
        return None

    async def refresh(self) -> None:
        await self._docstore.refresh()

    async def preload_knowledge(
        self, log_item: LogItem | None, knowledge_dirs: list[str], memory_subdir: str
    ) -> None:
        # SomaBrain handles knowledge centrally; nothing to preload locally.
        return None

    async def insert_text(self, text: str, metadata: dict | None = None) -> str:
        metadata = dict(metadata or {})
        if "area" not in metadata:
            metadata["area"] = MemoryArea.MAIN.value
        doc = Document(page_content=text, metadata=metadata)
        ids = await self.insert_documents([doc])
        if not ids:
            raise SomaClientError("Failed to insert memory via SomaBrain")
        return ids[0]

    async def insert_documents(self, docs: list[Document]) -> List[str]:
        return await self._docstore.insert_documents(docs)

    async def update_documents(self, docs: list[Document]) -> List[str]:
        return await self._docstore.update_documents(docs)

    async def search_similarity_threshold(
        self, query: str, limit: int, threshold: float, filter: str = ""
    ) -> List[Document]:
        return await self._docstore.search_similarity_threshold(query, limit, threshold, filter)

    async def delete_documents_by_query(
        self, query: str, threshold: float, filter: str = ""
    ) -> List[Document]:
        return await self._docstore.delete_documents_by_query(query, threshold, filter)

    async def delete_documents_by_ids(self, ids: list[str]) -> List[Document]:
        return await self._docstore.delete_documents_by_ids(ids)

    async def get_all_docs(self) -> Dict[str, Document]:
        return await self._docstore.get_all_docs()

    async def get_documents_by_ids(self, ids: Sequence[str]) -> List[Document]:
        return await self._docstore.get_documents_by_ids(ids)

    async def delete_by_ids(self, ids: Sequence[str]) -> List[Document]:
        return await self._docstore.delete_documents_by_ids(list(ids))

    def get_document_by_id(self, doc_id: str) -> Optional[Document]:
        return self._docstore.get_document_by_id_sync(doc_id)

    def get_timestamp(self):
        return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


class _SomaDocStoreAdapter:
    """Adapter exposing a FAISS-like interface expected by prior call sites."""

    def __init__(self, store: "_SomaDocStore") -> None:
        self._store = store

    async def aget_by_ids(self, ids: Sequence[str]) -> List[Document]:
        return await self._store.get_documents_by_ids(ids)

    def get_by_ids(self, ids: Sequence[str]) -> List[Document]:
        return self._store.get_documents_by_ids_sync(ids)

    async def adelete(self, ids: Sequence[str]) -> None:
        await self._store.delete_documents_by_ids(list(ids))

    async def aadd_documents(self, documents: list[Document], ids: list[str]) -> None:
        for doc, _id in zip(documents, ids, strict=False):
            doc.metadata["id"] = _id
        await self._store.insert_documents(documents)

    def get_all_docs(self) -> Dict[str, Document]:
        return self._store.get_all_docs_sync()


class _SomaDocStore:
    """Handles caching and transformations for SomaBrain memory payloads."""

    def __init__(self, memory: SomaMemory) -> None:
        self.memory = memory
        self._client = memory._client
        self._cache: Dict[str, Document] = {}
        self._cache_valid = False
        self._locks: WeakKeyDictionary[asyncio.AbstractEventLoop, asyncio.Lock] = (
            WeakKeyDictionary()
        )

    def _get_lock(self) -> asyncio.Lock:
        loop = asyncio.get_running_loop()
        lock = self._locks.get(loop)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[loop] = lock
        return lock

    async def refresh(self) -> Dict[str, Document]:
        async with self._get_lock():
            try:
                data = await self._client.migrate_export(
                    include_wm=SOMA_CACHE_INCLUDE_WM,
                    wm_limit=SOMA_CACHE_WM_LIMIT,
                )
                memories = data.get("memories", []) if isinstance(data, Mapping) else []
                self._cache = self._parse_memories(memories)
                self._cache_valid = True
            except SomaClientError as exc:
                # Keep existing cache (if any) and mark as invalid to retry later
                PrintStyle.error(f"SomaBrain export failed (cache kept): {exc}")
                self._cache_valid = False
            return self._cache

    async def _ensure_cache(self) -> Dict[str, Document]:
        if not self._cache_valid:
            return await self.refresh()
        return self._cache

    def _ensure_cache_sync(self) -> Dict[str, Document]:
        if self._cache_valid:
            return self._cache
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(self.refresh())
            return self._cache
        return loop.run_until_complete(self.refresh())

    async def get_all_docs(self) -> Dict[str, Document]:
        return await self._ensure_cache()

    def get_all_docs_sync(self) -> Dict[str, Document]:
        return self._ensure_cache_sync()

    async def get_documents_by_ids(self, ids: Sequence[str]) -> List[Document]:
        cache = await self._ensure_cache()
        return [cache[id] for id in ids if id in cache]

    def get_documents_by_ids_sync(self, ids: Sequence[str]) -> List[Document]:
        cache = self._ensure_cache_sync()
        return [cache[id] for id in ids if id in cache]

    def get_document_by_id_sync(self, doc_id: str) -> Optional[Document]:
        cache = self._ensure_cache_sync()
        return cache.get(doc_id)

    async def insert_documents(self, docs: list[Document]) -> List[str]:
        await self._ensure_cache()
        ids: List[str] = []
        for doc in docs:
            metadata = dict(doc.metadata)
            doc_id = metadata.get("id") or guids.generate_id(10)
            metadata["id"] = doc_id
            coord = (
                metadata.get("coord") or metadata.get("soma_coord") or self._generate_coord(doc_id)
            )
            metadata["coord"] = coord
            metadata["soma_coord"] = coord
            payload = self._build_payload(metadata, doc.page_content)
            try:
                coord_str = self._format_coord(coord)
                result = await self._client.remember(
                    payload,
                    universe=self.memory.memory_subdir,
                )
            except SomaClientError as exc:
                PrintStyle.error(f"Failed to store memory via SomaBrain: {exc}")
                continue
            else:
                if isinstance(result, Mapping):
                    returned_coord = result.get("coordinate") or result.get("coord")
                    if returned_coord:
                        metadata["coord"] = returned_coord
                        metadata["soma_coord"] = returned_coord
                    if result.get("trace_id"):
                        metadata["trace_id"] = result["trace_id"]
                    if result.get("request_id"):
                        metadata["request_id"] = result["request_id"]
            doc.metadata = metadata
            self._cache[doc_id] = doc
            ids.append(doc_id)
        self._cache_valid = True
        return ids

    async def update_documents(self, docs: list[Document]) -> List[str]:
        ids = [doc.metadata.get("id") for doc in docs if doc.metadata.get("id")]
        if ids:
            await self.delete_documents_by_ids([str(i) for i in ids if i])
        return await self.insert_documents(docs)

    async def delete_documents_by_ids(self, ids: list[str]) -> List[Document]:
        await self._ensure_cache()
        removed: List[Document] = []
        for doc_id in ids:
            doc = self._cache.get(doc_id)
            if not doc:
                continue
            coord = doc.metadata.get("coord") or doc.metadata.get("soma_coord")
            if coord is None:
                continue
            coord_list = self._parse_coord(coord)
            try:
                await self._client.delete(coord_list)
            except SomaClientError as exc:
                PrintStyle.error(f"Failed to delete memory {doc_id}: {exc}")
                continue
            removed.append(doc)
            self._cache.pop(doc_id, None)
        return removed

    async def search_similarity_threshold(
        self,
        query: str,
        limit: int,
        threshold: float,
        filter: str,
    ) -> List[Document]:
        try:
            response = await self._client.recall(
                query,
                top_k=limit or 3,
                universe=self.memory.memory_subdir,
                namespace=self.memory.memory_subdir,
            )
        except SomaClientError as exc:
            PrintStyle.error(f"SomaBrain recall failed: {exc}")
            return []

        memory_items: Optional[List[Any]] = None
        if isinstance(response, Mapping):
            candidates = response.get("memory")
            if isinstance(candidates, list):
                memory_items = candidates
            else:
                candidates = response.get("results")
                if isinstance(candidates, list):
                    memory_items = candidates
        if not isinstance(memory_items, list):
            return []

        comparator = Memory._get_comparator(filter) if filter else None
        docs: List[Document] = []
        for raw in memory_items:
            record = self._convert_memory_record(raw)
            if record is None:
                continue
            if record.score is not None and record.score < threshold:
                continue
            doc = self._record_to_document(record)
            if comparator and not comparator(doc.metadata):
                continue
            docs.append(doc)
        return docs

    async def delete_documents_by_query(
        self,
        query: str,
        threshold: float,
        filter: str,
    ) -> List[Document]:
        matches = await self.search_similarity_threshold(query, 100, threshold, filter)
        ids = [doc.metadata.get("id") for doc in matches if doc.metadata.get("id")]
        ids = [str(i) for i in ids if i]
        if ids:
            await self.delete_documents_by_ids(ids)
        return matches

    def _build_payload(self, metadata: MutableMapping[str, Any], content: str) -> Dict[str, Any]:
        payload: Dict[str, Any] = dict(metadata)
        payload.setdefault("memory_type", metadata.get("memory_type", "episodic"))
        payload.setdefault("importance", metadata.get("importance", 1))
        payload.setdefault("area", metadata.get("area", MemoryArea.MAIN.value))
        payload.setdefault("universe", metadata.get("universe", self.memory.memory_subdir))

        timestamp_val = metadata.get("timestamp")
        numeric_timestamp: float | None = None
        if isinstance(timestamp_val, (int, float)):
            numeric_timestamp = float(timestamp_val)
        elif isinstance(timestamp_val, str):
            # Try to parse numeric strings first
            try:
                numeric_timestamp = float(timestamp_val)
            except ValueError:
                try:
                    numeric_timestamp = datetime.fromisoformat(timestamp_val).timestamp()
                except ValueError:
                    numeric_timestamp = None

        if numeric_timestamp is None:
            numeric_timestamp = datetime.utcnow().timestamp()
            # preserve human readable timestamp alongside numeric value
            metadata["timestamp"] = datetime.utcnow().isoformat()

        payload["timestamp"] = numeric_timestamp
        payload["content"] = content
        payload["metadata"] = dict(metadata)
        return payload

    def _parse_coord(self, coord: Any) -> List[float]:
        if isinstance(coord, (list, tuple)):
            return [float(x) for x in coord[:3]]
        if isinstance(coord, str):
            parts = coord.split(",")
            return [float(p.strip()) for p in parts[:3]]
        raise ValueError(f"Unsupported coordinate format: {coord}")

    def _format_coord(self, coord: Any) -> str:
        if isinstance(coord, str):
            return coord
        if isinstance(coord, (list, tuple)):
            return ",".join(f"{float(c):.6f}" for c in coord[:3])
        return str(coord)

    def _generate_coord(self, seed: str) -> str:
        rng = random.Random(seed)
        return ",".join(f"{rng.uniform(-10.0, 10.0):.6f}" for _ in range(3))

    def _parse_memories(self, memories: Iterable[Any]) -> Dict[str, Document]:
        cache: Dict[str, Document] = {}
        for raw in memories:
            record = self._convert_memory_record(raw)
            if not record:
                continue
            doc = self._record_to_document(record)
            cache[record.identifier] = doc
        return cache

    def _convert_memory_record(self, raw: Any) -> Optional[SomaMemoryRecord]:
        if not isinstance(raw, Mapping):
            return None
        payload = raw.get("payload")
        if not isinstance(payload, Mapping):
            payload = {}
        identifier = (
            str(payload.get("id"))
            if payload.get("id")
            else str(raw.get("key") or raw.get("coord") or guids.generate_id(10))
        )
        coord_raw = raw.get("coord") or payload.get("coord")
        coordinate: Optional[List[float]] = None
        if coord_raw is not None:
            try:
                coordinate = self._parse_coord(coord_raw)
            except Exception:
                coordinate = None
        score = raw.get("score")
        try:
            score_val = float(score) if score is not None else None
        except (TypeError, ValueError):
            score_val = None
        retriever = raw.get("retriever")
        return SomaMemoryRecord(
            identifier=identifier,
            payload=payload,
            score=score_val,
            coordinate=coordinate,
            retriever=retriever if isinstance(retriever, str) else None,
        )

    def _record_to_document(self, record: SomaMemoryRecord) -> Document:
        metadata = dict(record.payload)
        metadata.setdefault("id", record.identifier)
        if record.coordinate:
            coord_str = ",".join(f"{c:.6f}" for c in record.coordinate)
            metadata["coord"] = coord_str
            metadata["soma_coord"] = coord_str
        if record.score is not None:
            metadata["score"] = record.score
        if record.retriever:
            metadata["retriever"] = record.retriever
        content_candidates = [
            metadata.get("content"),
            metadata.get("what"),
            metadata.get("text"),
            metadata.get("summary"),
            metadata.get("value"),
        ]
        content = next((c for c in content_candidates if isinstance(c, str)), "")
        metadata.setdefault("area", metadata.get("area", MemoryArea.MAIN.value))
        metadata.setdefault("universe", metadata.get("universe", self.memory.memory_subdir))
        return Document(page_content=content, metadata=metadata)


def get_memory_subdir_abs(agent: Agent) -> str:
    return files.get_abs_path("memory", agent.config.memory_subdir or "default")


def get_custom_knowledge_subdir_abs(agent: Agent) -> str:
    for dir in agent.config.knowledge_subdirs:
        if dir != "default":
            return files.get_abs_path("knowledge", dir)
    raise Exception("No custom knowledge subdir set")


def reload():
    # clear the memory index, this will force all DBs to reload
    Memory.index = {}
