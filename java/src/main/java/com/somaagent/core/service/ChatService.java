package com.somaagent.core.service;

import com.somaagent.core.domain.ModelConfig;
import reactor.core.publisher.Mono;

public interface ChatService {
    Mono<String> chat(String message, ModelConfig config);
}
