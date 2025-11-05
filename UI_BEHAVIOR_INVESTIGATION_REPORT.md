# UI BEHAVIOR INVESTIGATION REPORT
**Date:** 2025-01-XX  
**System:** SomaAgent01 vs Agent Zero  
**Focus:** Welcome messages, New Chat, and Restart functionality

---

## CASE 1: FRESH CHAT - WELCOME MESSAGE NOT APPEARING

### Expected Behavior
When a fresh chat session starts, an internal welcome message should appear:
> "Hello! 👋, I'm SomaAgent01, your AI assistant. How can I help you today?"

**Key requirement:** This is NOT from the LLM - it's an internal UI message.

### Current Status in SomaAgent01
❌ **NOT WORKING** - No welcome message appears on fresh chat

### Root Cause Analysis

#### Agent Zero Implementation
```javascript
// agent_zero/webui/index.js - Lines ~1100-1150
async function poll() {
  // ... polling logic ...
  // When no context exists and no sessions, agent_zero shows nothing
  // No explicit welcome message injection
}
```

**Agent Zero does NOT have a welcome message either!**

#### SomaAgent01 Implementation
```javascript
// somaAgent01/webui/index.js - Lines ~1800-1900
async function bootstrapSessions() {
  // ... loads sessions from server ...
  if (pick && pick.id) {
    setContext(pick.id);
  } else {
    // No sessions present. Golden UI parity requires an empty history here
    // (no default welcome/notification bubbles) so tests that assert
    // post-reset counts (≤ 1 bubble) remain stable. Do not inject any
    // default bubbles when there are no sessions.
  }
}
```

**FINDING:** SomaAgent01 explicitly REMOVED welcome messages to maintain "Golden UI parity" for test stability!

### What's Missing
Neither system has:
1. A `showWelcomeMessage()` function
2. Logic to inject an internal greeting on fresh session
3. A welcome message template in the messages system

### Where It Should Be Added
**Location:** `somaAgent01/webui/index.js` in `bootstrapSessions()` function

**Pseudocode:**
```javascript
if (!pick || items.length === 0) {
  // No sessions - show welcome
  const welcomeId = "welcome-" + generateGUID();
  setMessage(
    welcomeId,
    "system",  // or "info"
    "",
    "Hello! 👋, I'm SomaAgent01, your AI assistant. How can I help you today?",
    false,
    {}
  );
}
```

---

## CASE 2: NEW CHAT - WELCOME MESSAGE NOT APPEARING

### Expected Behavior
When clicking "New Chat" button:
1. Create a clean new chat session
2. Display the same welcome message as CASE 1

### Current Status in SomaAgent01
❌ **NOT WORKING** - No welcome message appears

### Root Cause Analysis

#### Agent Zero Implementation
```javascript
// agent_zero/webui/index.js - Line ~650
globalThis.newChat = async function () {
  try {
    newContext();
    updateAfterScroll();
  } catch (e) {
    globalThis.toastFetchError("Error creating new chat", e);
  }
};

export const newContext = function () {
  context = generateShortId();
  setContext(context);
}
```

**Agent Zero:** Creates new context, clears history, NO welcome message

#### SomaAgent01 Implementation
```javascript
// somaAgent01/webui/index.js - Lines ~1350-1370
export const newContext = function () {
  context = generateGUID();
  // New chats start as drafts (not persisted on the server yet)
  try { persistedSessions.delete(String(context)); } catch(_e) {}
  setContext(context);
  // Optimistically add the new chat to the sidebar list
  try {
    if (globalThis.Alpine && chatsSection) {
      const chatsAD = Alpine.$data(chatsSection);
      const items = Array.isArray(chatsAD?.contexts) ? chatsAD.contexts : [];
      const exists = items.some((c) => c.id === context);
      if (!exists) {
        chatsAD.contexts = [
          { id: context, name: "New chat", no: (items[0]?.no || 0) + 1, updated_at: new Date().toISOString() },
          ...items,
        ];
        chatsAD.selected = context;
      }
    }
  } catch(_e) {}
}

globalThis.newChat = function () {
  newContext();
  justToast("New chat created", "success", 1000, "chat-new");
};
```

