const { Badge, Card, Typography, Collapse, Tag, Spin, Alert } = antd;
const { Text, Paragraph } = Typography;
const { Panel } = Collapse;

function ToolCallDisplay({ events, isConnected, isConnecting }) {
    const [activeKeys, setActiveKeys] = React.useState([]);

    // Group events by conversation flow
    const toolEvents = React.useMemo(() => {
        const grouped = {};
        events.forEach(event => {
            const { type, data, timestamp } = event;

            // Only process tool-related events
            if (!data || !data.tool_call_id) {
                return; // Skip non-tool events like 'connected', 'keepalive'
            }

            const toolCallId = data.tool_call_id;

            if (!grouped[toolCallId]) {
                grouped[toolCallId] = {
                    toolCallId,
                    toolName: data.tool_name,
                    arguments: data.arguments,
                    events: []
                };
            }

            grouped[toolCallId].events.push({
                type,
                data,
                timestamp
            });
        });

        return Object.values(grouped);
    }, [events]);

    const getEventIcon = (type) => {
        switch (type) {
            case 'tool_call':
                return '🔧';
            case 'tool_response':
                return '✅';
            case 'tool_error':
                return '❌';
            default:
                return '📄';
        }
    };

    const getEventColor = (type) => {
        switch (type) {
            case 'tool_call':
                return 'blue';
            case 'tool_response':
                return 'green';
            case 'tool_error':
                return 'red';
            default:
                return 'default';
        }
    };

    const formatArguments = (args) => {
        try {
            return JSON.stringify(args, null, 2);
        } catch (error) {
            return String(args);
        }
    };

    const formatResult = (result) => {
        try {
            return JSON.stringify(JSON.parse(result), null, 2);
        } catch (error) {
            return String(result);
        }
    };

    if (toolEvents.length === 0) {
        return null; // Don't show if no tool calls
    }

    return React.createElement('div', {
        style: {
            margin: '16px 0',
            border: '1px solid #d9d9d9',
            borderRadius: '6px',
            backgroundColor: '#fafafa'
        }
    },
        React.createElement('div', {
            style: {
                padding: '12px 16px',
                borderBottom: '1px solid #d9d9d9',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                backgroundColor: '#fff'
            }
        },
            React.createElement('div', {
                style: {
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                }
            },
                React.createElement('span', {
                    style: {
                        fontSize: '16px',
                        fontWeight: 'bold'
                    }
                }, '🔧 Tool Calls'),
                React.createElement(Tag, {
                    color: isConnected ? 'green' : 'red',
                    icon: isConnecting ? React.createElement(Spin, { size: 'small' }) : null
                }, isConnected ? 'Live' : 'Disconnected')
            ),
            React.createElement('span', {
                style: {
                    fontSize: '12px',
                    color: '#666'
                }
            }, `${toolEvents.length} tools in progress`)
        ),
        React.createElement('div', {
            style: {
                padding: '8px 16px'
            }
        },
            React.createElement(Collapse, {
                activeKey: activeKeys,
                onChange: setActiveKeys,
                size: 'small'
            },
                toolEvents.map(toolEvent => 
                    React.createElement(Panel, {
                        key: toolEvent.toolCallId,
                        header: React.createElement('div', {
                            style: {
                                display: 'flex',
                                alignItems: 'center',
                                gap: '8px'
                            }
                        },
                            React.createElement('span', {
                                style: {
                                    fontSize: '14px'
                                }
                            }, getEventIcon('tool_call')),
                            React.createElement(Text, {
                                strong: true,
                                style: {
                                    marginRight: '8px'
                                }
                            }, toolEvent.toolName),
                            React.createElement(Tag, {
                                size: 'small',
                                color: 'purple'
                            }, toolEvent.toolCallId.substring(0, 8) + '...')
                        ),
                        extra: React.createElement(Badge, {
                            count: toolEvent.events.length,
                            style: {
                                backgroundColor: '#52c41a'
                            }
                        })
                    },
                        toolEvent.events.map((event, index) => 
                            React.createElement(Card, {
                                key: `${event.type}-${index}`,
                                size: 'small',
                                style: {
                                    marginBottom: index < toolEvent.events.length - 1 ? '8px' : '0px'
                                },
                                bodyStyle: {
                                    padding: '12px'
                                }
                            },
                                React.createElement('div', {
                                    style: {
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '8px',
                                        marginBottom: '8px'
                                    }
                                },
                                    React.createElement('span', {
                                        style: {
                                            fontSize: '16px'
                                        }
                                    }, getEventIcon(event.type)),
                                    React.createElement(Text, {
                                        strong: true,
                                        type: getEventColor(event.type) === 'red' ? 'danger' : 'secondary'
                                    }, event.type.replace('_', ' ').toUpperCase()),
                                    React.createElement(Text, {
                                        type: 'secondary',
                                        style: {
                                            fontSize: '11px',
                                            marginLeft: 'auto'
                                        }
                                    }, new Date(event.timestamp).toLocaleTimeString())
                                ),
                                event.type === 'tool_call' && React.createElement('div', {
                                    style: {
                                        marginTop: '8px'
                                    }
                                },
                                    React.createElement(Text, {
                                        type: 'secondary',
                                        style: {
                                            fontSize: '12px'
                                        }
                                    }, 'Arguments:'),
                                    React.createElement(Paragraph, {
                                        code: true,
                                        style: {
                                            fontSize: '12px',
                                            backgroundColor: '#f5f5f5',
                                            marginTop: '4px',
                                            marginBottom: '0px'
                                        }
                                    }, formatArguments(event.data.arguments))
                                ),
                                event.type === 'tool_response' && React.createElement('div', {
                                    style: {
                                        marginTop: '8px'
                                    }
                                },
                                    React.createElement(Text, {
                                        type: 'secondary',
                                        style: {
                                            fontSize: '12px'
                                        }
                                    }, 'Result:'),
                                    React.createElement(Paragraph, {
                                        code: true,
                                        style: {
                                            fontSize: '12px',
                                            backgroundColor: '#f5f5f5',
                                            marginTop: '4px',
                                            marginBottom: '0px',
                                            maxHeight: '200px',
                                            overflowY: 'auto'
                                        }
                                    }, formatResult(event.data.result))
                                ),
                                event.type === 'tool_error' && React.createElement(Alert, {
                                    type: 'error',
                                    message: 'Tool Error',
                                    description: event.data.error,
                                    showIcon: true,
                                    style: {
                                        fontSize: '12px',
                                        marginTop: '8px'
                                    }
                                })
                            )
                        )
                    )
                )
            )
        )
    );
}