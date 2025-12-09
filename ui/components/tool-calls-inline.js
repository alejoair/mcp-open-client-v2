const { Spin, Collapse } = antd;
const { Panel } = Collapse;

/**
 * Component to display tool calls inline in assistant messages
 * Shows a clean, minimal design with status icons and expandable details
 */
function ToolCallsInline({ toolCalls, toolResponses }) {
    if (!toolCalls || toolCalls.length === 0) {
        return null;
    }

    return React.createElement('div', {
        style: {
            display: 'flex',
            flexDirection: 'column',
            gap: '8px'
        }
    },
        toolCalls.map(function(tc) {
            // Find response
            const toolResponse = toolResponses ? toolResponses.find(function(tr) {
                return tr.tool_call_id === tc.id;
            }) : null;

            const isComplete = toolResponse && toolResponse._status === 'completed';
            const isError = toolResponse && toolResponse._status === 'error';
            const isPending = !toolResponse || toolResponse._status === 'pending';

            const statusIcon = isError ? '❌' : isComplete ? '✅' : '⏳';

            // Parse arguments
            let parsedArgs = null;
            try {
                parsedArgs = typeof tc.function.arguments === 'string'
                    ? JSON.parse(tc.function.arguments)
                    : tc.function.arguments;
            } catch (e) {
                parsedArgs = tc.function.arguments;
            }

            // Parse response
            let parsedResponse = null;
            if (toolResponse && toolResponse.content) {
                try {
                    // First try to parse as JSON
                    let content = toolResponse.content;

                    // Check if it's a CallToolResult string representation
                    if (typeof content === 'string' && content.includes('CallToolResult')) {
                        // Extract the text content from CallToolResult
                        const textMatch = content.match(/text='([^']+(?:\\'[^']*)*)'|text="([^"]+(?:\\"[^"]*)*)"/);
                        if (textMatch) {
                            content = textMatch[1] || textMatch[2];
                            // Unescape the content
                            content = content.replace(/\\n/g, '\n').replace(/\\"/g, '"').replace(/\\'/g, "'");
                        }
                    }

                    // Try to parse the extracted content as JSON
                    parsedResponse = JSON.parse(content);
                } catch (e) {
                    // If parsing fails, use the raw content
                    parsedResponse = toolResponse.content;
                }
            }

            return React.createElement('div', {
                key: tc.id,
                style: {
                    display: 'flex',
                    flexDirection: 'column',
                    background: 'rgba(255, 255, 255, 0.04)',
                    borderRadius: '6px',
                    overflow: 'hidden'
                }
            },
                // Header
                React.createElement('div', {
                    style: {
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '6px',
                        padding: '6px 12px',
                        fontSize: '12px'
                    }
                },
                    React.createElement('span', null, statusIcon),
                    React.createElement('span', {
                        style: {
                            color: 'rgba(255, 255, 255, 0.9)',
                            fontWeight: 500
                        }
                    }, tc.function.name),
                    isPending && React.createElement(Spin, { size: 'small', style: { marginLeft: '4px' } })
                ),
                // Expandable details
                React.createElement(Collapse, {
                    ghost: true,
                    bordered: false,
                    style: {
                        background: 'transparent'
                    }
                },
                    React.createElement(Panel, {
                        header: 'Ver detalles',
                        key: '1',
                        style: {
                            background: 'transparent',
                            border: 'none',
                            padding: 0
                        }
                    },
                        React.createElement('div', {
                            style: {
                                display: 'grid',
                                gridTemplateColumns: '1fr 1fr',
                                gap: '12px',
                                padding: '8px 12px 12px'
                            }
                        },
                            // Arguments column
                            React.createElement('div', {
                                style: {
                                    display: 'flex',
                                    flexDirection: 'column',
                                    gap: '6px'
                                }
                            },
                                React.createElement('div', {
                                    style: {
                                        fontSize: '11px',
                                        fontWeight: 600,
                                        color: 'rgba(255, 255, 255, 0.7)',
                                        textTransform: 'uppercase',
                                        letterSpacing: '0.5px'
                                    }
                                }, 'Argumentos'),
                                React.createElement('pre', {
                                    style: {
                                        background: 'rgba(0, 0, 0, 0.3)',
                                        padding: '8px',
                                        borderRadius: '4px',
                                        fontSize: '11px',
                                        overflow: 'auto',
                                        maxHeight: '200px',
                                        whiteSpace: 'pre-wrap',
                                        color: 'rgba(255, 255, 255, 0.85)',
                                        border: '1px solid rgba(255, 255, 255, 0.1)',
                                        margin: 0
                                    }
                                }, typeof parsedArgs === 'object'
                                    ? JSON.stringify(parsedArgs, null, 2)
                                    : String(parsedArgs))
                            ),
                            // Response column
                            React.createElement('div', {
                                style: {
                                    display: 'flex',
                                    flexDirection: 'column',
                                    gap: '6px'
                                }
                            },
                                React.createElement('div', {
                                    style: {
                                        fontSize: '11px',
                                        fontWeight: 600,
                                        color: 'rgba(255, 255, 255, 0.7)',
                                        textTransform: 'uppercase',
                                        letterSpacing: '0.5px'
                                    }
                                }, 'Respuesta'),
                                isPending
                                    ? React.createElement('div', {
                                        style: {
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            padding: '20px',
                                            color: 'rgba(255, 255, 255, 0.5)',
                                            fontSize: '11px'
                                        }
                                    },
                                        React.createElement(Spin, { size: 'small' }),
                                        React.createElement('span', { style: { marginLeft: '8px' } }, 'Ejecutando...')
                                    )
                                    : React.createElement('pre', {
                                        style: {
                                            background: isError ? 'rgba(255, 77, 79, 0.1)' : 'rgba(0, 0, 0, 0.3)',
                                            padding: '8px',
                                            borderRadius: '4px',
                                            fontSize: '11px',
                                            overflow: 'auto',
                                            maxHeight: '200px',
                                            whiteSpace: 'pre-wrap',
                                            color: isError ? 'rgba(255, 77, 79, 0.9)' : 'rgba(255, 255, 255, 0.85)',
                                            border: '1px solid ' + (isError ? 'rgba(255, 77, 79, 0.3)' : 'rgba(255, 255, 255, 0.1)'),
                                            margin: 0
                                        }
                                    }, parsedResponse
                                        ? (typeof parsedResponse === 'object'
                                            ? JSON.stringify(parsedResponse, null, 2)
                                            : String(parsedResponse))
                                        : 'Sin respuesta')
                            )
                        )
                    )
                )
            );
        })
    );
}
