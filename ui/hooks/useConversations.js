function useConversations() {
    const context = React.useContext(ConversationsContext);
    if (!context) {
        throw new Error('useConversations must be used within ConversationsProvider');
    }
    return context;
}
