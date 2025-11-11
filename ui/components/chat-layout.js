const { Tabs, Button, Dropdown, Typography, Space, message } = antd;
const { Text } = Typography;

function ChatLayout({ onOpenConversationChange }) {
    const { createConversation, updateConversation, deleteConversation, conversations } = useConversations();
    const [activeKey, setActiveKey] = React.useState(null);
    const [items, setItems] = React.useState([]);
    const [settingsVisible, setSettingsVisible] = React.useState(false);
    const [toolsVisible, setToolsVisible] = React.useState(false);
    const [selectedConversation, setSelectedConversation] = React.useState(null);

    const newTabIndex = React.useRef(0);

    // Function to open an existing conversation
    const openConversation = React.useCallback(function(conversation) {
        // Check if conversation is already open
        const existingTab = items.find(function(item) {
            return item.key === conversation.id;
        });

        if (existingTab) {
            // Just switch to the existing tab
            setActiveKey(conversation.id);
        } else {
            // Create new tab for the conversation
            const newTab = {
                key: conversation.id,
                label: renderTabLabel(conversation),
                children: React.createElement('div', {
                    style: {
                        padding: '24px',
                        height: '100%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                    }
                },
                    React.createElement(Text, {
                        style: { color: '#999', fontSize: '14px' }
                    }, 'Start chatting...')
                ),
                conversation: conversation
            };

            setItems(function(prevItems) {
                return [...prevItems, newTab];
            });
            setActiveKey(conversation.id);
        }
    }, [items]);

    // Expose openConversation function to parent component
    React.useEffect(function() {
        if (onOpenConversationChange) {
            onOpenConversationChange(openConversation);
        }
    }, [openConversation, onOpenConversationChange]);

    const onChange = function(key) {
        setActiveKey(key);
    };

    const add = async function() {
        try {
            newTabIndex.current = newTabIndex.current + 1;
            const conversation = await createConversation({
                title: 'New Conversation ' + newTabIndex.current,
                description: '',
                system_prompt: 'You are a helpful AI assistant.'
            });

            const newTab = {
                key: conversation.id,
                label: renderTabLabel(conversation),
                children: React.createElement('div', {
                    style: {
                        padding: '24px',
                        height: '100%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                    }
                },
                    React.createElement(Text, {
                        style: { color: '#999', fontSize: '14px' }
                    }, 'Start chatting...')
                ),
                conversation: conversation
            };

            setItems(function(prevItems) {
                return [...prevItems, newTab];
            });
            setActiveKey(conversation.id);
            message.success('Conversation created');
        } catch (err) {
            message.error('Failed to create conversation: ' + err.message);
        }
    };

    const renderTabLabel = function(conversation) {
        return React.createElement('div', {
            style: {
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
            }
        },
            React.createElement('span', null, conversation.title),
            React.createElement(Space, { size: 4 },
                React.createElement(Button, {
                    type: 'text',
                    size: 'small',
                    icon: React.createElement('i', { className: 'fas fa-cog', style: { fontSize: '12px' } }),
                    onClick: function(e) {
                        e.stopPropagation();
                        setSelectedConversation(conversation);
                        setSettingsVisible(true);
                    },
                    style: { padding: '2px 4px', height: 'auto' }
                }),
                React.createElement(Button, {
                    type: 'text',
                    size: 'small',
                    icon: React.createElement('i', { className: 'fas fa-wrench', style: { fontSize: '12px' } }),
                    onClick: function(e) {
                        e.stopPropagation();
                        setSelectedConversation(conversation);
                        setToolsVisible(true);
                    },
                    style: { padding: '2px 4px', height: 'auto' }
                })
            )
        );
    };

    const remove = async function(targetKey) {
        try {
            await deleteConversation(targetKey);

            const targetIndex = items.findIndex(function(pane) {
                return pane.key === targetKey;
            });
            const newPanes = items.filter(function(pane) {
                return pane.key !== targetKey;
            });

            if (newPanes.length && targetKey === activeKey) {
                const newActiveKey = newPanes[targetIndex === newPanes.length ? targetIndex - 1 : targetIndex].key;
                setActiveKey(newActiveKey);
            } else if (newPanes.length === 0) {
                setActiveKey(null);
            }

            setItems(newPanes);
            message.success('Conversation deleted');
        } catch (err) {
            message.error('Failed to delete conversation: ' + err.message);
        }
    };

    const onEdit = function(targetKey, action) {
        if (action === 'add') {
            add();
        } else {
            remove(targetKey);
        }
    };

    const menuItems = [
        {
            key: 'rename',
            label: (
                React.createElement('span', null,
                    React.createElement('i', { className: 'fas fa-edit', style: { marginRight: '8px' } }),
                    'Rename'
                )
            )
        },
        {
            key: 'duplicate',
            label: (
                React.createElement('span', null,
                    React.createElement('i', { className: 'fas fa-copy', style: { marginRight: '8px' } }),
                    'Duplicate'
                )
            )
        },
        {
            type: 'divider'
        },
        {
            key: 'close',
            label: (
                React.createElement('span', null,
                    React.createElement('i', { className: 'fas fa-times', style: { marginRight: '8px' } }),
                    'Close'
                )
            ),
            danger: true
        },
        {
            key: 'close-others',
            label: (
                React.createElement('span', null,
                    React.createElement('i', { className: 'fas fa-times-circle', style: { marginRight: '8px' } }),
                    'Close Others'
                )
            )
        },
        {
            key: 'close-all',
            label: (
                React.createElement('span', null,
                    React.createElement('i', { className: 'fas fa-ban', style: { marginRight: '8px' } }),
                    'Close All'
                )
            )
        }
    ];

    const handleMenuClick = function(info, tabKey) {
        if (info.key === 'close') {
            remove(tabKey);
        } else if (info.key === 'close-others') {
            const newPanes = items.filter(function(pane) {
                return pane.key === tabKey;
            });
            setItems(newPanes);
            setActiveKey(tabKey);
        } else if (info.key === 'close-all') {
            setItems([]);
            setActiveKey(null);
        }
    };

    const handleSaveSettings = async function(values) {
        try {
            const updated = await updateConversation(selectedConversation.id, values);

            setItems(function(prevItems) {
                return prevItems.map(function(item) {
                    if (item.key === updated.id) {
                        return {
                            ...item,
                            label: renderTabLabel(updated),
                            conversation: updated
                        };
                    }
                    return item;
                });
            });
        } catch (err) {
            throw err;
        }
    };

    const renderTabBar = function(props, DefaultTabBar) {
        return React.createElement(DefaultTabBar, Object.assign({}, props, {
            renderTabBarItem: function(tabProps) {
                const originalNode = React.createElement(DefaultTabBar.Tab, tabProps);

                return React.createElement(Dropdown, {
                    key: tabProps.key,
                    menu: {
                        items: menuItems,
                        onClick: function(info) {
                            handleMenuClick(info, tabProps.eventKey);
                        }
                    },
                    trigger: ['contextMenu']
                }, originalNode);
            }
        }));
    };

    return React.createElement('div', {
        style: {
            height: '100%',
            display: 'flex',
            flexDirection: 'column',
            background: '#fff',
            borderRadius: '8px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
            overflow: 'hidden'
        }
    },
        React.createElement(Tabs, {
            type: 'editable-card',
            onChange: onChange,
            activeKey: activeKey,
            onEdit: onEdit,
            items: items,
            tabBarStyle: {
                margin: 0,
                padding: '8px 16px 0',
                background: '#fafafa',
                borderBottom: '1px solid #e8e8e8'
            },
            style: {
                height: '100%'
            },
            renderTabBar: renderTabBar
        }),
        React.createElement(ConversationSettingsModal, {
            visible: settingsVisible,
            onClose: function() { setSettingsVisible(false); },
            conversation: selectedConversation,
            onSave: handleSaveSettings
        }),
        React.createElement(ConversationToolsModal, {
            visible: toolsVisible,
            onClose: function() { setToolsVisible(false); },
            conversationId: selectedConversation ? selectedConversation.id : null
        })
    );
}
