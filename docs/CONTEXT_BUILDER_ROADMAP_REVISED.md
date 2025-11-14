# Context Builder Implementation Roadmap (REVISED)

**Project:** SomaAgent01 Context Builder  
**Date:** 2025-01-13  
**Status:** Ready for Implementation  
**Based on:** Gap Analysis of actual codebase

---

## 🎯 Overview

Build a local orchestration layer (`ContextBuilder`) that:
1. Retrieves memories from Somabrain via existing `SomaClient.recall()`
2. Scores documents with salience + recency decay
3. Filters via OPA policy evaluation
4. Redacts PII with Presidio
5. Enforces token budget with tiktoken
6. Renders prompts with Jinja2
7. Sends feedback to Somabrain

**Key Insight:** `build_context()` already exists in `somabrain_client.py` but it's just a thin HTTP wrapper. All intelligence must be built locally.

---

## 📅 4-Week Timeline

| Week | Focus | Deliverables | Hours |
|------|-------|--------------|-------|
| **1** | Foundation | Dependencies, scaffolding, templates | 16h |
| **2** | Retrieval + Scoring | Salience API, composite scoring, recency | 20h |
| **3** | Guardrails + Rendering | Policy, redaction, budgeting, Jinja2 | 24h |
| **4** | Feedback + Observability | Metrics, E2E tests, docs | 20h |

**Total:** 80 hours (~2 weeks full-time)

---

## 🗓️ Week 1: Foundation

### Goals
- Add missing dependencies
- Create module scaffolding
- Set up templates directory
- Verify Docker build

### Tasks

#### 1.1 Update Dependencies (2h)
```bash
# Edit requirements.txt
echo "presidio-anonymizer>=2.2.0" >> requirements.txt
echo "jinja2>=3.1.2" >> requirements.txt
```

**Files changed:**
- `requirements.txt`

**Acceptance:**
- Dependencies added
- No version conflicts with existing packages

---

#### 1.2 Update Dockerfile (1h)
Verify new dependencies install correctly in Docker build.

**Files changed:**
- `Dockerfile` (if explicit pip install needed)

**Acceptance:**
- `docker build -t somaagent01:dev .` succeeds
- Image size increase <100MB

---

#### 1.3 Create ContextBuilder Module (4h)
```python
# python/context_builder.py
import logging
from typing import Any, Dict, List, Optional
from python.integrations.soma_client import SomaClient

logger = logging.getLogger(__name__)

class ContextBuilder:
    def __init__(self, max_tokens: int = 2000, client: Optional[SomaClient] = None):
        self.max_tokens = max_tokens
        self.client = client or SomaClient.get()
        logger.info(f"ContextBuilder initialized with max_tokens={max_tokens}")
    
    async def build(self, query: str, tenant_id: str) -> str:
        logger.info(f"Building context for query: {query[:50]}...")
        # Week 1: stub implementation
        return f"Context stub for: {query}"
```

**Files changed:**
- `python/context_builder.py` (new)

**Acceptance:**
- Module imports without errors
- Stub `build()` method returns string

---

#### 1.4 Create Templates Directory (2h)
```bash
mkdir -p templates
```

```jinja2
{# templates/context_prompt.j2 #}
{{ system_prompt }}

{% for doc in snippets %}
---
Source: {{ doc.metadata.source | default('unknown') }}
Score: {{ "%.3f" | format(doc.score) }}
{{ doc.content }}
{% endfor %}

User: {{ user_query }}
```

**Files changed:**
- `templates/context_prompt.j2` (new)

**Acceptance:**
- Template renders with sample data
- No Jinja2 syntax errors

---

#### 1.5 Add Unit Test (3h)
```python
# tests/unit/test_context_builder_import.py
import pytest
from python.context_builder import ContextBuilder

def test_import():
    assert ContextBuilder is not None

def test_init():
    cb = ContextBuilder(max_tokens=1000)
    assert cb.max_tokens == 1000

@pytest.mark.asyncio
async def test_build_stub():
    cb = ContextBuilder()
    result = await cb.build("test query", "default")
    assert "test query" in result
```

**Files changed:**
- `tests/unit/test_context_builder_import.py` (new)

**Acceptance:**
- `pytest tests/unit/test_context_builder_import.py` passes

---