**SomaAgent01:** Creates new context, adds to sidebar, shows toast, NO welcome message

### What's Missing
Both systems:
1. Call `setContext()` which clears `chatHistory.innerHTML = ""`
2. Never inject a welcome message after clearing
3. Rely on SSE/polling to populate messages (but there are none yet)

### Where It Should Be Added
**Location:** `somaAgent01/webui/index.js` in `newContext()` function

**Pseudocode:**
```javascript
export const newContext = function () {
  context = generateGUID();
  persistedSessions.delete(String(context));
  setContext(context);
  
  // ADD THIS:
  const welcomeId = "welcome-" + context;
  setMessage(
    welcomeId,
    "system",
    "",
    "Hello! 👋, I'm SomaAgent01, your AI assistant. How can I help you today?",
    false,
    {}
  );
  
  // ... rest of sidebar logic ...
}
```

---

## CASE 3: RESTART BUTTON - NOT WORKING

### Expected Behavior
Restart button should:
1. Restart the backend agent/server
2. Show appropriate feedback to user
3. Reconnect when backend is back online

### Current Status in SomaAgent01
⚠️ **DIFFERENT IMPLEMENTATION** - Shows info toast instead of restarting

### Root Cause Analysis

#### Agent Zero Implementation
```javascript
// agent_zero/webui/index.js - Lines ~900-930
globalThis.restart = async function () {
  try {
    if (!getConnectionStatus()) {
      await toastFrontendError(
        "Backend disconnected, cannot restart.",
        "Restart Error"
      );
      return;
    }
    // First try to initiate restart
    const resp = await sendJsonData("/restart", {});
  } catch (e) {
    // Show restarting message with no timeout and restart group
    await toastFrontendInfo("Restarting...", "System Restart", 9999, "restart");

    let retries = 0;
    const maxRetries = 240; // Maximum number of retries (60 seconds with 250ms interval)

    while (retries < maxRetries) {
      try {
        const resp = await sendJsonData("/health", {});
        // Server is back up, show success message
        await new Promise((resolve) => setTimeout(resolve, 250));
        await toastFrontendSuccess("Restarted", "System Restart", 5, "restart");
        return;
      } catch (e) {
        // Server still down, keep waiting
        retries++;
        await new Promise((resolve) => setTimeout(resolve, 250));
      }
    }

    // If we get here, restart failed or took too long
    await toastFrontendError(
      "Restart timed out or failed",
      "Restart Error",
      8,
      "restart"
    );
  }
};
```

**Agent Zero:**
- Calls `/restart` endpoint
- Polls `/health` endpoint to detect when backend is back
- Shows progress toasts
- Has retry logic with 60-second timeout

#### SomaAgent01 Implementation
```javascript
// somaAgent01/webui/index.js - Lines ~1280-1283
globalThis.restart = async function () {
  // No canonical restart endpoint; show info toast instead
  await toastFrontendInfo("Restart not supported in this UI. Use your process manager.", "System", 6, "restart");
};
```

**SomaAgent01:**
- Does NOT call any restart endpoint
- Shows a message saying restart is not supported
- Tells user to use process manager instead

### API Endpoint Differences

#### Agent Zero Backend
Has these endpoints:
- `POST /restart` - Initiates backend restart
- `GET /health` - Health check endpoint
- Uses CSRF token system

#### SomaAgent01 Backend
- Uses `/v1/*` versioned API
- No `/restart` endpoint mentioned
- Uses `/session/action` for actions
- Different authentication (no CSRF, uses same-origin cookies)

### What's Different

**Architecture:**
- **Agent Zero:** Monolithic backend that can restart itself
- **SomaAgent01:** Distributed system (Gateway + Workers) - can't restart from UI

**Restart Capability:**
- **Agent Zero:** Backend can restart and come back online
- **SomaAgent01:** Requires external process manager (Docker, systemd, etc.)

