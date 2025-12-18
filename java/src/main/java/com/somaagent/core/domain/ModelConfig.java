package com.somaagent.core.domain;

import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

import java.util.HashMap;
import java.util.Map;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ModelConfig {
    private ModelType type;
    private String provider;
    private String name;

    @Builder.Default
    private String apiBase = "";

    @Builder.Default
    private int ctxLength = 0;

    @Builder.Default
    private int limitRequests = 0;

    @Builder.Default
    private int limitInput = 0;

    @Builder.Default
    private int limitOutput = 0;

    @Builder.Default
    private boolean vision = false;

    @Builder.Default
    private Map<String, Object> kwargs = new HashMap<>();

    public Map<String, Object> buildKwargs() {
        Map<String, Object> mergedKwargs = new HashMap<>(kwargs);
        if (apiBase != null && !apiBase.isEmpty() && !mergedKwargs.containsKey("api_base")) {
            mergedKwargs.put("api_base", apiBase);
        }
        return mergedKwargs;
    }
}
