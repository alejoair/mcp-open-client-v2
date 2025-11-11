const { Content } = antd.Layout;

function MainContent({ onOpenConversationChange }) {
    return (
        <Content style={{ padding: '24px', margin: 0, height: 'calc(100vh - 64px)', overflow: 'auto' }}>
            <ChatLayout onOpenConversationChange={onOpenConversationChange} />
        </Content>
    );
}
