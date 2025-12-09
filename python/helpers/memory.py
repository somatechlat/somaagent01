"""Memory module - Local FAISS and Remote SomaBrain memory stores."""
from __future__ import annotations
import json, logging, os
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Mapping, Sequence

try:
    import faiss
    FAISS_AVAILABLE = True
except Exception:
    faiss = None
    FAISS_AVAILABLE = False

LC_AVAILABLE = True
try:
    try:
        from langchain.embeddings.cache import CacheBackedEmbeddings as LC_CacheBackedEmbeddings
    except Exception:
        from langchain.embeddings import CacheBackedEmbeddings as LC_CacheBackedEmbeddings
    from langchain.storage import InMemoryByteStore, LocalFileStore
    from langchain_community.docstore.in_memory import InMemoryDocstore
    from langchain_community.vectorstores import FAISS
    from langchain_community.vectorstores.utils import DistanceStrategy
    from langchain_core.documents import Document
except Exception:
    LC_AVAILABLE = False
    LC_CacheBackedEmbeddings = InMemoryByteStore = LocalFileStore = None
    InMemoryDocstore = FAISS = DistanceStrategy = None
    class Document:
        def __init__(self, page_content: str = "", metadata: dict | None = None):
            self.page_content, self.metadata = page_content, metadata or {}

try:
    from simpleeval import simple_eval
except Exception:
    def simple_eval(expr: str, names: Mapping[str, Any] | None = None) -> bool:
        try:
            if names and "==" in expr:
                left, right = expr.split("==", 1)
                return str(names.get(left.strip())) == right.strip().strip("'\"")
        except Exception:
            pass
        return False

import models
from agent import Agent
from python.helpers import guids, knowledge_import
from python.helpers.log import LogItem
from python.helpers.print_style import PrintStyle
from python.helpers.memory_stores import SomaMemory
from . import files

logging.getLogger("langchain_core.vectorstores.base").setLevel(logging.ERROR)

def _env_flag(name: str, default: bool) -> bool:
    v = os.environ.get(name)
    return v.strip().lower() in {"1", "true", "yes", "on"} if v else default


SOMABRAIN_ENABLED = _env_flag("SA01_SOMABRAIN_ENABLED", True)
CACHE_INCLUDE_WM = _env_flag("SA01_CACHE_INCLUDE_WM", False)
CACHE_WM_LIMIT = int(os.environ.get("SA01_CACHE_WM_LIMIT", "128"))


class MemoryArea(Enum):
    MAIN = "main"
    FRAGMENTS = "fragments"
    SOLUTIONS = "solutions"
    INSTRUMENTS = "instruments"


if FAISS_AVAILABLE and LC_AVAILABLE and FAISS is not None:
    class MyFaiss(FAISS):
        def get_by_ids(self, ids: Sequence[str], /) -> List[Document]:
            return [self.docstore._dict[id] for id in (ids if isinstance(ids, list) else [ids]) if id in self.docstore._dict]
        async def aget_by_ids(self, ids: Sequence[str], /) -> List[Document]:
            return self.get_by_ids(ids)
        def get_all_docs(self):
            return self.docstore._dict
else:
    class MyFaiss:
        pass


