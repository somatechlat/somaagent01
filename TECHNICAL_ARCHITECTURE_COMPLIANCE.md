# Technical Architecture for 100% Compliance
## System Design & Implementation Details

---

## 1. Model Governance Service

### Architecture
```
services/model_governance/
├── __init__.py
├── models.py                 # SQLAlchemy models
├── registry.py               # Model registry logic
├── versioning.py             # Version management
├── validation.py             # Validation framework
├── performance.py            # Performance tracking
├── lifecycle.py              # Lifecycle management
├── schemas.py                # Pydantic schemas
└── routes.py                 # FastAPI endpoints
```

### Database Schema
```python
# models.py
from sqlalchemy import Column, String, DateTime, JSON, Enum
from sqlalchemy.dialects.postgresql import UUID
import uuid

class Model(Base):
    __tablename__ = "models"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    version = Column(String, nullable=False)  # semantic versioning
    provider = Column(String, nullable=False)  # openai, anthropic, groq, etc.
    status = Column(Enum(ModelStatus), default=ModelStatus.DRAFT)
    
    # Metadata
    capabilities = Column(JSON)  # vision, reasoning, etc.
    limitations = Column(JSON)   # known limitations
    training_data = Column(JSON) # training data documentation
    performance_baseline = Column(JSON)  # baseline metrics
    
    # Lifecycle
    created_at = Column(DateTime, default=datetime.utcnow)
    validated_at = Column(DateTime, nullable=True)
    deployed_at = Column(DateTime, nullable=True)
    deprecated_at = Column(DateTime, nullable=True)
    
    # Governance
    owner_id = Column(String)
    approval_status = Column(Enum(ApprovalStatus))
    approval_notes = Column(String)

class ModelVersion(Base):
    __tablename__ = "model_versions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id = Column(UUID, ForeignKey("models.id"))
    version = Column(String)
    changes = Column(JSON)  # changelog
    created_at = Column(DateTime, default=datetime.utcnow)

class ModelPerformance(Base):
    __tablename__ = "model_performance"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id = Column(UUID, ForeignKey("models.id"))
    metric_name = Column(String)  # accuracy, latency, cost, etc.
    metric_value = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON)  # additional context
```

### API Endpoints
```python
# routes.py
from fastapi import APIRouter, HTTPException, Depends
from typing import List

router = APIRouter(prefix="/v1/admin/models", tags=["model-governance"])

@router.post("/register")
async def register_model(model: ModelCreate, current_user = Depends(get_current_admin)):
    """Register a new model"""
    # Validate model metadata
    # Create model record
    # Generate model card
    # Return model ID

@router.get("/{model_id}")
async def get_model(model_id: str):
    """Get model details"""
    # Return model metadata, status, performance

@router.get("/{model_id}/performance")
async def get_model_performance(model_id: str, days: int = 30):
    """Get model performance metrics"""
    # Return performance trends

@router.post("/{model_id}/validate")
async def validate_model(model_id: str, validation_data: ValidationRequest):
    """Validate model against requirements"""
    # Run validation tests
    # Update validation status
    # Return validation report

@router.post("/{model_id}/deploy")
async def deploy_model(model_id: str, deployment_config: DeploymentConfig):
    """Deploy model to production"""
    # Check approval status
    # Deploy model
    # Update status
    # Log deployment

@router.post("/{model_id}/deprecate")
async def deprecate_model(model_id: str, reason: str):
    """Deprecate a model"""
    # Mark as deprecated
    # Notify users
    # Log deprecation
```

---

## 2. Fairness & Bias Detection Service

### Architecture
```
services/fairness/
├── __init__.py
├── metrics.py                # Fairness metrics
├── detector.py               # Bias detection
├── testing.py                # Fairness testing
├── reporting.py              # Report generation
├── schemas.py                # Pydantic schemas
└── routes.py                 # FastAPI endpoints
```

