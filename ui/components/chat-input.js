const { Input, Button, Space } = antd;
const { TextArea } = Input;

function ChatInput({ onSend, disabled }) {
    const [value, setValue] = React.useState('');

    const handleSend = React.useCallback(function() {
        if (!value.trim() || disabled) return;
        onSend(value);
        setValue('');
    }, [value, disabled, onSend]);

    const handleKeyPress = React.useCallback(function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    }, [handleSend]);

    return React.createElement('div', {
        style: {
            padding: '16px',
            background: '#2a2a2a',
            borderTop: '1px solid rgba(255, 255, 255, 0.1)'
        }
    },
        React.createElement(Space.Compact, {
            style: { width: '100%' }
        },
            React.createElement(TextArea, {
                value: value,
                onChange: function(e) { setValue(e.target.value); },
                onKeyPress: handleKeyPress,
                placeholder: 'Type your message... (Enter to send, Shift+Enter for new line)',
                disabled: disabled,
                autoSize: { minRows: 1, maxRows: 6 },
                style: { resize: 'none' }
            }),
            React.createElement(Button, {
                type: 'primary',
                onClick: handleSend,
                disabled: disabled || !value.trim(),
                icon: React.createElement('i', { className: 'fas fa-paper-plane' }),
                style: {
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    borderColor: '#667eea',
                    fontWeight: 600,
                    minHeight: '32px',
                    display: 'flex',
                    alignItems: 'center'
                }
            })
        )
    );
}
