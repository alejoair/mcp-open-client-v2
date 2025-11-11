const { List, Typography, Space, Button, Tag, Empty, Spin, Modal, message: antMessage } = antd;
const { Text } = Typography;
const { confirm } = Modal;

function ConversationsList({ onSelectConversation }) {
    const { conversations, loading, loadConversations, deleteConversation } = useConversations();
    const [selectedId, setSelectedId] = React.useState(null);

    React.useEffect(function() {
        loadConversations();
    }, [loadConversations]);

    const handleSelect = function(conversation) {
        setSelectedId(conversation.id);
        if (onSelectConversation) {
            onSelectConversation(conversation);
        }
    };

    const handleDelete = function(conversation, e) {
        e.stopPropagation();

        confirm({
            title: 'Delete Conversation',
            icon: React.createElement('i', {
                className: 'fas fa-exclamation-triangle',
                style: { color: '#ff4d4f', marginRight: '8px' }
            }),
            content: React.createElement('div', null,
                React.createElement('p', null, 'Are you sure you want to delete this conversation?'),
                React.createElement('p', { style: { fontWeight: 'bold', marginTop: '8px' } },
                    '"' + conversation.title + '"'
                ),
                React.createElement('p', { style: { color: '#999', fontSize: '12px', marginTop: '8px' } },
                    'This action cannot be undone.'
                )
            ),
            okText: 'Delete',
            okType: 'danger',
            cancelText: 'Cancel',
            onOk: async function() {
                try {
                    await deleteConversation(conversation.id);
                    antMessage.success('Conversation deleted');
                    await loadConversations();
                } catch (err) {
                    antMessage.error('Failed to delete conversation: ' + err.message);
                }
            }
        });
    };

    if (loading && conversations.length === 0) {
        return React.createElement('div', {
            style: { padding: '20px', textAlign: 'center' }
        },
            React.createElement(Spin, { tip: 'Loading...' })
        );
    }

    if (conversations.length === 0) {
        return React.createElement('div', {
            style: { padding: '20px' }
        },
            React.createElement(Empty, {
                description: React.createElement(Text, {
                    style: { color: '#999', fontSize: '12px' }
                }, 'No conversations yet'),
                image: Empty.PRESENTED_IMAGE_SIMPLE
            })
        );
    }

    return React.createElement('div', {
        style: {
            padding: '8px',
            maxHeight: 'calc(100vh - 300px)',
            overflow: 'auto'
        }
    },
        React.createElement(List, {
            dataSource: conversations,
            size: 'small',
            renderItem: function(conversation) {
                const isSelected = selectedId === conversation.id;

                return React.createElement(List.Item, {
                    style: {
                        padding: '8px 12px',
                        cursor: 'pointer',
                        borderRadius: '4px',
                        marginBottom: '4px',
                        background: isSelected ? '#667eea' : 'transparent',
                        transition: 'all 0.2s ease',
                        border: 'none'
                    },
                    onClick: function() {
                        handleSelect(conversation);
                    },
                    onMouseEnter: function(e) {
                        if (!isSelected) {
                            e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)';
                        }
                    },
                    onMouseLeave: function(e) {
                        if (!isSelected) {
                            e.currentTarget.style.background = 'transparent';
                        }
                    }
                },
                    React.createElement('div', {
                        style: { width: '100%' }
                    },
                        React.createElement('div', {
                            style: {
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'flex-start',
                                marginBottom: '4px'
                            }
                        },
                            React.createElement('div', {
                                style: { flex: 1, minWidth: 0 }
                            },
                                React.createElement(Text, {
                                    strong: true,
                                    style: {
                                        color: isSelected ? '#fff' : '#e8e8e8',
                                        fontSize: '13px',
                                        display: 'block',
                                        overflow: 'hidden',
                                        textOverflow: 'ellipsis',
                                        whiteSpace: 'nowrap'
                                    }
                                }, conversation.title)
                            ),
                            React.createElement('div', {
                                style: {
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '4px',
                                    marginLeft: '8px'
                                }
                            },
                                conversation.enabled_tools && conversation.enabled_tools.length > 0 && React.createElement(Tag, {
                                    color: isSelected ? 'success' : 'default',
                                    style: {
                                        fontSize: '10px',
                                        padding: '0 4px',
                                        lineHeight: '16px',
                                        margin: 0
                                    }
                                }, conversation.enabled_tools.length + ' tools'),
                                React.createElement(Button, {
                                    type: 'text',
                                    size: 'small',
                                    danger: true,
                                    icon: React.createElement('i', {
                                        className: 'fas fa-trash',
                                        style: { fontSize: '11px' }
                                    }),
                                    onClick: function(e) {
                                        handleDelete(conversation, e);
                                    },
                                    style: {
                                        padding: '2px 4px',
                                        height: 'auto',
                                        opacity: 0.7
                                    },
                                    onMouseEnter: function(e) {
                                        e.currentTarget.style.opacity = 1;
                                    },
                                    onMouseLeave: function(e) {
                                        e.currentTarget.style.opacity = 0.7;
                                    }
                                })
                            )
                        ),
                        conversation.description && React.createElement(Text, {
                            type: 'secondary',
                            style: {
                                fontSize: '11px',
                                color: isSelected ? 'rgba(255,255,255,0.8)' : '#999',
                                display: 'block',
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                                whiteSpace: 'nowrap'
                            }
                        }, conversation.description)
                    )
                );
            }
        })
    );
}
