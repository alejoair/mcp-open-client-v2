/**
 * Hook for Server-Sent Events tool call streaming
 */

const { useState, useEffect, useRef } = React;

function useToolCallStream(conversationId) {
    const [events, setEvents] = useState([]);
    const [isConnected, setIsConnected] = useState(false);
    const [isConnecting, setIsConnecting] = useState(false);
    const eventSourceRef = useRef(null);

    const connect = React.useCallback(() => {
        if (!conversationId || eventSourceRef.current) {
            return;
        }

        setIsConnecting(true);
        const baseUrl = window.location.origin;
        const sseUrl = `${baseUrl}/sse/conversations/${conversationId}`;
        
        const eventSource = new EventSource(sseUrl);
        eventSourceRef.current = eventSource;

        eventSource.onopen = function() {
            console.log('SSE connection opened for conversation:', conversationId);
            setIsConnecting(false);
            setIsConnected(true);
        };

        eventSource.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                console.log('SSE Event received:', data);
                
                setEvents(prev => [...prev, {
                    ...data,
                    id: Date.now() + Math.random()
                }]);
            } catch (error) {
                console.error('Error parsing SSE event data:', error);
            }
        };

        eventSource.onerror = function(error) {
            console.error('SSE connection error:', error);
            setIsConnecting(false);
            setIsConnected(false);
            
            // Auto-reconnect after 3 seconds
            setTimeout(() => {
                if (eventSourceRef.current) {
                    eventSourceRef.current.close();
                    eventSourceRef.current = null;
                    connect();
                }
            }, 3000);
        };

    }, [conversationId]);

    const disconnect = React.useCallback(() => {
        if (eventSourceRef.current) {
            eventSourceRef.current.close();
            eventSourceRef.current = null;
        }
        setIsConnected(false);
        setIsConnecting(false);
    }, []);

    const clearEvents = React.useCallback(() => {
        setEvents([]);
    }, []);

    // Auto-connect when conversationId changes
    useEffect(() => {
        if (conversationId) {
            connect();
        } else {
            disconnect();
        }

        return () => {
            disconnect();
        };
    }, [conversationId, connect, disconnect]);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            disconnect();
        };
    }, [disconnect]);

    return {
        events,
        isConnected,
        isConnecting,
        connect,
        disconnect,
        clearEvents
    };
}