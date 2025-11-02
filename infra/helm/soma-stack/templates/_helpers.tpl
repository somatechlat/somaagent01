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

{{- define "soma-stack.imagePullSecrets" -}}
{{- $secrets := .Values.global.imagePullSecrets | default list -}}
{{- if $secrets }}
{{- range $s := $secrets }}
- name: {{ $s }}
{{- end }}
{{- end }}
{{- end -}}

{{- define "soma-stack.ingressAnnotations" -}}
{{- /* Merge a global cert-manager issuer annotation with service-specific annotations. */ -}}
{{- $root := .root -}}
{{- $svcAnns := .svcAnns | default dict -}}
{{- $base := dict -}}
{{- if $root.Values.global.CERT_MANAGER_CLUSTER_ISSUER }}
{{- $_ := set $base "cert-manager.io/cluster-issuer" $root.Values.global.CERT_MANAGER_CLUSTER_ISSUER -}}
{{- end -}}
{{- toYaml (merge $base $svcAnns) -}}
{{- end -}}
