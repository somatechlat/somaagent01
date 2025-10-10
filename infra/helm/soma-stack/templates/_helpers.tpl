{{- define "soma-stack.name" -}}
{{ .Chart.Name }}
{{- end }}

{{- define "soma-stack.fullname" -}}
{{ .Release.Name }}-{{ .Chart.Name }}
{{- end }}

{{- define "soma-stack.chart" -}}
{{ .Chart.Name }}-{{ .Chart.Version }}
{{- end }}