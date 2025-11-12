const { message: antMessage } = antd;

function ChatContainer({ conversationId }) {
    const [messages, setMessages] = React.useState([]);
    const [filteredMessages, setFilteredMessages] = React.useState([]);
    const [loading, setLoading] = React.useState(false);
    const [tokenInfo, setTokenInfo] = React.useState(null);
    const [conversation, setConversation] = React.useState(null);
    const { sendMessage, getConversation } = useConversations();
    
    // Import hook dynamically to avoid circular dependencies
    const [toolEvents, setToolEvents] = React.useState([]);
    const [isSSEConnected, setIsSSEConnected] = React.useState(false);
    const [isSSEConnecting, setIsSSEConnecting] = React.useState(false);
    
    // Setup SSE connection
    React.useEffect(function() {
        if (!conversationId) return;
        
        setIsSSEConnecting(true);
        setToolEvents([]);
        
        const baseUrl = window.location.origin;
        const sseUrl = `${baseUrl}/sse/conversations/${conversationId}`;
        
        const eventSource = new EventSource(sseUrl);
        
        eventSource.onopen = function() {
            console.log('SSE connection opened for conversation:', conversationId);
            setIsSSEConnecting(false);
            setIsSSEConnected(true);
        };
        
        eventSource.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                console.log('SSE Event received:', data);
                setToolEvents(prev => [...prev, {
                    ...data,
                    id: Date.now() + Math.random()
                }]);
            } catch (error) {
                console.error('Error parsing SSE event data:', error);
            }
        };
        
        eventSource.onerror = function(error) {
            console.error('SSE connection error:', error);
            setIsSSEConnecting(false);
            setIsSSEConnected(false);
        };
        
        return function() {
            eventSource.close();
            setIsSSEConnected(false);
            setIsSSEConnecting(false);
        };
    }, [conversationId]);

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

                // Load messages
                const messagesData = await conversationsService.getMessages(conversationId);
                setMessages(messagesData.messages || []);
            } catch (err) {
                console.error('Failed to load conversation data:', err);
                antMessage.error('Failed to load conversation data');
            }
        }

        loadData();
    }, [conversationId, getConversation]);

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

                // Reload all messages to include tool calls and tool responses
                try {
                    const messagesData = await conversationsService.getMessages(conversationId);
                    setMessages(messagesData.messages || []);
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
    }, [conversationId, sendMessage]);

    return React.createElement('div', {
        style: {
            height: '100%',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden'
        }
    },
        // Token info display (if available)
        tokenInfo && React.createElement('div', {
            style: {
                padding: '8px 16px',
                backgroundColor: '#f0f0f0',
                borderBottom: '1px solid #d9d9d9',
                display: 'flex',
                gap: '12px',
                flexWrap: 'wrap',
                alignItems: 'center'
            }
        },
            React.createElement(antd.Tag, { color: 'blue' },
                'Tokens: ' + tokenInfo.tokenCount
            ),
            React.createElement(antd.Tag, { color: 'green' },
                'Sent: ' + tokenInfo.tokensSent
            ),
            React.createElement(antd.Tag, { color: 'orange' },
                'Messages: ' + tokenInfo.messagesInContext
            ),
            // Show hidden messages indicator
            conversation && conversation.max_messages && messages.length > conversation.max_messages && React.createElement('div', {
                style: {
                    marginLeft: 'auto',
                    fontSize: '12px',
                    color: '#666',
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
            }),
            // Tool call streaming display
            React.createElement(ToolCallDisplay, {
                events: toolEvents,
                isConnected: isSSEConnected,
                isConnecting: isSSEConnecting
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