### Recommendation

**Option A - Keep Current Behavior (Recommended)**
SomaAgent01's approach is actually MORE CORRECT for production systems:
- Distributed systems shouldn't restart from UI
- Process managers (Docker, K8s, systemd) should handle restarts
- Current message is honest and appropriate

**Option B - Add Gateway Restart Endpoint**
If you want parity with Agent Zero:
1. Add `POST /v1/system/restart` endpoint to Gateway
2. Gateway signals workers to gracefully shutdown
3. Process manager detects exit and restarts containers
4. UI polls for reconnection

**Option C - Improve UI Feedback**
Keep no-restart but improve the message:
```javascript
globalThis.restart = async function () {
  await toastFrontendInfo(
    "To restart SomaAgent01, use: make dev-down && make dev-up",
    "System Restart",
    10,
    "restart"
  );
};
```

---

## SUMMARY TABLE

| Case | Agent Zero | SomaAgent01 | Status | Fix Needed |
|------|-----------|-------------|--------|------------|
| **Fresh Chat Welcome** | ❌ No welcome | ❌ No welcome | BOTH BROKEN | Add `showWelcomeMessage()` |
| **New Chat Welcome** | ❌ No welcome | ❌ No welcome | BOTH BROKEN | Add welcome in `newContext()` |
| **Restart Button** | ✅ Works (polls /health) | ⚠️ Different (shows info) | ARCHITECTURAL DIFFERENCE | Keep current or add `/v1/system/restart` |

---

## DETAILED FIX LOCATIONS

### Fix for CASE 1 & 2: Welcome Messages

**File:** `somaAgent01/webui/index.js`

**Function to add:**
```javascript
function showWelcomeMessage() {
  const welcomeId = "welcome-" + generateGUID();
  setMessage(
    welcomeId,
    "system",  // or "info" or "hint"
    "",
    "Hello! 👋, I'm SomaAgent01, your AI assistant. How can I help you today?",
    false,
    {}
  );
}
```

**Call in `bootstrapSessions()` (Line ~1850):**
```javascript
if (!pick || items.length === 0) {
  showWelcomeMessage();  // ADD THIS
}
```

**Call in `newContext()` (Line ~1370):**
```javascript
export const newContext = function () {
  context = generateGUID();
  persistedSessions.delete(String(context));
  setContext(context);
  showWelcomeMessage();  // ADD THIS
  // ... rest of code ...
}
```

### Fix for CASE 3: Restart (Optional)

**If you want Agent Zero parity:**

1. Add Gateway endpoint: `POST /v1/system/restart`
2. Update `index.js`:
```javascript
globalThis.restart = async function () {
  try {
    if (!getConnectionStatus()) {
      await toastFrontendError("Backend disconnected, cannot restart.", "Restart Error");
      return;
    }
    await api.fetchApi("/v1/system/restart", { method: "POST" });
    await toastFrontendInfo("Restarting...", "System Restart", 9999, "restart");
    
    // Poll for reconnection
    let retries = 0;
    while (retries < 240) {
      try {
        await api.fetchApi("/v1/health");
        await toastFrontendSuccess("Restarted", "System Restart", 5, "restart");
        return;
      } catch (e) {
        retries++;
        await new Promise(r => setTimeout(r, 250));
      }
    }
    await toastFrontendError("Restart timed out", "Restart Error", 8, "restart");
  } catch (e) {
    toastFetchError("Error restarting", e);
  }
};
```

---

## CONCLUSION

**CASE 1 & 2:** Both systems are missing welcome messages. This is NOT a regression - Agent Zero never had them either. You need to implement this feature from scratch.

**CASE 3:** SomaAgent01 intentionally removed restart functionality because of its distributed architecture. This is a design decision, not a bug. Agent Zero's restart works because it's a monolithic backend.

**Next Steps:**
1. Decide if you want welcome messages (recommended: YES)
2. Decide if you want restart functionality (recommended: NO, keep current)
3. Implement welcome message function
4. Test with fresh sessions and new chat button
