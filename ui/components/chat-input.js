const { Input, Button, Space } = antd;
const { TextArea } = Input;

function ChatInput({ onSend, disabled, onSendFailed }) {
    const [value, setValue] = React.useState('');
    const textAreaRef = React.useRef(null);

    const handleSend = React.useCallback(function() {
        if (!value.trim() || disabled) return;
        const messageContent = value;
        setValue(''); // Clear immediately for optimistic UI

        // Call onSend and handle potential restoration on failure
        const result = onSend(messageContent);

        // Refocus the textarea after sending
        setTimeout(function() {
            if (textAreaRef.current) {
                textAreaRef.current.focus();
            }
        }, 0);

        // If onSend returns a promise that might fail, handle it
        if (result && result.catch) {
            result.catch(function(error) {
                // Restore message content on failure
                if (onSendFailed) {
                    onSendFailed(messageContent);
                }
                setValue(messageContent);
            });
        }
    }, [value, disabled, onSend, onSendFailed]);

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
                ref: textAreaRef,
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
