const { createContext, useContext, useState, useEffect } = React;

const DevModeContext = createContext();

function DevModeProvider({ children }) {
    const [devMode, setDevMode] = useState(() => {
        // Load from localStorage
        const saved = localStorage.getItem('devMode');
        return saved === 'true';
    });

    useEffect(() => {
        // Save to localStorage
        localStorage.setItem('devMode', devMode);

        // Add/remove class to body for CSS transitions
        if (devMode) {
            document.body.classList.add('dev-mode');
        } else {
            document.body.classList.remove('dev-mode');
        }
    }, [devMode]);

    const toggleDevMode = () => {
        setDevMode(prev => !prev);
    };

    return React.createElement(
        DevModeContext.Provider,
        { value: { devMode, toggleDevMode } },
        children
    );
}

function useDevMode() {
    const context = useContext(DevModeContext);
    if (!context) {
        throw new Error('useDevMode must be used within DevModeProvider');
    }
    return context;
}
