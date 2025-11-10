const { Sider } = antd.Layout;

function RightSidebar({ collapsed, onCollapse }) {
    return (
        <Sider
            collapsible
            collapsed={collapsed}
            onCollapse={onCollapse}
            reverseArrow
            style={{ background: '#1f1f1f' }}
        >
            Right Sidebar
        </Sider>
    );
}
