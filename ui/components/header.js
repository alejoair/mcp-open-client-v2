const { Header: AntHeader } = antd.Layout;
const { Typography, Space } = antd;
const { Title, Text } = Typography;

function Header() {
    return (
        React.createElement(AntHeader, {
            style: {
                background: '#1f1f1f',
                padding: '0 24px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
                borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
                height: '64px',
                position: 'sticky',
                top: 0,
                zIndex: 1000
            }
        },
            React.createElement(Space, { size: 'large', align: 'center' },
                React.createElement('div', {
                    style: {
                        display: 'flex',
                        alignItems: 'center',
                        gap: '12px'
                    }
                },
                    React.createElement('div', {
                        style: {
                            width: '40px',
                            height: '40px',
                            background: 'rgba(255, 255, 255, 0.2)',
                            borderRadius: '8px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            backdropFilter: 'blur(10px)',
                            border: '1px solid rgba(255, 255, 255, 0.3)'
                        }
                    },
                        React.createElement('i', {
                            className: 'fas fa-plug',
                            style: {
                                fontSize: '24px',
                                color: '#fff'
                            }
                        })
                    ),
                    React.createElement('div', null,
                        React.createElement(Title, {
                            level: 4,
                            style: {
                                margin: 0,
                                color: '#fff',
                                fontWeight: 700,
                                letterSpacing: '-0.5px'
                            }
                        }, 'MCP Open Client'),
                        React.createElement(Text, {
                            style: {
                                fontSize: '11px',
                                color: 'rgba(255, 255, 255, 0.8)',
                                display: 'block',
                                marginTop: '-4px'
                            }
                        }, 'Model Context Protocol Manager')
                    )
                )
            ),
            React.createElement('div', {
                style: {
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '6px 12px',
                    background: 'rgba(255, 255, 255, 0.1)',
                    borderRadius: '20px',
                    backdropFilter: 'blur(10px)',
                    border: '1px solid rgba(255, 255, 255, 0.15)'
                }
            },
                React.createElement('i', {
                    className: 'fas fa-bolt',
                    style: {
                        fontSize: '14px',
                        color: '#10b981'
                    }
                }),
                React.createElement(Text, {
                    style: {
                        color: '#fff',
                        fontSize: '12px',
                        fontWeight: 500
                    }
                }, 'Active')
            )
        )
    );
}
