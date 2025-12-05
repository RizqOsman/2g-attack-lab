"""
WebSocket Endpoint for Real-Time Log Streaming
Provides live feed of IMSI attach/detach and other Osmocom events
"""

from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import asyncio
import uuid

from app.services.log_monitor import monitor_manager, LogMonitor
from app.models.schemas import LiveFeedEvent


async def websocket_live_feed(websocket: WebSocket):
    """
    **WebSocket Live Feed Endpoint**
    
    Path: /ws/live-feed
    
    Streams real-time events from Osmocom log files:
    - IMSI Attach/Detach
    - Location Updates
    - Authentication Requests
    - SMS Delivery
    
    Messages are sent as JSON with the following structure:
    ```json
    {
        "timestamp": "2025-12-04T10:15:00",
        "event_type": "IMSI_ATTACH",
        "imsi": "001010000000001",
        "details": {},
        "raw_log": "Original log line"
    }
    ```
    
    Usage example (JavaScript):
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/ws/live-feed');
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Event:', data);
    };
    ```
    
    Args:
        websocket: WebSocket connection object
    """
    # Generate unique connection ID
    connection_id = str(uuid.uuid4())
    
    # Accept connection
    await websocket.accept()
    
    # Add to active connections
    await monitor_manager.add_connection(connection_id, websocket)
    
    # Get or create log monitor
    monitor = monitor_manager.get_monitor()
    
    try:
        # Send welcome message
        welcome_event = LiveFeedEvent(
            timestamp=datetime.utcnow(),
            event_type="UNKNOWN",
            imsi=None,
            details={"message": "Connected to live feed"},
            raw_log="Connection established"
        )
        await websocket.send_json(welcome_event.model_dump(mode='json'))
        
        # Start monitoring if not already started
        if not monitor.monitoring:
            await monitor.start_monitoring(
                callback=monitor_manager.broadcast_event
            )
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for client messages (ping/pong, etc.)
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )
                
                # Handle client commands if needed
                if data == "ping":
                    await websocket.send_text("pong")
            
            except asyncio.TimeoutError:
                # Send heartbeat to keep connection alive
                heartbeat = LiveFeedEvent(
                    timestamp=datetime.utcnow(),
                    event_type="UNKNOWN",
                    imsi=None,
                    details={"heartbeat": True},
                    raw_log="Heartbeat"
                )
                await websocket.send_json(heartbeat.model_dump(mode='json'))
    
    except WebSocketDisconnect:
        # Client disconnected
        await monitor_manager.remove_connection(connection_id)
    
    except Exception as e:
        # Error occurred
        try:
            error_event = LiveFeedEvent(
                timestamp=datetime.utcnow(),
                event_type="UNKNOWN",
                imsi=None,
                details={"error": str(e)},
                raw_log=f"Error: {str(e)}"
            )
            await websocket.send_json(error_event.model_dump(mode='json'))
        except Exception:
            pass
        
        await monitor_manager.remove_connection(connection_id)
    
    finally:
        # Cleanup
        try:
            await websocket.close()
        except Exception:
            pass
