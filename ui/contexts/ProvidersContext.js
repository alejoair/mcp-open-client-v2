const { createContext } = React;

const ProvidersContext = createContext();

function ProvidersProvider({ children }) {
    const [providers, setProviders] = React.useState([]);
    const [defaultProvider, setDefaultProviderState] = React.useState(null);
    const [loading, setLoading] = React.useState(false);
    const [error, setError] = React.useState(null);

    // Load providers
    const loadProviders = React.useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await providersService.getAll();
            setProviders(response.providers || []);
            setDefaultProviderState(response.default_provider);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, []);

    // Get provider by ID
    const getProvider = React.useCallback(async (id) => {
        try {
            const response = await providersService.getById(id);
            return response.provider;
        } catch (err) {
            setError(err.message);
            throw err;
        }
    }, []);

    // Set model configuration
    const updateModelConfig = React.useCallback(async (providerId, modelType, config) => {
        setLoading(true);
        setError(null);
        try {
            await providersService.setModel(providerId, modelType, config);
            await loadProviders(); // Reload providers after update
        } catch (err) {
            setError(err.message);
            throw err;
        } finally {
            setLoading(false);
        }
    }, [loadProviders]);

    // Update provider partial data (API key, etc.)
    const updateProviderPartial = React.useCallback(async (providerId, data) => {
        setError(null);
        try {
            const result = await providersService.partialUpdate(providerId, data);
            // Update the provider in the local state without reloading
            setProviders(prev => prev.map(p =>
                p.id === providerId
                    ? { ...p, config: { ...p.config, ...data } }
                    : p
            ));
            return result;
        } catch (err) {
            setError(err.message);
            throw err;
        }
    }, []);

    // Test provider connection
    const testProvider = React.useCallback(async (providerId) => {
        setLoading(true);
        setError(null);
        try {
            const result = await providersService.test(providerId);
            return result;
        } catch (err) {
            setError(err.message);
            throw err;
        } finally {
            setLoading(false);
        }
    }, []);

    // Set default provider
    const setDefaultProvider = React.useCallback(async (providerId) => {
        setError(null);
        try {
            await providersService.setDefault(providerId);
            // Update default provider in local state without reloading
            setDefaultProviderState(providerId);
        } catch (err) {
            setError(err.message);
            throw err;
        }
    }, []);

    // Load providers on mount
    React.useEffect(() => {
        loadProviders();
    }, [loadProviders]);

    const value = {
        providers,
        defaultProvider,
        loading,
        error,
        loadProviders,
        getProvider,
        updateModelConfig,
        updateProviderPartial,
        testProvider,
        setDefaultProvider,
    };

    return (
        <ProvidersContext.Provider value={value}>
            {children}
        </ProvidersContext.Provider>
    );
}
