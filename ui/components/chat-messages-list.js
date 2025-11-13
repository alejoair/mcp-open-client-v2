const { Spin, Empty } = antd;

function ChatMessagesList({ messages, loading }) {
    const messagesEndRef = React.useRef(null);

    // Group assistant messages with their tool responses
    // IMPORTANT: Must be called before any conditional returns (Rules of Hooks)
    const groupedMessages = React.useMemo(function() {
        if (!messages || !Array.isArray(messages)) {
            return [];
        }

        const groups = [];
        let i = 0;

        while (i < messages.length) {
            const msg = messages[i];

            // If assistant message with tool_calls, group with following tool messages
            if (msg.role === 'assistant' && msg.tool_calls && msg.tool_calls.length > 0) {
                const toolCallIds = msg.tool_calls.map(function(tc) { return tc.id; });
                const toolResponses = [];

                // Collect consecutive tool responses that match the tool_calls
                let j = i + 1;
                while (j < messages.length && messages[j].role === 'tool') {
                    const toolMsg = messages[j];
                    if (toolCallIds.includes(toolMsg.tool_call_id)) {
                        toolResponses.push(toolMsg);
                        j++;
                    } else {
                        break;
                    }
                }

                groups.push({
                    type: 'assistant_with_tools',
                    message: msg,
                    toolResponses: toolResponses
                });

                i = j; // Skip the tool messages we just grouped
            } else {
                groups.push({
                    type: 'single',
                    message: msg
                });
                i++;
            }
        }

        return groups;
    }, [messages]);

    // Auto-scroll to bottom when messages change
    React.useEffect(function() {
        if (messagesEndRef.current) {
            messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [messages, loading]);

    // Empty state
    if (!messages || messages.length === 0) {
        return React.createElement('div', {
            style: {
                height: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                background: '#0a0a0f'
            }
        },
            React.createElement(Empty, {
                description: React.createElement('span', {
                    style: { color: 'rgba(255, 255, 255, 0.5)' }
                }, 'No messages yet. Start a conversation!'),
                image: Empty.PRESENTED_IMAGE_SIMPLE,
                imageStyle: { opacity: 0.3 }
            })
        );
    }

    return React.createElement('div', {
        style: {
            padding: '16px',
            display: 'flex',
            flexDirection: 'column',
            minHeight: '100%',
            background: '#0a0a0f'
        }
    },
        // Render grouped messages
        groupedMessages.map(function(group, idx) {
            if (group.type === 'assistant_with_tools') {
                return React.createElement(ChatMessage, {
                    key: group.message.id,
                    message: group.message,
                    toolResponses: group.toolResponses
                });
            } else {
                return React.createElement(ChatMessage, {
                    key: group.message.id,
                    message: group.message
                });
            }
        }),
        // Loading indicator
        loading ? React.createElement('div', {
            style: {
                display: 'flex',
                justifyContent: 'flex-start',
                marginBottom: '16px'
            }
        },
            React.createElement('div', {
                style: {
                    background: '#2a2a2a',
                    padding: '12px 16px',
                    borderRadius: '12px',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
                    color: 'rgba(255, 255, 255, 0.9)'
                }
            },
                React.createElement(Spin, {
                    size: 'small',
                    tip: 'Thinking...'
                })
            )
        ) : null,
        // Scroll anchor
        React.createElement('div', {
            ref: messagesEndRef
        })
    );
}
