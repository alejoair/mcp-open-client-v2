const { Typography, Tag, Collapse, Space, Spin } = antd;
const { Text } = Typography;
const { Panel } = Collapse;

function ChatMessage({ message, toolResponses }) {
    const isUser = message.role === 'user';
    const isAssistant = message.role === 'assistant';
    const isTool = message.role === 'tool';
    const isPending = message._status === 'pending';
    const isError = message._status === 'error';

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
                    minWidth: '200px',
                    maxWidth: '70%',
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    color: 'white',
                    padding: '12px 16px',
                    borderRadius: '12px',
                    borderBottomRightRadius: '4px',
                    position: 'relative'
                }
            },
                React.createElement(Text, {
                    style: { color: 'white', display: 'block' }
                }, message.content),
                React.createElement(Text, {
                    style: {
                        color: 'rgba(255,255,255,0.5)',
                        fontSize: '9px',
                        position: 'absolute',
                        bottom: '4px',
                        right: '8px'
                    }
                }, timestamp)
            )
        );
    }

    // Assistant message style
    if (isAssistant) {
        const hasToolCalls = message.tool_calls && message.tool_calls.length > 0;

        return React.createElement('div', {
            style: {
                display: 'flex',
                justifyContent: 'flex-start',
                marginBottom: '16px'
            }
        },
            React.createElement('div', {
                style: {
                    maxWidth: '90%',
                    background: '#0d0d15',
                    padding: '10px 14px',
                    borderRadius: '12px',
                    borderBottomLeftRadius: '4px',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
                    position: 'relative',
                    color: 'rgba(255, 255, 255, 0.9)'
                }
            },
                // Show tool calls if present
                hasToolCalls && React.createElement('div', {
                    style: {
                        marginBottom: message.content ? '12px' : '0',
                        paddingBottom: message.content ? '12px' : '0',
                        borderBottom: message.content ? '1px solid rgba(255, 255, 255, 0.08)' : 'none'
                    }
                },
                    React.createElement(ToolCallsInline, {
                        toolCalls: message.tool_calls,
                        toolResponses: toolResponses
                    })
                ),
                // Show content if present
                message.content ? React.createElement(MarkdownRenderer, {
                    content: message.content
                }) : null,
                React.createElement(Text, {
                    style: {
                        color: 'rgba(255,255,255,0.4)',
                        fontSize: '9px',
                        position: 'absolute',
                        bottom: '4px',
                        right: '8px'
                    }
                }, timestamp)
            )
        );
    }

    // Tool response message style
    if (isTool) {
        // Try to parse the tool response as JSON
        let parsedResponse = null;
        let isValidJSON = false;

        if (message.content) {
            try {
                parsedResponse = JSON.parse(message.content);
                isValidJSON = true;
            } catch (e) {
                // Not valid JSON, will display as text
                parsedResponse = message.content;
            }
        }

        return React.createElement('div', {
            style: {
                display: 'flex',
                justifyContent: 'flex-start',
                marginBottom: '8px',
                marginLeft: '20px',
                opacity: isPending ? 0.7 : 1
            }
        },
            React.createElement('div', {
                style: {
                    maxWidth: 'calc(70% - 20px)',
                    background: isError ? '#3d1a1a' : '#2a2a2a',
                    padding: '10px 14px',
                    borderRadius: '12px',
                    borderLeft: '4px solid ' + (isError ? '#ff4d4f' : '#1890ff'),
                    position: 'relative',
                    color: 'rgba(255, 255, 255, 0.9)'
                }
            },
                React.createElement(Space, { direction: 'vertical', style: { width: '100%' } },
                    React.createElement('div', {
                        style: { display: 'flex', gap: '6px', alignItems: 'center' }
                    },
                        React.createElement(Tag, {
                            color: isError ? 'red' : 'blue',
                            style: { fontSize: '11px', padding: '0 6px', margin: 0 }
                        }, message.name),
                        isPending && React.createElement(Spin, { size: 'small' }),
                        isPending && React.createElement(Text, {
                            type: 'secondary',
                            style: { fontSize: '11px' }
                        }, 'Executing...')
                    ),
                    !isPending && message.content && React.createElement(Collapse, {
                        ghost: true,
                        defaultActiveKey: []
                    },
                        React.createElement(Panel, {
                            header: isError ? 'Error' : (isValidJSON ? 'Tool Response (JSON)' : 'Tool Response'),
                            key: '1'
                        },
                            isValidJSON ? React.createElement('pre', {
                                style: {
                                    background: '#1a1a1a',
                                    padding: '8px',
                                    borderRadius: '4px',
                                    fontSize: '12px',
                                    overflow: 'auto',
                                    maxHeight: '300px',
                                    whiteSpace: 'pre-wrap',
                                    color: 'rgba(255, 255, 255, 0.9)',
                                    border: '1px solid rgba(255, 255, 255, 0.1)'
                                }
                            }, JSON.stringify(parsedResponse, null, 2)) :
                            React.createElement('pre', {
                                style: {
                                    background: '#1a1a1a',
                                    padding: '8px',
                                    borderRadius: '4px',
                                    fontSize: '12px',
                                    overflow: 'auto',
                                    maxHeight: '300px',
                                    whiteSpace: 'pre-wrap',
                                    color: 'rgba(255, 255, 255, 0.9)',
                                    border: '1px solid rgba(255, 255, 255, 0.1)'
                                }
                            }, message.content)
                        )
                    ),
                    React.createElement(Text, {
                        style: {
                            color: 'rgba(255,255,255,0.4)',
                            fontSize: '9px',
                            position: 'absolute',
                            bottom: '4px',
                            right: '8px'
                        }
                    }, timestamp)
                )
            )
        );
    }

    // Fallback for unknown message types
    return React.createElement('div', {
        style: { marginBottom: '16px' }
    },
        React.createElement(Text, {
            type: 'secondary',
            style: { color: 'rgba(255, 255, 255, 0.7)' }
        },
            `Unknown message type: ${message.role}`
        )
    );
}
