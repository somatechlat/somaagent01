# Implementation Tasks — Phase 4: Agent Interfaces

**Phase:** 4 of 4  
**Priority:** P1  
**Duration:** 3-4 weeks  
**Dependencies:** Phase 1-3 complete

---

## 1. Chat Interface

### 1.1 Endpoints

| Endpoint | Method | Task | Estimated |
|----------|--------|------|-----------|
| `/chat/conversations` | GET | List conversations | 2h |
| `/chat/conversations` | POST | Create conversation | 2h |
| `/chat/conversations/{id}` | GET | Get conversation | 1h |
| `/chat/conversations/{id}` | DELETE | Delete conversation | 2h |
| `/chat/conversations/{id}/messages` | GET | Get messages | 2h |
| `/chat/conversations/{id}/messages` | POST | Send message | 4h |
| `/chat/stream` | WS | Streaming responses | 6h |

### 1.2 Components

| Component | Priority | Estimated |
|-----------|----------|-----------|
| `saas-chat-view.ts` | P0 | 8h |
| `saas-conversation-list.ts` | P0 | 4h |
| `saas-message-bubble.ts` | P0 | 3h |
| `saas-chat-input.ts` | P0 | 4h |
| `saas-tool-status.ts` | P0 | 3h |
| `saas-mode-selector.ts` | P0 | 2h |

### 1.3 WebSocket Streaming

```python
# api/consumers/chat.py

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = await get_user_from_token(self.scope)
        self.conversation_id = self.scope["url_route"]["kwargs"]["id"]
        
        # Check permission
        if not await check_permission(
            self.user.id, "chat:send", "conversation", self.conversation_id
        ):
            await self.close(code=4003)
            return
        
        await self.accept()
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        
        if data["type"] == "message":
            async for chunk in self.process_message(data["content"]):
                await self.send(json.dumps({
                    "type": "chunk",
                    "content": chunk,
                }))
            
            await self.send(json.dumps({"type": "done"}))
        
        elif data["type"] == "cancel":
            # Cancel ongoing generation
            pass
    
    async def process_message(self, content: str):
        """Process message and yield response chunks."""
        # Get agent config
        agent = await get_agent(self.conversation_id)
        
        # Semantic recall from SomaBrain
        memories = await somabrain.recall(content, agent.tenant_id)
        
        # Build prompt
        prompt = build_prompt(content, memories)
        
        # Stream from LLM
        async for chunk in llm.stream(prompt, model=agent.config["chat_model"]):
            yield chunk
        
        # Store to memory
        await somabrain.remember(content, response, agent.tenant_id)
```

---

## 2. Memory Browser

### 2.1 Endpoints

| Endpoint | Method | Task | Estimated |
|----------|--------|------|-----------|
| `/memory` | GET | List memories | 3h |
| `/memory` | POST | Create memory | 2h |
| `/memory/{id}` | GET | Get memory | 1h |
| `/memory/{id}` | PUT | Update memory | 2h |
| `/memory/{id}` | DELETE | Delete memory | 2h |
| `/memory/search` | POST | Semantic search | 4h |
| `/memory/export` | GET | Export all | 3h |

### 2.2 Components

| Component | Priority | Estimated |
|-----------|----------|-----------|
| `saas-memory-view.ts` | P0 | 6h |
| `saas-memory-card.ts` | P0 | 3h |
| `saas-memory-detail.ts` | P0 | 3h |
| `saas-memory-search.ts` | P0 | 3h |

---

## 3. Voice Integration

### 3.1 Endpoints

| Endpoint | Method | Task | Estimated |
|----------|--------|------|-----------|
| `/voice/settings` | GET/PUT | Voice config | 2h |
| `/voice/transcribe` | POST | STT | 4h |
| `/voice/synthesize` | POST | TTS | 4h |
| `/voice/voices` | GET | List voices | 1h |
| `/voice/test` | POST | Test connection | 2h |
| `/voice/stream` | WS | Real-time voice | 8h |

### 3.2 Components

| Component | Priority | Estimated |
|-----------|----------|-----------|
| `saas-voice-settings.ts` | P1 | 5h |
| `saas-voice-button.ts` | P1 | 4h |
| `saas-voice-visualizer.ts` | P2 | 4h |

