package com.somaagent.core.service;

import com.somaagent.core.domain.ModelConfig;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Mono;

@Service
public class ChatServiceImpl implements ChatService {

    @Override
    public Mono<String> chat(String message, ModelConfig config) {
        // Placeholder for actual LLM integration (e.g., using LangChain4j or similar)
        return Mono.just("Echo: " + message);
    }
}
