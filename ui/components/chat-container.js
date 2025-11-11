const { message: antMessage } = antd;

function ChatContainer({ conversationId }) {
    const [messages, setMessages] = React.useState([]);
    const [loading, setLoading] = React.useState(false);
    const [tokenInfo, setTokenInfo] = React.useState(null);
    const { sendMessage } = useConversations();

    // Load messages when conversation changes
    React.useEffect(function() {
        if (!conversationId) {
            setMessages([]);
            return;
        }

        async function loadMessages() {
            try {
                const response = await conversationsService.getMessages(conversationId);
                setMessages(response.messages || []);
            } catch (err) {
                console.error('Failed to load messages:', err);
                antMessage.error('Failed to load messages');
            }
        }

        loadMessages();
    }, [conversationId]);

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
                flexWrap: 'wrap'
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
                messages: messages,
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
