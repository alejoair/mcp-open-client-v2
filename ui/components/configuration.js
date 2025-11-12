const { Form, Select, InputNumber, Button, message, Input, Space, Switch, Typography, Modal, Alert } = antd;
const { Text } = Typography;

function Configuration() {
    const { providers, defaultProvider, loading, updateModelConfig, updateProviderPartial, testProvider, setDefaultProvider, createProvider } = useProviders();
    const [form] = Form.useForm();
    const [newProviderForm] = Form.useForm();
    const [saving, setSaving] = React.useState(false);
    const [testing, setTesting] = React.useState(false);
    const [availableModels, setAvailableModels] = React.useState([]);
    const [modelsFetched, setModelsFetched] = React.useState(false);
    const [initialized, setInitialized] = React.useState(false);
    const [selectedProviderId, setSelectedProviderId] = React.useState(null);
    const [createModalVisible, setCreateModalVisible] = React.useState(false);
    const [creating, setCreating] = React.useState(false);

    // Set initial values when default provider loads (only once)
    React.useEffect(() => {
        if (!initialized && defaultProvider && providers.length > 0) {
            const provider = providers.find(p => p.id === defaultProvider);
            if (provider) {
                form.setFieldsValue({
                    provider_id: provider.id,
                    api_key: provider.config?.api_key || '',
                    main_model: provider.config?.models?.main?.model_name || '',
                    main_max_tokens: provider.config?.models?.main?.max_tokens || 4000,
                    small_model: provider.config?.models?.small?.model_name || '',
                    small_max_tokens: provider.config?.models?.small?.max_tokens || 2000,
                });

                // Set selected provider ID
                setSelectedProviderId(provider.id);

                // If models are already configured, mark as fetched
                if (provider.config?.models?.main || provider.config?.models?.small) {
                    setModelsFetched(true);
                }

                setInitialized(true);
            }
        }
    }, [defaultProvider, providers, form, initialized]);

    const handleTest = async () => {
        const providerId = form.getFieldValue('provider_id');
        const apiKey = form.getFieldValue('api_key');

        if (!providerId) {
            message.error('Please select a provider');
            return;
        }

        if (!apiKey) {
            message.error('Please enter an API key');
            return;
        }

        setTesting(true);
        try {
            // First update the API key
            await updateProviderPartial(providerId, { api_key: apiKey });

            // Then test the provider
            const result = await testProvider(providerId);

            if (result.success && result.available_models) {
                setAvailableModels(result.available_models);
                setModelsFetched(true);
                message.success(`Provider tested successfully! Found ${result.available_models.length} models`);
            } else {
                message.error(result.error_message || 'Failed to fetch models from provider');
                setModelsFetched(false);
            }
        } catch (error) {
            message.error('Failed to test provider: ' + error.message);
            setModelsFetched(false);
        } finally {
            setTesting(false);
        }
    };

    const handleSetDefault = async (providerId, checked) => {
        if (checked) {
            try {
                await setDefaultProvider(providerId);
                message.success('Default provider updated successfully');
            } catch (error) {
                message.error('Failed to set default provider: ' + error.message);
            }
        }
    };

    const handleSave = async (values) => {
        if (!modelsFetched) {
            message.error('Please test the provider first to fetch available models');
            return;
        }

        setSaving(true);
        try {
            // Update main model
            await updateModelConfig(values.provider_id, 'main', {
                model_name: values.main_model,
                max_tokens: values.main_max_tokens,
            });

            // Update small model
            await updateModelConfig(values.provider_id, 'small', {
                model_name: values.small_model,
                max_tokens: values.small_max_tokens,
            });

            message.success('Configuration saved successfully');
        } catch (error) {
            message.error('Failed to save configuration: ' + error.message);
        } finally {
            setSaving(false);
        }
    };

    const handleCreateProvider = async (values) => {
        setCreating(true);
        try {
            await createProvider({
                name: values.name,
                type: 'openai',
                base_url: values.base_url,
                api_key: ''
            });
            message.success('Provider created successfully');
            setCreateModalVisible(false);
            newProviderForm.resetFields();
        } catch (error) {
            message.error('Failed to create provider: ' + error.message);
        } finally {
            setCreating(false);
        }
    };

    return (
        <div style={{ padding: '16px', color: 'rgba(255, 255, 255, 0.9)' }}>
            <Button
                type="dashed"
                block
                icon={React.createElement('i', { className: 'fas fa-plus' })}
                onClick={() => setCreateModalVisible(true)}
                style={{
                    background: 'rgba(255, 255, 255, 0.05)',
                    borderColor: 'rgba(255, 255, 255, 0.3)',
                    color: 'rgba(255, 255, 255, 0.85)',
                    marginBottom: '16px'
                }}
            >
                Create New Provider
            </Button>

            <Form form={form} layout="vertical" onFinish={handleSave}>
                <Form.Item
                    label={React.createElement('span', { style: { color: 'rgba(255, 255, 255, 0.85)' } }, 'Provider')}
                    name="provider_id"
                    rules={[{ required: true, message: 'Please select a provider' }]}
                >
                    <Select
                        placeholder="Select provider"
                        loading={loading}
                        onChange={(value) => setSelectedProviderId(value)}
                    >
                        {providers.map(p => (
                            <Select.Option key={p.id} value={p.id}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <span>{p.config?.name || p.id}</span>
                                    {defaultProvider === p.id && (
                                        <Text type="success" style={{ fontSize: '12px' }}>Active</Text>
                                    )}
                                </div>
                            </Select.Option>
                        ))}
                    </Select>
                </Form.Item>

                <Form.Item>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Text style={{ color: 'rgba(255, 255, 255, 0.85)' }}>Set as active provider</Text>
                        <Switch
                            checked={selectedProviderId === defaultProvider}
                            onChange={(checked) => handleSetDefault(selectedProviderId, checked)}
                            disabled={!selectedProviderId}
                        />
                    </div>
                </Form.Item>

                <Form.Item
                    label={React.createElement('span', { style: { color: 'rgba(255, 255, 255, 0.85)' } }, 'API Key')}
                    name="api_key"
                    rules={[{ required: true, message: 'Please enter API key' }]}
                >
                    <Input.Password
                        placeholder="Enter API key"
                        autoComplete="off"
                    />
                </Form.Item>

                <Form.Item>
                    <Button
                        type="default"
                        onClick={handleTest}
                        block
                        loading={testing}
                    >
                        Test & Fetch Models
                    </Button>
                </Form.Item>

                {modelsFetched && (
                    <>
                        <Form.Item
                            label={React.createElement('span', { style: { color: 'rgba(255, 255, 255, 0.85)' } }, 'Main Model')}
                            name="main_model"
                            rules={[{ required: true, message: 'Please select main model' }]}
                        >
                            <Select placeholder="Select main model">
                                {availableModels.map(model => (
                                    <Select.Option key={model} value={model}>
                                        {model}
                                    </Select.Option>
                                ))}
                            </Select>
                        </Form.Item>

                        <Form.Item
                            label={React.createElement('span', { style: { color: 'rgba(255, 255, 255, 0.85)' } }, 'Main Model Max Tokens')}
                            name="main_max_tokens"
                            rules={[{ required: true, message: 'Please enter max tokens' }]}
                        >
                            <InputNumber
                                min={1}
                                max={100000}
                                style={{ width: '100%' }}
                                placeholder="Enter max tokens"
                            />
                        </Form.Item>

                        <Form.Item
                            label={React.createElement('span', { style: { color: 'rgba(255, 255, 255, 0.85)' } }, 'Small Model')}
                            name="small_model"
                            rules={[{ required: true, message: 'Please select small model' }]}
                        >
                            <Select placeholder="Select small model">
                                {availableModels.map(model => (
                                    <Select.Option key={model} value={model}>
                                        {model}
                                    </Select.Option>
                                ))}
                            </Select>
                        </Form.Item>

                        <Form.Item
                            label={React.createElement('span', { style: { color: 'rgba(255, 255, 255, 0.85)' } }, 'Small Model Max Tokens')}
                            name="small_max_tokens"
                            rules={[{ required: true, message: 'Please enter max tokens' }]}
                        >
                            <InputNumber
                                min={1}
                                max={100000}
                                style={{ width: '100%' }}
                                placeholder="Enter max tokens"
                            />
                        </Form.Item>

                        <Form.Item>
                            <Button type="primary" htmlType="submit" block loading={saving}>
                                Save
                            </Button>
                        </Form.Item>
                    </>
                )}
            </Form>

            <Modal
                title="Create New Provider"
                open={createModalVisible}
                onCancel={() => {
                    setCreateModalVisible(false);
                    newProviderForm.resetFields();
                }}
                footer={null}
            >
                <Alert
                    message="OpenAI-Compatible APIs Only"
                    description="Currently, only OpenAI-compatible API providers are supported. This includes OpenAI, Azure OpenAI, and other services that implement the OpenAI API format."
                    type="info"
                    showIcon
                    style={{ marginBottom: '16px' }}
                />
                <Form
                    form={newProviderForm}
                    layout="vertical"
                    onFinish={handleCreateProvider}
                >
                    <Form.Item
                        label="Provider Name"
                        name="name"
                        rules={[{ required: true, message: 'Please enter provider name' }]}
                    >
                        <Input placeholder="e.g., My OpenAI Provider" />
                    </Form.Item>

                    <Form.Item
                        label="Base URL"
                        name="base_url"
                        rules={[
                            { required: true, message: 'Please enter base URL' },
                            { type: 'url', message: 'Please enter a valid URL' }
                        ]}
                    >
                        <Input placeholder="e.g., https://api.openai.com/v1" />
                    </Form.Item>

                    <Form.Item>
                        <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
                            <Button onClick={() => {
                                setCreateModalVisible(false);
                                newProviderForm.resetFields();
                            }}>
                                Cancel
                            </Button>
                            <Button type="primary" htmlType="submit" loading={creating}>
                                Create
                            </Button>
                        </Space>
                    </Form.Item>
                </Form>
            </Modal>
        </div>
    );
}
