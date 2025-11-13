---
layout: default
title: Frontend Implementation Plan
---

# Frontend Implementation Plan - Chat UI

## Current Architecture

### Communication Layer

**Base API Client:** `ui/services/api.js`
```javascript
api.get(endpoint)
api.post(endpoint, body)
api.put(endpoint, body)
api.delete(endpoint)
```
- Base URL: `http://127.0.0.1:8001`
- Auto JSON parsing
- Error handling with console logs

**Conversations Service:** `ui/services/conversationsService.js`
- Wraps API client with conversation-specific methods
- Provides: CRUD, messages, context, tools, editors

**React Context:** `ui/contexts/ConversationsContext.js`
- Global state management
- Auto-loads conversations on mount
- Exposes hooks via `useConversations()`

### Existing Components

**Layout:**
- `main_layout.js` - Root layout with sidebar
- `chat-layout.js` - Tab container for conversations
- `left_sidebar.js` - Menu with conversations list
- `conversations-list.js` - List of conversations

**Modals:**
- `conversation-settings-modal.js` - Edit title, description, system prompt
- `conversation-tools-modal.js` - Enable/disable tools

## Implementation Plan

### Phase 1: Data Layer (Service + Context)

#### 1.1 Add Chat Methods to Service
**File:** `ui/services/conversationsService.js`

Add method:
```javascript
async sendMessage(conversationId, content) {
    return await api.post(`/conversations/${conversationId}/chat`, { content });
}
```

#### 1.2 Extend Context
**File:** `ui/contexts/ConversationsContext.js`

Add to context value:
```javascript
sendMessage: async (conversationId, content) => {
    const response = await conversationsService.sendMessage(conversationId, content);
    return response; // { success, user_message, assistant_message }
}
```

### Phase 2: Core Chat Components

#### 2.1 Chat Message Component
**File:** `ui/components/chat-message.js`

**Props:**
- `message` - Message object with role, content, tool_calls, etc.

**Responsibilities:**
- Render user messages (right-aligned, blue background)
- Render assistant messages (left-aligned, white background)
- Render tool messages (collapsed by default, gray)
- Use markdown for content
- Show timestamps

**Key Structure:**
```javascript
function ChatMessage({ message }) {
    // Different styles for user/assistant/tool
    // Markdown rendering for content
    // Tool calls display if present
}
```

#### 2.2 Messages List Component
**File:** `ui/components/chat-messages-list.js`

**Props:**
- `messages` - Array of message objects
- `loading` - Boolean for typing indicator

**Responsibilities:**
- Render list of ChatMessage components
- Auto-scroll to bottom on new messages
- Show typing indicator while waiting
- Empty state when no messages

**Key Structure:**
```javascript
function ChatMessagesList({ messages, loading }) {
    const messagesEndRef = React.useRef(null);

    // Auto-scroll effect
    React.useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);
}
```

#### 2.3 Chat Input Component
**File:** `ui/components/chat-input.js`

**Props:**
- `onSend` - Callback(content)
- `disabled` - Boolean (while loading)

**Responsibilities:**
- Textarea with auto-resize
- Send button (or Enter key)
- Disable while message sending
- Clear input after send

**Key Structure:**
```javascript
function ChatInput({ onSend, disabled }) {
    const [value, setValue] = React.useState('');

    const handleSend = () => {
        if (!value.trim() || disabled) return;
        onSend(value);
        setValue('');
    };
}
```

#### 2.4 Chat Container Component
**File:** `ui/components/chat-container.js`

**Props:**
- `conversationId` - Current conversation ID

**Responsibilities:**
- Fetch and display messages
- Handle send message
- Manage loading state
- Coordinate messages list and input