#### 1.6 Update CI Pipeline (2h)
Ensure new tests run in CI.

**Files changed:**
- `.github/workflows/ci.yml` (if needed)

**Acceptance:**
- CI runs new tests
- No regressions in existing tests

---

#### 1.7 Documentation Stub (2h)
```markdown
# docs/context_builder.md
# Context Builder

## Overview
Local orchestration layer for building LLM context from Somabrain memories.

## Status
🚧 Week 1: Foundation complete
```

**Files changed:**
- `docs/context_builder.md` (new)

**Acceptance:**
- Documentation builds with mkdocs

---

### Week 1 Acceptance Criteria
- [ ] Docker image builds successfully
- [ ] `ContextBuilder` imports without errors
- [ ] Template renders sample data
- [ ] Unit tests pass
- [ ] Documentation stub exists

---

## 🗓️ Week 2: Retrieval + Scoring

### Goals
- Extend SomaClient with salience endpoint
- Implement retrieval logic
- Add composite scoring with recency decay
- Integration test with live Somabrain

### Tasks

#### 2.1 Add Salience Method to SomaClient (4h)
```python
# python/integrations/soma_client.py
async def salience(
    self,
    doc_id: str,
    *,
    tenant: Optional[str] = None,
) -> float:
    """Get salience score for a document."""
    params = {"tenant": tenant or self._tenant_id or "default"}
    response = await self._request(
        "GET",
        f"/brain/salience/{doc_id}",
        params=params,
        allow_404=True,
    )
    if response is None:
        return 0.0
    return float(response.get("salience", 0.0))
```

**Files changed:**
- `python/integrations/soma_client.py`

**Acceptance:**
- Method calls `/brain/salience/{doc_id}`
- Returns float between 0.0 and 1.0
- Handles 404 gracefully (returns 0.0)

---

#### 2.2 Implement Retrieval (4h)
```python
# python/context_builder.py
async def _retrieve(
    self,
    query: str,
    tenant_id: str,
    top_k: int = 200,
) -> List[Dict[str, Any]]:
    """Retrieve candidate documents from Somabrain."""
    response = await self.client.recall(
        query=query,
        top_k=top_k,
        tenant=tenant_id,
    )
    return response.get("results", [])
```

**Files changed:**
- `python/context_builder.py`

**Acceptance:**
- Calls `client.recall()` with correct params
- Returns list of documents
- Logs retrieval count

---

#### 2.3 Implement Scoring (6h)
```python
# python/context_builder.py
import asyncio
import time
from datetime import datetime

async def _score(
    self,
    docs: List[Dict[str, Any]],
    tenant_id: str,
) -> List[tuple[float, Dict[str, Any]]]:
    """Score documents with salience + recency decay."""
    
    # Parallel salience calls
    salience_tasks = [
        self.client.salience(doc["id"], tenant=tenant_id)
        for doc in docs
    ]
    saliences = await asyncio.gather(*salience_tasks, return_exceptions=True)
    
    scored = []
    now = datetime.utcnow()
    
    for doc, sal in zip(docs, saliences):
        # Handle exceptions from salience calls
        if isinstance(sal, Exception):
            sal = 0.0
        
        # Similarity from recall
        sim = doc.get("score", 0.0)
        
        # Recency decay: exp(-days/30)
        ts = doc.get("metadata", {}).get("timestamp")
        if ts:
            delta = (now - datetime.fromisoformat(ts)).days
            recency = math.exp(-delta / 30.0)
        else:
            recency = 0.5  # default
        
        # Composite: 0.5*sim + 0.3*sal + 0.2*rec
        composite = 0.5 * sim + 0.3 * sal + 0.2 * recency
        
        scored.append((composite, doc))
    
    # Sort descending
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored
```

**Files changed:**
- `python/context_builder.py`

**Acceptance:**
- Salience calls run in parallel
- Recency decay calculated correctly
- Composite score formula matches spec
- Results sorted by score descending

---

#### 2.4 Integration Test (4h)
```python
# tests/integration/test_context_builder_retrieval.py
import pytest
from python.context_builder import ContextBuilder

@pytest.mark.asyncio
async def test_retrieval_and_scoring(somabrain_container):
    """Test against live Somabrain container."""
    cb = ContextBuilder()
    
    # Build context
    result = await cb.build("test query", "default")
    
    # Verify structure
    assert isinstance(result, str)
    assert len(result) > 0
```

