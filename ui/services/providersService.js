// Providers API Service
const providersService = {
    // Get all providers
    async getAll() {
        return await api.get('/providers');
    },

    // Get single provider
    async getById(id) {
        return await api.get(`/providers/${id}`);
    },

    // Create provider
    async create(data) {
        return await api.post('/providers', data);
    },

    // Update provider
    async update(id, data) {
        return await api.put(`/providers/${id}`, data);
    },

    // Delete provider
    async delete(id) {
        return await api.delete(`/providers/${id}`);
    },

    // Set default provider
    async setDefault(id) {
        return await api.post(`/providers/${id}/set-default`);
    },

    // Get models for provider
    async getModels(id) {
        return await api.get(`/providers/${id}/models`);
    },

    // Set model configuration
    async setModel(id, modelType, data) {
        return await api.post(`/providers/${id}/models/${modelType}`, data);
    },

    // Partial update provider (PATCH)
    async partialUpdate(id, data) {
        return await api.patch(`/providers/${id}`, data);
    },

    // Test provider and get available models
    async test(id) {
        return await api.post(`/providers/${id}/test`, {});
    },
};
