{{- define "outbox-sync.fullname" -}}
{{- printf "%s-%s" .Release.Name "outbox-sync" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "outbox-sync.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
{{- default (include "outbox-sync.fullname" .) .Values.serviceAccount.name -}}
{{- else -}}
{{- default "default" .Values.serviceAccount.name -}}
{{- end -}}
{{- end -}}
