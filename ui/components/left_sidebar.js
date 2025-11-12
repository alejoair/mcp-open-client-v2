const { Sider } = antd.Layout;
const { Collapse, Divider, Typography, Tooltip } = antd;
const { Title } = Typography;

function LeftSidebar({ collapsed, onCollapse, onSelectConversation }) {
    const items = [
        {
            key: '1',
            label: React.createElement('span', null,
                React.createElement('i', { className: 'fas fa-comments', style: { marginRight: '8px' } }),
                'Conversations'
            ),
            children: React.createElement(ConversationsList, {
                onSelectConversation: onSelectConversation
            })
        },
        {
            key: '2',
            label: React.createElement('span', null,
                React.createElement('i', { className: 'fas fa-cog', style: { marginRight: '8px' } }),
                'Configuration'
            ),
            children: React.createElement(Configuration)
        },
        {
            key: '3',
            label: React.createElement('span', null,
                React.createElement('i', { className: 'fas fa-server', style: { marginRight: '8px' } }),
                'MCP Servers'
            ),
            children: React.createElement(MCPServers)
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
                React.createElement('div', { style: { padding: '16px' } },
                    React.createElement(Title, {
                        level: 4,
                        style: { margin: 0, color: 'white' }
                    }, 'MCP Open Client')
                ),
                React.createElement(Divider, { style: { margin: 0 } }),
                React.createElement(Collapse, {
                    accordion: true,
                    items: items,
                    defaultActiveKey: ['1']
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
