# TOON Integration Design for Agent Zero

**Status:** Design Phase  
**Author:** Architecture Team  
**Date:** 2025-01-XX  
**Target:** Token cost reduction (30-60%)

## Executive Summary

TOON (Token-Oriented Object Notation) integration will reduce LLM token costs by 30-60% when passing structured data. Agent Zero is ideal because it sends large context windows (conversation history, tool schemas, memory recalls) in uniform tabular formats.

**Strategy:** Implement TOON as an optional encoding layer at LLM call boundaries only, not for APIs or storage.

---

## 1. Integration Points

### 1.1 Primary (High Impact)

#### A. LLM Context Preparation (`python/helpers/call_llm.py`)
- **Current:** JSON-serialized conversation history, tool schemas, memory context
- **TOON:** Encode uniform arrays before LLM invocation
- **Savings:** 40-50% on memory context (500-2000 tokens/call)

#### B. Tool Schema Transmission (`services/conversation_worker/main.py`)
- **Current:** Full JSON schemas for tool discovery
- **TOON:** Compact tool parameter schemas
- **Savings:** 30-40% on tool schemas (200-500 tokens/call)

#### C. Memory Recall Results (`python/tools/memory_load.py`)
- **Current:** JSON array of memory objects from SomaBrain
- **TOON:** Encode recalled memories before prompt injection
- **Savings:** 45-55% on memory recalls (1000+ tokens)

#### D. Session History (`services/gateway/main.py`)
- **Current:** Markdown-formatted history
- **TOON:** Provide TOON-encoded history endpoint
- **Savings:** 35-45% on history context

### 1.2 Secondary (Medium Impact)

#### E. Prompt Templates (`prompts/`)
- Update examples to show TOON format
- Teach LLM to expect TOON natively

#### F. Agent-to-Agent Communication (`python/tools/call_subordinate.py`)
- Encode subordinate context in TOON
- **Savings:** 30-40% on inter-agent messages

### 1.3 Where NOT to Use TOON

❌ Gateway HTTP APIs (keep JSON for REST)  
❌ Kafka events (keep JSON for schema validation)  
❌ PostgreSQL storage (keep JSONB for queries)  
❌ Redis cache (keep JSON for interoperability)  
❌ UI ↔ Gateway (keep JSON for browsers)

**Rule:** TOON is LLM-input only.

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Agent Zero Stack                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐         ┌──────────────┐             │
│  │   Gateway    │────────▶│  Kafka       │             │
│  │   (JSON)     │         │  (JSON)      │             │
│  └──────────────┘         └──────────────┘             │
│         │                        │                       │
│         │                        ▼                       │
│         │              ┌──────────────────┐             │
│         │              │ Conversation     │             │
│         │              │ Worker           │             │
│         │              └──────────────────┘             │
│         │                        │                       │
│         │                        ▼                       │
│         │              ┌──────────────────┐             │
│         │              │ TOON Encoder     │◀────────┐   │
│         │              │ (NEW LAYER)      │         │   │
│         │              └──────────────────┘         │   │
│         │                        │                  │   │
│         │                        ▼                  │   │
│         │              ┌──────────────────┐         │   │
│         │              │ LLM Provider     │         │   │
│         │              └──────────────────┘         │   │
│         │                                           │   │
│         ▼                                           │   │
│  ┌──────────────┐                                  │   │
│  │ SomaBrain    │──────────────────────────────────┘   │
│  │ (JSON)       │  Memory Recall (JSON → TOON)         │
│  └──────────────┘                                       │
└─────────────────────────────────────────────────────────┘
```

**Principle:** TOON encoding at last moment before LLM, nowhere else.

---

## 3. Module Structure

```
python/helpers/
├── toon_encoder.py          # NEW: TOON encoding wrapper
├── call_llm.py              # MODIFIED: Add TOON option
└── tokens.py                # MODIFIED: TOON token counting

python/integrations/
└── toon/                    # NEW: Python TOON library
    ├── __init__.py
    ├── encoder.py
    └── decoder.py

services/conversation_worker/
└── main.py                  # MODIFIED: Use TOON for context

python/tools/
├── memory_load.py           # MODIFIED: Encode recalls
└── call_subordinate.py      # MODIFIED: Encode subordinate context

prompts/
├── agent.system.main.md     # MODIFIED: Add TOON examples
└── agent.system.tools.md    # MODIFIED: Show TOON schemas
```

---

## 4. Implementation: Core Encoder

```python
# python/helpers/toon_encoder.py

from typing import Any
import os

_toon_module = None

def _get_toon():
    global _toon_module
    if _toon_module is None:
        try:
            from python.integrations.toon import encoder
            _toon_module = encoder
        except ImportError:
            raise ImportError("Install: pip install python-toon")
    return _toon_module

def is_toon_enabled() -> bool:
    return os.getenv("AGENT_TOON_ENABLED", "false").lower() in {
        "true", "1", "yes", "on"
    }

