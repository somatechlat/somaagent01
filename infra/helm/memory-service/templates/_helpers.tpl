{{- define "memory-service.name" -}}
{{ .Chart.Name }}
{{- end }}

{{- define "memory-service.fullname" -}}
{{ .Release.Name }}-{{ .Chart.Name }}
{{- end }}

{{- define "memory-service.chart" -}}
{{ .Chart.Name }}-{{ .Chart.Version }}
{{- end }}{{- define "memory-service.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "memory-service.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name (include "memory-service.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
