"""
Test chat endpoint with tool calling capabilities.
"""

import json
import sys

import requests

# Fix Windows encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://127.0.0.1:8001"


def test_chat_with_tools():
    """Test the chat endpoint with a conversation that has tools enabled."""

    # 1. Create a new conversation
    print("\n1. Creating conversation...")
    response = requests.post(
        f"{BASE_URL}/conversations",
        json={
            "title": "Test Chat with Tools",
            "description": "Testing tool calling functionality",
            "system_prompt": "You are a helpful assistant with access to tools. When asked about the weather, use the get_weather tool.",
        },
    )
    response.raise_for_status()
    conversation = response.json()["conversation"]
    conversation_id = conversation["id"]
    print(f"✓ Created conversation: {conversation_id}")

    # 2. Check available tools
    print("\n2. Checking available tools...")
    response = requests.get(
        f"{BASE_URL}/conversations/{conversation_id}/tools/available"
    )
    response.raise_for_status()
    available_tools = response.json()["available_tools"]
    print(f"✓ Found {len(available_tools)} available tools")
    for tool in available_tools:
        print(
            f"  - {tool['tool_name']} from {tool['server_name']} ({tool['server_id']})"
        )

    if not available_tools:
        print("\n⚠ No tools available. Make sure MCP servers are running.")
        print("Skipping tool enablement, will test basic chat instead.")
        enabled_tool = False
    else:
        # 3. Enable a tool (use the first available tool)
        print(f"\n3. Enabling tool: {available_tools[0]['tool_name']}...")
        response = requests.post(
            f"{BASE_URL}/conversations/{conversation_id}/tools",
            json={
                "server_id": available_tools[0]["server_id"],
                "tool_name": available_tools[0]["tool_name"],
            },
        )
        response.raise_for_status()
        enabled_tools = response.json()["enabled_tools"]
        print(f"✓ Enabled {len(enabled_tools)} tool(s)")
        enabled_tool = True

    # 4. Send a message that should trigger tool use (if tools enabled)
    print("\n4. Sending message to LLM...")
    if enabled_tool:
        message_content = (
            f"Can you use the {available_tools[0]['tool_name']} tool to help me?"
        )
    else:
        message_content = "Hello! Can you help me with something?"

    response = requests.post(
        f"{BASE_URL}/conversations/{conversation_id}/chat",
        json={"content": message_content},
    )

    if response.status_code != 200:
        print(f"✗ Chat failed: {response.status_code}")
        print(f"Response: {response.text}")
        return

    chat_response = response.json()
    print("✓ Chat completed successfully")

    # 5. Display messages
    print("\n5. Chat Response:")
    print(f"\nUser message:")
    print(f"  ID: {chat_response['user_message']['id']}")
    print(f"  Content: {chat_response['user_message']['content']}")

    print(f"\nAssistant message:")
    print(f"  ID: {chat_response['assistant_message']['id']}")
    print(f"  Content: {chat_response['assistant_message']['content']}")
    if chat_response["assistant_message"].get("tool_calls"):
        print(f"  Tool Calls: {len(chat_response['assistant_message']['tool_calls'])}")
        for tc in chat_response["assistant_message"]["tool_calls"]:
            print(f"    - {tc['function']['name']}: {tc['function']['arguments']}")

    # 6. Get all messages to see tool responses
    print("\n6. Fetching all messages...")
    response = requests.get(f"{BASE_URL}/conversations/{conversation_id}/messages")
    response.raise_for_status()
    all_messages = response.json()["messages"]
    print(f"✓ Found {len(all_messages)} total messages")

    print("\n7. All messages in conversation:")
    for msg in all_messages:
        print(f"\n  [{msg['role']}] {msg['id']}")
        if msg.get("content"):
            print(f"    Content: {msg['content'][:100]}...")
        if msg.get("tool_calls"):
            print(f"    Tool Calls: {json.dumps(msg['tool_calls'], indent=6)}")
        if msg.get("tool_call_id"):
            print(f"    Tool Call ID: {msg['tool_call_id']}")
            print(f"    Tool Name: {msg.get('name')}")

    print("\n✓ Test completed successfully!")


if __name__ == "__main__":
    try:
        test_chat_with_tools()
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback

        traceback.print_exc()