**Key Structure:**
```javascript
function ChatContainer({ conversationId }) {
    const [messages, setMessages] = React.useState([]);
    const [loading, setLoading] = React.useState(false);
    const { sendMessage } = useConversations();

    // Load messages on mount
    React.useEffect(() => {
        loadMessages(conversationId);
    }, [conversationId]);

    const handleSend = async (content) => {
        setLoading(true);
        const response = await sendMessage(conversationId, content);
        setMessages(prev => [...prev, response.user_message, response.assistant_message]);
        setLoading(false);
    };
}
```

### Phase 3: Tool Display Components

#### 3.1 Tool Call Display
**File:** `ui/components/tool-call-display.js`

**Props:**
- `toolCall` - Tool call object

**Renders:**
- Tool name badge
- Arguments in collapsible JSON viewer
- Icon for tool type

#### 3.2 Tool Response Display
**File:** `ui/components/tool-response-display.js`

**Props:**
- `toolResponse` - Tool response message

**Renders:**
- Tool name badge
- Result in collapsible JSON/text viewer
- Success/error indicator

### Phase 4: Integration

#### 4.1 Update Chat Layout
**File:** `ui/components/chat-layout.js`

Replace tab content from empty div to:
```javascript
children: React.createElement(ChatContainer, {
    conversationId: conversation.id
})
```

#### 4.2 Add Markdown Renderer
**Use:** CDN library like `marked` or `react-markdown`

Add to `ui/index.html`:
```html
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
```

Create `ui/components/markdown-renderer.js`:
```javascript
function MarkdownRenderer({ content }) {
    const html = marked.parse(content);
    return React.createElement('div', {
        className: 'markdown-content',
        dangerouslySetInnerHTML: { __html: html }
    });
}
```

## API Endpoints Used

```
GET  /conversations/{id}/messages     - Load conversation messages
POST /conversations/{id}/chat         - Send message to LLM
```

**Request:**
```json
{ "content": "user message" }
```

**Response:**
```json
{
  "success": true,
  "user_message": { "id": "...", "role": "user", "content": "..." },
  "assistant_message": { "id": "...", "role": "assistant", "content": "..." }
}
```

## Message Flow

```
User types message
    ↓
ChatInput.handleSend()
    ↓
ChatContainer.handleSend()
    ↓
ConversationsContext.sendMessage()
    ↓
conversationsService.sendMessage()
    ↓
api.post('/conversations/{id}/chat')
    ↓
Backend processes (tool calling loop)
    ↓
Response with user_message + assistant_message
    ↓
Update messages state
    ↓
ChatMessagesList re-renders
    ↓
Auto-scroll to bottom
```

## File Load Order

**Current:**
1. `services/api.js`
2. `services/conversationsService.js`
3. `contexts/ConversationsContext.js`
4. `hooks/useConversations.js`
5. Existing components

**Add:**
6. `components/markdown-renderer.js`
7. `components/tool-call-display.js`
8. `components/tool-response-display.js`
9. `components/chat-message.js`
10. `components/chat-messages-list.js`
11. `components/chat-input.js`
12. `components/chat-container.js`

## Styling Approach

**Use Ant Design components:**
- `List` for messages
- `Input.TextArea` for chat input
- `Button` for send
- `Spin` for loading
- `Empty` for empty state
- `Tag` for tool names
- `Collapse` for tool details

**Custom CSS:**
- Message bubbles (user vs assistant)
- Auto-scroll container
- Markdown content styles

## Implementation Order

1. **Service Layer** - Add `sendMessage()` to service and context
2. **ChatMessage** - Single message rendering
3. **ChatMessagesList** - List with auto-scroll
4. **ChatInput** - Input with send button
5. **ChatContainer** - Orchestrate everything
6. **MarkdownRenderer** - Render message content
7. **Tool Components** - Display tool calls/responses
8. **Integration** - Connect to chat-layout.js

## Testing Strategy

1. Load conversation → See empty state
2. Send message → See user + assistant messages
3. Send with tools enabled → See tool calls/responses
4. Markdown rendering → Code blocks, lists, etc.
5. Auto-scroll → Always at bottom
6. Loading states → Disabled input, typing indicator
