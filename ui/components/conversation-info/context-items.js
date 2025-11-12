const { Typography } = antd;
const { Text } = Typography;

function ContextItems({ conversationId }) {
    const [contexts, setContexts] = React.useState([]);
    const [loading, setLoading] = React.useState(false);

    React.useEffect(function() {
        if (!conversationId) {
            setContexts([]);
            return;
        }

        async function loadContexts() {
            setLoading(true);
            try {
                const response = await fetch(`/conversations/${conversationId}/context`);
                const data = await response.json();
                const contextArray = Array.isArray(data.context) ? data.context : [];
                setContexts(contextArray);
            } catch (err) {
                console.error('Failed to load contexts:', err);
                setContexts([]);
            } finally {
                setLoading(false);
            }
        }

        loadContexts();
    }, [conversationId]);

    if (!conversationId) {
        return null;
    }

    return React.createElement('div', {
        style: {
            background: 'rgba(255, 255, 255, 0.05)',
            borderRadius: '8px',
            padding: '16px',
            border: '1px solid rgba(255, 255, 255, 0.1)'
        }
    },
        React.createElement('div', {
            style: {
                marginBottom: '12px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
            }
        },
            React.createElement('i', {
                className: 'fas fa-layer-group',
                style: { color: '#8b5cf6', fontSize: '14px' }
            }),
            React.createElement(Text, {
                style: {
                    color: '#fff',
                    fontWeight: 600,
                    fontSize: '13px'
                }
            }, 'Context Items'),
            React.createElement('div', {
                style: {
                    marginLeft: 'auto',
                    background: 'rgba(139, 92, 246, 0.2)',
                    borderRadius: '10px',
                    padding: '2px 8px',
                    fontSize: '11px',
                    color: '#8b5cf6',
                    fontWeight: 600
                }
            }, contexts.length)
        ),
        React.createElement('div', {
            style: {
                maxHeight: '200px',
                overflow: 'auto'
            }
        },
            loading ? React.createElement('div', {
                style: {
                    textAlign: 'center',
                    color: 'rgba(255, 255, 255, 0.5)',
                    fontSize: '12px',
                    padding: '8px'
                }
            }, 'Loading...') : contexts.length === 0 ? React.createElement('div', {
                style: {
                    textAlign: 'center',
                    color: 'rgba(255, 255, 255, 0.5)',
                    fontSize: '12px',
                    padding: '8px'
                }
            }, 'No context items') : contexts.map(function(context, index) {
                return React.createElement('div', {
                    key: context.id || index,
                    style: {
                        background: 'rgba(0, 0, 0, 0.2)',
                        borderRadius: '4px',
                        padding: '8px',
                        marginBottom: index < contexts.length - 1 ? '8px' : 0,
                        border: '1px solid rgba(255, 255, 255, 0.05)'
                    }
                },
                    React.createElement('div', {
                        style: {
                            fontSize: '11px',
                            color: 'rgba(255, 255, 255, 0.5)',
                            marginBottom: '4px',
                            textTransform: 'uppercase',
                            fontWeight: 600
                        }
                    }, context.type || 'text'),
                    React.createElement('div', {
                        style: {
                            fontSize: '12px',
                            color: 'rgba(255, 255, 255, 0.9)',
                            maxHeight: '60px',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'pre-wrap',
                            wordBreak: 'break-word'
                        }
                    }, context.content)
                );
            })
        )
    );
}
