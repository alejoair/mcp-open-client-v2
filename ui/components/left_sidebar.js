const { Sider } = antd.Layout;
const { Collapse, Divider, Typography } = antd;
const { Title } = Typography;

function LeftSidebar({ collapsed, onCollapse }) {
    const items = [
        {
            key: '1',
            label: 'Configuration',
            children: <Configuration />
        },
        {
            key: '2',
            label: 'MCP Servers',
            children: <MCPServers />
        }
    ];

    return (
        <Sider
            collapsible
            collapsed={collapsed}
            onCollapse={onCollapse}
            width={300}
            collapsedWidth={80}
            style={{ background: '#1f1f1f' }}
        >
            {!collapsed && (
                <>
                    <div style={{ padding: '16px' }}>
                        <Title level={4} style={{ margin: 0, color: 'white' }}>
                            MCP Open Client
                        </Title>
                    </div>
                    <Divider style={{ margin: 0 }} />
                    <Collapse
                        accordion
                        items={items}
                        defaultActiveKey={['1']}
                    />
                </>
            )}
        </Sider>
    );
}
