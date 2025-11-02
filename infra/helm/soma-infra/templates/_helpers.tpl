{{- /*
Helper template functions for the Soma Infra Helm chart.
Provides a standard naming convention for resources.
*/ -}}

{{- define "soma-infra.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}

{{- define "soma-infra.name" -}}
{{- default .Chart.Name .Values.nameOverride }}
{{- end }}

{{- define "soma-infra.labels" -}}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name (.Chart.Version | replace "+" "_") | quote }}
app.kubernetes.io/name: {{ include "soma-infra.name" . | quote }}
app.kubernetes.io/instance: {{ .Release.Name | quote }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service | quote }}
{{- end }}

{{- define "soma-infra.imagePullSecrets" -}}
{{- $secrets := .Values.imagePullSecrets | default list -}}
{{- if $secrets }}
{{- range $s := $secrets }}
- name: {{ $s | quote }}
{{- end }}
{{- end }}
{{- end -}}
