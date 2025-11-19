const { message: antMessage, Button } = antd;

function ChatContainer({ conversationId, onOpenSettings, onOpenTools, onConversationUpdate }) {
    const [messages, setMessages] = React.useState([]);
    const [filteredMessages, setFilteredMessages] = React.useState([]);
    const [loading, setLoading] = React.useState(false);
    const [tokenInfo, setTokenInfo] = React.useState(null);
    const [conversation, setConversation] = React.useState(null);
    const { sendMessage, getConversation } = useConversations();

    // SSE connection for real-time tool and context events
    const handleToolEvent = React.useCallback(function(eventType, eventData) {
        const data = eventData.data;

        // Handle context events (pass through - other components may listen)
        if (eventType === 'context_added' || eventType === 'context_updated' || eventType === 'context_deleted') {
            // Just log for now, context-items will be updated via props
            console.log('[SSE] Context event received:', eventType);
            return;
        }

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
                    console.log('[Tool Event] Created temporary assistant message');
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

                console.log('[Tool Event] Total messages after adding temp:', newMessages.length);
                console.log('[Tool Event] Temporary messages in new array:', newMessages.filter(m => m._isTemporary).length);
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

            // Remove optimistic user messages - they should now be in DB
            if (msg.role === 'user' && msg._source === 'optimistic') {
                return false;
            }

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

                // Calculate approximate token count (rough estimate: 4 chars = 1 token)
                if (dbMessages.length > 0) {
                    const totalChars = dbMessages.reduce(function(sum, msg) {
                        const contentLength = msg.content ? msg.content.length : 0;
                        return sum + contentLength;
                    }, 0);
                    const estimatedTokens = Math.ceil(totalChars / 4);

                    setTokenInfo({
                        tokenCount: estimatedTokens,
                        tokensSent: estimatedTokens,
                        messagesInContext: dbMessages.length
                    });
                }
            } catch (err) {
                console.error('Failed to load conversation data:', err);
                antMessage.error('Failed to load conversation data');
            }
        }

        loadData();
    }, [conversationId, getConversation, mergeMessages]);

    // Filter messages based on max_messages setting
    React.useEffect(function() {
        console.log('[Filter Effect] Running with', messages.length, 'messages, conversation:', conversation ? 'exists' : 'null');
        console.log('[Filter Effect] Temporary messages in input:', messages.filter(m => m._isTemporary).length);

        if (!conversation || !messages.length) {
            console.log('[Filter Effect] No conversation or no messages, setting all messages');
            setFilteredMessages(messages);
            return;
        }

        const maxMessages = conversation.max_messages;
        if (!maxMessages || maxMessages >= messages.length) {
            console.log('[Filter Effect] No limit or within limit, setting all messages');
            setFilteredMessages(messages);
        } else {
            // Show only the last maxMessages messages
            const startIndex = messages.length - maxMessages;
            console.log('[Filter Effect] Applying limit, slicing from', startIndex, 'to', messages.length);
            const sliced = messages.slice(startIndex);
            console.log('[Filter Effect] After slice, temp messages:', sliced.filter(m => m._isTemporary).length);
            setFilteredMessages(sliced);
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

        // 1. OPTIMISTIC UPDATE: Add user message immediately
        const tempUserId = 'temp-user-' + Date.now();
        const optimisticUserMsg = {
            id: tempUserId,
            role: 'user',
            content: content,
            timestamp: new Date().toISOString(),
            _isTemporary: true,
            _status: 'pending',
            _source: 'optimistic'
        };

        setMessages(function(prev) {
            return [...prev, optimisticUserMsg];
        });

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
                // Request failed - rollback optimistic message
                setMessages(function(prev) {
                    return prev.filter(function(m) {
                        return m.id !== tempUserId;
                    });
                });
                antMessage.error('Failed to send message');
                throw new Error('Failed to send message'); // Trigger catch in ChatInput
            }
        } catch (err) {
            console.error('Failed to send message:', err);

            // 2. ROLLBACK: Remove optimistic message on error
            setMessages(function(prev) {
                return prev.filter(function(m) {
                    return m.id !== tempUserId;
                });
            });

            antMessage.error('Failed to send message: ' + err.message);
            throw err; // Re-throw to allow ChatInput to restore content
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
                loading: loading,
                conversationId: conversationId
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