### 3.3 Voice Controller

```typescript
// controllers/voice-controller.ts

export class VoiceController implements ReactiveController {
  host: ReactiveControllerHost;
  
  private mediaRecorder: MediaRecorder | null = null;
  private audioContext: AudioContext | null = null;
  private ws: WebSocket | null = null;
  
  @state() recording = false;
  @state() playing = false;
  @state() transcription = '';
  @state() error = '';
  
  constructor(host: ReactiveControllerHost) {
    this.host = host;
    host.addController(this);
  }
  
  async startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      this.mediaRecorder = new MediaRecorder(stream);
      
      const chunks: Blob[] = [];
      this.mediaRecorder.ondataavailable = (e) => chunks.push(e.data);
      
      this.mediaRecorder.onstop = async () => {
        const blob = new Blob(chunks, { type: 'audio/webm' });
        await this.transcribe(blob);
      };
      
      this.mediaRecorder.start();
      this.recording = true;
      this.host.requestUpdate();
    } catch (err) {
      this.error = 'Microphone access denied';
    }
  }
  
  stopRecording() {
    if (this.mediaRecorder) {
      this.mediaRecorder.stop();
      this.recording = false;
      this.host.requestUpdate();
    }
  }
  
  async transcribe(audio: Blob) {
    const formData = new FormData();
    formData.append('audio', audio);
    
    const response = await fetch('/api/v2/voice/transcribe', {
      method: 'POST',
      body: formData,
    });
    
    if (response.ok) {
      const data = await response.json();
      this.transcription = data.text;
      this.host.requestUpdate();
    }
  }
  
  async synthesize(text: string) {
    const response = await fetch('/api/v2/voice/synthesize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    });
    
    if (response.ok) {
      const audioBlob = await response.blob();
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      
      this.playing = true;
      audio.onended = () => {
        this.playing = false;
        this.host.requestUpdate();
      };
      
      audio.play();
      this.host.requestUpdate();
    }
  }
}
```

---

## 4. Developer Mode (DEV)

### 4.1 Components

| Component | Priority | Estimated |
|-----------|----------|-----------|
| `saas-debug-console.ts` | P2 | 6h |
| `saas-api-logs.ts` | P2 | 4h |
| `saas-mcp-inspector.ts` | P2 | 5h |
| `saas-tool-playground.ts` | P2 | 5h |
| `saas-ws-monitor.ts` | P2 | 4h |

### 4.2 Debug Console

```typescript
// components/saas-debug-console.ts

@customElement('saas-debug-console')
export class SaasDebugConsole extends LitElement {
  @state() logs: LogEntry[] = [];
  @state() paused = false;
  @state() filters = { debug: true, info: true, warn: true, error: true };
  
  private ws: WebSocket | null = null;
  
  connectedCallback() {
    super.connectedCallback();
    this.connectWebSocket();
  }
  
  private connectWebSocket() {
    this.ws = new WebSocket(`wss://${location.host}/api/v2/dev/logs`);
    
    this.ws.onmessage = (event) => {
      if (this.paused) return;
      
      const log = JSON.parse(event.data);
      if (this.filters[log.level]) {
        this.logs = [...this.logs.slice(-999), log];
      }
    };
  }
  
  render() {
    return html`
      <div class="console">
        <div class="toolbar">
          <saas-button @click=${() => this.paused = !this.paused}>
            ${this.paused ? '▶️ Resume' : '⏸️ Pause'}
          </saas-button>
          <saas-button @click=${() => this.logs = []}>
            🗑️ Clear
          </saas-button>
          <div class="filters">
            ${Object.keys(this.filters).map(level => html`
              <label>
                <input
                  type="checkbox"
                  .checked=${this.filters[level]}
                  @change=${() => this.filters[level] = !this.filters[level]}
                >
                ${level.toUpperCase()}
              </label>
            `)}
          </div>
        </div>
        
        <div class="logs">
          ${this.logs.map(log => html`
            <div class="log-entry ${log.level}">
              <span class="timestamp">${log.timestamp}</span>
              <span class="level">[${log.level}]</span>
              <span class="source">[${log.source}]</span>
              <span class="message">${log.message}</span>
            </div>
          `)}
        </div>
      </div>
    `;
  }
}
```

---

## 5. Training Mode (TRN)

### 5.1 Endpoints

| Endpoint | Method | Task | Estimated |
|----------|--------|------|-----------|
| `/cognitive/neuromodulators` | GET/PUT | Get/set levels | 3h |
| `/cognitive/adaptation` | GET/PUT | Get/set params | 2h |
| `/cognitive/adaptation/reset` | POST | Reset adaptation | 2h |
| `/cognitive/sleep-cycle` | POST | Trigger sleep | 3h |

### 5.2 Components

| Component | Priority | Estimated |
|-----------|----------|-----------|
| `saas-cognitive-panel.ts` | P2 | 6h |
| `saas-neuromodulator-slider.ts` | P2 | 3h |
| `saas-learning-curves.ts` | P2 | 5h |
| `saas-training-sessions.ts` | P2 | 4h |

---

## 6. Degradation Handling

### 6.1 Implementation

```typescript
// controllers/degradation-controller.ts