### Fairness Metrics Implementation
```python
# metrics.py
import numpy as np
from typing import Dict, List

class FairnessMetrics:
    @staticmethod
    def demographic_parity(predictions: List[int], groups: List[str]) -> Dict:
        """
        Calculate demographic parity (equal selection rates across groups)
        """
        results = {}
        for group in set(groups):
            group_mask = np.array(groups) == group
            selection_rate = np.mean(np.array(predictions)[group_mask])
            results[group] = selection_rate
        
        # Calculate disparities
        rates = list(results.values())
        max_rate = max(rates)
        min_rate = min(rates)
        disparity = max_rate - min_rate
        
        return {
            "selection_rates": results,
            "disparity": disparity,
            "compliant": disparity < 0.1  # 10% threshold
        }
    
    @staticmethod
    def equalized_odds(y_true: List[int], y_pred: List[int], groups: List[str]) -> Dict:
        """
        Calculate equalized odds (equal TPR and FPR across groups)
        """
        results = {}
        for group in set(groups):
            group_mask = np.array(groups) == group
            y_true_group = np.array(y_true)[group_mask]
            y_pred_group = np.array(y_pred)[group_mask]
            
            tp = np.sum((y_true_group == 1) & (y_pred_group == 1))
            fp = np.sum((y_true_group == 0) & (y_pred_group == 1))
            fn = np.sum((y_true_group == 1) & (y_pred_group == 0))
            tn = np.sum((y_true_group == 0) & (y_pred_group == 0))
            
            tpr = tp / (tp + fn) if (tp + fn) > 0 else 0
            fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
            
            results[group] = {"tpr": tpr, "fpr": fpr}
        
        return results
    
    @staticmethod
    def disparate_impact_ratio(predictions: List[int], groups: List[str]) -> Dict:
        """
        Calculate disparate impact ratio (80% rule)
        """
        results = {}
        selection_rates = {}
        
        for group in set(groups):
            group_mask = np.array(groups) == group
            selection_rate = np.mean(np.array(predictions)[group_mask])
            selection_rates[group] = selection_rate
        
        # Calculate ratios
        reference_rate = max(selection_rates.values())
        for group, rate in selection_rates.items():
            ratio = rate / reference_rate if reference_rate > 0 else 1.0
            results[group] = {
                "selection_rate": rate,
                "ratio": ratio,
                "compliant": ratio >= 0.8  # 80% rule
            }
        
        return results
```

### Bias Detection Routes
```python
# routes.py
@router.post("/assess")
async def assess_fairness(assessment: FairnessAssessment):
    """Assess fairness of model predictions"""
    metrics = FairnessMetrics()
    
    results = {
        "demographic_parity": metrics.demographic_parity(
            assessment.predictions, assessment.groups
        ),
        "equalized_odds": metrics.equalized_odds(
            assessment.y_true, assessment.predictions, assessment.groups
        ),
        "disparate_impact": metrics.disparate_impact_ratio(
            assessment.predictions, assessment.groups
        )
    }
    
    # Store results
    # Generate report
    # Return results
    return results

@router.get("/report/{model_id}")
async def get_fairness_report(model_id: str):
    """Get fairness assessment report for model"""
    # Retrieve stored assessments
    # Generate report
    # Return report
```

---

## 3. Reasoning Trace System

### Architecture
```
services/explainability/
├── __init__.py
├── tracer.py                 # Trace collection
├── exporter.py               # Trace export
├── explainer.py              # Decision explanation
├── storage.py                # Trace storage
├── schemas.py                # Pydantic schemas
└── routes.py                 # FastAPI endpoints
```

### Trace Collection
```python
# tracer.py
from typing import Dict, Any, List
from datetime import datetime
import json

class ReasoningTracer:
    def __init__(self, session_id: str, decision_id: str):
        self.session_id = session_id
        self.decision_id = decision_id
        self.traces: List[Dict[str, Any]] = []
        self.start_time = datetime.utcnow()
    
    def add_step(self, step_type: str, content: Dict[str, Any]):
        """Add a reasoning step"""
        self.traces.append({
            "timestamp": datetime.utcnow().isoformat(),
            "type": step_type,  # input, model_selection, reasoning, output
            "content": content
        })
    
    def add_model_selection(self, model_id: str, rationale: str, alternatives: List[str]):
        """Record model selection decision"""
        self.add_step("model_selection", {
            "selected_model": model_id,
            "rationale": rationale,
            "alternatives": alternatives
        })
    
    def add_reasoning_step(self, step_number: int, reasoning: str, confidence: float):
        """Record reasoning step"""
        self.add_step("reasoning", {
            "step": step_number,
            "reasoning": reasoning,
            "confidence": confidence
        })
    
    def add_output(self, output: str, confidence: float, alternatives: List[str]):
        """Record final output"""
        self.add_step("output", {
            "output": output,
            "confidence": confidence,
            "alternatives": alternatives
        })
    
    def finalize(self) -> Dict[str, Any]:
        """Finalize trace"""
        return {
            "session_id": self.session_id,
            "decision_id": self.decision_id,
            "start_time": self.start_time.isoformat(),
            "end_time": datetime.utcnow().isoformat(),
            "traces": self.traces
        }
```

