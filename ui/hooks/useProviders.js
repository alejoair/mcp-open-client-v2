function useProviders() {
    const context = React.useContext(ProvidersContext);

    if (!context) {
        throw new Error('useProviders must be used within ProvidersProvider');
    }

    return context;
}
