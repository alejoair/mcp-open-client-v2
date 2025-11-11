const conversationsService = {
    // Conversations CRUD
    async getAll() {
        return await api.get('/conversations');
    },

    async getById(id) {
        return await api.get(`/conversations/${id}`);
    },

    async create(data) {
        return await api.post('/conversations', data);
    },

    async update(id, data) {
        return await api.put(`/conversations/${id}`, data);
    },

    async delete(id) {
        return await api.delete(`/conversations/${id}`);
    },

    async search(query) {
        return await api.get(`/conversations/search?q=${encodeURIComponent(query)}`);
    },

    // Messages
    async getMessages(conversationId) {
        return await api.get(`/conversations/${conversationId}/messages`);
    },

    async addMessage(conversationId, message) {
        return await api.post(`/conversations/${conversationId}/messages`, message);
    },

    async deleteMessage(conversationId, messageId) {
        return await api.delete(`/conversations/${conversationId}/messages/${messageId}`);
    },

    // Context
    async getContext(conversationId) {
        return await api.get(`/conversations/${conversationId}/context`);
    },

    async addContext(conversationId, context) {
        return await api.post(`/conversations/${conversationId}/context`, context);
    },

    async updateContext(conversationId, contextId, context) {
        return await api.put(`/conversations/${conversationId}/context/${contextId}`, context);
    },

    async deleteContext(conversationId, contextId) {
        return await api.delete(`/conversations/${conversationId}/context/${contextId}`);
    },

    // Tools
    async getTools(conversationId) {
        return await api.get(`/conversations/${conversationId}/tools`);
    },

    async getAvailableTools(conversationId) {
        return await api.get(`/conversations/${conversationId}/tools/available`);
    },

    async enableTool(conversationId, tool) {
        return await api.post(`/conversations/${conversationId}/tools`, tool);
    },

    async disableTool(conversationId, serverId, toolName) {
        return await api.delete(`/conversations/${conversationId}/tools?server_id=${serverId}&tool_name=${encodeURIComponent(toolName)}`);
    },

    // Open Editors
    async getEditors(conversationId) {
        return await api.get(`/conversations/${conversationId}/editors`);
    },

    async addEditor(conversationId, editor) {
        return await api.post(`/conversations/${conversationId}/editors`, editor);
    },

    async removeEditor(conversationId, filePath) {
        return await api.delete(`/conversations/${conversationId}/editors?file_path=${encodeURIComponent(filePath)}`);
    },

    // Chat
    async sendMessage(conversationId, content) {
        return await api.post(`/conversations/${conversationId}/chat`, { content });
    }
};
