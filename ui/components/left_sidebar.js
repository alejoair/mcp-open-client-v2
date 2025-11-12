const { Sider } = antd.Layout;
const { Collapse, Divider, Typography, Tooltip } = antd;
const { Title } = Typography;

function LeftSidebar({ collapsed, onCollapse, onSelectConversation }) {
    // Restore active panel from localStorage or default to '1'
    const [activePanel, setActivePanel] = React.useState(function() {
        const saved = StorageService.get('mcp-sidebar');
        return saved && saved.activePanel ? [saved.activePanel] : ['1'];
    });

    // Save active panel when it changes
    React.useEffect(function() {
        StorageService.set('mcp-sidebar', {
            activePanel: activePanel[0] || null
        });
    }, [activePanel]);

    const items = [
        {
            key: '1',
            label: React.createElement('span', { style: { color: 'rgba(255, 255, 255, 0.85)' } },
                React.createElement('i', { className: 'fas fa-comments', style: { marginRight: '8px' } }),
                'Conversations'
            ),
            children: React.createElement(ConversationsList, {
                onSelectConversation: onSelectConversation
            }),
            style: { background: 'transparent', borderColor: 'rgba(255, 255, 255, 0.1)' }
        },
        {
            key: '2',
            label: React.createElement('span', { style: { color: 'rgba(255, 255, 255, 0.85)' } },
                React.createElement('i', { className: 'fas fa-cog', style: { marginRight: '8px' } }),
                'Configuration'
            ),
            children: React.createElement(Configuration),
            style: { background: 'transparent', borderColor: 'rgba(255, 255, 255, 0.1)' }
        },
        {
            key: '3',
            label: React.createElement('span', { style: { color: 'rgba(255, 255, 255, 0.85)' } },
                React.createElement('i', { className: 'fas fa-server', style: { marginRight: '8px' } }),
                'MCP Servers'
            ),
            children: React.createElement(MCPServers),
            style: { background: 'transparent', borderColor: 'rgba(255, 255, 255, 0.1)' }
        }
    ];

    // Custom trigger button
    const customTrigger = React.createElement(Tooltip, {
        title: collapsed ? 'Expand sidebar' : 'Collapse sidebar',
        placement: 'right'
    },
        React.createElement('div', {
            onClick: function() { onCollapse(!collapsed); },
            style: {
                width: '100%',
                height: '48px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
                background: 'rgba(255, 255, 255, 0.05)',
                borderTop: '1px solid rgba(255, 255, 255, 0.1)',
                transition: 'all 0.3s',
                position: 'absolute',
                bottom: 0,
                left: 0
            },
            onMouseEnter: function(e) {
                e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)';
            },
            onMouseLeave: function(e) {
                e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)';
            }
        },
            React.createElement('i', {
                className: collapsed ? 'fas fa-angles-right' : 'fas fa-angles-left',
                style: {
                    color: '#fff',
                    fontSize: '18px',
                    transition: 'transform 0.3s'
                }
            })
        )
    );

    return (
        React.createElement(Sider, {
            collapsed: collapsed,
            onCollapse: onCollapse,
            width: 300,
            collapsedWidth: 50,
            style: {
                background: '#1f1f1f',
                position: 'relative'
            },
            trigger: null
        },
            !collapsed && React.createElement('div', {
                style: {
                    height: 'calc(100% - 48px)',
                    overflowY: 'auto'
                }
            },
                React.createElement('div', {
                    style: {
                        padding: '16px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '12px'
                    }
                },
                    React.createElement('i', {
                        className: 'fas fa-bars',
                        style: {
                            color: 'rgba(255, 255, 255, 0.7)',
                            fontSize: '20px'
                        }
                    }),
                    React.createElement(Title, {
                        level: 4,
                        style: { margin: 0, color: 'white' }
                    }, 'Menu')
                ),
                React.createElement(Divider, { style: { margin: 0, background: 'rgba(255, 255, 255, 0.1)' } }),
                React.createElement(Collapse, {
                    accordion: true,
                    items: items,
                    activeKey: activePanel,
                    onChange: setActivePanel,
                    style: {
                        background: 'transparent',
                        border: 'none'
                    },
                    expandIconPosition: 'end',
                    styles: {
                        header: {
                            background: 'rgba(255, 255, 255, 0.05)',
                            color: 'rgba(255, 255, 255, 0.85)'
                        },
                        content: {
                            background: '#1a1a1a',
                            borderTop: '1px solid rgba(255, 255, 255, 0.1)'
                        }
                    }
                })
            ),
            collapsed && React.createElement('div', {
                style: {
                    height: 'calc(100% - 48px)',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    paddingTop: '20px',
                    gap: '20px'
                }
            },
                React.createElement(Tooltip, { title: 'Conversations', placement: 'right' },
                    React.createElement('i', {
                        className: 'fas fa-comments',
                        style: {
                            color: 'rgba(255, 255, 255, 0.7)',
                            fontSize: '20px',
                            cursor: 'pointer'
                        }
                    })
                ),
                React.createElement(Tooltip, { title: 'Configuration', placement: 'right' },
                    React.createElement('i', {
                        className: 'fas fa-cog',
                        style: {
                            color: 'rgba(255, 255, 255, 0.7)',
                            fontSize: '20px',
                            cursor: 'pointer'
                        }
                    })
                ),
                React.createElement(Tooltip, { title: 'MCP Servers', placement: 'right' },
                    React.createElement('i', {
                        className: 'fas fa-server',
                        style: {
                            color: 'rgba(255, 255, 255, 0.7)',
                            fontSize: '20px',
                            cursor: 'pointer'
                        }
                    })
                )
            ),
            customTrigger
        )
    );
}
