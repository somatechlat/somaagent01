# 📁 SOMAAGENT01 DOCUMENTATION STRUCTURE
## Organization & Navigation Guide

**Last Updated:** 2025-12-14  
**Purpose:** Standard documentation structure for all somaAgent01 docs

---

## 📂 FOLDER STRUCTURE

```
docs/
├── architecture/          # System architecture & components
│   ├── CONTEXT_BUILDER_DEEP_DIVE.md
│   ├── AGENT_FSM.md
│   ├── SOMABRAIN_INTEGRATION.md
│   └── DEGRADATION_MODE.md
│
├── flows/                 # Message & process flows
│   ├── ULTIMATE_COMPLETE_FLOW.md (ALL scenarios)
│   ├── COMPLETE_MULTIMODAL_FLOW.md
│   └── MESSAGE_FLOW_DIAGRAM.md
│
├── reference/             # Reference documentation
│   ├── DATA_MODELS.md (Mermaid ER diagrams)
│   ├── COMPLETE_AGENT_SETTINGS_CATALOG.md
│   ├── API_ENDPOINTS.md
│   └── TOOL_CATALOG.md
│
├── guides/                # How-to guides
│   ├── GETTING_STARTED.md
│   ├── ADDING_NEW_ROUTER.md
│   ├── IMPLEMENTING_TOOLS.md
│   └── DEPLOYMENT_GUIDE.md
│
├── ui-integration/        # UI/UX documentation
│   ├── PERSONA_CAPSULES_TOOLS_UI.md
│   ├── COMPLETE_AGENTSKIN_UIX_SPEC.md
│   └── WEBUI_PATTERNS.md
│
└── README.md              # THIS FILE - Index

---

## 🎯 STANDARDS

### Mermaid Diagrams (REQUIRED)
All documentation **MUST** include Mermaid diagrams for:
- **Data Models**: Use `erDiagram` for entities
- **Flows**: Use `sequenceDiagram` for processes
- **Architecture**: Use `graph` or `flowchart` for components
- **State Machines**: Use `stateDiagram-v2` for states

### File Naming
- Use `SCREAMING_SNAKE_CASE.md` for major docs
- Use `kebab-case.md` for guides
- Always include extension `.md`

### Document Structure
```markdown
# Title
## Subtitle

**Key Info Block**

---

## Section 1

### Subsection

\`\`\`mermaid
<diagram>
\`\`\`

<content>
```

---

## 🗂️ DOCUMENT INDEX

### Architecture (5 docs)
| Document | Description | Lines |
|----------|-------------|-------|
| [CONTEXT_BUILDER_DEEP_DIVE.md](architecture/CONTEXT_BUILDER_DEEP_DIVE.md) | Memory retrieval & token budgeting | 350+ |
| [AGENT_BEHAVIOR_SETTINGS.md](architecture/AGENT_BEHAVIOR_SETTINGS.md) | Agent configuration & behavior | 200+ |
| AGENT_FSM.md | Finite state machine flow | TBD |
| SOMABRAIN_INTEGRATION.md | SomaBrain API integration | TBD |
| DEGRADATION_MODE.md | System degradation handling | TBD |

### Flows (3 docs)
| Document | Description | Lines |
|----------|-------------|-------|
| [ULTIMATE_COMPLETE_FLOW.md](flows/ULTIMATE_COMPLETE_FLOW.md) | ALL scenarios + degradation | 450+ |
| [COMPLETE_MULTIMODAL_FLOW.md](flows/COMPLETE_MULTIMODAL_FLOW.md) | Text/Voice/Files/Vision | 400+ |
| [MESSAGE_FLOW_DIAGRAM.md](flows/MESSAGE_FLOW_DIAGRAM.md) | Basic text message flow | 300+ |

### Reference (4 docs)
| Document | Description | Lines |
|----------|-------------|-------|
| [DATA_MODELS.md](reference/DATA_MODELS.md) | All Mermaid ER diagrams | 250+ |
| [COMPLETE_AGENT_SETTINGS_CATALOG.md](reference/COMPLETE_AGENT_SETTINGS_CATALOG.md) | 100+ settings | 292 |
| API_ENDPOINTS.md | Complete API reference | TBD |
| TOOL_CATALOG.md | All 19 tools documented | TBD |

### Guides (4 docs)
| Document | Description | Lines |
|----------|-------------|-------|
| GETTING_STARTED.md | New developer onboarding | TBD |
| ADDING_NEW_ROUTER.md | How to add API endpoints | TBD |
| IMPLEMENTING_TOOLS.md | How to create tools | TBD |
| DEPLOYMENT_GUIDE.md | Production deployment | TBD |

### UI Integration (3 docs)
| Document | Description | Lines |
|----------|-------------|-------|
| [PERSONA_CAPSULES_TOOLS_UI.md](ui-integration/PERSONA_CAPSULES_TOOLS_UI.md) | Persona/Capsules/Tools UI | 450+ |
| [COMPLETE_AGENTSKIN_UIX_SPEC.md](ui-integration/COMPLETE_AGENTSKIN_UIX_SPEC.md) | AgentSkin complete spec | 840+ |
| WEBUI_PATTERNS.md | Alpine.js patterns | TBD |

---

## 🚀 FROM NOW ON: USE THIS STRUCTURE

**All new documentation must:**
1. ✅ Be saved in appropriate `docs/` subfolder
2. ✅ Include Mermaid diagrams for models/flows
3. ✅ Follow naming conventions
4. ✅ Be added to this index

**No more scattered docs!** Everything is organized in `docs/`.

---

**Total Docs:** 19 (10 complete, 9 TBD)  
**Total Lines:** ~3,500+ lines documented
