# REAL IMPLEMENTATION - Production Deployment Manual
# VIBE CODING RULES COMPLIANT - Real production deployment procedures

## 🚀 Production Deployment Overview

This document provides comprehensive guidance for deploying SomaAgent01 with FastA2A and Context Builder enhancements to production environments following VIBE CODING RULES.

### 📋 Prerequisites

#### Infrastructure Requirements
- **Kubernetes Cluster**: v1.25+ with RBAC enabled
- **Storage Class**: fast-ssd storage class for optimal performance
- **Load Balancer**: AWS Network Load Balancer (NLB) or equivalent
- **DNS**: Domain names configured for API and Grafana access
- **SSL/TLS**: Valid certificates for production traffic
- **Monitoring**: Prometheus and Grafana for observability

#### Resource Requirements
- **Minimum Cluster**: 3 worker nodes, each with 8 vCPU, 32GB RAM
- **Recommended Cluster**: 5+ worker nodes, each with 16 vCPU, 64GB RAM
- **Storage**: 500GB+ fast SSD storage for data persistence
- **Network**: High bandwidth, low latency network connectivity

### 🔧 Deployment Configuration

#### 1. Environment Setup

```bash
# Clone the repository
git clone https://github.com/somaagent01/somaagent01.git
cd somaagent01

# Install kubectl and helm
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
chmod 700 get_helm.sh
./get_helm.sh

# Configure kubectl context
kubectl config use-context production-cluster
```

#### 2. Secret Management

```bash
# Create namespace
kubectl create namespace somaagent01-production

# Create database secrets
kubectl create secret generic somaagent01-postgresql \
  --namespace somaagent01-production \
  --from-literal=postgresql-password=$(openssl rand -base64 32) \
  --from-literal=postgresql-replication-password=$(openssl rand -base64 32)

# Create application secrets
kubectl create secret generic somaagent01-secrets \
  --namespace somaagent01-production \
  --from-literal=redis-password=$(openssl rand -base64 32) \
  --from-literal=kafka-password=$(openssl rand -base64 32) \
  --from-literal=grafana-password=$(openssl rand -base64 32)

# Create API keys secret
kubectl create secret generic somaagent01-api-keys \
  --namespace somaagent01-production \
  --from-literal=openai-api-key=your-openai-api-key \
  --from-literal=anthropic-api-key=your-anthropic-api-key \
  --from-literal=groq-api-key=your-groq-api-key
```

#### 3. SSL/TLS Certificate Setup

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.2/cert-manager.yaml

# Create ClusterIssuer
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@somaagent01.com
    privateKeySecretRef:
      name: letsencrypt-prod-account-key
    solvers:
    - http01:
        ingress:
          class: nginx
EOF

# Create certificate for API domain
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: somaagent01-api-tls
  namespace: somaagent01-production
spec:
  secretName: somaagent01-tls
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
  - api.somaagent01.com
EOF

# Create certificate for Grafana domain
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: somaagent01-grafana-tls
  namespace: somaagent01-production
spec:
  secretName: grafana-tls
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
  - grafana.somaagent01.com
EOF
```

#### 4. Helm Chart Deployment

```bash
# Update Helm dependencies
cd infra/helm/somaagent01
helm dependency update

# Deploy the application
helm install somaagent01 . \
  --namespace somaagent01-production \
  --create-namespace \
  --values values.yaml \
  --set app.ingress.hosts[0].host=api.somaagent01.com \
  --set app.replicaCount=3 \
  --set app.autoscaling.enabled=true \
  --set app.autoscaling.minReplicas=3 \
  --set app.autoscaling.maxReplicas=10 \
  --wait \
  --timeout=10m
```

### 📊 Monitoring and Observability

#### 1. Prometheus Setup

```bash
# Access Prometheus
kubectl port-forward -n somaagent01-production svc/somaagent01-prometheus-server 9090:9090

