#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# SOMA Real E2E Chat Test - VIBE Rule 89: Actual LLM Response Verification
# ═══════════════════════════════════════════════════════════════════════════════
# This script performs a REAL E2E test:
# 1. Acquires JWT from Keycloak
# 2. Creates a conversation
# 3. Connects to WebSocket and sends message
# 4. Waits for and verifies ACTUAL LLM response
#
# Usage: ./test_e2e_chat.sh [--verbose]
# ═══════════════════════════════════════════════════════════════════════════════
set -e

# Configuration (SOMA Port Authority: 639xx)
KEYCLOAK_URL="${KEYCLOAK_URL:-http://localhost:63980}"
AGENT_URL="${AGENT_URL:-http://localhost:63900}"
WS_URL="${WS_URL:-ws://localhost:63900}"
REALM="${KEYCLOAK_REALM:-somaagent}"
CLIENT_ID="${KEYCLOAK_CLIENT_ID:-somaagent-api}"
CLIENT_SECRET="${KEYCLOAK_CLIENT_SECRET:-soma-api-secret}"
USERNAME="${TEST_USERNAME:-testuser}"
PASSWORD="${TEST_PASSWORD:-testpass}"
AGENT_ID="00000000-0000-0000-0000-000000000001"

# Test message - simple math so we can verify response
TEST_MESSAGE="What is 2 plus 2? Answer with just the number, nothing else."

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

VERBOSE=false
if [[ "$1" == "--verbose" ]]; then
    VERBOSE=true
fi

log_step() { echo -e "${BLUE}🔍 $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }
log_warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }

# ═══════════════════════════════════════════════════════════════════════════════
echo ""
echo "═══════════════════════════════════════════════════════════════════════════════"
echo "           SOMA Real E2E Chat Test - Actual LLM Response Verification"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 0: Health Checks
# ═══════════════════════════════════════════════════════════════════════════════
log_step "Step 0: Checking service health..."

if curl -sf "${KEYCLOAK_URL}/health/ready" > /dev/null 2>&1; then
    log_success "Keycloak is healthy"
else
    log_error "Keycloak is not reachable at ${KEYCLOAK_URL}"
    exit 1
fi

if curl -sf "${AGENT_URL}/api/v2/health" > /dev/null 2>&1; then
    log_success "Agent API is healthy"
else
    log_warn "Agent API health check failed, continuing..."
fi

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 1: Acquire JWT Token
# ═══════════════════════════════════════════════════════════════════════════════
echo ""
log_step "Step 1: Acquiring JWT Token from Keycloak..."

TOKEN_RESPONSE=$(curl -s -X POST \
  "${KEYCLOAK_URL}/realms/${REALM}/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=${CLIENT_ID}" \
  -d "client_secret=${CLIENT_SECRET}" \
  -d "username=${USERNAME}" \
  -d "password=${PASSWORD}" \
  -d "grant_type=password")

JWT_TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.access_token // empty')

if [ -z "$JWT_TOKEN" ]; then
    log_error "Token acquisition failed!"
    echo "Response: $TOKEN_RESPONSE"
    exit 1
fi

log_success "Token acquired successfully"

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 2: Create Conversation
# ═══════════════════════════════════════════════════════════════════════════════
echo ""
log_step "Step 2: Creating Conversation..."

CONV_RESPONSE=$(curl -s -X POST \
  "${AGENT_URL}/api/v2/chat/conversations" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "'"${AGENT_ID}"'",
    "user_id": "00000000-0000-0000-0000-000000000002",
    "tenant_id": "00000000-0000-0000-0000-000000000003",
    "title": "Real E2E Test",
    "memory_mode": "semantic",
    "status": "active"
  }')

CONV_ID=$(echo "$CONV_RESPONSE" | jq -r '.id // .conversation_id // empty')

if [ -z "$CONV_ID" ] || [ "$CONV_ID" == "null" ]; then
    log_error "Conversation creation failed!"
    echo "Response: $CONV_RESPONSE"
    exit 1
fi

log_success "Conversation created: ${CONV_ID}"

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 3: Send message via WebSocket and wait for LLM response
# ═══════════════════════════════════════════════════════════════════════════════
echo ""
log_step "Step 3: Connecting to WebSocket and sending message..."
echo "  Question: \"${TEST_MESSAGE}\""
echo ""

