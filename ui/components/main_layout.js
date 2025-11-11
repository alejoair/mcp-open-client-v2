const { Layout } = antd;

function MainLayout() {
    const [leftCollapsed, setLeftCollapsed] = React.useState(false);
    const [rightCollapsed, setRightCollapsed] = React.useState(false);
    const [openConversationFn, setOpenConversationFn] = React.useState(null);

    const handleOpenConversationChange = React.useCallback(function(fn) {
        setOpenConversationFn(function() {
            return fn;
        });
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
                <MainContent onOpenConversationChange={handleOpenConversationChange} />
            </Layout>
            <RightSidebar
                collapsed={rightCollapsed}
                onCollapse={setRightCollapsed}
            />
        </Layout>
    );
}
