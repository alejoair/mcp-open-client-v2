const { Modal, List, Switch, Typography, Spin, Empty, Tag, Collapse, message: antMessage } = antd;
const { Panel } = Collapse;
const { Text } = Typography;

function ConversationToolsModal({ visible, onClose, conversationId }) {
    const { getTools, getAvailableTools, enableTool, disableTool } = useConversations();
    const [availableTools, setAvailableTools] = React.useState([]);
    const [enabledTools, setEnabledTools] = React.useState([]);
    const [loading, setLoading] = React.useState(false);
    const [groupedTools, setGroupedTools] = React.useState({});

    const loadTools = React.useCallback(async function() {
        if (!visible || !conversationId) return;

        setLoading(true);
        try {
            const [available, enabled] = await Promise.all([
                getAvailableTools(conversationId),
                getTools(conversationId)
            ]);
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
            antMessage.error('Failed to load tools: ' + err.message);
        } finally {
            setLoading(false);
        }
    }, [visible, conversationId, getAvailableTools, getTools]);

    React.useEffect(function() {
        loadTools();
    }, [loadTools]);

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
        loading ? React.createElement(Spin, { tip: 'Loading tools...', style: { display: 'block', padding: '40px' } }) :
        availableTools.length === 0 ? React.createElement(Empty, {
            description: 'No tools available. Start some MCP servers first.',
            style: { padding: '40px 0' }
        }) :
        React.createElement(Collapse, {
            defaultActiveKey: Object.keys(groupedTools),
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
    );
}
