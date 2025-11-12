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
                    background: '#2a2a2a',
                    padding: '10px 14px',
                    borderRadius: '12px',
                    borderBottomLeftRadius: '4px',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
                    position: 'relative',
                    color: 'rgba(255, 255, 255, 0.9)'
                }
            },
                // Show tool calls if present - Ultra compact design
                hasToolCalls ?
                    React.createElement('div', { style: { marginBottom: '8px' } },
                        message.tool_calls.map(function(tc, idx) {
                            // Parse arguments
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

                            // Find response
                            const toolResponse = toolResponses ? toolResponses.find(function(tr) {
                                return tr.tool_call_id === tc.id;
                            }) : null;

                            // Parse response
                            let parsedResponse = null;
                            let isValidResponseJSON = false;
                            let responseError = false;
                            if (toolResponse && toolResponse.content) {
                                try {
                                    parsedResponse = JSON.parse(toolResponse.content);
                                    isValidResponseJSON = true;
                                } catch (e) {
                                    parsedResponse = toolResponse.content;
                                }
                                responseError = toolResponse._status === 'error';
                            }

                            const statusColor = toolResponse ? (responseError ? 'red' : 'green') : 'blue';
                            const statusIcon = toolResponse ? (responseError ? '❌' : '✅') : '⏳';

                            return React.createElement(Collapse, {
                                key: tc.id,
                                ghost: true,
                                size: 'small',
                                defaultActiveKey: [],
                                style: { marginBottom: idx < message.tool_calls.length - 1 ? '2px' : 0 }
                            },
                                React.createElement(Panel, {
                                    header: React.createElement('span', {
                                        style: { fontSize: '11px', display: 'flex', alignItems: 'center', gap: '6px' }
                                    },
                                        React.createElement('span', null, statusIcon),
                                        React.createElement(Tag, {
                                            color: statusColor,
                                            style: { fontSize: '10px', margin: 0, padding: '0 4px' }
                                        }, tc.function.name),
                                        toolResponse && toolResponse._status === 'pending' && React.createElement(Spin, { size: 'small' })
                                    ),
                                    key: '1'
                                },
                                    React.createElement('div', {
                                        style: {
                                            display: 'grid',
                                            gridTemplateColumns: toolResponse ? '1fr 1fr' : '1fr',
                                            gap: '8px',
                                            fontSize: '10px'
                                        }
                                    },
                                        // Arguments column
                                        React.createElement('div', null,
                                            React.createElement('div', {
                                                style: { fontWeight: 600, marginBottom: '4px', color: 'rgba(255, 255, 255, 0.7)' }
                                            }, 'Arguments:'),
                                            React.createElement('pre', {
                                                style: {
                                                    background: '#1a1a1a',
                                                    padding: '4px',
                                                    borderRadius: '3px',
                                                    fontSize: '9px',
                                                    overflow: 'auto',
                                                    maxHeight: '100px',
                                                    margin: 0,
                                                    whiteSpace: 'pre-wrap',
                                                    lineHeight: '1.2',
                                                    color: 'rgba(255, 255, 255, 0.9)',
                                                    border: '1px solid rgba(255, 255, 255, 0.1)'
                                                }
                                            }, isValidJSON ? JSON.stringify(parsedArgs, null, 2) : parsedArgs || 'No arguments')
                                        ),
                                        // Response column
                                        toolResponse && React.createElement('div', null,
                                            React.createElement('div', {
                                                style: { fontWeight: 600, marginBottom: '4px', color: responseError ? '#ff4d4f' : '#52c41a' }
                                            }, responseError ? 'Error:' : 'Result:'),
                                            toolResponse._status !== 'pending' && React.createElement('pre', {
                                                style: {
                                                    background: responseError ? '#3d1a1a' : '#1a3d1a',
                                                    padding: '4px',
                                                    borderRadius: '3px',
                                                    fontSize: '9px',
                                                    overflow: 'auto',
                                                    maxHeight: '100px',
                                                    margin: 0,
                                                    whiteSpace: 'pre-wrap',
                                                    lineHeight: '1.2',
                                                    color: responseError ? '#ff7875' : '#95de64',
                                                    border: '1px solid ' + (responseError ? 'rgba(255, 77, 79, 0.3)' : 'rgba(82, 196, 26, 0.3)')
                                                }
                                            }, isValidResponseJSON ? JSON.stringify(parsedResponse, null, 2) : parsedResponse)
                                        )
                                    )
                                )
                            );
                        })
                    ) : null,
                // Show content if present
                message.content ? React.createElement(MarkdownRenderer, {
                    content: message.content,
                    style: hasToolCalls ? { marginTop: '12px', paddingTop: '12px', borderTop: '1px solid rgba(255, 255, 255, 0.1)' } : {}
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