class Memory:
    """Local FAISS-based memory store."""
    Area = MemoryArea
    index: dict[str, "MyFaiss"] = {}
    _remote_instances: Dict[str, "SomaMemory"] = {}

    @staticmethod
    def _get_soma(agent, memory_subdir: str) -> SomaMemory:
        if memory_subdir not in Memory._remote_instances:
            soma = SomaMemory(agent=agent, memory_subdir=memory_subdir, memory_area_enum=MemoryArea)
            soma._docstore.configure(CACHE_INCLUDE_WM, CACHE_WM_LIMIT)
            Memory._remote_instances[memory_subdir] = soma
        return Memory._remote_instances[memory_subdir]

    @staticmethod
    async def get(agent: Agent):
        memory_subdir = agent.config.memory_subdir or "default"
        if SOMABRAIN_ENABLED:
            return Memory._get_soma(agent, memory_subdir)
        if Memory.index.get(memory_subdir) is None:
            log_item = agent.context.log.log(type="util", heading=f"Initializing VectorDB in '/{memory_subdir}'")
            db, _ = Memory.initialize(log_item, agent.config.embeddings_model, memory_subdir, False)
            Memory.index[memory_subdir] = db
            wrap = Memory(db, memory_subdir=memory_subdir)
            if agent.config.knowledge_subdirs:
                await wrap.preload_knowledge(log_item, agent.config.knowledge_subdirs, memory_subdir)
            return wrap
        return Memory(db=Memory.index[memory_subdir], memory_subdir=memory_subdir)

    @staticmethod
    async def get_by_subdir(memory_subdir: str, log_item: LogItem | None = None, preload_knowledge: bool = True):
        if SOMABRAIN_ENABLED:
            return Memory._get_soma(None, memory_subdir)
        if not Memory.index.get(memory_subdir):
            import initialize
            agent_config = initialize.initialize_agent()
            db, _ = Memory.initialize(log_item, agent_config.embeddings_model, memory_subdir, False)
            wrap = Memory(db, memory_subdir=memory_subdir)
            if preload_knowledge and agent_config.knowledge_subdirs:
                await wrap.preload_knowledge(log_item, agent_config.knowledge_subdirs, memory_subdir)
            Memory.index[memory_subdir] = db
        return Memory(db=Memory.index[memory_subdir], memory_subdir=memory_subdir)

    @staticmethod
    async def reload(agent: Agent):
        memory_subdir = agent.config.memory_subdir or "default"
        if SOMABRAIN_ENABLED:
            if memory_subdir in Memory._remote_instances:
                await Memory._remote_instances[memory_subdir].refresh()
                return Memory._remote_instances[memory_subdir]
            return await Memory.get(agent)
        Memory.index.pop(memory_subdir, None)
        return await Memory.get(agent)

    @staticmethod
    def initialize(log_item: LogItem | None, model_config: models.ModelConfig, memory_subdir: str, in_memory=False) -> tuple[MyFaiss, bool]:
        PrintStyle.standard("Initializing VectorDB...")
        if log_item:
            log_item.stream(progress="\nInitializing VectorDB")

        em_dir = files.get_abs_path("memory/embeddings")
        db_dir = Memory._abs_db_dir(memory_subdir)
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

        embeddings_model = models.get_embedding_model(model_config.provider, model_config.name, **model_config.build_kwargs())
        embeddings_model_id = files.safe_file_name(model_config.provider + "_" + model_config.name)

        if LC_CacheBackedEmbeddings is None:
            raise RuntimeError("LangChain CacheBackedEmbeddings not available")
        embedder = LC_CacheBackedEmbeddings.from_bytes_store(embeddings_model, store, namespace=embeddings_model_id)

        db: MyFaiss | None = None
        created = False

        if os.path.exists(db_dir) and files.exists(db_dir, "index.faiss"):
            db = MyFaiss.load_local(folder_path=db_dir, embeddings=embedder, allow_dangerous_deserialization=True,
                                    distance_strategy=DistanceStrategy.COSINE, relevance_score_fn=Memory._cosine_normalizer)
            emb_ok = False
            emb_set_file = files.get_abs_path(db_dir, "embedding.json")
            if files.exists(emb_set_file):
                embedding_set = json.loads(files.read_file(emb_set_file))
                if embedding_set["model_provider"] == model_config.provider and embedding_set["model_name"] == model_config.name:
                    emb_ok = True
            if db and not emb_ok:
                db = None

        if not db:
            if not FAISS_AVAILABLE:
                raise RuntimeError("Local FAISS library not installed. Set SOMABRAIN_ENABLED=true for remote memory.")
            index = faiss.IndexFlatIP(len(embedder.embed_query("example")))
            db = MyFaiss(embedding_function=embedder, index=index,
                        docstore=(InMemoryDocstore() if LC_AVAILABLE and InMemoryDocstore else None),
                        index_to_docstore_id={}, distance_strategy=DistanceStrategy.COSINE,
                        relevance_score_fn=Memory._cosine_normalizer)
            created = True

        return db, created

    def __init__(self, db: MyFaiss, memory_subdir: str):
        self.db = db
        self.memory_subdir = memory_subdir

    async def preload_knowledge(self, log_item: LogItem | None, kn_dirs: list[str], memory_subdir: str):
        if log_item:
            log_item.update(heading="Preloading knowledge...")
        db_dir = Memory._abs_db_dir(memory_subdir)
        index_path = files.get_abs_path(db_dir, "knowledge_import.json")
        os.makedirs(db_dir, exist_ok=True)

        index: dict[str, knowledge_import.KnowledgeImport] = {}
        if os.path.exists(index_path):
            with open(index_path, "r") as f:
                index = json.load(f)

        for kn_dir in kn_dirs:
            for area in Memory.Area:
                index = knowledge_import.load_knowledge(log_item, files.get_abs_path("knowledge", kn_dir, area.value), index, {"area": area.value})
        index = knowledge_import.load_knowledge(log_item, files.get_abs_path("instruments"), index, {"area": Memory.Area.INSTRUMENTS.value}, filename_pattern="**/*.md")

        for file in index:
            if index[file]["state"] in ["changed", "removed"] and index[file].get("ids", []):
                await self.delete_documents_by_ids(index[file]["ids"])
            if index[file]["state"] == "changed":
                index[file]["ids"] = await self.insert_documents(index[file]["documents"])

        index = {k: v for k, v in index.items() if v["state"] != "removed"}
        for file in index:
            index[file].pop("documents", None)
            index[file].pop("state", None)
        with open(index_path, "w") as f:
            json.dump(index, f)

    def get_document_by_id(self, id: str) -> Document | None:
        return self.db.get_by_ids(id)[0]

    async def search_similarity_threshold(self, query: str, limit: int, threshold: float, filter: str = ""):
        comparator = Memory._get_comparator(filter) if filter else None
        return await self.db.asearch(query, search_type="similarity_score_threshold", k=limit, score_threshold=threshold, filter=comparator)

    async def delete_documents_by_query(self, query: str, threshold: float, filter: str = ""):
        k, tot, removed = 100, 0, []
        while True:
            docs = await self.search_similarity_threshold(query, limit=k, threshold=threshold, filter=filter)
            removed += docs
            document_ids = [result.metadata["id"] for result in docs]
            if document_ids:
                await self.db.adelete(ids=document_ids)
                tot += len(document_ids)
            if len(document_ids) < k:
                break
        if tot:
            self._save_db()
        return removed

    async def delete_documents_by_ids(self, ids: list[str]):
        rem_docs = await self.db.aget_by_ids(ids)
        if rem_docs:
            rem_ids = [doc.metadata["id"] for doc in rem_docs]
            await self.db.adelete(ids=rem_ids)
            self._save_db()
        return rem_docs

    async def get_all_docs(self) -> dict[str, Document]:
        return self.db.get_all_docs()

    async def get_documents_by_ids(self, ids: Sequence[str]) -> List[Document]:
        return await self.db.aget_by_ids(ids)

    async def delete_by_ids(self, ids: Sequence[str]) -> List[Document]:
        return await self.delete_documents_by_ids(list(ids))

    async def insert_text(self, text, metadata: dict = {}):
        doc = Document(text, metadata=metadata)
        ids = await self.insert_documents([doc])
        return ids[0]

    async def insert_documents(self, docs: list[Document]):
        ids = [self._generate_doc_id() for _ in range(len(docs))]
        timestamp = self.get_timestamp()
        for doc, id in zip(docs, ids, strict=False):
            doc.metadata["id"] = id
            doc.metadata["timestamp"] = timestamp
            if not doc.metadata.get("area", ""):
                doc.metadata["area"] = Memory.Area.MAIN.value
        await self.db.aadd_documents(documents=docs, ids=ids)
        self._save_db()
        return ids

    async def update_documents(self, docs: list[Document]):
        ids = [doc.metadata["id"] for doc in docs]
        await self.db.adelete(ids=ids)
        ins = await self.db.aadd_documents(documents=docs, ids=ids)
        self._save_db()
        return ins

    def _save_db(self):
        Memory._save_db_file(self.db, self.memory_subdir)

    def _generate_doc_id(self):
        while True:
            doc_id = guids.generate_id(10)
            if not self.db.get_by_ids(doc_id):
                return doc_id

    @staticmethod
    def _save_db_file(db: MyFaiss, memory_subdir: str):
        db.save_local(folder_path=Memory._abs_db_dir(memory_subdir))

    @staticmethod
    def _get_comparator(condition: str):
        def comparator(data: dict[str, Any]):
            try:
                return simple_eval(condition, names=data)
            except Exception as e:
                PrintStyle.error(f"Error evaluating condition: {e}")
                return False
        return comparator

    @staticmethod
    def _cosine_normalizer(val: float) -> float:
        return max(0, min(1, (1 + val) / 2))

    @staticmethod
    def _abs_db_dir(memory_subdir: str) -> str:
        return files.get_abs_path("memory", memory_subdir)

    @staticmethod
    def format_docs_plain(docs: list[Document]) -> list[str]:
        result = []
        for doc in docs:
            text = "".join(f"{k}: {v}\n" for k, v in doc.metadata.items())
            text += f"Content: {doc.page_content}"
            result.append(text)
        return result

    @staticmethod
    def get_timestamp():
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_memory_subdir_abs(agent: Agent) -> str:
    return files.get_abs_path("memory", agent.config.memory_subdir or "default")


def get_custom_knowledge_subdir_abs(agent: Agent) -> str:
    for dir in agent.config.knowledge_subdirs:
        if dir != "default":
            return files.get_abs_path("knowledge", dir)
    raise Exception("No custom knowledge subdir set")


def reload():
    Memory.index = {}
