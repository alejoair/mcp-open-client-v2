const { Sider } = antd.Layout;
const { Collapse, Divider, Typography } = antd;
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