export class DegradationController implements ReactiveController {
  host: ReactiveControllerHost;
  
  @state() status: DegradationStatus = {
    mode: 'normal',
    services: {},
  };
  
  constructor(host: ReactiveControllerHost) {
    this.host = host;
    host.addController(this);
    this.startPolling();
  }
  
  private async startPolling() {
    while (true) {
      await this.checkHealth();
      await new Promise(r => setTimeout(r, 30000)); // 30s
    }
  }
  
  private async checkHealth() {
    try {
      const response = await fetch('/api/v2/health');
      const health = await response.json();
      
      const services = {
        postgresql: health.postgresql?.status ?? 'unknown',
        redis: health.redis?.status ?? 'unknown',
        somabrain: health.somabrain?.status ?? 'unknown',
        llm: health.llm?.status ?? 'unknown',
        voice: health.voice?.status ?? 'unknown',
      };
      
      const degraded = Object.values(services).some(s => s !== 'healthy');
      
      this.status = {
        mode: degraded ? 'degraded' : 'normal',
        services,
      };
      
      this.host.requestUpdate();
    } catch {
      this.status = { mode: 'degraded', services: {} };
      this.host.requestUpdate();
    }
  }
  
  getServiceMessage(service: string): string {
    const msgs = {
      somabrain: 'Memory service unavailable. Session-only mode.',
      llm: 'AI service degraded. Responses may be slower.',
      voice: 'Voice unavailable. Use text input.',
    };
    return msgs[service] || `${service} unavailable`;
  }
}
```

### 6.2 Components

| Component | Priority | Estimated |
|-----------|----------|-----------|
| `saas-degradation-banner.ts` | P0 | 3h |
| `saas-service-status.ts` | P1 | 2h |

---

## 7. Checklist

### Week 1
- [ ] Chat view component
- [ ] Conversation list
- [ ] Message streaming (WebSocket)
- [ ] Tool execution display
- [ ] Mode selector

### Week 2
- [ ] Memory browser
- [ ] Semantic search
- [ ] Memory detail view
- [ ] Settings pages
- [ ] Voice settings

### Week 3
- [ ] Voice recording
- [ ] Voice playback
- [ ] Degradation handling
- [ ] DEV mode console
- [ ] API logs viewer

### Week 4
- [ ] MCP inspector
- [ ] TRN mode cognitive panel
- [ ] Neuromodulator controls
- [ ] Learning curves
- [ ] Final integration testing

---

## Total Implementation Summary

| Phase | Duration | Priority |
|-------|----------|----------|
| Phase 1: Foundation | 2-3 weeks | P0 |
| Phase 2: Authentication | 1-2 weeks | P0 |
| Phase 3: Admin Interfaces | 2-3 weeks | P0 |
| Phase 4: Agent Interfaces | 3-4 weeks | P1 |
| **TOTAL** | **8-12 weeks** | |

---

**Implementation Complete!**

See [INDEX.md](../srs/INDEX.md) for full documentation structure.
