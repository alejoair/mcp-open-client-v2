const { Card, Statistic, Row, Col, Typography, Tag } = antd;
const { Text } = Typography;

function TokenCounter({ tokenInfo, conversation, messageCount }) {
    if (!tokenInfo && !messageCount) {
        return React.createElement('div', {
            style: {
                padding: '16px',
                textAlign: 'center',
                color: 'rgba(255, 255, 255, 0.5)',
                fontSize: '12px'
            }
        }, 'Send a message to see statistics');
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
                className: 'fas fa-chart-bar',
                style: { color: '#10b981', fontSize: '14px' }
            }),
            React.createElement(Text, {
                style: {
                    color: '#fff',
                    fontWeight: 600,
                    fontSize: '13px'
                }
            }, 'Usage Statistics')
        ),
        React.createElement(Row, { gutter: [12, 12] },
            React.createElement(Col, { span: 12 },
                React.createElement('div', {
                    style: {
                        background: 'rgba(16, 185, 129, 0.1)',
                        borderRadius: '6px',
                        padding: '12px',
                        border: '1px solid rgba(16, 185, 129, 0.2)'
                    }
                },
                    React.createElement('div', {
                        style: {
                            fontSize: '24px',
                            fontWeight: 700,
                            color: '#10b981',
                            lineHeight: 1
                        }
                    }, tokenInfo ? tokenInfo.tokenCount : '0'),
                    React.createElement('div', {
                        style: {
                            fontSize: '11px',
                            color: 'rgba(255, 255, 255, 0.6)',
                            marginTop: '4px'
                        }
                    }, 'Tokens')
                )
            ),
            React.createElement(Col, { span: 12 },
                React.createElement('div', {
                    style: {
                        background: 'rgba(59, 130, 246, 0.1)',
                        borderRadius: '6px',
                        padding: '12px',
                        border: '1px solid rgba(59, 130, 246, 0.2)'
                    }
                },
                    React.createElement('div', {
                        style: {
                            fontSize: '24px',
                            fontWeight: 700,
                            color: '#3b82f6',
                            lineHeight: 1
                        }
                    }, tokenInfo ? tokenInfo.messagesInContext : (messageCount || '0')),
                    React.createElement('div', {
                        style: {
                            fontSize: '11px',
                            color: 'rgba(255, 255, 255, 0.6)',
                            marginTop: '4px'
                        }
                    }, 'Messages')
                )
            )
        ),
        // Limits info
        conversation && (conversation.max_tokens || conversation.max_messages) && React.createElement('div', {
            style: {
                marginTop: '12px',
                padding: '8px',
                background: 'rgba(0, 0, 0, 0.2)',
                borderRadius: '4px'
            }
        },
            React.createElement('div', {
                style: {
                    fontSize: '11px',
                    color: 'rgba(255, 255, 255, 0.5)',
                    marginBottom: '4px'
                }
            }, 'Limits'),
            conversation.max_tokens && React.createElement('div', {
                style: {
                    fontSize: '11px',
                    color: 'rgba(255, 255, 255, 0.8)'
                }
            }, `Max tokens: ${conversation.max_tokens}`),
            conversation.max_messages && React.createElement('div', {
                style: {
                    fontSize: '11px',
                    color: 'rgba(255, 255, 255, 0.8)'
                }
            }, `Max messages: ${conversation.max_messages}`)
        )
    );
}