### Trace Storage
```python
# storage.py
from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid

class ReasoningTrace(Base):
    __tablename__ = "reasoning_traces"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID)
    decision_id = Column(UUID)
    trace_data = Column(JSON)  # Full trace
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexing for fast retrieval
    __table_args__ = (
        Index('idx_session_id', 'session_id'),
        Index('idx_decision_id', 'decision_id'),
    )
```

### Explainability Routes
```python
# routes.py
@router.get("/sessions/{session_id}/reasoning")
async def get_session_reasoning(session_id: str):
    """Get reasoning traces for session"""
    traces = db.query(ReasoningTrace).filter(
        ReasoningTrace.session_id == session_id
    ).all()
    return [t.trace_data for t in traces]

@router.get("/decisions/{decision_id}/explanation")
async def get_decision_explanation(decision_id: str):
    """Get explanation for specific decision"""
    trace = db.query(ReasoningTrace).filter(
        ReasoningTrace.decision_id == decision_id
    ).first()
    
    if not trace:
        raise HTTPException(status_code=404)
    
    # Generate human-readable explanation
    explanation = generate_explanation(trace.trace_data)
    return explanation

def generate_explanation(trace_data: Dict) -> str:
    """Generate human-readable explanation from trace"""
    explanation = []
    
    for step in trace_data["traces"]:
        if step["type"] == "model_selection":
            explanation.append(
                f"Selected model: {step['content']['selected_model']} "
                f"because {step['content']['rationale']}"
            )
        elif step["type"] == "reasoning":
            explanation.append(
                f"Step {step['content']['step']}: {step['content']['reasoning']} "
                f"(confidence: {step['content']['confidence']:.2%})"
            )
        elif step["type"] == "output":
            explanation.append(
                f"Final decision: {step['content']['output']} "
                f"(confidence: {step['content']['confidence']:.2%})"
            )
    
    return "\n".join(explanation)
```

---

## 4. Risk Management Service

### Database Schema
```python
# models.py
class Risk(Base):
    __tablename__ = "risks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category = Column(String)  # security, performance, fairness, etc.
    description = Column(String)
    likelihood = Column(Integer)  # 1-5
    impact = Column(Integer)  # 1-5
    risk_score = Column(Integer)  # likelihood * impact
    status = Column(Enum(RiskStatus))  # identified, mitigating, mitigated, accepted
    
    # Mitigation
    mitigation_strategy = Column(String)
    mitigation_owner = Column(String)
    mitigation_deadline = Column(DateTime)
    mitigation_status = Column(String)
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
```

### Risk Assessment Routes
```python
# routes.py
@router.post("/risks")
async def create_risk(risk: RiskCreate):
    """Create new risk"""
    risk_score = risk.likelihood * risk.impact
    db_risk = Risk(
        category=risk.category,
        description=risk.description,
        likelihood=risk.likelihood,
        impact=risk.impact,
        risk_score=risk_score,
        status=RiskStatus.IDENTIFIED
    )
    db.add(db_risk)
    db.commit()
    return db_risk

@router.get("/risks")
async def list_risks(category: str = None, status: str = None):
    """List risks with filtering"""
    query = db.query(Risk)
    if category:
        query = query.filter(Risk.category == category)
    if status:
        query = query.filter(Risk.status == status)
    return query.order_by(Risk.risk_score.desc()).all()

@router.post("/risks/{risk_id}/mitigate")
async def mitigate_risk(risk_id: str, mitigation: MitigationPlan):
    """Create mitigation plan for risk"""
    risk = db.query(Risk).filter(Risk.id == risk_id).first()
    risk.mitigation_strategy = mitigation.strategy
    risk.mitigation_owner = mitigation.owner
    risk.mitigation_deadline = mitigation.deadline
    risk.status = RiskStatus.MITIGATING
    db.commit()
    return risk
```

