const { message: antMessage, Button } = antd;

function ChatContainer({ conversationId, onOpenSettings, onOpenTools, onConversationUpdate }) {
    const [messages, setMessages] = React.useState([]);
    const [filteredMessages, setFilteredMessages] = React.useState([]);
    const [loading, setLoading] = React.useState(false);
    const [tokenInfo, setTokenInfo] = React.useState(null);
    const [conversation, setConversation] = React.useState(null);
    const { sendMessage, getConversation } = useConversations();

    // SSE connection for real-time tool events
    const handleToolEvent = React.useCallback(function(eventType, event) {
        const data = event.data;

        if (eventType === 'tool_call') {
            console.log('[Tool Event] Tool call started:', data.tool_name, data.tool_call_id);

            // Create temporary assistant message with tool_calls (if not exists)
            setMessages(function(prev) {
                // Check if assistant message already exists for this tool_call
                const hasAssistantMsg = prev.some(function(m) {
                    return m.role === 'assistant' && m.tool_calls && m.tool_calls.some(function(tc) {
                        return tc.id === data.tool_call_id;
                    });
                });

                const newMessages = [...prev];

                if (!hasAssistantMsg) {
                    // Add temporary assistant message
                    newMessages.push({
                        id: 'temp-assistant-' + data.tool_call_id,
                        role: 'assistant',
                        content: data.assistant_content || '',
                        timestamp: data.timestamp,
                        tool_calls: [{
                            id: data.tool_call_id,
                            type: 'function',
                            function: {
                                name: data.tool_name,
                                arguments: JSON.stringify(data.arguments)
                            }
                        }],
                        _source: 'sse',
                        _status: 'pending',
                        _isTemporary: true
                    });
                }

                // Add temporary tool message (pending)
                newMessages.push({
                    id: 'temp-tool-' + data.tool_call_id,
                    role: 'tool',
                    content: null,
                    timestamp: data.timestamp,
                    tool_call_id: data.tool_call_id,
                    name: data.tool_name,
                    _source: 'sse',
                    _status: 'pending',
                    _isTemporary: true
                });

                return newMessages;
            });
        }
        else if (eventType === 'tool_response') {
            console.log('[Tool Event] Tool response received:', data.tool_name, data.tool_call_id);

            // Update temporary tool message with result
            setMessages(function(prev) {
                return prev.map(function(msg) {
                    if (msg.tool_call_id === data.tool_call_id && msg._isTemporary) {
                        return {
                            ...msg,
                            content: data.result,
                            _status: 'completed',
                            timestamp: data.timestamp
                        };
                    }
                    return msg;
                });
            });
        }
        else if (eventType === 'tool_error') {
            console.log('[Tool Event] Tool error:', data.tool_name, data.error);

            // Update temporary tool message with error
            setMessages(function(prev) {
                return prev.map(function(msg) {
                    if (msg.tool_call_id === data.tool_call_id && msg._isTemporary) {
                        return {
                            ...msg,
                            content: JSON.stringify({ error: data.error }),
                            _status: 'error',
                            timestamp: data.timestamp
                        };
                    }
                    return msg;
                });
            });
        }
    }, []);

    // Connect to SSE
    const { connected: sseConnected } = useSSEConnection(conversationId, handleToolEvent);

    // Merge DB messages with temporary SSE messages
    const mergeMessages = React.useCallback(function(dbMessages, currentMessages) {
        console.log('[Merge] Merging', dbMessages.length, 'DB messages with', currentMessages.length, 'current messages');

        // Get temporary tool_call_ids
        const tempToolCallIds = new Set();
        currentMessages.forEach(function(msg) {
            if (msg._isTemporary && msg.tool_call_id) {
                tempToolCallIds.add(msg.tool_call_id);
            }
        });

        // Filter out temporary messages that now exist in DB
        const filteredTemp = currentMessages.filter(function(msg) {
            if (!msg._isTemporary) return false;

            // Keep temporary tool messages only if no DB version exists
            if (msg.role === 'tool') {
                const hasDBVersion = dbMessages.some(function(db) {
                    return db.role === 'tool' && db.tool_call_id === msg.tool_call_id;
                });
                return !hasDBVersion;
            }

            // Keep temporary assistant messages only if no DB version with this tool_call exists
            if (msg.role === 'assistant' && msg.tool_calls) {
                const toolCallId = msg.tool_calls[0]?.id;
                const hasDBVersion = dbMessages.some(function(db) {
                    return db.role === 'assistant' && db.tool_calls &&
                           db.tool_calls.some(function(tc) { return tc.id === toolCallId; });
                });
                return !hasDBVersion;
            }

            return true;
        });

        // Add metadata to DB messages
        const dbMessagesWithMeta = dbMessages.map(function(msg) {
            return {
                ...msg,
                _source: 'db',
                _status: 'completed',
                _isTemporary: false
            };
        });

        // Merge and sort by timestamp
        const merged = [...dbMessagesWithMeta, ...filteredTemp];
        merged.sort(function(a, b) {
            return new Date(a.timestamp) - new Date(b.timestamp);
        });

        console.log('[Merge] Result:', merged.length, 'messages');
        return merged;
    }, []);

    // Load conversation and messages when conversation changes
    React.useEffect(function() {
        if (!conversationId) {
            setMessages([]);
            setFilteredMessages([]);
            setConversation(null);
            return;
        }

        async function loadData() {
            try {
                // Load conversation settings
                const conversationData = await getConversation(conversationId);
                setConversation(conversationData);

                // Load messages and merge with temporary ones
                const messagesData = await conversationsService.getMessages(conversationId);
                const dbMessages = messagesData.messages || [];
                setMessages(function(prev) {
                    return mergeMessages(dbMessages, prev);
                });
            } catch (err) {
                console.error('Failed to load conversation data:', err);
                antMessage.error('Failed to load conversation data');
            }
        }

        loadData();
    }, [conversationId, getConversation, mergeMessages]);

    // Filter messages based on max_messages setting
    React.useEffect(function() {
        if (!conversation || !messages.length) {
            setFilteredMessages(messages);
            return;
        }

        const maxMessages = conversation.max_messages;
        if (!maxMessages || maxMessages >= messages.length) {
            setFilteredMessages(messages);
        } else {
            // Show only the last maxMessages messages
            const startIndex = messages.length - maxMessages;
            setFilteredMessages(messages.slice(startIndex));
        }
    }, [messages, conversation]);

    // Notify parent of conversation updates
    React.useEffect(function() {
        if (onConversationUpdate) {
            onConversationUpdate({
                conversation: conversation,
                tokenInfo: tokenInfo,
                messageCount: messages.length
            });
        }
    }, [conversation, tokenInfo, messages.length, onConversationUpdate]);

    const handleSend = React.useCallback(async function(content) {
        if (!conversationId) {
            antMessage.error('No conversation selected');
            return;
        }

        setLoading(true);
        try {
            const response = await sendMessage(conversationId, content);

            if (response.success) {
                // Update token info
                setTokenInfo({
                    tokenCount: response.token_count,
                    tokensSent: response.tokens_sent,
                    messagesInContext: response.messages_in_context
                });

                // Wait a bit for SSE events to arrive, then reload
                await new Promise(function(resolve) { setTimeout(resolve, 500); });

                // Reload all messages and merge with temporary ones
                try {
                    const messagesData = await conversationsService.getMessages(conversationId);
                    const dbMessages = messagesData.messages || [];
                    setMessages(function(prev) {
                        return mergeMessages(dbMessages, prev);
                    });
                    // Reload conversation data to get updated settings
                    const conversationData = await getConversation(conversationId);
                    setConversation(conversationData);
                } catch (err) {
                    console.error('Failed to reload messages:', err);
                    // Fallback: just add user and assistant messages
                    setMessages(function(prev) {
                        return [...prev, response.user_message, response.assistant_message];
                    });
                }
            } else {
                antMessage.error('Failed to send message');
            }
        } catch (err) {
            console.error('Failed to send message:', err);
            antMessage.error('Failed to send message: ' + err.message);
        } finally {
            setLoading(false);
        }
    }, [conversationId, sendMessage, mergeMessages, getConversation]);

    return React.createElement('div', {
        style: {
            height: '100%',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden'
        }
    },
        // Info bar with tokens and buttons (always visible)
        React.createElement('div', {
            style: {
                padding: '8px 16px',
                backgroundColor: '#2a2a2a',
                borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
                display: 'flex',
                gap: '12px',
                flexWrap: 'wrap',
                alignItems: 'center'
            }
        },
            // Show token info if available
            tokenInfo && React.createElement(React.Fragment, null,
                React.createElement(antd.Tag, { color: 'blue' },
                    'Tokens: ' + tokenInfo.tokenCount
                ),
                React.createElement(antd.Tag, { color: 'orange' },
                    'Messages: ' + tokenInfo.messagesInContext
                )
            ),
            // Show hidden messages indicator
            tokenInfo && conversation && conversation.max_messages && messages.length > conversation.max_messages && React.createElement('div', {
                style: {
                    fontSize: '12px',
                    color: 'rgba(255, 255, 255, 0.7)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                }
            },
                React.createElement(antd.Tag, { color: 'default', size: 'small' },
                    `${messages.length - conversation.max_messages} hidden`
                ),
                React.createElement('span', null,
                    `Showing ${filteredMessages.length} of ${messages.length} messages`
                )
            ),
            // Settings and tools buttons (always visible)
            React.createElement('div', {
                style: {
                    marginLeft: 'auto',
                    display: 'flex',
                    gap: '8px'
                }
            },
                React.createElement(Button, {
                    type: 'default',
                    size: 'small',
                    icon: React.createElement('i', { className: 'fas fa-cog' }),
                    onClick: onOpenSettings,
                    title: 'Conversation Settings'
                }, 'Settings'),
                React.createElement(Button, {
                    type: 'default',
                    size: 'small',
                    icon: React.createElement('i', { className: 'fas fa-wrench' }),
                    onClick: onOpenTools,
                    title: 'Configure Tools'
                }, 'Tools')
            )
        ),
        // Messages list (takes remaining space with scroll)
        React.createElement('div', {
            style: {
                flex: 1,
                overflowY: 'auto',
                minHeight: 0
            }
        },
            React.createElement(ChatMessagesList, {
                messages: filteredMessages,
                loading: loading
            })
        ),
        // Input at bottom (fixed)
        React.createElement('div', {
            style: {
                flexShrink: 0
            }
        },
            React.createElement(ChatInput, {
                onSend: handleSend,
                disabled: loading
            })
        )
    );
}
