const { Typography, Tooltip } = antd;
const { Text } = Typography;

function OpenEditors({ conversationId }) {
    const [editors, setEditors] = React.useState([]);
    const [loading, setLoading] = React.useState(false);

    React.useEffect(function() {
        if (!conversationId) {
            setEditors([]);
            return;
        }

        async function loadEditors() {
            setLoading(true);
            try {
                const response = await fetch(`/conversations/${conversationId}/editors`);
                const data = await response.json();
                const editorsArray = Array.isArray(data.open_editors) ? data.open_editors : [];
                setEditors(editorsArray);
            } catch (err) {
                console.error('Failed to load editors:', err);
                setEditors([]);
            } finally {
                setLoading(false);
            }
        }

        loadEditors();
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
                className: 'fas fa-file-code',
                style: { color: '#06b6d4', fontSize: '14px' }
            }),
            React.createElement(Text, {
                style: {
                    color: '#fff',
                    fontWeight: 600,
                    fontSize: '13px'
                }
            }, 'Open Editors'),
            React.createElement('div', {
                style: {
                    marginLeft: 'auto',
                    background: 'rgba(6, 182, 212, 0.2)',
                    borderRadius: '10px',
                    padding: '2px 8px',
                    fontSize: '11px',
                    color: '#06b6d4',
                    fontWeight: 600
                }
            }, editors.length)
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
            }, 'Loading...') : editors.length === 0 ? React.createElement('div', {
                style: {
                    textAlign: 'center',
                    color: 'rgba(255, 255, 255, 0.5)',
                    fontSize: '12px',
                    padding: '8px'
                }
            }, 'No open editors') : editors.map(function(editor, index) {
                const fileName = editor.file_path ? editor.file_path.split(/[\\/]/).pop() : 'Unknown';
                return React.createElement('div', {
                    key: editor.id || index,
                    style: {
                        background: 'rgba(0, 0, 0, 0.2)',
                        borderRadius: '4px',
                        padding: '8px',
                        marginBottom: index < editors.length - 1 ? '8px' : 0,
                        border: '1px solid rgba(255, 255, 255, 0.05)'
                    }
                },
                    React.createElement('div', {
                        style: {
                            fontSize: '12px',
                            color: '#fff',
                            fontWeight: 500,
                            marginBottom: '4px',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '6px'
                        }
                    },
                        React.createElement('i', {
                            className: 'fas fa-file',
                            style: { fontSize: '10px', color: '#06b6d4' }
                        }),
                        fileName
                    ),
                    React.createElement('div', {
                        style: {
                            fontSize: '10px',
                            color: 'rgba(255, 255, 255, 0.5)',
                            whiteSpace: 'nowrap',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis'
                        },
                        title: editor.file_path
                    }, editor.file_path || 'No path')
                );
            })
        )
    );
}
