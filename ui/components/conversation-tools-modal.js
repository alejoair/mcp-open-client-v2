const { Modal, List, Switch, Typography, Spin, Empty, Tag, Collapse, Progress, message: antMessage } = antd;
const { Panel } = Collapse;
const { Text } = Typography;

function ConversationToolsModal({ visible, onClose, conversationId }) {
    const { getTools, getAvailableTools, enableTool, disableTool } = useConversations();
    const [availableTools, setAvailableTools] = React.useState([]);
    const [enabledTools, setEnabledTools] = React.useState([]);
    const [loading, setLoading] = React.useState(false);
    const [groupedTools, setGroupedTools] = React.useState({});
    const [startingServers, setStartingServers] = React.useState(false);
    const [serverStatus, setServerStatus] = React.useState({});

    const startServers = React.useCallback(async function() {
        setStartingServers(true);
        try {
            // Get all servers
            const serversResponse = await api.get('/servers/');
            const servers = serversResponse.servers || [];

            // Initialize status
            const status = {};
            servers.forEach(function(server) {
                status[server.id] = {
                    name: server.config.name,
                    status: server.status,
                    starting: false
                };
            });
            setServerStatus(status);

            // Start servers that are not running
            const startPromises = servers
                .filter(function(server) { return server.status !== 'running'; })
                .map(async function(server) {
                    try {
                        setServerStatus(function(prev) {
                            return {
                                ...prev,
                                [server.id]: { ...prev[server.id], starting: true, status: 'starting' }
                            };
                        });

                        await api.post('/servers/' + server.id + '/start');

                        setServerStatus(function(prev) {
                            return {
                                ...prev,
                                [server.id]: { ...prev[server.id], starting: false, status: 'running' }
                            };
                        });
                    } catch (err) {
                        console.error('Failed to start server ' + server.config.name + ':', err);
                        setServerStatus(function(prev) {
                            return {
                                ...prev,
                                [server.id]: { ...prev[server.id], starting: false, status: 'error' }
                            };
                        });
                    }
                });

            await Promise.all(startPromises);
        } catch (err) {
            antMessage.error('Failed to start servers: ' + err.message);
        } finally {
            setStartingServers(false);
        }
    }, []);

    React.useEffect(function() {
        if (!visible || !conversationId) return;

        let cancelled = false;

        async function loadTools() {
            setLoading(true);
            try {
                // First, start all servers
                await startServers();

                if (cancelled) return;

                // Then load tools
                const [available, enabled] = await Promise.all([
                    getAvailableTools(conversationId),
                    getTools(conversationId)
                ]);

                if (cancelled) return;

                setAvailableTools(available);
                setEnabledTools(enabled);

                // Group tools by server
                const grouped = {};
                available.forEach(function(tool) {
                    if (!grouped[tool.server_id]) {
                        grouped[tool.server_id] = {
                            server_id: tool.server_id,
                            server_name: tool.server_name,
                            server_slug: tool.server_slug,
                            tools: []
                        };
                    }
                    grouped[tool.server_id].tools.push(tool);
                });
                setGroupedTools(grouped);
            } catch (err) {
                if (!cancelled) {
                    console.error('Failed to load tools:', err);
                    antMessage.error('Failed to load tools: ' + err.message);
                }
            } finally {
                if (!cancelled) {
                    setLoading(false);
                }
            }
        }

        loadTools();

        return function() {
            cancelled = true;
        };
    }, [visible, conversationId, getAvailableTools, getTools, startServers]);

    const isToolEnabled = function(tool) {
        return enabledTools.some(function(t) {
            return t.server_id === tool.server_id && t.tool_name === tool.tool_name;
        });
    };

    const handleToggleTool = async function(tool, enabled) {
        try {
            let updated;
            if (enabled) {
                updated = await enableTool(conversationId, {
                    server_id: tool.server_id,
                    tool_name: tool.tool_name
                });
            } else {
                updated = await disableTool(conversationId, tool.server_id, tool.tool_name);
            }
            setEnabledTools(updated);
            antMessage.success(enabled ? 'Tool enabled' : 'Tool disabled');
        } catch (err) {
            antMessage.error('Failed to toggle tool: ' + err.message);
        }
    };

    const renderToolsList = function(tools) {
        return React.createElement(List, {
            dataSource: tools,
            size: 'small',
            renderItem: function(tool) {
                const enabled = isToolEnabled(tool);

                return React.createElement(List.Item, {
                    style: { padding: '8px 0', borderBottom: 'none' }
                },
                    React.createElement('div', {
                        style: {
                            width: '100%',
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'flex-start'
                        }
                    },
                        React.createElement('div', { style: { flex: 1, marginRight: '16px' } },
                            React.createElement(Text, {
                                strong: true,
                                style: { fontSize: '13px', display: 'block', marginBottom: '4px' }
                            }, tool.tool_name),
                            tool.tool_description && React.createElement(Text, {
                                type: 'secondary',
                                style: {
                                    fontSize: '11px',
                                    display: 'block',
                                    lineHeight: '1.4'
                                }
                            }, tool.tool_description)
                        ),
                        React.createElement(Switch, {
                            checked: enabled,
                            size: 'small',
                            onChange: function(checked) {
                                handleToggleTool(tool, checked);
                            }
                        })
                    )
                );
            }
        });
    };

    const renderServerStatus = function() {
        const servers = Object.entries(serverStatus);
        if (servers.length === 0) return null;

        return React.createElement('div', {
            style: {
                marginBottom: '16px',
                padding: '16px',
                background: '#f5f5f5',
                borderRadius: '4px'
            }
        },
            React.createElement('div', {
                style: {
                    display: 'flex',
                    alignItems: 'center',
                    marginBottom: '12px'
                }
            },
                React.createElement('i', {
                    className: 'fas fa-server',
                    style: { marginRight: '8px', color: '#1890ff' }
                }),
                React.createElement(Text, { strong: true }, 'Starting MCP Servers')
            ),
            React.createElement(List, {
                size: 'small',
                dataSource: servers,
                renderItem: function([serverId, server]) {
                    let statusColor = '#d9d9d9';
                    let statusIcon = 'fa-circle';
                    let statusText = server.status;

                    if (server.status === 'running') {
                        statusColor = '#52c41a';
                        statusIcon = 'fa-check-circle';
                    } else if (server.status === 'starting' || server.starting) {
                        statusColor = '#1890ff';
                        statusIcon = 'fa-circle-notch fa-spin';
                    } else if (server.status === 'error') {
                        statusColor = '#ff4d4f';
                        statusIcon = 'fa-times-circle';
                    }

                    return React.createElement(List.Item, {
                        style: {
                            padding: '8px 0',
                            borderBottom: 'none'
                        }
                    },
                        React.createElement('div', {
                            style: {
                                display: 'flex',
                                alignItems: 'center',
                                width: '100%',
                                gap: '8px'
                            }
                        },
                            React.createElement('i', {
                                className: 'fas ' + statusIcon,
                                style: {
                                    color: statusColor,
                                    fontSize: '14px',
                                    width: '16px'
                                }
                            }),
                            React.createElement(Text, {
                                style: { flex: 1 }
                            }, server.name),
                            React.createElement(Tag, {
                                color: server.status === 'running' ? 'success' :
                                       server.status === 'starting' || server.starting ? 'processing' :
                                       server.status === 'error' ? 'error' : 'default',
                                style: { fontSize: '11px' }
                            }, statusText)
                        )
                    );
                }
            })
        );
    };

    return React.createElement(Modal, {
        title: React.createElement('span', null,
            React.createElement('i', { className: 'fas fa-wrench', style: { marginRight: '8px' } }),
            'Manage Tools'
        ),
        open: visible,
        onCancel: onClose,
        footer: null,
        width: 800
    },
        startingServers ? React.createElement('div', { style: { padding: '20px' } },
            renderServerStatus()
        ) :
        loading ? React.createElement(Spin, { tip: 'Loading tools...', style: { display: 'block', padding: '40px' } }) :
        availableTools.length === 0 ? React.createElement(Empty, {
            description: 'No tools available. Start some MCP servers first.',
            style: { padding: '40px 0' }
        }) :
        React.createElement('div', null,
            Object.keys(serverStatus).length > 0 && renderServerStatus(),
            React.createElement(Collapse, {
                defaultActiveKey: [],
                style: { background: '#fff' }
            },
                Object.values(groupedTools).map(function(server) {
                    const enabledCount = server.tools.filter(function(tool) {
                        return isToolEnabled(tool);
                    }).length;

                    return React.createElement(Panel, {
                        key: server.server_id,
                        header: React.createElement('div', {
                            style: {
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                                paddingRight: '16px'
                            }
                        },
                            React.createElement('div', {
                                style: {
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '8px'
                                }
                            },
                                React.createElement('i', {
                                    className: 'fas fa-server',
                                    style: { color: '#1890ff', fontSize: '14px' }
                                }),
                                React.createElement(Text, {
                                    strong: true,
                                    style: { fontSize: '14px' }
                                }, server.server_name),
                                React.createElement(Tag, {
                                    color: 'default',
                                    style: { fontSize: '11px', marginLeft: '4px' }
                                }, server.tools.length + ' tools')
                            ),
                            enabledCount > 0 && React.createElement(Tag, {
                                color: 'success',
                                style: { fontSize: '11px' }
                            }, enabledCount + ' enabled')
                        )
                    },
                        renderToolsList(server.tools)
                    );
                })
            )
        )
    );
}
