// MCP Servers API Service
const serversService = {
    // Get all servers
    async getAll() {
        return await api.get('/servers');
    },

    // Get single server
    async getById(id) {
        return await api.get(`/servers/${id}`);
    },

    // Create server
    async create(data) {
        return await api.post('/servers', data);
    },

    // Update server
    async update(id, data) {
        return await api.put(`/servers/${id}`, data);
    },

    // Delete server
    async delete(id) {
        return await api.delete(`/servers/${id}`);
    },

    // Start server
    async start(id) {
        return await api.post(`/servers/${id}/start`);
    },

    // Stop server
    async stop(id) {
        return await api.post(`/servers/${id}/stop`);
    },

    // Get server tools
    async getTools(id) {
        return await api.get(`/servers/${id}/tools`);
    },
};
