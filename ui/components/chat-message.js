const { Typography, Tag, Collapse, Space, Spin } = antd;
const { Text } = Typography;
const { Panel } = Collapse;

function ChatMessage({ message }) {
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
        // Reduce spacing when message has tool calls (response will follow)
        const hasToolCalls = message.tool_calls && message.tool_calls.length > 0;

        return React.createElement('div', {
            style: {
                display: 'flex',
                justifyContent: 'flex-start',
                marginBottom: hasToolCalls ? '4px' : '16px'
            }
        },
            React.createElement('div', {
                style: {
                    maxWidth: '70%',
                    background: 'white',
                    padding: '10px 14px',
                    borderRadius: '12px',
                    borderBottomLeftRadius: '4px',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
                }
            },
                // Show tool calls if present
                hasToolCalls ?
                    React.createElement(Space, { direction: 'vertical', style: { width: '100%', marginBottom: '4px' } },
                        React.createElement(Text, { strong: true, style: { fontSize: '11px' } }, 'Tool Calls:'),
                        message.tool_calls.map(function(tc) {
                            // Parse arguments if available
                            let parsedArgs = null;
                            let isValidJSON = false;
                            
                            if (tc.function.arguments) {
                                try {
                                    parsedArgs = JSON.parse(tc.function.arguments);
                                    isValidJSON = true;
                                } catch (e) {
                                    parsedArgs = tc.function.arguments;
                                }
                            }
                            
                            // Create summary for header
                            let argsDisplay = '';
                            if (parsedArgs && typeof parsedArgs === 'object') {
                                const keys = Object.keys(parsedArgs);
                                if (keys.length === 0) {
                                    argsDisplay = 'no arguments';
                                } else {
                                    argsDisplay = `${keys[0]}: ${parsedArgs[keys[0]]}`;
                                    if (keys.length > 1) argsDisplay += '...';
                                }
                            } else if (typeof parsedArgs === 'string') {
                                argsDisplay = 'arguments provided';
                            }
                            
                            return React.createElement(Collapse, {
                                key: tc.id,
                                ghost: true,
                                defaultActiveKey: []
                            },
                                React.createElement(Panel, {
                                    header: isValidJSON ? 'Tool Call (JSON)' : 'Tool Call Arguments',
                                    key: '1'
                                },
                                    React.createElement('pre', {
                                        style: {
                                            background: 'white',
                                            padding: '8px',
                                            borderRadius: '4px',
                                            fontSize: '12px',
                                            overflow: 'auto',
                                            maxHeight: '300px',
                                            margin: 0,
                                            whiteSpace: 'pre-wrap'
                                        }
                                    }, isValidJSON ? JSON.stringify(parsedArgs, null, 2) : parsedArgs || 'No arguments provided')
                                )
                            );
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
                    background: isError ? '#fff1f0' : '#f5f5f5',
                    padding: '10px 14px',
                    borderRadius: '12px',
                    borderLeft: '4px solid ' + (isError ? '#ff4d4f' : '#1890ff')
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
                                    background: 'white',
                                    padding: '8px',
                                    borderRadius: '4px',
                                    fontSize: '12px',
                                    overflow: 'auto',
                                    maxHeight: '300px',
                                    whiteSpace: 'pre-wrap'
                                }
                            }, JSON.stringify(parsedResponse, null, 2)) :
                            React.createElement('pre', {
                                style: {
                                    background: 'white',
                                    padding: '8px',
                                    borderRadius: '4px',
                                    fontSize: '12px',
                                    overflow: 'auto',
                                    maxHeight: '300px',
                                    whiteSpace: 'pre-wrap'
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
