"""
Log Monitor Service
Real-time log tailing and event parsing for WebSocket streaming
Monitors Osmocom log files for IMSI attach/detach and other events
"""

import asyncio
import aiofiles
from typing import Optional, Callable, AsyncIterator
from datetime import datetime
from app.config import settings
from app.utils.helpers import parse_log_event
from app.models.schemas import LiveFeedEvent


class LogMonitor:
    """
    Async log file monitor for real-time event streaming
    Tails Osmocom log files and parses relevant events
    """
    
    def __init__(self, log_path: str = None):
        """
        Initialize log monitor
        
        Args:
            log_path: Path to log file (defaults to settings)
        """
        self.log_path = log_path or settings.osmocom_log_path
        self.monitoring = False
        self.monitor_task: Optional[asyncio.Task] = None
    
    async def tail_log(self, callback: Optional[Callable] = None) -> AsyncIterator[LiveFeedEvent]:
        """
        Tail log file and yield parsed events
        
        Args:
            callback: Optional callback function for each event
            
        Yields:
            LiveFeedEvent objects
        """
        try:
            async with aiofiles.open(self.log_path, mode='r') as log_file:
                # Seek to end of file initially
                await log_file.seek(0, 2)  # 2 = SEEK_END
                
                self.monitoring = True
                
                while self.monitoring:
                    # Read new lines
                    line = await log_file.readline()
                    
                    if line:
                        # Parse log line
                        event_data = parse_log_event(line)
                        
                        if event_data:
                            # Create LiveFeedEvent
                            event = LiveFeedEvent(
                                timestamp=event_data.get('timestamp', datetime.utcnow()),
                                event_type=event_data.get('event_type', 'UNKNOWN'),
                                imsi=event_data.get('imsi'),
                                details={},
                                raw_log=event_data.get('raw_log', line.strip())
                            )
                            
                            # Call callback if provided
                            if callback:
                                await callback(event)
                            
                            yield event
                    else:
                        # No new data, wait briefly
                        await asyncio.sleep(0.1)
        
        except FileNotFoundError:
            # Log file doesn't exist yet
            # Yield error event
            error_event = LiveFeedEvent(
                timestamp=datetime.utcnow(),
                event_type="UNKNOWN",
                imsi=None,
                details={"error": f"Log file not found: {self.log_path}"},
                raw_log=f"ERROR: Log file {self.log_path} not found"
            )
            yield error_event
            
            # Wait and retry
            while self.monitoring:
                await asyncio.sleep(5)
                try:
                    # Try again
                    async for event in self.tail_log(callback):
                        yield event
                    break
                except FileNotFoundError:
                    continue
        
        except Exception as e:
            # Yield error event
            error_event = LiveFeedEvent(
                timestamp=datetime.utcnow(),
                event_type="UNKNOWN",
                imsi=None,
                details={"error": str(e)},
                raw_log=f"ERROR: {str(e)}"
            )
            yield error_event
    
    async def start_monitoring(self, callback: Callable):
        """
        Start monitoring in background task
        
        Args:
            callback: Async callback function for events
        """
        if self.monitoring:
            return
        
        async def monitor_loop():
            async for event in self.tail_log(callback):
                # Events are handled by callback
                pass
        
        self.monitor_task = asyncio.create_task(monitor_loop())
    
    async def stop_monitoring(self):
        """Stop monitoring task"""
        self.monitoring = False
        
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
            self.monitor_task = None


class LogMonitorManager:
    """
    Manager for multiple log monitor instances
    Handles WebSocket clients and event broadcasting
    """
    
    def __init__(self):
        """Initialize monitor manager"""
        self.monitors = {}
        self.active_connections = set()
    
    async def add_connection(self, connection_id: str, websocket):
        """
        Add WebSocket connection
        
        Args:
            connection_id: Unique connection identifier
            websocket: WebSocket connection object
        """
        self.active_connections.add((connection_id, websocket))
    
    async def remove_connection(self, connection_id: str):
        """
        Remove WebSocket connection
        
        Args:
            connection_id: Connection identifier to remove
        """
        self.active_connections = {
            (cid, ws) for cid, ws in self.active_connections if cid != connection_id
        }
    
    async def broadcast_event(self, event: LiveFeedEvent):
        """
        Broadcast event to all connected WebSocket clients
        
        Args:
            event: LiveFeedEvent to broadcast
        """
        # Remove disconnected clients
        disconnected = set()
        
        for connection_id, websocket in self.active_connections:
            try:
                # Convert event to JSON and send
                await websocket.send_json(event.model_dump(mode='json'))
            except Exception:
                # Mark for removal
                disconnected.add(connection_id)
        
        # Clean up disconnected clients
        for connection_id in disconnected:
            await self.remove_connection(connection_id)
    
    def get_monitor(self, log_path: str = None) -> LogMonitor:
        """
        Get or create log monitor instance
        
        Args:
            log_path: Path to log file
            
        Returns:
            LogMonitor instance
        """
        path = log_path or settings.osmocom_log_path
        
        if path not in self.monitors:
            self.monitors[path] = LogMonitor(path)
        
        return self.monitors[path]
    
    async def cleanup(self):
        """Stop all monitors and close connections"""
        for monitor in self.monitors.values():
            await monitor.stop_monitoring()
        
        self.monitors.clear()
        self.active_connections.clear()


# Global monitor manager instance
monitor_manager = LogMonitorManager()
