package com.somaagent.gateway;

import com.somaagent.core.service.ChatService;
import com.somaagent.core.domain.ModelConfig;
import com.somaagent.core.domain.ModelType;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Mono;

import java.time.Instant;
import java.util.Map;

@RestController
public class GatewayController {

    private final ChatService chatService;

    public GatewayController(ChatService chatService) {
        this.chatService = chatService;
    }

    @GetMapping("/health")
    public Map<String, Object> health() {
        return Map.of("status", "ok", "timestamp", Instant.now().getEpochSecond());
    }

    @GetMapping("/healths")
    public Map<String, Object> aggregatedHealth() {
        // Placeholder for aggregated health check logic
        return Map.of("overall", "healthy", "components", Map.of("gateway", Map.of("status", "healthy", "code", 200)));
    }

    @GetMapping("/test-chat")
    public Mono<String> testChat(@RequestParam(defaultValue = "Hello") String msg) {
        ModelConfig dummyConfig = ModelConfig.builder()
                .type(ModelType.CHAT)
                .provider("test")
                .name("test-model")
                .build();
        return chatService.chat(msg, dummyConfig);
    }
}