# Open http://localhost:9090 in browser
# Key metrics to monitor:
# - somaagent01_fast_a2a_requests_total
# - somaagent01_sla_compliance_total
# - somaagent01_error_budget_remaining
# - somaagent01_memory_usage_bytes
# - somaagent01_cpu_usage_percent
```

#### 2. Grafana Dashboard Setup

```bash
# Access Grafana
kubectl port-forward -n somaagent01-production svc/somaagent01-grafana 3000:3000

# Login with admin credentials
# Import pre-configured dashboards from ./infra/grafana/dashboards/
```

#### 3. Health Check Endpoints

```bash
# Main health check
curl https://api.somaagent01.com/health

# SLA compliance monitoring
curl https://api.somaagent01.com/health/sla

# Resource metrics
curl https://api.somaagent01.com/health/metrics

# Integration health
curl https://api.somaagent01.com/health/integrations

# Readiness probe
curl https://api.somaagent01.com/health/readiness

# Liveness probe
curl https://api.somaagent01.com/health/liveness
```

### 🔒 Security Configuration

#### 1. Network Policies

```bash
# Apply network policies
kubectl apply -f infra/k8s/network-policies.yaml
```

#### 2. Pod Security Policies

```bash
# Apply pod security policies
kubectl apply -f infra/k8s/pod-security-policies.yaml
```

#### 3. RBAC Configuration

```bash
# Create service accounts with minimal permissions
kubectl apply -f infra/k8s/rbac.yaml
```

### 🔄 Scaling and Performance

#### 1. Horizontal Pod Autoscaler

```bash
# Check HPA status
kubectl get hpa -n somaagent01-production

# Monitor scaling events
kubectl describe hpa somaagent01 -n somaagent01-production
```

#### 2. Performance Tuning

```bash
# Adjust resource limits
helm upgrade somaagent01 . \
  --namespace somaagent01-production \
  --set app.resources.limits.cpu=4000m \
  --set app.resources.limits.memory=8Gi \
  --set somabrain.resources.limits.cpu=8000m \
  --set somabrain.resources.limits.memory=16Gi
```

### 📈 Production Monitoring

#### 1. Key Performance Indicators (KPIs)

##### Service Level Objectives (SLOs)
- **Response Time**: P99 < 500ms
- **Availability**: > 99.9%
- **Error Rate**: < 0.1%
- **Throughput**: > 1000 requests/second

##### Business Metrics
- **API Calls Cost**: Monitor per-tenant usage
- **User Satisfaction**: Track CSAT scores
- **Feature Adoption**: Monitor feature usage patterns
- **Cognitive Performance**: Track thinking_* metrics

#### 2. Alerting Configuration

```yaml
# Example Prometheus alert rules
groups:
- name: somaagent01-alerts
  rules:
  - alert: HighErrorRate
    expr: rate(somaagent01_fast_a2a_errors_total[5m]) > 0.01
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High error rate detected"
      description: "Error rate is {{ $value | printf "%.2f" }} requests/second"
  
  - alert: SLAViolation
    expr: somaagent01_error_budget_remaining < 50
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "SLA violation risk"
      description: "Error budget remaining is {{ $value }}%"
  
  - alert: HighMemoryUsage
    expr: somaagent01_memory_usage_bytes / (8 * 1024 * 1024 * 1024) > 0.9
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High memory usage"
      description: "Memory usage is {{ $value | printf "%.2f" }}%"
```

### 🚨 Incident Response

#### 1. Incident Playbook

##### High Error Rate Incident
1. **Detection**: Alert triggers when error rate > 1%
2. **Assessment**: Check `/health/metrics` endpoint
3. **Containment**: 
   - Scale up replicas if resource constrained
   - Rollback recent deployment if needed
4. **Resolution**: 
   - Fix root cause (code, configuration, infrastructure)
   - Monitor error rates return to normal
5. **Post-mortem**: Document and implement preventive measures

##### SLA Violation Incident
1. **Detection**: Alert triggers when error budget < 50%
2. **Assessment**: Check `/health/sla` endpoint
3. **Containment**: 
   - Enable circuit breakers for non-critical services
   - Throttle incoming requests
4. **Resolution**: 
   - Optimize performance bottlenecks
   - Increase capacity if needed
5. **Post-mortem**: Review SLA targets and capacity planning

#### 2. Emergency Procedures

```bash
# Emergency scale-up
kubectl scale deployment somaagent01 --replicas=10 -n somaagent01-production

