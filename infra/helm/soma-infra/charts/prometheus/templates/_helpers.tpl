{{- define "prometheus.fullname" -}}
{{- printf "%s-%s" .Release.Name .Chart.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "prometheus.name" -}}
{{- .Chart.Name -}}
{{- end -}}

{{- define "prometheus.labels" -}}
helm.sh/chart: {{ (printf "%s-%s" .Chart.Name (.Chart.Version | replace "+" "_")) | quote }}
app.kubernetes.io/name: {{ include "prometheus.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ printf "%s" .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}
