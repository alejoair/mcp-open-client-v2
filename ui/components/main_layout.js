const { Layout } = antd;

function MainLayout() {
    const [leftCollapsed, setLeftCollapsed] = React.useState(false);
    const [rightCollapsed, setRightCollapsed] = React.useState(false);

    return (
        <Layout style={{ minHeight: '100vh' }}>
            <LeftSidebar
                collapsed={leftCollapsed}
                onCollapse={setLeftCollapsed}
            />
            <Layout>
                <Header />
                <MainContent />
            </Layout>
            <RightSidebar
                collapsed={rightCollapsed}
                onCollapse={setRightCollapsed}
            />
        </Layout>
    );
}
