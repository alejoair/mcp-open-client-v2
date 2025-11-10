function useServers() {
    const context = React.useContext(ServersContext);

    if (!context) {
        throw new Error('useServers must be used within ServersProvider');
    }

    return context;
}