**Files changed:**
- `tests/integration/test_context_builder_retrieval.py` (new)

**Acceptance:**
- Test runs against live Somabrain
- Retrieves ≥3 documents
- Scores logged to `/root/subordinate_progress.log`

---

#### 2.5 Update build() Method (2h)
Wire retrieval + scoring into main build method.

**Files changed:**
- `python/context_builder.py`

**Acceptance:**
- `build()` calls `_retrieve()` and `_score()`
- Returns scored documents

---

### Week 2 Acceptance Criteria
- [ ] `SomaClient.salience()` method works
- [ ] Retrieval fetches documents from Somabrain
- [ ] Scoring applies composite formula
- [ ] Integration test passes with live Somabrain
- [ ] Scores logged correctly

---

## 🗓️ Week 3: Guardrails + Rendering

### Goals
- Add OPA policy evaluation per document
- Implement PII redaction with Presidio
- Add token budgeting with tiktoken
- Render final prompt with Jinja2
- Hook into preload.py

### Tasks

#### 3.1 Add Policy Evaluation to SomaClient (4h)
```python
# python/integrations/soma_client.py
async def evaluate_policy(
    self,
    content: str,
    tenant: str,
) -> bool:
    """Evaluate if content passes OPA policy."""
    payload = {
        "input": {
            "content": content,
            "tenant": tenant,
        }
    }
    response = await self._request(
        "POST",
        "/opa/evaluate",
        json=payload,
    )
    return response.get("result", {}).get("allow", False)
```

**Files changed:**
- `python/integrations/soma_client.py`

**Acceptance:**
- Calls `/opa/evaluate` with content
- Returns boolean
- Handles errors gracefully

---

#### 3.2 Implement Policy Filter (3h)
```python
# python/context_builder.py
async def _filter_policy(
    self,
    scored_docs: List[tuple[float, Dict]],
    tenant_id: str,
) -> List[tuple[float, Dict]]:
    """Filter documents through OPA policy."""
    filtered = []
    for score, doc in scored_docs:
        content = doc.get("content", "")
        allowed = await self.client.evaluate_policy(content, tenant_id)
        if allowed:
            filtered.append((score, doc))
        else:
            logger.warning(f"Doc {doc.get('id')} blocked by policy")
    return filtered
```

**Files changed:**
- `python/context_builder.py`

**Acceptance:**
- Calls `evaluate_policy()` for each doc
- Drops denied documents
- Logs policy blocks

---

#### 3.3 Implement PII Redaction (4h)
```python
# python/context_builder.py
from presidio_anonymizer import AnonymizerEngine
from presidio_analyzer import AnalyzerEngine

class ContextBuilder:
    def __init__(self, ...):
        # ...
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
    
    async def _redact(
        self,
        scored_docs: List[tuple[float, Dict]],
    ) -> List[tuple[float, Dict]]:
        """Redact PII from documents."""
        redacted = []
        for score, doc in scored_docs:
            content = doc.get("content", "")
            
            # Analyze for PII
            results = self.analyzer.analyze(
                text=content,
                language="en",
            )
            
            # Anonymize
            anonymized = self.anonymizer.anonymize(
                text=content,
                analyzer_results=results,
            )
            
            # Update doc
            doc_copy = doc.copy()
            doc_copy["content"] = anonymized.text
            redacted.append((score, doc_copy))
        
        return redacted
```

**Files changed:**
- `python/context_builder.py`

**Acceptance:**
- Presidio detects PII (email, SSN, phone)
- Content redacted with placeholders
- Original docs unchanged

---

#### 3.4 Implement Token Budgeting (4h)
```python
# python/context_builder.py
import tiktoken

class ContextBuilder:
    def __init__(self, ...):
        # ...
        self.encoding = tiktoken.get_encoding("cl100k_base")
    
    async def _budget(
        self,
        scored_docs: List[tuple[float, Dict]],
        max_tokens: int,
    ) -> List[tuple[float, Dict]]:
        """Prune documents to fit token budget."""
        budgeted = []
        total_tokens = 0
        
        for score, doc in scored_docs:
            content = doc.get("content", "")
            tokens = len(self.encoding.encode(content))
            
            if total_tokens + tokens <= max_tokens:
                budgeted.append((score, doc))
                total_tokens += tokens
            else:
                logger.info(f"Token budget reached: {total_tokens}/{max_tokens}")
                break
        
        return budgeted
```

