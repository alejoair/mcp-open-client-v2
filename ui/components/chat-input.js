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
            background: 'white',
            borderTop: '1px solid #f0f0f0'
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
                style: { height: 'auto' }
            })
        )
    );
}
