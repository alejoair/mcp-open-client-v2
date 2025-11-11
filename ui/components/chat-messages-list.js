const { Spin, Empty } = antd;

function ChatMessagesList({ messages, loading }) {
    const messagesEndRef = React.useRef(null);

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
                justifyContent: 'center'
            }
        },
            React.createElement(Empty, {
                description: 'No messages yet. Start a conversation!'
            })
        );
    }

    return React.createElement('div', {
        style: {
            padding: '16px',
            display: 'flex',
            flexDirection: 'column',
            minHeight: '100%'
        }
    },
        // Render all messages
        messages.map(function(message) {
            return React.createElement(ChatMessage, {
                key: message.id,
                message: message
            });
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
                    background: 'white',
                    padding: '12px 16px',
                    borderRadius: '12px',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
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