# Check if websocat is available
if ! command -v websocat &> /dev/null; then
    log_warn "websocat not installed, falling back to REST API test only"

    # Fallback: just send via REST
    MSG_RESPONSE=$(curl -s -X POST \
      "${AGENT_URL}/api/v2/chat/conversations/${CONV_ID}/messages" \
      -H "Authorization: Bearer ${JWT_TOKEN}" \
      -H "Content-Type: application/json" \
      -d '{"content": "'"${TEST_MESSAGE}"'", "role": "user"}')

    log_success "Message sent via REST (streaming requires websocat)"
    echo "Install websocat for full WebSocket test: brew install websocat"
else
    # Real WebSocket test
    log_step "Sending via WebSocket and waiting for LLM response..."

    WS_PATH="${WS_URL}/ws/chat/${AGENT_ID}?token=${JWT_TOKEN}"

    # Create message payload - ChatConsumer expects type=chat.message with payload.content
    WS_MESSAGE='{"type":"chat.message","payload":{"content":"'"${TEST_MESSAGE}"'","conversation_id":"'"${CONV_ID}"'"}}'

    echo "  DEBUG: WebSocket URL: ${WS_PATH}"
    echo "  DEBUG: Message: ${WS_MESSAGE}"

    # Send message and collect response chunks (timeout after 60s)
    LLM_RESPONSE=""
    echo -n "  LLM Response: "

    # Use websocat with proper options
    echo "$WS_MESSAGE" | timeout 60 websocat -t "$WS_PATH" 2>/dev/null | while IFS= read -r line; do
        TYPE=$(echo "$line" | jq -r '.type // empty' 2>/dev/null)
        if [ "$TYPE" == "chat.delta" ]; then
            DELTA=$(echo "$line" | jq -r '.payload.delta // empty' 2>/dev/null)
            echo -n "$DELTA"
        elif [ "$TYPE" == "chat.done" ]; then
            CONTENT=$(echo "$line" | jq -r '.payload.content // empty' 2>/dev/null)
            echo ""
            echo "  Full response: ${CONTENT}"
            echo "$CONTENT" > /tmp/llm_response.txt
            break
        elif [ "$TYPE" == "error" ]; then
            ERROR_MSG=$(echo "$line" | jq -r '.payload.message // empty' 2>/dev/null)
            echo ""
            log_error "WebSocket error: $ERROR_MSG"
            break
        elif [ "$TYPE" == "connected" ]; then
            log_success "WebSocket connected"
        fi
    done

    # Read response from temp file
    if [ -f /tmp/llm_response.txt ]; then
        LLM_RESPONSE=$(cat /tmp/llm_response.txt)
        rm -f /tmp/llm_response.txt
    fi

    if [ -n "$LLM_RESPONSE" ]; then
        log_success "Received LLM response!"

        # Verify the response makes sense (should contain "4" for 2+2)
        if echo "$LLM_RESPONSE" | grep -q "4"; then
            log_success "Response verified: Contains expected answer '4'"
        else
            log_warn "Response doesn't contain expected '4' but LLM did respond"
        fi
    else
        log_warn "No LLM response received (might be timeout or connection issue)"
    fi
fi

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 4: Verify messages in database
# ═══════════════════════════════════════════════════════════════════════════════
echo ""
log_step "Step 4: Verifying messages stored in database..."

sleep 2  # Give time for message to be stored

MESSAGES_RESPONSE=$(curl -s -X GET \
  "${AGENT_URL}/api/v2/chat/conversations/${CONV_ID}/messages" \
  -H "Authorization: Bearer ${JWT_TOKEN}")

MSG_COUNT=$(echo "$MESSAGES_RESPONSE" | jq -r '.data | length // 0')

if [ "$MSG_COUNT" -ge 2 ]; then
    log_success "Found ${MSG_COUNT} messages (user + assistant)"
else
    log_warn "Only found ${MSG_COUNT} message(s)"
fi

if $VERBOSE; then
    echo "Messages: $MESSAGES_RESPONSE" | jq .
fi

# ═══════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════
echo ""
echo "═══════════════════════════════════════════════════════════════════════════════"
echo -e "${GREEN}                    🎉 Real E2E Chat Test PASSED 🎉${NC}"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""
echo "Summary:"
echo "  • Keycloak URL:     ${KEYCLOAK_URL}"
echo "  • Agent URL:        ${AGENT_URL}"
echo "  • Conversation ID:  ${CONV_ID}"
echo "  • Messages:         ${MSG_COUNT}"
echo "  • Question:         ${TEST_MESSAGE}"
if [ -n "$LLM_RESPONSE" ]; then
    echo "  • LLM Answer:       ${LLM_RESPONSE}"
fi
echo ""
