const { Modal, Form, Input, message } = antd;
const { TextArea } = Input;

function ConversationSettingsModal({ visible, onClose, conversation, onSave }) {
    const [form] = Form.useForm();
    const [saving, setSaving] = React.useState(false);

    React.useEffect(function() {
        if (visible && conversation) {
            form.setFieldsValue({
                title: conversation.title,
                description: conversation.description,
                system_prompt: conversation.system_prompt
            });
        }
    }, [visible, conversation, form]);

    const handleSave = async function() {
        try {
            const values = await form.validateFields();
            setSaving(true);
            await onSave(values);
            message.success('Conversation settings updated');
            onClose();
        } catch (err) {
            if (err.errorFields) {
                return;
            }
            message.error('Failed to update settings: ' + err.message);
        } finally {
            setSaving(false);
        }
    };

    return React.createElement(Modal, {
        title: React.createElement('span', null,
            React.createElement('i', { className: 'fas fa-cog', style: { marginRight: '8px' } }),
            'Conversation Settings'
        ),
        open: visible,
        onCancel: onClose,
        onOk: handleSave,
        confirmLoading: saving,
        width: 600
    },
        React.createElement(Form, {
            form: form,
            layout: 'vertical'
        },
            React.createElement(Form.Item, {
                name: 'title',
                label: 'Title',
                rules: [{ required: true, message: 'Please enter a title' }]
            },
                React.createElement(Input, {
                    placeholder: 'Enter conversation title'
                })
            ),
            React.createElement(Form.Item, {
                name: 'description',
                label: 'Description'
            },
                React.createElement(TextArea, {
                    rows: 3,
                    placeholder: 'Enter conversation description (optional)'
                })
            ),
            React.createElement(Form.Item, {
                name: 'system_prompt',
                label: 'System Prompt'
            },
                React.createElement(TextArea, {
                    rows: 4,
                    placeholder: 'You are a helpful AI assistant.'
                })
            )
        )
    );
}