**Files changed:**
- `python/context_builder.py`

**Acceptance:**
- Counts tokens with tiktoken
- Stops when budget reached
- Logs final token count

---

#### 3.5 Implement Prompt Rendering (4h)
```python
# python/context_builder.py
from jinja2 import Environment, FileSystemLoader

class ContextBuilder:
    def __init__(self, ...):
        # ...
        self.jinja_env = Environment(
            loader=FileSystemLoader("templates")
        )
    
    async def _render(
        self,
        scored_docs: List[tuple[float, Dict]],
        query: str,
    ) -> str:
        """Render final prompt with Jinja2."""
        template = self.jinja_env.get_template("context_prompt.j2")
        
        snippets = []
        for score, doc in scored_docs:
            snippets.append({
                "content": doc.get("content", ""),
                "score": score,
                "metadata": doc.get("metadata", {}),
            })
        
        return template.render(
            system_prompt="You are a helpful assistant.",
            snippets=snippets,
            user_query=query,
        )
```

**Files changed:**
- `python/context_builder.py`

**Acceptance:**
- Loads Jinja2 template
- Renders with snippets
- Returns formatted string

---

#### 3.6 Wire Full Pipeline (3h)
Update `build()` to call all stages.

```python
async def build(self, query: str, tenant_id: str) -> str:
    # 1. Retrieve
    docs = await self._retrieve(query, tenant_id)
    
    # 2. Score
    scored = await self._score(docs, tenant_id)
    
    # 3. Filter policy
    filtered = await self._filter_policy(scored, tenant_id)
    
    # 4. Redact PII
    redacted = await self._redact(filtered)
    
    # 5. Budget tokens
    budgeted = await self._budget(redacted, self.max_tokens)
    
    # 6. Render prompt
    prompt = await self._render(budgeted, query)
    
    return prompt
```

**Files changed:**
- `python/context_builder.py`

**Acceptance:**
- All stages execute in order
- Prompt returned
- No errors

---

#### 3.7 Hook into preload.py (2h)
```python
# preload.py
async def preload():
    # ... existing preloads ...
    
    # Preload ContextBuilder
    async def preload_context_builder():
        try:
            from python.context_builder import ContextBuilder
            max_tokens = int(os.getenv('SOMA_MAX_TOKENS', '2000'))
            cb = ContextBuilder(max_tokens=max_tokens)
            # Store in global registry if needed
            return cb
        except Exception as e:
            PrintStyle().error(f"Error in preload_context_builder: {e}")
    
    tasks = [
        preload_embedding(),
        preload_context_builder(),
    ]
    await asyncio.gather(*tasks, return_exceptions=True)
```

**Files changed:**
- `preload.py`

**Acceptance:**
- ContextBuilder instantiated on startup
- No import errors
- Logs "ContextBuilder initialized"

---

### Week 3 Acceptance Criteria
- [ ] Policy evaluation works per document
- [ ] PII redaction removes sensitive data
- [ ] Token budgeting enforces limit
- [ ] Jinja2 renders final prompt
- [ ] Prompt ≤ `SOMA_MAX_TOKENS`
- [ ] No PII in output (regex verified)
- [ ] All snippets pass OPA
- [ ] preload.py instantiates ContextBuilder

---

## 🗓️ Week 4: Feedback + Observability

### Goals
- Implement feedback loop
- Add Prometheus metrics
- E2E test
- Complete documentation

### Tasks

#### 4.1 Implement Feedback (3h)
```python
# python/context_builder.py
async def feedback(
    self,
    doc_id: str,
    success: bool,
    tenant_id: str,
) -> None:
    """Send feedback to Somabrain."""
    payload = {
        "doc_id": doc_id,
        "helpful": success,
        "tenant": tenant_id,
    }
    await self.client.context_feedback(payload)
    logger.info(f"Feedback sent for doc {doc_id}: {success}")
```

**Files changed:**
- `python/context_builder.py`

**Acceptance:**
- Calls `client.context_feedback()`
- Logs feedback
- Handles errors gracefully

