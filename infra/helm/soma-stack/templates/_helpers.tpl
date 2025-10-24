{{- define "soma-stack.fullname" -}}
{{- printf "%s-%s" .Release.Name "soma" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "soma-stack.saName" -}}
{{- if .Values.serviceAccounts.create -}}
{{- include "soma-stack.fullname" . -}}
{{- else -}}
default
{{- end -}}
{{- end -}}

{{- define "soma-stack.annotations" -}}
{{- $g := .Values.global -}}
{{- $anns := dict -}}
{{- if $g.ISTIO_INJECTION }}
{{- $_ := set $anns "sidecar.istio.io/inject" (ternary "true" "false" $g.ISTIO_INJECTION) -}}
{{- end -}}
{{- if $g.VAULT_AGENT_INJECT }}
{{- $_ := set $anns "vault.hashicorp.com/agent-inject" (ternary "true" "false" $g.VAULT_AGENT_INJECT) -}}
{{- end -}}
{{- toYaml $anns -}}
{{- end -}}
