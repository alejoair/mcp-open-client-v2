const { Typography, Tooltip } = antd;
const { Text, Paragraph } = Typography;

function MetadataPanel({ conversation }) {
    if (!conversation) {
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
                className: 'fas fa-info-circle',
                style: { color: '#3b82f6', fontSize: '14px' }
            }),
            React.createElement(Text, {
                style: {
                    color: '#fff',
                    fontWeight: 600,
                    fontSize: '13px'
                }
            }, 'Conversation Info')
        ),
        // Title
        React.createElement('div', { style: { marginBottom: '12px' } },
            React.createElement('div', {
                style: {
                    fontSize: '11px',
                    color: 'rgba(255, 255, 255, 0.5)',
                    marginBottom: '4px'
                }
            }, 'Title'),
            React.createElement(Text, {
                style: {
                    color: '#fff',
                    fontSize: '13px',
                    display: 'block'
                }
            }, conversation.title || 'Untitled')
        ),
        // Description
        conversation.description && React.createElement('div', { style: { marginBottom: '12px' } },
            React.createElement('div', {
                style: {
                    fontSize: '11px',
                    color: 'rgba(255, 255, 255, 0.5)',
                    marginBottom: '4px'
                }
            }, 'Description'),
            React.createElement(Text, {
                style: {
                    color: 'rgba(255, 255, 255, 0.8)',
                    fontSize: '12px',
                    display: 'block'
                }
            }, conversation.description)
        ),
        // System Prompt
        conversation.system_prompt && React.createElement('div', null,
            React.createElement('div', {
                style: {
                    fontSize: '11px',
                    color: 'rgba(255, 255, 255, 0.5)',
                    marginBottom: '4px'
                }
            }, 'System Prompt'),
            React.createElement('div', {
                style: {
                    background: 'rgba(0, 0, 0, 0.3)',
                    borderRadius: '4px',
                    padding: '8px',
                    fontSize: '11px',
                    color: 'rgba(255, 255, 255, 0.8)',
                    maxHeight: '100px',
                    overflow: 'auto',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word'
                }
            }, conversation.system_prompt)
        )
    );
}
