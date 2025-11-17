#!/usr/bin/env python3
"""
Simple chat API test for SomaAgent01
Tests the chat functionality without the UI
"""

import requests
import json
import time
import uuid

# Configuration
GATEWAY_URL = "http://localhost:21016"
INTERNAL_TOKEN = ***REMOVED***
headers = {
    "Authorization": f"Bearer {INTERNAL_TOKEN}",
    "Content-Type": "application/json"
}

def test_chat_functionality():
    print("🚀 Testing SomaAgent01 Chat Functionality")
    print("=" * 50)
    
    # Step 1: Check Gateway health
    print("1. Checking Gateway health...")
    try:
        response = requests.get(f"{GATEWAY_URL}/v1/health", headers=headers)
        if response.status_code == 200:
            health = response.json()
            print(f"   ✅ Gateway is healthy: {health.get('status', 'unknown')}")
        else:
            print(f"   ❌ Gateway health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Gateway health check error: {e}")
        return False
    
    # Step 2: List existing sessions
    print("\n2. Listing existing sessions...")
    try:
        response = requests.get(f"{GATEWAY_URL}/v1/sessions", headers=headers)
        if response.status_code == 200:
            sessions = response.json()
            print(f"   ✅ Found {len(sessions)} existing sessions")
            
            # Use the most recent session
            if sessions:
                session_id = sessions[0]['session_id']
                print(f"   📋 Using session: {session_id}")
            else:
                # Create a new session if none exist
                session_id = str(uuid.uuid4())
                print(f"   📝 Created new session: {session_id}")
        else:
            print(f"   ❌ Failed to list sessions: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Session listing error: {e}")
        return False
    
    # Step 3: Check session events
    print(f"\n3. Checking events for session {session_id}...")
    try:
        response = requests.get(f"{GATEWAY_URL}/v1/sessions/{session_id}/events", headers=headers)
        if response.status_code == 200:
            events = response.json()
            print(f"   ✅ Found {len(events.get('events', []))} events in session")
        else:
            print(f"   ❌ Failed to get events: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Events check error: {e}")
    
    # Step 4: Send a test message
    print(f"\n4. Sending test message to session {session_id}...")
    test_message = "Hello! This is a test message. Can you please respond?"
    
    try:
        # Send message via session message endpoint
        message_data = {
            "session_id": session_id,
            "message": test_message,
            "persona_id": "default"
        }
        
        response = requests.post(
            f"{GATEWAY_URL}/v1/session/message",
            headers=headers,
            json=message_data
        )
        
        if response.status_code == 200:
            print(f"   ✅ Message sent successfully")
            print(f"   📝 Message: {test_message}")
        else:
            print(f"   ❌ Failed to send message: {response.status_code}")
            print(f"   📄 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Message sending error: {e}")
        return False
    
    # Step 5: Wait for response and check events
    print(f"\n5. Waiting for AI response...")
    time.sleep(5)  # Wait for processing
    
    try:
        response = requests.get(f"{GATEWAY_URL}/v1/sessions/{session_id}/events", headers=headers)
        if response.status_code == 200:
            events = response.json()
            event_list = events.get('events', [])
            print(f"   📊 Total events: {len(event_list)}")
            
            # Find the last few events
            for event in event_list[-3:]:
                payload = event.get('payload', {})
                role = payload.get('role', 'unknown')
                msg_type = payload.get('type', 'unknown')
                message = payload.get('message', '')[:100]
                
                print(f"   📝 {role} ({msg_type}): {message}...")
                
            # Check if we got an AI response
            ai_responses = [e for e in event_list if e.get('payload', {}).get('role') == 'assistant']
            if ai_responses:
                print(f"   ✅ Found {len(ai_responses)} AI responses")
                return True
            else:
                print(f"   ⚠️  No AI responses found yet")
                return False
        else:
            print(f"   ❌ Failed to get updated events: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Response check error: {e}")
        return False

if __name__ == "__main__":
    success = test_chat_functionality()
    if success:
        print("\n🎉 Chat functionality test PASSED!")
        print("✅ Agent can send and receive messages")
    else:
        print("\n❌ Chat functionality test FAILED!")
        print("🔧 Need to configure LLM provider and check policies")