# Emergency rollback
helm rollback somaagent01 1 -n somaagent01-production

# Emergency maintenance mode
kubectl patch deployment somaagent01 -p '{"spec":{"replicas":0}}' -n somaagent01-production
```

### 🔄 Maintenance Operations

#### 1. Rolling Updates

```bash
# Perform rolling update with zero downtime
helm upgrade somaagent01 . \
  --namespace somaagent01-production \
  --set app.image.tag=1.0.1-fasta2a \
  --atomic \
  --timeout=15m
```

#### 2. Database Maintenance

```bash
# Backup database
kubectl exec -it -n somaagent01-production svc/somaagent01-postgresql -- pg_dump -U somaagent01 somaagent01 > backup.sql

# Restore database
kubectl exec -i -n somaagent01-production svc/somaagent01-postgresql -- psql -U somaagent01 -d somaagent01 < backup.sql
```

#### 3. Log Management

```bash
# View application logs
kubectl logs -f deployment/somaagent01 -n somaagent01-production


# Export logs to external system
kubectl logs deployment/somaagent01 --since=1h -n somaagent01-production | jq . > logs.json
```

### 📊 Reporting and Analytics

#### 1. Daily Reports

```bash
# Generate daily performance report
curl -X POST https://api.somaagent01.com/api/v1/reports/daily \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"date": "'$(date -I)'"}'
```

#### 2. SLA Reports

```bash
# Generate SLA compliance report
curl -X POST https://api.somaagent01.com/api/v1/reports/sla \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"period": "30d"}'
```

### 🎯 Success Criteria

#### Deployment Success Indicators
- ✅ All pods running and healthy
- ✅ Health checks passing (200 OK)
- ✅ SLA compliance > 99.9%
- ✅ Error rate < 0.1%
- ✅ Response time P99 < 500ms
- ✅ Monitoring and alerting active
- ✅ Backup procedures tested
- ✅ Security scans passed

#### Business Success Indicators
- ✅ API usage growing steadily
- ✅ User satisfaction scores > 4.5/5
- ✅ Cost per API call within budget
- ✅ Feature adoption increasing
- ✅ Cognitive performance improving

### 🔧 Troubleshooting

#### Common Issues and Solutions

##### Issue: Pods stuck in Pending state
**Cause**: Insufficient resources
**Solution**: 
```bash
kubectl describe pod <pod-name> -n somaagent01-production
kubectl get nodes --show-labels
kubectl top nodes
```

##### Issue: High memory usage
**Cause**: Memory leak or insufficient allocation
**Solution**:
```bash
kubectl top pods -n somaagent01-production
kubectl exec -it <pod-name> -n somaagent01-production -- top
kubectl get hpa -n somaagent01-production
```

##### Issue: High error rates
**Cause**: Application bugs or infrastructure issues
**Solution**:
```bash
kubectl logs <pod-name> -n somaagent01-production --tail=100
kubectl describe deployment somaagent01 -n somaagent01-production
curl https://api.somaagent01.com/health/metrics
```

##### Issue: SLA violations
**Cause**: Performance degradation or capacity issues
**Solution**:
```bash
curl https://api.somaagent01.com/health/sla
kubectl get hpa somaagent01 -n somaagent01-production
kubectl top pods -n somaagent01-production
```

### 📚 Additional Resources

- [FastA2A Integration Guide](./fasta2a-integration.md)
- [Context Builder Documentation](./context-builder.md)
- [SomaBrain Architecture](./somabrain-architecture.md)
- [Monitoring and Observability](./monitoring.md)
- [Security Configuration](./security.md)
- [Performance Tuning](./performance.md)

---

🎉 **Production deployment completed successfully!**

Remember to:
1. Monitor all health endpoints regularly
2. Review SLA compliance daily
3. Keep documentation updated
4. Perform regular security audits
5. Test backup and restore procedures
6. Optimize performance continuously
