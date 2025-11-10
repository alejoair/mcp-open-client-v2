const { createContext } = React;

const ServersContext = createContext();

function ServersProvider({ children }) {
    const [servers, setServers] = React.useState([]);
    const [loading, setLoading] = React.useState(false);
    const [error, setError] = React.useState(null);

    // Load servers
    const loadServers = React.useCallback(async function() {
        setLoading(true);
        setError(null);
        try {
            const response = await serversService.getAll();
            setServers(response.servers || []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, []);

    // Get server by ID
    const getServer = React.useCallback(async function(id) {
        try {
            const response = await serversService.getById(id);
            return response.server;
        } catch (err) {
            setError(err.message);
            throw err;
        }
    }, []);

    // Create server
    const createServer = React.useCallback(async function(data) {
        setLoading(true);
        setError(null);
        try {
            const response = await serversService.create(data);
            await loadServers();
            return response;
        } catch (err) {
            setError(err.message);
            throw err;
        } finally {
            setLoading(false);
        }
    }, [loadServers]);

    // Update server
    const updateServer = React.useCallback(async function(id, data) {
        setLoading(true);
        setError(null);
        try {
            const response = await serversService.update(id, data);
            await loadServers();
            return response;
        } catch (err) {
            setError(err.message);
            throw err;
        } finally {
            setLoading(false);
        }
    }, [loadServers]);

    // Delete server
    const deleteServer = React.useCallback(async function(id) {
        setLoading(true);
        setError(null);
        try {
            await serversService.delete(id);
            await loadServers();
        } catch (err) {
            setError(err.message);
            throw err;
        } finally {
            setLoading(false);
        }
    }, [loadServers]);

    // Start server
    const startServer = React.useCallback(async function(id) {
        setError(null);
        try {
            const response = await serversService.start(id);
            setServers(function(prev) {
                return prev.map(function(s) {
                    return s.id === id ? response.server : s;
                });
            });
            return response;
        } catch (err) {
            setError(err.message);
            throw err;
        }
    }, []);

    // Stop server
    const stopServer = React.useCallback(async function(id) {
        setError(null);
        try {
            const response = await serversService.stop(id);
            setServers(function(prev) {
                return prev.map(function(s) {
                    return s.id === id ? response.server : s;
                });
            });
            return response;
        } catch (err) {
            setError(err.message);
            throw err;
        }
    }, []);

    // Get server tools
    const getServerTools = React.useCallback(async function(id) {
        setError(null);
        try {
            const response = await serversService.getTools(id);
            return response.tools || [];
        } catch (err) {
            setError(err.message);
            throw err;
        }
    }, []);

    // Load servers on mount
    React.useEffect(function() {
        loadServers();
    }, [loadServers]);

    const value = {
        servers: servers,
        loading: loading,
        error: error,
        loadServers: loadServers,
        getServer: getServer,
        createServer: createServer,
        updateServer: updateServer,
        deleteServer: deleteServer,
        startServer: startServer,
        stopServer: stopServer,
        getServerTools: getServerTools,
    };

    return (
        <ServersContext.Provider value={value}>
            {children}
        </ServersContext.Provider>
    );
}
