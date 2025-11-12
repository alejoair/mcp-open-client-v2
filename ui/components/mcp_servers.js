const { List, Button, Space, Typography, Tag, Popconfirm, message, Tooltip, Modal, Form, Input, InputNumber, Collapse } = antd;
const { Text } = Typography;

function MCPServers() {
    const { servers, loading, deleteServer, startServer, stopServer, createServer, getServerTools } = useServers();
    const [actionLoading, setActionLoading] = React.useState({});
    const [createModalVisible, setCreateModalVisible] = React.useState(false);
    const [form] = Form.useForm();
    const [creating, setCreating] = React.useState(false);
    const [serverTools, setServerTools] = React.useState({});
    const [loadingTools, setLoadingTools] = React.useState({});

    const getStatusColor = function(status) {
        const colors = {
            configured: 'default',
            starting: 'processing',
            running: 'success',
            stopping: 'warning',
            stopped: 'default',
            error: 'error',
        };
        return colors[status] || 'default';
    };

    const handleStart = async function(serverId) {
        setActionLoading(function(prev) {
            return { ...prev, [serverId]: 'starting' };
        });
        try {
            await startServer(serverId);
            message.success('Server started');
            
            // Get server tools after successful start
            setLoadingTools(function(prev) {
                return { ...prev, [serverId]: true };
            });
            try {
                const tools = await getServerTools(serverId);
                setServerTools(function(prev) {
                    return { ...prev, [serverId]: tools };
                });
            } catch (toolsError) {
                // Don't show error for tools, server started successfully
                console.warn('Failed to get tools:', toolsError);
            } finally {
                setLoadingTools(function(prev) {
                    return { ...prev, [serverId]: false };
                });
            }
        } catch (error) {
            message.error('Failed to start: ' + error.message);
        } finally {
            setActionLoading(function(prev) {
                return { ...prev, [serverId]: null };
            });
        }
    };

    const handleStop = async function(serverId) {
        setActionLoading(function(prev) {
            return { ...prev, [serverId]: 'stopping' };
        });
        try {
            await stopServer(serverId);
            message.success('Server stopped');
            
            // Clear tools when server is stopped
            setServerTools(function(prev) {
                const newTools = { ...prev };
                delete newTools[serverId];
                return newTools;
            });
        } catch (error) {
            message.error('Failed to stop: ' + error.message);
        } finally {
            setActionLoading(function(prev) {
                return { ...prev, [serverId]: null };
            });
        }
    };

    const handleDelete = async function(serverId) {
        try {
            await deleteServer(serverId);
            message.success('Server deleted');
        } catch (error) {
            message.error('Failed to delete: ' + error.message);
        }
    };

    const handleCreate = async function(values) {
        setCreating(true);
        try {
            // Prepare server configuration
            const serverConfig = {
                name: values.name,
                slug: values.slug || undefined,
                transport: "stdio",
                command: values.command,
                args: values.args ? values.args.split(' ').filter(arg => arg.trim()) : [],
                env: values.env ? values.env.split(',').map(pair => {
                    const [key, value] = pair.split('=');
                    return key.trim() + '=' + (value || '').trim();
                }).reduce((acc, pair) => {
                    const [key, value] = pair.split('=');
                    acc[key] = value;
                    return acc;
                }, {}) : null,
                cwd: values.cwd || null
            };

            await createServer({ server: serverConfig });
            message.success('Server created successfully');
            setCreateModalVisible(false);
            form.resetFields();
        } catch (error) {
            message.error('Failed to create server: ' + error.message);
        } finally {
            setCreating(false);
        }
    };

    const handleCancelCreate = function() {
        setCreateModalVisible(false);
        form.resetFields();
    };

    return (
        <div style={{ padding: '8px' }}>
            <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '8px'
            }}>
                <Text strong style={{ fontSize: '14px', color: 'rgba(255, 255, 255, 0.9)' }}>MCP Servers</Text>
                <Button
                    type="primary"
                    size="small"
                    onClick={function() { setCreateModalVisible(true); }}
                    icon="+"
                >
                    Add Server
                </Button>
            </div>
            <List
                loading={loading}
                dataSource={servers}
                size="small"
                locale={{ emptyText: 'No servers' }}
                renderItem={function(server) {
                    return (
                        <List.Item
                            key={server.id}
                            style={{
                                padding: '8px 0',
                                borderBottom: '1px solid rgba(255, 255, 255, 0.1)'
                            }}
                        >
                            <div style={{ width: '100%' }}>
                                <div style={{
                                    display: 'flex',
                                    justifyContent: 'space-between',
                                    alignItems: 'center',
                                    marginBottom: '4px'
                                }}>
                                    <Text strong style={{ fontSize: '13px', color: 'rgba(255, 255, 255, 0.9)' }}>
                                        {server.config.name}
                                    </Text>
                                    <Tag
                                        color={getStatusColor(server.status)}
                                        style={{ margin: 0, fontSize: '11px' }}
                                    >
                                        {server.status}
                                    </Tag>
                                </div>
                                <div style={{
                                    display: 'flex',
                                    gap: '4px',
                                    marginTop: '6px'
                                }}>
                                    <Button
                                        size="small"
                                        type={server.status === 'running' ? 'default' : 'primary'}
                                        block
                                        onClick={function() {
                                            if (server.status === 'running') {
                                                handleStop(server.id);
                                            } else {
                                                handleStart(server.id);
                                            }
                                        }}
                                        loading={actionLoading[server.id] === 'starting' || actionLoading[server.id] === 'stopping'}
                                        disabled={server.status === 'starting' || server.status === 'stopping'}
                                    >
                                        {server.status === 'running' ? 'Stop' : 'Start'}
                                    </Button>
                                    <Popconfirm
                                        title="Delete?"
                                        onConfirm={function() { handleDelete(server.id); }}
                                        okText="Yes"
                                        cancelText="No"
                                    >
                                        <Button size="small" danger>
                                            Del
                                        </Button>
                                    </Popconfirm>
                                </div>
                                {server.error_message && (
                                    <Text
                                        type="danger"
                                        style={{
                                            fontSize: '11px',
                                            display: 'block',
                                            marginTop: '4px'
                                        }}
                                    >
                                        {server.error_message}
                                    </Text>
                                )}
                                
                                {/* Show tools when server is running */}
                                {server.status === 'running' && (serverTools[server.id] || loadingTools[server.id]) && (
                                    <div style={{
                                        marginTop: '8px',
                                        padding: '8px',
                                        backgroundColor: '#2a2a2a',
                                        borderRadius: '4px',
                                        border: '1px solid rgba(255, 255, 255, 0.1)'
                                    }}>
                                        <Text strong style={{ fontSize: '12px', marginBottom: '4px', display: 'block', color: 'rgba(255, 255, 255, 0.85)' }}>
                                            Available Tools:
                                        </Text>
                                        {loadingTools[server.id] ? (
                                            <Text style={{ fontSize: '11px', color: 'rgba(255, 255, 255, 0.6)' }}>Loading tools...</Text>
                                        ) : (
                                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                                                {(serverTools[server.id] || []).map(function(tool) {
                                                    return (
                                                        <Tag
                                                            key={tool.name}
                                                            size="small"
                                                            color="blue"
                                                            style={{ fontSize: '10px' }}
                                                        >
                                                            {tool.name}
                                                        </Tag>
                                                    );
                                                })}
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        </List.Item>
                    );
                }}
            />
            
            <Modal
                title="Create New MCP Server"
                open={createModalVisible}
                onOk={form.submit}
                onCancel={handleCancelCreate}
                confirmLoading={creating}
                width={600}
            >
                <Form
                    form={form}
                    layout="vertical"
                    onFinish={handleCreate}
                >
                    <Form.Item
                        label="Server Name"
                        name="name"
                        rules={[{ required: true, message: 'Please enter server name' }]}
                    >
                        <Input placeholder="e.g., My Custom Server" />
                    </Form.Item>

                    <Form.Item
                        label="Slug (optional)"
                        name="slug"
                        help="Human-readable identifier, auto-generated from name if not provided"
                    >
                        <Input placeholder="e.g., my-custom-server" />
                    </Form.Item>

                    <Form.Item
                        label="Command"
                        name="command"
                        rules={[{ required: true, message: 'Please enter command' }]}
                        extra="The command to execute (e.g., npx.cmd)"
                    >
                        <Input placeholder="e.g., npx.cmd" />
                    </Form.Item>

                    <Form.Item
                        label="Arguments"
                        name="args"
                        help="Space-separated arguments"
                        extra="Example: -y @modelcontextprotocol/server-filesystem ."
                    >
                        <Input placeholder="-y @modelcontextprotocol/server-filesystem ." />
                    </Form.Item>

                    <Form.Item
                        label="Working Directory (optional)"
                        name="cwd"
                        extra="Directory where the command will be executed"
                    >
                        <Input placeholder="e.g., c:/path/to/project" />
                    </Form.Item>

                    <Form.Item
                        label="Environment Variables (optional)"
                        name="env"
                        help="Comma-separated key=value pairs"
                        extra="Example: API_KEY=123,TYPE=dev"
                    >
                        <Input placeholder="KEY1=value1,KEY2=value2" />
                    </Form.Item>
                </Form>
            </Modal>
        </div>
    );
}
