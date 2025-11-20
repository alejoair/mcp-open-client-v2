const { Tabs, Dropdown, Typography, message } = antd;
const { Text } = Typography;

function ChatLayout({ onOpenConversationChange, onActiveConversationChange }) {
    const { createConversation, updateConversation, deleteConversation, conversations } = useConversations();
    const [activeKey, setActiveKey] = React.useState(null);
    const [items, setItems] = React.useState([]);
    const [settingsVisible, setSettingsVisible] = React.useState(false);
    const [toolsVisible, setToolsVisible] = React.useState(false);
    const [selectedConversation, setSelectedConversation] = React.useState(null);
    const [activeConversationData, setActiveConversationData] = React.useState(null);
    const [isRestored, setIsRestored] = React.useState(false);
    const [toolsRefreshKey, setToolsRefreshKey] = React.useState(0);
    const [contextRefreshKey, setContextRefreshKey] = React.useState(0);

    const newTabIndex = React.useRef(0);

    // Function to open an existing conversation
    const openConversation = React.useCallback(function(conversation) {
        const handleOpenSettings = function() {
            const freshConversation = conversations.find(function(c) { return c.id === conversation.id; }) || conversation;
            setSelectedConversation(freshConversation);
            setSettingsVisible(true);
        };

        const handleOpenTools = function() {
            setSelectedConversation(conversation);
            setToolsVisible(true);
        };

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
                children: React.createElement(ChatContainer, {
                    conversationId: conversation.id,
                    onConversationUpdate: function(data) {
                        handleConversationUpdate({
                            ...data,
                            onOpenSettings: handleOpenSettings,
                            onOpenTools: handleOpenTools,
                            toolsRefreshKey: toolsRefreshKey,
                            contextRefreshKey: contextRefreshKey
                        });
                    },
                    onContextRefresh: function() {
                        setContextRefreshKey(function(prev) { return prev + 1; });
                    }
                }),
                conversation: conversation,
                onOpenSettings: handleOpenSettings,
                onOpenTools: handleOpenTools
            };

            setItems(function(prevItems) {
                return [...prevItems, newTab];
            });
            setActiveKey(conversation.id);
        }
    }, [items, conversations]);

    // Expose openConversation function to parent component
    React.useEffect(function() {
        if (onOpenConversationChange) {
            onOpenConversationChange(openConversation);
        }
    }, [openConversation, onOpenConversationChange]);

    const onChange = function(key) {
        setActiveKey(key);
    };

    // Notify parent when active conversation changes
    React.useEffect(function() {
        if (onActiveConversationChange) {
            onActiveConversationChange(activeConversationData);
        }
    }, [activeConversationData, onActiveConversationChange]);

    const handleConversationUpdate = React.useCallback(function(data) {
        setActiveConversationData(data);
    }, []);

    // Update toolsRefreshKey in activeConversationData when it changes
    React.useEffect(function() {
        if (activeConversationData) {
            setActiveConversationData(function(prev) {
                if (prev) {
                    return { ...prev, toolsRefreshKey: toolsRefreshKey };
                }
                return prev;
            });
        }
    }, [toolsRefreshKey]);

    // Auto-start MCP servers when a conversation is opened
    React.useEffect(function() {
        if (!activeKey) return;

        let cancelled = false;

        async function startConversationServers() {
            try {
                // Get the conversation's enabled tools
                const response = await api.get('/conversations/' + activeKey + '/tools');
                if (cancelled) return;

                const enabledTools = response.enabled_tools || [];
                if (enabledTools.length === 0) return;

                // Extract unique server IDs
                const serverIds = [...new Set(enabledTools.map(function(tool) {
                    return tool.server_id;
                }))];

                // Get current server status
                const serversResponse = await api.get('/servers/');
                if (cancelled) return;

                const servers = serversResponse.servers || [];

                // Start servers that are not running
                const serversToStart = servers.filter(function(server) {
                    return serverIds.includes(server.id) && server.status !== 'running';
                });

                if (serversToStart.length > 0) {
                    console.log('[AutoStart] Starting ' + serversToStart.length + ' MCP servers for conversation');

                    // Start all servers in parallel
                    await Promise.all(serversToStart.map(async function(server) {
                        try {
                            await api.post('/servers/' + server.id + '/start');
                            console.log('[AutoStart] Started server: ' + server.config.name);
                        } catch (err) {
                            console.error('[AutoStart] Failed to start server ' + server.config.name + ':', err);
                        }
                    }));
                }
            } catch (err) {
                if (!cancelled) {
                    console.error('[AutoStart] Failed to start conversation servers:', err);
                }
            }
        }

        startConversationServers();

        return function() {
            cancelled = true;
        };
    }, [activeKey]);

    // Restore tabs from localStorage on mount
    React.useEffect(function() {
        if (!isRestored && conversations.length > 0 && openConversation) {
            const savedTabs = StorageService.get('mcp-tabs');
            if (savedTabs && savedTabs.open && savedTabs.open.length > 0) {
                // Restore tabs
                savedTabs.open.forEach(function(convId) {
                    const conv = conversations.find(function(c) { return c.id === convId; });
                    if (conv) {
                        openConversation(conv);
                    }
                });
                // Restore active tab
                if (savedTabs.active) {
                    setActiveKey(savedTabs.active);
                }
            }
            setIsRestored(true);
        }
    }, [conversations, openConversation, isRestored]);

    // Save tabs to localStorage when they change
    React.useEffect(function() {
        if (isRestored) {
            const openTabIds = items.map(function(item) { return item.key; });
            StorageService.set('mcp-tabs', {
                open: openTabIds,
                active: activeKey
            });
        }
    }, [items, activeKey, isRestored]);

    const add = async function() {
        try {
            newTabIndex.current = newTabIndex.current + 1;
            const conversation = await createConversation({
                title: 'New Conversation ' + newTabIndex.current,
                description: '',
                system_prompt: 'You are a helpful AI assistant.'
            });

            const handleOpenSettings = function() {
                const freshConversation = conversations.find(function(c) { return c.id === conversation.id; }) || conversation;
                setSelectedConversation(freshConversation);
                setSettingsVisible(true);
            };

            const handleOpenTools = function() {
                setSelectedConversation(conversation);
                setToolsVisible(true);
            };

            const newTab = {
                key: conversation.id,
                label: renderTabLabel(conversation),
                children: React.createElement(ChatContainer, {
                    conversationId: conversation.id,
                    onConversationUpdate: function(data) {
                        handleConversationUpdate({
                            ...data,
                            onOpenSettings: handleOpenSettings,
                            onOpenTools: handleOpenTools,
                            toolsRefreshKey: toolsRefreshKey,
                            contextRefreshKey: contextRefreshKey
                        });
                    },
                    onContextRefresh: function() {
                        setContextRefreshKey(function(prev) { return prev + 1; });
                    }
                }),
                conversation: conversation,
                onOpenSettings: handleOpenSettings,
                onOpenTools: handleOpenTools
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
        return React.createElement('span', null, conversation.title);
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

            // Update selected conversation so modal shows updated values if reopened
            setSelectedConversation(updated);
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
            onClose: function() {
                setSettingsVisible(false);
                setSelectedConversation(null);
            },
            conversation: selectedConversation,
            onSave: handleSaveSettings
        }),
        React.createElement(ConversationToolsModal, {
            visible: toolsVisible,
            onClose: function() {
                setToolsVisible(false);
                setToolsRefreshKey(function(prev) { return prev + 1; });
            },
            conversationId: selectedConversation ? selectedConversation.id : null
        })
    );
}
