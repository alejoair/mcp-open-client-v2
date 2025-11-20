const { Layout } = antd;

function MainLayout() {
    const [leftCollapsed, setLeftCollapsed] = React.useState(false);
    const [rightCollapsed, setRightCollapsed] = React.useState(false);
    const [openConversationFn, setOpenConversationFn] = React.useState(null);
    const [activeConversationData, setActiveConversationData] = React.useState(null);

    const handleOpenConversationChange = React.useCallback(function(fn) {
        setOpenConversationFn(function() {
            return fn;
        });
    }, []);

    const handleActiveConversationChange = React.useCallback(function(data) {
        setActiveConversationData(data);
    }, []);

    return (
        <Layout style={{ minHeight: '100vh' }}>
            <LeftSidebar
                collapsed={leftCollapsed}
                onCollapse={setLeftCollapsed}
                onSelectConversation={openConversationFn}
            />
            <Layout>
                <Header />
                <MainContent
                    onOpenConversationChange={handleOpenConversationChange}
                    onActiveConversationChange={handleActiveConversationChange}
                />
            </Layout>
            <RightSidebar
                collapsed={rightCollapsed}
                onCollapse={setRightCollapsed}
                activeConversation={activeConversationData ? activeConversationData.conversation : null}
                tokenInfo={activeConversationData ? activeConversationData.tokenInfo : null}
                messageCount={activeConversationData ? activeConversationData.messageCount : null}
                onOpenSettings={activeConversationData ? activeConversationData.onOpenSettings : null}
                onOpenTools={activeConversationData ? activeConversationData.onOpenTools : null}
                toolsRefreshKey={activeConversationData ? activeConversationData.toolsRefreshKey : 0}
                contextRefreshKey={activeConversationData ? activeConversationData.contextRefreshKey : 0}
            />
        </Layout>
    );
}