---

## 5. Incident Management Service

### Database Schema
```python
class Incident(Base):
    __tablename__ = "incidents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(String)  # security, performance, data, compliance, operational
    severity = Column(Enum(Severity))  # critical, high, medium, low
    title = Column(String)
    description = Column(String)
    status = Column(Enum(IncidentStatus))  # open, investigating, resolved, closed
    
    # Timeline
    created_at = Column(DateTime, default=datetime.utcnow)
    detected_at = Column(DateTime)
    resolved_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    
    # Escalation
    escalation_level = Column(Integer)  # 1-3
    escalated_to = Column(String)
    escalation_reason = Column(String)
    
    # Post-Incident
    root_cause = Column(String)
    lessons_learned = Column(String)
    preventive_measures = Column(JSON)
```

### Incident Routes
```python
# routes.py
@router.post("/incidents")
async def create_incident(incident: IncidentCreate):
    """Create new incident"""
    db_incident = Incident(
        type=incident.type,
        severity=incident.severity,
        title=incident.title,
        description=incident.description,
        status=IncidentStatus.OPEN,
        detected_at=datetime.utcnow()
    )
    db.add(db_incident)
    db.commit()
    
    # Trigger escalation if needed
    if incident.severity in [Severity.CRITICAL, Severity.HIGH]:
        escalate_incident(db_incident)
    
    return db_incident

@router.post("/incidents/{incident_id}/resolve")
async def resolve_incident(incident_id: str, resolution: IncidentResolution):
    """Resolve incident"""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    incident.status = IncidentStatus.RESOLVED
    incident.resolved_at = datetime.utcnow()
    incident.root_cause = resolution.root_cause
    db.commit()
    return incident

@router.post("/incidents/{incident_id}/postmortem")
async def create_postmortem(incident_id: str, postmortem: PostmortemData):
    """Create post-incident review"""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    incident.lessons_learned = postmortem.lessons_learned
    incident.preventive_measures = postmortem.preventive_measures
    incident.status = IncidentStatus.CLOSED
    incident.closed_at = datetime.utcnow()
    db.commit()
    return incident
```

---

## 6. Data Governance Service

### Database Schema
```python
class DataAsset(Base):
    __tablename__ = "data_assets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String)
    classification = Column(Enum(DataClassification))  # public, internal, confidential, restricted
    owner = Column(String)
    retention_period = Column(Integer)  # days
    deletion_policy = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime)
    scheduled_deletion = Column(DateTime, nullable=True)
```

### Data Governance Routes
```python
# routes.py
@router.post("/data-assets")
async def register_data_asset(asset: DataAssetCreate):
    """Register data asset"""
    db_asset = DataAsset(
        name=asset.name,
        classification=asset.classification,
        owner=asset.owner,
        retention_period=asset.retention_period,
        deletion_policy=asset.deletion_policy
    )
    db.add(db_asset)
    db.commit()
    return db_asset

@router.get("/data-assets")
async def list_data_assets(classification: str = None):
    """List data assets"""
    query = db.query(DataAsset)
    if classification:
        query = query.filter(DataAsset.classification == classification)
    return query.all()

@router.post("/data-assets/{asset_id}/schedule-deletion")
async def schedule_deletion(asset_id: str):
    """Schedule data asset for deletion"""
    asset = db.query(DataAsset).filter(DataAsset.id == asset_id).first()
    asset.scheduled_deletion = datetime.utcnow() + timedelta(days=asset.retention_period)
    db.commit()
    return asset
```

---

## 7. Compliance Dashboard Service

### Metrics Collection
```python
# metrics.py
from prometheus_client import Gauge, Counter

# Compliance metrics
compliance_score = Gauge('compliance_score', 'Overall compliance score', ['control'])
audit_findings = Counter('audit_findings', 'Number of audit findings', ['severity'])
remediation_rate = Gauge('remediation_rate', 'Remediation completion rate')

# Fairness metrics
fairness_score = Gauge('fairness_score', 'Fairness score', ['model_id'])
bias_detected = Counter('bias_detected', 'Bias detection events', ['model_id'])

# Security metrics
vulnerabilities = Gauge('vulnerabilities', 'Number of vulnerabilities', ['severity'])
security_incidents = Counter('security_incidents', 'Security incidents', ['type'])

# Performance metrics
model_accuracy = Gauge('model_accuracy', 'Model accuracy', ['model_id'])
model_latency = Gauge('model_latency', 'Model latency', ['model_id'])
```

