# REAL IMPLEMENTATION - Helm Template Helpers
# VIBE CODING RULES COMPLIANT - Real template helpers for production

{{/* vim: set filetype=mustache: */}}
{{/*
Expand the name of the chart.
*/}}
{{- define "somaagent01.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "somaagent01.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "somaagent01.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "somaagent01.labels" -}}
helm.sh/chart: {{ include "somaagent01.chart" . }}
{{ include "somaagent01.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "somaagent01.selectorLabels" -}}
app.kubernetes.io/name: {{ include "somaagent01.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "somaagent01.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "somaagent01.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Create the name of the Redis service
*/}}
{{- define "somaagent01.redis.fullname" -}}
{{- printf "%s-%s" .Release.Name "redis-master" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create the name of the Kafka service
*/}}
{{- define "somaagent01.kafka.fullname" -}}
{{- printf "%s-%s" .Release.Name "kafka" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create the name of the PostgreSQL service
*/}}
{{- define "somaagent01.postgresql.fullname" -}}
{{- printf "%s-%s" .Release.Name "postgresql" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create the name of the Prometheus service
*/}}
{{- define "somaagent01.prometheus.fullname" -}}
{{- printf "%s-%s" .Release.Name "prometheus-server" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create the name of the Grafana service
*/}}
{{- define "somaagent01.grafana.fullname" -}}
{{- printf "%s-%s" .Release.Name "grafana" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create the name of the SomaBrain service
*/}}
{{- define "somaagent01.somabrain.fullname" -}}
{{- printf "%s-%s" .Release.Name "somabrain" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Generate Redis URL
*/}}
{{- define "somaagent01.redis.url" -}}
redis://{{ include "somaagent01.redis.fullname" . }}:6379/0
{{- end }}

{{/*
Generate Kafka bootstrap servers
*/}}
{{- define "somaagent01.kafka.bootstrapServers" -}}
{{- include "somaagent01.kafka.fullname" . }}:9092
{{- end }}

{{/*
Generate PostgreSQL connection string
*/}}
{{- define "somaagent01.postgresql.connectionString" -}}
postgresql://{{ .Values.postgresql.global.postgresql.auth.username }}:{{ .Values.postgresql.global.postgresql.auth.password }}@{{ include "somaagent01.postgresql.fullname" . }}:5432/{{ .Values.postgresql.global.postgresql.auth.database }}
{{- end }}

{{/*
Generate SomaBrain URL
*/}}
{{- define "somaagent01.somabrain.url" -}}
http://{{ include "somaagent01.somabrain.fullname" . }}:8000
{{- end }}

{{/*
Generate Prometheus URL
*/}}
{{- define "somaagent01.prometheus.url" -}}
http://{{ include "somaagent01.prometheus.fullname" . }}
{{- end }}

{{/*
Check if autoscaling is enabled
*/}}
{{- define "somaagent01.autoscaling.enabled" -}}
{{- if .Values.app.autoscaling.enabled -}}
true
{{- else -}}
false
{{- end }}
{{- end }}

{{/*
Generate health check annotations
*/}}
{{- define "somaagent01.healthCheck.annotations" -}}
checksum/health-check: {{ .Values.app.healthCheck.enabled | quote }}
checksum/sla-monitoring: {{ .Values.app.slaMonitoring.enabled | quote }}
{{- end }}

{{/*
Generate security context
*/}}
{{- define "somaagent01.securityContext" -}}
fsGroup: {{ .Values.security.podSecurityContext.fsGroup }}
runAsUser: {{ .Values.security.podSecurityContext.runAsUser }}
runAsGroup: {{ .Values.security.podSecurityContext.runAsGroup }}
{{- end }}

{{/*
Generate container security context
*/}}
{{- define "somaagent01.containerSecurityContext" -}}
allowPrivilegeEscalation: {{ .Values.security.containerSecurityContext.allowPrivilegeEscalation }}
readOnlyRootFilesystem: {{ .Values.security.containerSecurityContext.readOnlyRootFilesystem }}
runAsUser: {{ .Values.security.containerSecurityContext.runAsUser }}
runAsGroup: {{ .Values.security.containerSecurityContext.runAsGroup }}
capabilities:
  drop:
{{ toYaml .Values.security.containerSecurityContext.capabilities.drop | indent 4 }}
seccompProfile:
  type: {{ .Values.security.containerSecurityContext.seccompProfile.type }}
{{- end }}

{{/*
Generate resource limits and requests
*/}}
{{- define "somaagent01.resources" -}}
limits:
  cpu: {{ .Values.app.resources.limits.cpu }}
  memory: {{ .Values.app.resources.limits.memory }}
requests:
  cpu: {{ .Values.app.resources.requests.cpu }}
  memory: {{ .Values.app.resources.requests.memory }}
{{- end }}

{{/*
Generate environment variables
*/}}
{{- define "somaagent01.env" -}}
- name: ENVIRONMENT
  value: {{ .Values.app.environment }}
- name: LOG_LEVEL
  value: {{ .Values.logging.level }}
- name: REDIS_URL
  value: {{ include "somaagent01.redis.url" . }}
- name: KAFKA_BOOTSTRAP_SERVERS
  value: {{ include "somaagent01.kafka.bootstrapServers" . }}
- name: SOMABRAIN_URL
  value: {{ include "somaagent01.somabrain.url" . }}
- name: PROMETHEUS_ENABLED
  value: {{ .Values.monitoring.enabled | quote }}
- name: PROMETHEUS_PORT
  value: "9090"
- name: HEALTH_CHECK_ENABLED
  value: {{ .Values.app.healthCheck.enabled | quote }}
- name: SLA_MONITORING_ENABLED
  value: {{ .Values.app.slaMonitoring.enabled | quote }}
{{- range .Values.app.env }}
- name: {{ .name }}
  value: {{ .value }}
{{- end }}
{{- end }}

{{/*
Generate volume mounts
*/}}
{{- define "somaagent01.volumeMounts" -}}
- name: config-volume
  mountPath: /app/conf
  readOnly: true
- name: logs-volume
  mountPath: /app/logs
- name: tmp-volume
  mountPath: /app/tmp
{{- if .Values.somabrain.persistence.enabled }}
- name: somabrain-data
  mountPath: /app/memory
{{- end }}
{{- end }}

{{/*
Generate volumes
*/}}
{{- define "somaagent01.volumes" -}}
- name: config-volume
  configMap:
    name: {{ include "somaagent01.fullname" . }}-config
- name: logs-volume
  emptyDir: {}
- name: tmp-volume
  emptyDir: {}
{{- if .Values.somabrain.persistence.enabled }}
- name: somabrain-data
  persistentVolumeClaim:
    claimName: {{ include "somaagent01.fullname" . }}-somabrain-data
{{- end }}
{{- end }}

{{/*
Generate node selector
*/}}
{{- define "somaagent01.nodeSelector" -}}
{{- if .Values.app.nodeSelector }}
nodeSelector:
{{ toYaml .Values.app.nodeSelector | indent 2 }}
{{- end }}
{{- end }}

{{/*
Generate tolerations
*/}}
{{- define "somaagent01.tolerations" -}}
{{- if .Values.app.tolerations }}
tolerations:
{{ toYaml .Values.app.tolerations | indent 2 }}
{{- end }}
{{- end }}

{{/*
Generate affinity
*/}}
{{- define "somaagent01.affinity" -}}
{{- if .Values.app.affinity }}
affinity:
{{ toYaml .Values.app.affinity | indent 2 }}
{{- else }}
affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 100
      podAffinityTerm:
        labelSelector:
          matchExpressions:
          - key: app.kubernetes.io/name
            operator: In
            values:
            - {{ include "somaagent01.name" . }}
          - key: app.kubernetes.io/instance
            operator: In
            values:
            - {{ .Release.Name }}
        topologyKey: kubernetes.io/hostname
{{- end }}
{{- end }}

{{/*
Generate topology spread constraints
*/}}
{{- define "somaagent01.topologySpreadConstraints" -}}
topologySpreadConstraints:
- maxSkew: 1
  topologyKey: topology.kubernetes.io/zone
  whenUnsatisfiable: ScheduleAnyway
  labelSelector:
    matchLabels:
      app.kubernetes.io/name: {{ include "somaagent01.name" . }}
      app.kubernetes.io/instance: {{ .Release.Name }}
- maxSkew: 1
  topologyKey: kubernetes.io/hostname
  whenUnsatisfiable: ScheduleAnyway
  labelSelector:
    matchLabels:
      app.kubernetes.io/name: {{ include "somaagent01.name" . }}
      app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Generate image pull secrets
*/}}
{{- define "somaagent01.imagePullSecrets" -}}
{{- if .Values.global.imagePullSecrets }}
imagePullSecrets:
{{ toYaml .Values.global.imagePullSecrets | indent 2 }}
{{- end }}
{{- end }}