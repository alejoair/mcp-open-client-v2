const { Typography, Tag, Empty } = antd;
const { Text } = Typography;

function ToolsList({ conversationId }) {
    const [tools, setTools] = React.useState([]);
    const [loading, setLoading] = React.useState(false);
    const [serverMap, setServerMap] = React.useState({});

    // Load servers to get slugs
    React.useEffect(function() {
        async function loadServers() {
            try {
                const response = await fetch('/servers/');
                const data = await response.json();
                const servers = Array.isArray(data) ? data : [];
                const map = {};
                servers.forEach(function(server) {
                    map[server.id] = server.config.slug || server.config.name;
                });
                setServerMap(map);
            } catch (err) {
                console.error('Failed to load servers:', err);
            }
        }
        loadServers();
    }, []);

    const loadTools = React.useCallback(async function() {
        if (!conversationId) {
            setTools([]);
            return;
        }

        setLoading(true);
        try {
            const response = await fetch(`/conversations/${conversationId}/tools`);
            const data = await response.json();
            const toolsArray = Array.isArray(data.enabled_tools) ? data.enabled_tools : [];
            setTools(toolsArray);
        } catch (err) {
            console.error('Failed to load tools:', err);
            setTools([]);
        } finally {
            setLoading(false);
        }
    }, [conversationId]);

    // Initial load
    React.useEffect(function() {
        loadTools();
    }, [loadTools]);

    if (!conversationId) {
        return null;
    }

    return React.createElement('div', {
        style: {
            background: 'rgba(255, 255, 255, 0.05)',
            borderRadius: '8px',
            padding: '16px',
            border: '1px solid rgba(255, 255, 255, 0.1)'
        }
    },
        React.createElement('div', {
            style: {
                marginBottom: '12px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
            }
        },
            React.createElement('i', {
                className: 'fas fa-wrench',
                style: { color: '#f59e0b', fontSize: '14px' }
            }),
            React.createElement(Text, {
                style: {
                    color: '#fff',
                    fontWeight: 600,
                    fontSize: '13px'
                }
            }, 'Enabled Tools'),
            React.createElement('div', {
                style: {
                    marginLeft: 'auto',
                    background: 'rgba(245, 158, 11, 0.2)',
                    borderRadius: '10px',
                    padding: '2px 8px',
                    fontSize: '11px',
                    color: '#f59e0b',
                    fontWeight: 600
                }
            }, tools.length)
        ),
        React.createElement('div', {
            style: {
                maxHeight: '200px',
                overflow: 'auto'
            }
        },
            loading ? React.createElement('div', {
                style: {
                    textAlign: 'center',
                    color: 'rgba(255, 255, 255, 0.5)',
                    fontSize: '12px',
                    padding: '8px'
                }
            }, 'Loading...') : tools.length === 0 ? React.createElement('div', {
                style: {
                    textAlign: 'center',
                    color: 'rgba(255, 255, 255, 0.5)',
                    fontSize: '12px',
                    padding: '8px'
                }
            }, 'No tools enabled') : tools.map(function(tool, index) {
                return React.createElement('div', {
                    key: index,
                    style: {
                        background: 'rgba(0, 0, 0, 0.2)',
                        borderRadius: '4px',
                        padding: '8px',
                        marginBottom: index < tools.length - 1 ? '8px' : 0,
                        border: '1px solid rgba(255, 255, 255, 0.05)'
                    }
                },
                    React.createElement('div', {
                        style: {
                            fontSize: '12px',
                            color: '#fff',
                            fontWeight: 500,
                            marginBottom: '4px',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '6px'
                        }
                    },
                        React.createElement('i', {
                            className: 'fas fa-code',
                            style: { fontSize: '10px', color: '#10b981' }
                        }),
                        tool.tool_name
                    ),
                    React.createElement('div', {
                        style: {
                            fontSize: '10px',
                            color: 'rgba(255, 255, 255, 0.5)'
                        }
                    }, `Server: ${serverMap[tool.server_id] || tool.server_id}`)
                );
            })
        )
    );
}