---

#### 4.2 Add Prometheus Metrics (4h)
```python
# python/context_builder.py
from prometheus_client import Counter, Histogram, Gauge

CONTEXT_PROMPT_TOTAL = Counter(
    "context_builder_prompt_total",
    "Total context prompts built",
)
CONTEXT_PROMPT_SECONDS = Histogram(
    "context_builder_prompt_seconds",
    "Context prompt build latency",
)
CONTEXT_SNIPPETS_TOTAL = Counter(
    "context_builder_snippets_total",
    "Snippets at each stage",
    labelnames=("stage",),
)
CONTEXT_TOKENS_USED = Gauge(
    "context_builder_tokens_used",
    "Tokens used in final prompt",
)
```

**Files changed:**
- `python/context_builder.py`

**Acceptance:**
- Metrics defined
- Incremented at each stage
- Visible in Prometheus scrape

---

#### 4.3 Instrument build() Method (2h)
Wrap `build()` with metrics.

```python
async def build(self, query: str, tenant_id: str) -> str:
    start = time.perf_counter()
    try:
        # ... pipeline ...
        CONTEXT_PROMPT_TOTAL.inc()
        return prompt
    finally:
        duration = time.perf_counter() - start
        CONTEXT_PROMPT_SECONDS.observe(duration)
```

**Files changed:**
- `python/context_builder.py`

**Acceptance:**
- Latency recorded
- Counter incremented
- Metrics exported

---

#### 4.4 E2E Test (6h)
```python
# tests/e2e/test_context_builder_e2e.py
@pytest.mark.asyncio
async def test_full_pipeline(somabrain_container):
    cb = ContextBuilder(max_tokens=2000)
    
    # Build prompt
    prompt = await cb.build("What is the capital of France?", "default")
    
    # Verify
    assert len(prompt) > 0
    assert len(prompt.split()) <= 2000  # rough token check
    assert "@" not in prompt  # no emails
    assert "---" in prompt  # has snippets
    
    # Send feedback
    await cb.feedback("doc_123", True, "default")
```

**Files changed:**
- `tests/e2e/test_context_builder_e2e.py` (new)

**Acceptance:**
- Full pipeline executes
- Prompt meets all criteria
- Feedback stored in Somabrain

---

#### 4.5 Documentation (5h)
Complete `docs/context_builder.md` with:
- Architecture diagram (Mermaid)
- Configuration table
- Usage examples
- API reference

**Files changed:**
- `docs/context_builder.md`
- `README.md` (add Context Builder section)
- `docs/configuration.md` (add env vars)

**Acceptance:**
- Documentation builds with mkdocs
- All sections complete
- Examples runnable

---

### Week 4 Acceptance Criteria
- [ ] Feedback method works
- [ ] Prometheus metrics visible
- [ ] E2E test passes
- [ ] Documentation complete
- [ ] All tests pass (unit + integration + e2e)
- [ ] Code coverage ≥80%

---

## 📊 Final Deliverables

### Code
- `python/context_builder.py` - Full implementation
- `python/integrations/soma_client.py` - Extended with salience + evaluate_policy
- `templates/context_prompt.j2` - Jinja2 template
- `preload.py` - ContextBuilder instantiation

### Tests
- `tests/unit/test_context_builder_*.py` - Unit tests
- `tests/integration/test_context_builder_retrieval.py` - Integration test
- `tests/e2e/test_context_builder_e2e.py` - E2E test

### Documentation
- `docs/CONTEXT_BUILDER_GAP_ANALYSIS.md` - Gap analysis
- `docs/CONTEXT_BUILDER_ROADMAP_REVISED.md` - This roadmap
- `docs/context_builder.md` - Feature documentation
- `README.md` - Updated with Context Builder section

### Configuration
- `requirements.txt` - Updated with presidio + jinja2
- Environment variables documented

---

## 🎯 Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Prompt latency** | ≤150ms (p95) | Prometheus histogram |
| **Token utilization** | 70-90% | Gauge metric |
| **Context precision** | ≥0.78 | Comet evaluation |
| **Test coverage** | ≥80% | pytest-cov |
| **PII leakage** | 0 incidents | Regex tests |
| **Policy violations** | 0 incidents | OPA logs |

---

**Status:** Ready for Week 1 kickoff
