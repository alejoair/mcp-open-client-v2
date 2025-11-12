const { Sider } = antd.Layout;
const { Typography, Divider } = antd;
const { Title, Text } = Typography;

function RightSidebar({ collapsed, onCollapse, activeConversation, tokenInfo, messageCount }) {
    return React.createElement(Sider, {
        collapsible: true,
        collapsed: collapsed,
        onCollapse: onCollapse,
        reverseArrow: true,
        width: 320,
        collapsedWidth: 80,
        style: {
            background: '#1f1f1f',
            overflowY: 'auto',
            overflowX: 'hidden'
        }
    },
        !collapsed && React.createElement('div', {
            style: {
                height: '100%',
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
        )
    );
}
