/**
 * Hook for establishing SSE connection to receive real-time tool execution events
 */
function useSSEConnection(conversationId, onToolEvent) {
    const [connected, setConnected] = React.useState(false);
    const [connecting, setConnecting] = React.useState(false);

    React.useEffect(function() {
        if (!conversationId) {
            setConnected(false);
            setConnecting(false);
            return;
        }

        setConnecting(true);

        const baseUrl = window.location.origin;
        const sseUrl = `${baseUrl}/sse/conversations/${conversationId}`;

        console.log('[SSE] Connecting to:', sseUrl);
        const eventSource = new EventSource(sseUrl);

        eventSource.onopen = function() {
            console.log('[SSE] Connection opened for conversation:', conversationId);
            setConnecting(false);
            setConnected(true);
        };

        eventSource.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                console.log('[SSE] Event received:', data);

                // Filter tool and context events
                if (data.type === 'tool_call' || data.type === 'tool_response' || data.type === 'tool_error' ||
                    data.type === 'context_added' || data.type === 'context_updated' || data.type === 'context_deleted') {
                    if (onToolEvent) {
                        onToolEvent(data.type, data);
                    }
                }
            } catch (error) {
                console.error('[SSE] Error parsing event data:', error);
            }
        };

        eventSource.onerror = function(error) {
            console.error('[SSE] Connection error:', error);
            setConnecting(false);
            setConnected(false);
        };

        // Cleanup on unmount
        return function() {
            console.log('[SSE] Closing connection for conversation:', conversationId);
            eventSource.close();
            setConnected(false);
            setConnecting(false);
        };
    }, [conversationId, onToolEvent]);

    return { connected, connecting };
}
