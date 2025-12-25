package com.somaagent.core.domain;

public enum ModelType {
    CHAT("Chat"),
    EMBEDDING("Embedding");

    private final String value;

    ModelType(String value) {
        this.value = value;
    }

    public String getValue() {
        return value;
    }
}