### Dashboard Routes
```python
# routes.py
@router.get("/compliance/status")
async def get_compliance_status():
    """Get overall compliance status"""
    return {
        "overall_score": calculate_compliance_score(),
        "controls": get_control_status(),
        "audit_findings": get_audit_findings(),
        "remediation_rate": get_remediation_rate()
    }

@router.get("/compliance/matrix")
async def get_compliance_matrix():
    """Get compliance matrix"""
    return {
        "iso_iec_controls": get_iso_controls_status(),
        "oecd_principles": get_oecd_principles_status()
    }

@router.get("/compliance/audit-schedule")
async def get_audit_schedule():
    """Get audit schedule"""
    return get_scheduled_audits()
```

---

## 8. Integration Points

### LLM Call Instrumentation
```python
# In conversation worker
from services.explainability.tracer import ReasoningTracer

async def invoke_llm(prompt, model_id, session_id, decision_id):
    tracer = ReasoningTracer(session_id, decision_id)
    
    # Record model selection
    tracer.add_model_selection(
        model_id=model_id,
        rationale="Selected based on task requirements",
        alternatives=["model_b", "model_c"]
    )
    
    # Call LLM
    response = await llm_client.invoke(prompt, model=model_id)
    
    # Record output
    tracer.add_output(
        output=response.text,
        confidence=response.confidence,
        alternatives=response.alternatives
    )
    
    # Store trace
    trace_data = tracer.finalize()
    store_reasoning_trace(trace_data)
    
    return response
```

### Audit Trail Integration
```python
# In audit store
async def log_compliance_event(event_type, details):
    """Log compliance-related events"""
    await audit_store.log(
        action=f"compliance.{event_type}",
        resource="compliance",
        details=details,
        subject=get_current_user()
    )
```

---

## 9. Deployment Architecture

### Kubernetes Manifests
```yaml
# services/model_governance/k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: model-governance-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: model-governance
  template:
    metadata:
      labels:
        app: model-governance
    spec:
      containers:
      - name: model-governance
        image: somaagent01/model-governance:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

---

## 10. Testing Strategy

### Unit Tests
```python
# tests/unit/test_fairness_metrics.py
def test_demographic_parity():
    predictions = [1, 1, 0, 0, 1, 0]
    groups = ['A', 'A', 'B', 'B', 'A', 'B']
    
    result = FairnessMetrics.demographic_parity(predictions, groups)
    
    assert result['selection_rates']['A'] == 2/3
    assert result['selection_rates']['B'] == 1/3
    assert result['compliant'] == False

# tests/unit/test_reasoning_tracer.py
def test_reasoning_tracer():
    tracer = ReasoningTracer("session-1", "decision-1")
    tracer.add_model_selection("model-1", "best fit", ["model-2"])
    tracer.add_reasoning_step(1, "analyzing input", 0.95)
    
    trace = tracer.finalize()
    
    assert len(trace['traces']) == 2
    assert trace['session_id'] == "session-1"
```

### Integration Tests
```python
# tests/integration/test_compliance_flow.py
@pytest.mark.asyncio
async def test_end_to_end_compliance():
    # Register model
    model = await register_model(...)
    
    # Assess fairness
    fairness = await assess_fairness(...)
    
    # Create risk
    risk = await create_risk(...)
    
    # Verify compliance score updated
    compliance = await get_compliance_status()
    assert compliance['overall_score'] > 0
```

---

## Conclusion

This technical architecture provides:
- **Modular design** for independent deployment
- **Scalable infrastructure** using Kubernetes
- **Comprehensive data models** for compliance tracking
- **RESTful APIs** for integration
- **Monitoring and metrics** for continuous compliance
- **Testing framework** for quality assurance

Implementation follows **microservices best practices** and integrates seamlessly with existing SomaAgent01 infrastructure.
