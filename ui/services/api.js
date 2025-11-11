// Base API client
// Use the same origin as the page to avoid CORS issues
const API_BASE_URL = window.location.origin;

async function request(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;

    const config = {
        headers: {
            'Content-Type': 'application/json',
            ...options.headers,
        },
        ...options,
    };

    try {
        const response = await fetch(url, config);
        const data = await response.json();

        if (!response.ok) {
            const errorMessage = typeof data.detail === 'string'
                ? data.detail
                : (data.detail && typeof data.detail === 'object'
                    ? JSON.stringify(data.detail)
                    : (data.error || 'Request failed'));

            console.error('API Error:', {
                status: response.status,
                statusText: response.statusText,
                url: url,
                data: data
            });

            throw new Error(errorMessage);
        }

        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

const api = {
    get: (endpoint) => request(endpoint, { method: 'GET' }),
    post: (endpoint, body) => request(endpoint, { method: 'POST', body: JSON.stringify(body) }),
    put: (endpoint, body) => request(endpoint, { method: 'PUT', body: JSON.stringify(body) }),
    patch: (endpoint, body) => request(endpoint, { method: 'PATCH', body: JSON.stringify(body) }),
    delete: (endpoint) => request(endpoint, { method: 'DELETE' }),
};
