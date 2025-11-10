const { Form, Select, InputNumber, Button } = antd;

function Configuration() {
    return (
        <div style={{ padding: '16px' }}>
            <Form layout="vertical">
                <Form.Item label="Provider">
                    <Select placeholder="Select provider">
                        <Select.Option value="openai">OpenAI</Select.Option>
                        <Select.Option value="anthropic">Anthropic</Select.Option>
                    </Select>
                </Form.Item>

                <Form.Item label="Main Model">
                    <Select placeholder="Select main model">
                        <Select.Option value="gpt-4">GPT-4</Select.Option>
                        <Select.Option value="gpt-3.5">GPT-3.5</Select.Option>
                    </Select>
                </Form.Item>

                <Form.Item label="Main Model Max Tokens">
                    <InputNumber
                        min={1}
                        max={100000}
                        style={{ width: '100%' }}
                        placeholder="Enter max tokens"
                    />
                </Form.Item>

                <Form.Item label="Small Model">
                    <Select placeholder="Select small model">
                        <Select.Option value="gpt-3.5">GPT-3.5</Select.Option>
                        <Select.Option value="gpt-4">GPT-4</Select.Option>
                    </Select>
                </Form.Item>

                <Form.Item label="Small Model Max Tokens">
                    <InputNumber
                        min={1}
                        max={100000}
                        style={{ width: '100%' }}
                        placeholder="Enter max tokens"
                    />
                </Form.Item>

                <Form.Item>
                    <Button type="primary" block>
                        Save
                    </Button>
                </Form.Item>
            </Form>
        </div>
    );
}
