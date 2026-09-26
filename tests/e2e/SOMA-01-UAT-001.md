# SOMAAGENT01 — USER ACCEPTANCE TESTING CHECKLIST

## Document Control

| Field | Value |
|-------|-------|
| Document Title | User Acceptance Testing Checklist |
| Document Identifier | SOMA-01-UAT-001 |
| Version | 1.0.0 |
| Date | 2026-06-15 |
| Status | Active |

---

## 1. AUTHENTICATION FLOW

| ID | Test Case | Steps | Expected Result | Pass/Fail |
|----|-----------|-------|-----------------|-----------|
| UAT-001 | Login with email/password | 1. Navigate to login page 2. Enter credentials 3. Click Login | Redirected to dashboard, httpOnly cookie set | |
| UAT-002 | OAuth login (Google) | 1. Click "Sign in with Google" 2. Complete Google flow | Redirected back with session | |
| UAT-003 | Token refresh | 1. Wait 14 minutes 2. Make API call | Token refreshed transparently | |
| UAT-004 | Logout | 1. Click Logout 2. Try protected endpoint | Cookies cleared, 401 on protected endpoint | |
| UAT-005 | Account lockout | 1. Enter wrong password 5 times | Account locked for 15 minutes | |
| UAT-006 | Password change | 1. Go to profile 2. Change password 3. Login with new password | Login succeeds with new password | |
| UAT-007 | Registration | 1. Click Register 2. Enter email/password 3. Submit | User created, verification email sent | |

## 2. CHAT FLOW

| ID | Test Case | Steps | Expected Result | Pass/Fail |
|----|-----------|-------|-----------------|-----------|
| UAT-010 | Create conversation | 1. Select agent 2. Click New Chat | Conversation created, chat view opens | |
| UAT-011 | Send message | 1. Type message 2. Press Enter | Message sent, streaming response received | |
| UAT-012 | Streaming response | 1. Send message 2. Observe response | Tokens appear incrementally (streaming) | |
| UAT-013 | Tool execution | 1. Ask agent to use a tool 2. Observe | Tool executed, result included in response | |
| UAT-014 | Conversation history | 1. Send 5 messages 2. Refresh page | All messages preserved | |
| UAT-015 | Multiple conversations | 1. Create 2 conversations 2. Switch between them | Each conversation has independent history | |
| UAT-016 | WebSocket reconnection | 1. Disconnect network 2. Reconnect | WebSocket reconnects automatically | |
| UAT-017 | Agent selection | 1. View agent list 2. Select different agent | Chat switches to selected agent | |

## 3. MEMORY FLOW

| ID | Test Case | Steps | Expected Result | Pass/Fail |
|----|-----------|-------|-----------------|-----------|
| UAT-020 | Memory recall | 1. Tell agent a fact 2. Ask about it later | Agent recalls the fact | |
| UAT-021 | Cross-session memory | 1. Tell agent something in session A 2. Ask in session B | Agent recalls from previous session | |
| UAT-022 | Memory search | 1. Go to memory page 2. Search for term | Relevant memories returned | |

## 4. ADMIN FLOW

| ID | Test Case | Steps | Expected Result | Pass/Fail |
|----|-----------|-------|-----------------|-----------|
| UAT-030 | View agents | 1. Go to agents page | List of agents displayed | |
| UAT-031 | Create agent | 1. Click Create Agent 2. Fill form 3. Submit | Agent created, appears in list | |
| UAT-032 | Edit agent | 1. Select agent 2. Edit settings 3. Save | Changes saved, reflected in chat | |
| UAT-033 | View users | 1. Go to users page | List of users displayed | |
| UAT-034 | View audit logs | 1. Go to audit page | Auth events logged | |
| UAT-035 | View health status | 1. Go to health page | All components show status | |

## 5. DEPLOYMENT MODES

| ID | Test Case | Steps | Expected Result | Pass/Fail |
|----|-----------|-------|-----------------|-----------|
| UAT-040 | Standalone mode | 1. Deploy with SA01_DEPLOYMENT_MODE=STANDALONE 2. Test chat | Chat works without Brain/SFM | |
| UAT-041 | AAAS mode | 1. Deploy full triad 2. Test chat | Chat works with Brain + SFM memory | |
| UAT-042 | Degraded mode | 1. Stop SomaBrain 2. Send chat message | Chat works with SFM fallback | |

## 6. PERFORMANCE

| ID | Test Case | Steps | Expected Result | Pass/Fail |
|----|-----------|-------|-----------------|-----------|
| UAT-050 | Response latency | 1. Send message 2. Measure time to first token | < 2 seconds | |
| UAT-051 | Page load time | 1. Load dashboard | < 3 seconds | |
| UAT-052 | Concurrent users | 1. 10 users chat simultaneously | All responses received | |

---

## SIGN-OFF

| Role | Name | Date | Decision |
|------|------|------|----------|
| Product Owner | | | ☐ PASS ☐ FAIL |
| QA Lead | | | ☐ PASS ☐ FAIL |
| Engineering Lead | | | ☐ PASS ☐ FAIL |
| Security Lead | | | ☐ PASS ☐ FAIL |

---

End of Document
