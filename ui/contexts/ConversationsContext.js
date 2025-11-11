const ConversationsContext = React.createContext(null);

function ConversationsProvider({ children }) {
    const [conversations, setConversations] = React.useState([]);
    const [loading, setLoading] = React.useState(false);
    const [error, setError] = React.useState(null);

    const loadConversations = React.useCallback(async function() {
        setLoading(true);
        setError(null);
        try {
            const response = await conversationsService.getAll();
            setConversations(response.conversations || []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, []);

    const getConversation = React.useCallback(async function(id) {
        try {
            const response = await conversationsService.getById(id);
            return response.conversation;
        } catch (err) {
            setError(err.message);
            throw err;
        }
    }, []);

    const createConversation = React.useCallback(async function(data) {
        setLoading(true);
        setError(null);
        try {
            const response = await conversationsService.create(data);
            await loadConversations();
            return response.conversation;
        } catch (err) {
            setError(err.message);
            throw err;
        } finally {
            setLoading(false);
        }
    }, [loadConversations]);

    const updateConversation = React.useCallback(async function(id, data) {
        setLoading(true);
        setError(null);
        try {
            const response = await conversationsService.update(id, data);
            await loadConversations();
            return response.conversation;
        } catch (err) {
            setError(err.message);
            throw err;
        } finally {
            setLoading(false);
        }
    }, [loadConversations]);

    const deleteConversation = React.useCallback(async function(id) {
        setLoading(true);
        setError(null);
        try {
            await conversationsService.delete(id);
            await loadConversations();
        } catch (err) {
            setError(err.message);
            throw err;
        } finally {
            setLoading(false);
        }
    }, [loadConversations]);

    const getTools = React.useCallback(async function(conversationId) {
        try {
            const response = await conversationsService.getTools(conversationId);
            return response.enabled_tools || [];
        } catch (err) {
            setError(err.message);
            throw err;
        }
    }, []);

    const getAvailableTools = React.useCallback(async function(conversationId) {
        try {
            const response = await conversationsService.getAvailableTools(conversationId);
            return response.available_tools || [];
        } catch (err) {
            setError(err.message);
            throw err;
        }
    }, []);

    const enableTool = React.useCallback(async function(conversationId, tool) {
        try {
            const response = await conversationsService.enableTool(conversationId, tool);
            return response.enabled_tools || [];
        } catch (err) {
            setError(err.message);
            throw err;
        }
    }, []);

    const disableTool = React.useCallback(async function(conversationId, serverId, toolName) {
        try {
            const response = await conversationsService.disableTool(conversationId, serverId, toolName);
            return response.enabled_tools || [];
        } catch (err) {
            setError(err.message);
            throw err;
        }
    }, []);

    React.useEffect(function() {
        loadConversations();
    }, [loadConversations]);

    const value = {
        conversations: conversations,
        loading: loading,
        error: error,
        loadConversations: loadConversations,
        getConversation: getConversation,
        createConversation: createConversation,
        updateConversation: updateConversation,
        deleteConversation: deleteConversation,
        getTools: getTools,
        getAvailableTools: getAvailableTools,
        enableTool: enableTool,
        disableTool: disableTool
    };

    return React.createElement(ConversationsContext.Provider, { value: value }, children);
}
