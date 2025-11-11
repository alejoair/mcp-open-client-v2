const { Typography, Tag, Collapse, Space } = antd;
const { Text } = Typography;
const { Panel } = Collapse;

function ChatMessage({ message }) {
    const isUser = message.role === 'user';
    const isAssistant = message.role === 'assistant';
    const isTool = message.role === 'tool';

    // Format timestamp
    const timestamp = React.useMemo(function() {
        return new Date(message.timestamp).toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
        });
    }, [message.timestamp]);

    // User message style
    if (isUser) {
        return React.createElement('div', {
            style: {
                display: 'flex',
                justifyContent: 'flex-end',
                marginBottom: '16px'
            }
        },
            React.createElement('div', {
                style: {
                    maxWidth: '70%',
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    color: 'white',
                    padding: '12px 16px',
                    borderRadius: '12px',
                    borderBottomRightRadius: '4px'
                }
            },
                React.createElement(Text, {
                    style: { color: 'white', display: 'block', marginBottom: '4px' }
                }, message.content),
                React.createElement(Text, {
                    style: { color: 'rgba(255,255,255,0.7)', fontSize: '12px' }
                }, timestamp)
            )
        );
    }

    // Assistant message style
    if (isAssistant) {
        return React.createElement('div', {
            style: {
                display: 'flex',
                justifyContent: 'flex-start',
                marginBottom: '16px'
            }
        },
            React.createElement('div', {
                style: {
                    maxWidth: '70%',
                    background: 'white',
                    padding: '12px 16px',
                    borderRadius: '12px',
                    borderBottomLeftRadius: '4px',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
                }
            },
                // Show tool calls if present
                message.tool_calls && message.tool_calls.length > 0 ?
                    React.createElement(Space, { direction: 'vertical', style: { width: '100%', marginBottom: '8px' } },
                        React.createElement(Text, { strong: true, style: { fontSize: '12px' } }, 'Tool Calls:'),
                        message.tool_calls.map(function(tc) {
                            return React.createElement(Tag, {
                                key: tc.id,
                                color: 'blue',
                                style: { marginBottom: '4px' }
                            }, tc.function.name);
                        })
                    ) : null,
                // Show content if present
                message.content ? React.createElement(MarkdownRenderer, {
                    content: message.content
                }) : null,
                React.createElement(Text, {
                    style: { color: 'rgba(0,0,0,0.45)', fontSize: '12px', display: 'block', marginTop: '4px' }
                }, timestamp)
            )
        );
    }

    // Tool response message style
    if (isTool) {
        return React.createElement('div', {
            style: {
                display: 'flex',
                justifyContent: 'flex-start',
                marginBottom: '16px'
            }
        },
            React.createElement('div', {
                style: {
                    maxWidth: '70%',
                    background: '#f5f5f5',
                    padding: '12px 16px',
                    borderRadius: '12px',
                    borderLeft: '3px solid #1890ff'
                }
            },
                React.createElement(Space, { direction: 'vertical', style: { width: '100%' } },
                    React.createElement(Tag, { color: 'blue' }, message.name),
                    React.createElement(Collapse, {
                        ghost: true,
                        defaultActiveKey: []
                    },
                        React.createElement(Panel, {
                            header: 'Tool Response',
                            key: '1'
                        },
                            React.createElement('pre', {
                                style: {
                                    background: 'white',
                                    padding: '8px',
                                    borderRadius: '4px',
                                    fontSize: '12px',
                                    overflow: 'auto',
                                    maxHeight: '300px'
                                }
                            }, message.content)
                        )
                    ),
                    React.createElement(Text, {
                        style: { color: 'rgba(0,0,0,0.45)', fontSize: '12px' }
                    }, timestamp)
                )
            )
        );
    }

    // Fallback for unknown message types
    return React.createElement('div', {
        style: { marginBottom: '16px' }
    },
        React.createElement(Text, { type: 'secondary' },
            `Unknown message type: ${message.role}`
        )
    );
}
