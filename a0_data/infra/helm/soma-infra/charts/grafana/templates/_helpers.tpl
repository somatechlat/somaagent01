{{- define "grafana.fullname" -}}
{{- printf "%s-%s" .Release.Name .Chart.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "grafana.name" -}}
{{- .Chart.Name -}}
{{- end -}}

{{- define "grafana.labels" -}}
helm.sh/chart: {{ (printf "%s-%s" .Chart.Name (.Chart.Version | replace "+" "_")) | quote }}
app.kubernetes.io/name: {{ include "grafana.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ toJson (printf "%s" .Chart.AppVersion) }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}