def should_use_toon_for(data: Any) -> bool:
    """Heuristic: Use TOON for uniform arrays of objects."""
    if not isinstance(data, (dict, list)):
        return False
    
    if isinstance(data, dict):
        for value in data.values():
            if isinstance(value, list) and len(value) > 2:
                if all(isinstance(item, dict) for item in value):
                    if len(value) >= 2:
                        keys1 = set(value[0].keys())
                        keys2 = set(value[1].keys())
                        if keys1 == keys2:
                            return True
    
    if isinstance(data, list) and len(data) > 2:
        if all(isinstance(item, dict) for item in data):
            if len(data) >= 2:
                keys1 = set(data[0].keys())
                keys2 = set(data[1].keys())
                if keys1 == keys2:
                    return True
    
    return False

def encode_for_llm(
    data: Any,
    force_toon: bool = False,
    delimiter: str = ",",
    indent: int = 2
) -> str:
    """Encode data for LLM consumption."""
    if not is_toon_enabled() and not force_toon:
        import json
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    if not force_toon and not should_use_toon_for(data):
        import json
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    try:
        toon = _get_toon()
        return toon.encode(data, delimiter=delimiter, indent=indent)
    except Exception as exc:
        import json
        import logging
        logging.getLogger(__name__).warning(
            f"TOON encoding failed, fallback to JSON: {exc}"
        )
        return json.dumps(data, ensure_ascii=False, indent=2)
```

---

## 5. Configuration

### Environment Variables

```bash
# Enable TOON globally
AGENT_TOON_ENABLED=true

# Delimiter (comma, tab, pipe)
AGENT_TOON_DELIMITER=","

# Indentation spaces
AGENT_TOON_INDENT=2

# Force contexts (comma-separated)
AGENT_TOON_FORCE_CONTEXTS="memories,tools,history"

# Disable for specific models
AGENT_TOON_DISABLED_MODELS="gpt-3.5-turbo"
```

### UI Settings

```json
{
  "llm": {
    "toon_enabled": true,
    "toon_delimiter": ",",
    "toon_contexts": ["memories", "tools", "history"]
  }
}
```

---

## 6. Rollout Plan

### Phase 1: Foundation (Week 1)
- [ ] Install `python-toon` library
- [ ] Implement `toon_encoder.py`
- [ ] Add environment variable support
- [ ] Write unit tests

### Phase 2: Core Integration (Week 2)
- [ ] Integrate into `call_llm.py`
- [ ] Update Conversation Worker
- [ ] Modify `memory_load.py`
- [ ] Update prompt templates

### Phase 3: Testing (Week 3)
- [ ] Integration tests
- [ ] Measure token savings
- [ ] Test multiple LLM providers
- [ ] Validate accuracy

### Phase 4: Production (Week 4)
- [ ] Deploy with `AGENT_TOON_ENABLED=false`
- [ ] Enable for 10% traffic (canary)
- [ ] Monitor metrics
- [ ] Enable globally

---

## 7. Monitoring

### Prometheus Metrics

```python
TOON_ENCODINGS = Counter(
    "agent_toon_encodings_total",
    "Total TOON encodings",
    labelnames=["context_type", "result"]
)

TOON_TOKEN_SAVINGS = Histogram(
    "agent_toon_token_savings_ratio",
    "Token savings ratio",
    labelnames=["context_type"]
)
```

### Grafana Dashboard

- Panel 1: TOON Encoding Rate
- Panel 2: Token Savings by Context
- Panel 3: Fallback Rate

---

## 8. Cost-Benefit Analysis

### Estimated Savings (Monthly)

**Assumptions:**
- 10,000 LLM calls/day
- 2,000 tokens/call average
- 40% reduction with TOON
- $0.01 per 1K tokens (GPT-4)

**Before:** 600M tokens/month = $6,000  
**After:** 360M tokens/month = $3,600  
**Savings:** $2,400/month (40%)

**Implementation:** 4 weeks effort  
**ROI:** Positive after 1 month

---

## 9. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| LLM parsing errors | High | Feature flag + JSON fallback |
| Token counting inaccurate | Medium | Use tiktoken with TOON |
| Performance overhead | Low | Measure in tests |
| Non-uniform data | Medium | Heuristic + fallback |
| Model incompatibility | Medium | Per-model disable |

---

## 10. Success Criteria

**Must Have:**
- 30%+ token reduction on uniform data
- No accuracy degradation
- Feature flag for safe rollout
- JSON fallback on errors

**Nice to Have:**
- 40%+ token reduction
- Sub-5ms encoding overhead
- All LLM provider support
- UI toggle

---

## References

- TOON Specification: https://github.com/toon-format/spec
- Python Implementation: https://github.com/xaviviro/python-toon
- TOON Benchmarks: https://github.com/toon-format/toon#benchmarks

---

## Appendix: Example Transformations

### Before (JSON)
```json
{
  "memories": [
    {"id": 1, "content": "User prefers Python", "timestamp": "2025-01-15T10:00:00Z", "area": "main"},
    {"id": 2, "content": "Deadline March 1st", "timestamp": "2025-01-16T14:30:00Z", "area": "main"}
  ]
}
```

### After (TOON)
```toon
memories[2]{id,content,timestamp,area}:
  1,User prefers Python,2025-01-15T10:00:00Z,main
  2,Deadline March 1st,2025-01-16T14:30:00Z,main
```

**Token Count:**
- JSON: ~85 tokens
- TOON: ~45 tokens
- **Savings: 47%**
