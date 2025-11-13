const { Sider } = antd.Layout;
const { Typography, Divider, Tooltip, Button } = antd;
const { Title, Text } = Typography;

function RightSidebar({ collapsed, onCollapse, activeConversation, tokenInfo, messageCount, onOpenSettings, onOpenTools, toolsRefreshKey }) {
    // Get dev mode context
    const { devMode, toggleDevMode } = useDevMode();

    // Custom trigger button
    const customTrigger = React.createElement(Tooltip, {
        title: collapsed ? 'Expand sidebar' : 'Collapse sidebar',
        placement: 'left'
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
                className: collapsed ? 'fas fa-angles-left' : 'fas fa-angles-right',
                style: {
                    color: '#fff',
                    fontSize: '18px',
                    transition: 'transform 0.3s'
                }
            })
        )
    );

    return React.createElement(Sider, {
        collapsed: collapsed,
        onCollapse: onCollapse,
        width: 320,
        collapsedWidth: 50,
        style: {
            background: '#1f1f1f',
            overflowX: 'hidden',
            position: 'relative',
            height: '100vh'
        },
        trigger: null
    },
        !collapsed && React.createElement('div', {
            style: {
                height: 'calc(100% - 48px)',
                display: 'flex',
                flexDirection: 'column'
            }
        },
            // Header
            React.createElement('div', {
                style: { padding: '16px' }
            },
                React.createElement(Title, {
                    level: 5,
                    style: {
                        margin: 0,
                        color: 'white',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px'
                    }
                },
                    React.createElement('i', {
                        className: 'fas fa-info-circle',
                        style: { fontSize: '16px' }
                    }),
                    'Conversation'
                )
            ),
            React.createElement(Divider, { style: { margin: 0, background: 'rgba(255, 255, 255, 0.1)' } }),

            // Action buttons (Settings and Tools)
            activeConversation && React.createElement('div', {
                style: {
                    padding: '12px 16px',
                    display: 'flex',
                    gap: '8px',
                    borderBottom: '1px solid rgba(255, 255, 255, 0.1)'
                }
            },
                React.createElement(Button, {
                    type: 'default',
                    size: 'small',
                    block: true,
                    icon: React.createElement('i', { className: 'fas fa-cog', style: { marginRight: '6px' } }),
                    onClick: onOpenSettings,
                    style: {
                        background: 'rgba(255, 255, 255, 0.05)',
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        color: 'rgba(255, 255, 255, 0.85)'
                    }
                }, 'Settings'),
                React.createElement(Button, {
                    type: 'default',
                    size: 'small',
                    block: true,
                    icon: React.createElement('i', { className: 'fas fa-wrench', style: { marginRight: '6px' } }),
                    onClick: onOpenTools,
                    style: {
                        background: 'rgba(255, 255, 255, 0.05)',
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        color: 'rgba(255, 255, 255, 0.85)'
                    }
                }, 'Tools')
            ),

            // Hackerman Image with Button
            activeConversation && React.createElement('div', {
                style: {
                    padding: '12px 16px',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: '8px',
                    borderBottom: '1px solid rgba(255, 255, 255, 0.1)'
                }
            },
                React.createElement('img', {
                    src: '/ui/images/hackerman.gif',
                    alt: 'Hackerman',
                    style: {
                        width: '100%',
                        maxWidth: '200px',
                        borderRadius: '8px',
                        border: '2px solid rgba(255, 255, 255, 0.1)'
                    }
                }),
                React.createElement(Button, {
                    type: 'primary',
                    size: 'small',
                    block: true,
                    icon: React.createElement('i', {
                        className: devMode ? 'fas fa-terminal' : 'fas fa-code',
                        style: { marginRight: '6px' }
                    }),
                    onClick: toggleDevMode,
                    style: {
                        background: devMode ? '#bd93f9' : '#52c41a',
                        border: 'none',
                        color: devMode ? '#16161e' : 'white',
                        marginTop: '4px',
                        transition: 'all 0.3s ease',
                        textShadow: 'none',
                        boxShadow: devMode ? '0 0 20px rgba(189, 147, 249, 0.5), inset 0 0 12px rgba(189, 147, 249, 0.15)' : 'none',
                        fontFamily: devMode ? "'Fira Code', 'Consolas', 'Monaco', monospace" : 'inherit',
                        fontWeight: devMode ? '700' : 'normal',
                        letterSpacing: devMode ? '1px' : 'normal'
                    }
                }, devMode ? 'DRACULA MODE' : 'Dev Mode')
            ),

            // Content
            React.createElement('div', {
                style: {
                    flex: 1,
                    padding: '16px',
                    overflowY: 'auto',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '16px'
                }
            },
                !activeConversation ? React.createElement('div', {
                    style: {
                        textAlign: 'center',
                        color: 'rgba(255, 255, 255, 0.5)',
                        fontSize: '13px',
                        padding: '32px 16px'
                    }
                },
                    React.createElement('i', {
                        className: 'fas fa-comments',
                        style: {
                            fontSize: '48px',
                            marginBottom: '16px',
                            opacity: 0.3,
                            display: 'block'
                        }
                    }),
                    'Open a conversation to see details'
                ) : React.createElement(React.Fragment, null,
                    React.createElement(TokenCounter, {
                        tokenInfo: tokenInfo,
                        conversation: activeConversation,
                        messageCount: messageCount
                    }),
                    React.createElement(MetadataPanel, {
                        conversation: activeConversation
                    }),
                    React.createElement(ToolsList, {
                        key: toolsRefreshKey,
                        conversationId: activeConversation ? activeConversation.id : null
                    }),
                    React.createElement(ContextItems, {
                        conversationId: activeConversation ? activeConversation.id : null
                    }),
                    React.createElement(OpenEditors, {
                        conversationId: activeConversation ? activeConversation.id : null
                    })
                )
            )
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
            React.createElement(Tooltip, { title: 'Conversation Info', placement: 'left' },
                React.createElement('i', {
                    className: 'fas fa-info-circle',
                    style: {
                        color: 'rgba(255, 255, 255, 0.7)',
                        fontSize: '20px',
                        cursor: 'pointer'
                    }
                })
            )
        ),
        customTrigger
    );
}
