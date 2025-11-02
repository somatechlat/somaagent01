{{- define "etcd.fullname" -}}
{{- printf "%s-%s" .Release.Name .Chart.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "etcd.name" -}}
{{- .Chart.Name -}}
{{- end -}}

{{- define "etcd.labels" -}}
helm.sh/chart: {{ (printf "%s-%s" .Chart.Name (.Chart.Version | replace "+" "_")) | quote }}
app.kubernetes.io/name: {{ include "etcd.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}
