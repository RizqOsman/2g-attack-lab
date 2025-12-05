"""
Async VTY Client for Osmocom Communication
Provides telnet-based connection to Osmocom VTY interface
Ports: 4242 (MSC/NITB), 4241 (BTS)
"""

import asyncio
import telnetlib3
from typing import Optional, Tuple
from app.config import settings


class VTYClient:
    """
    Async Telnet client for Osmocom VTY (Virtual Terminal) interface
    Handles connection, command execution, and response parsing
    """
    
    def __init__(self, host: str = None, port: int = None, timeout: int = None):
        """
        Initialize VTY client
        
        Args:
            host: VTY host address (defaults to settings.vty_host)
            port: VTY port number (defaults to MSC port 4242)
            timeout: Connection timeout in seconds (defaults to settings)
        """
        self.host = host or settings.vty_host
        self.port = port or settings.vty_msc_port
        self.timeout = timeout or settings.vty_timeout
        
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.connected = False
    
    async def connect(self) -> Tuple[bool, str]:
        """
        Establish connection to VTY interface
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Use telnetlib3 for async telnet connection
            self.reader, self.writer = await asyncio.wait_for(
                telnetlib3.open_connection(self.host, self.port),
                timeout=self.timeout
            )
            
            # Wait for initial prompt/banner
            await asyncio.wait_for(
                self._read_until_prompt(),
                timeout=5
            )
            
            self.connected = True
            return True, f"Connected to VTY at {self.host}:{self.port}"
        
        except asyncio.TimeoutError:
            return False, f"Connection timeout to {self.host}:{self.port}"
        except ConnectionRefusedError:
            return False, f"Connection refused to {self.host}:{self.port}. Is Osmocom running?"
        except Exception as e:
            return False, f"Failed to connect to VTY: {str(e)}"
    
    async def _read_until_prompt(self, timeout: int = 5) -> str:
        """
        Read from VTY until prompt is detected
        
        Args:
            timeout: Read timeout in seconds
            
        Returns:
            Accumulated output
        """
        output = ""
        try:
            while True:
                chunk = await asyncio.wait_for(
                    self.reader.read(1024),
                    timeout=timeout
                )
                if not chunk:
                    break
                
                output += chunk
                
                # Check for common VTY prompts
                if any(prompt in output for prompt in ['>', '#', 'OsmoMSC>', 'OsmoBTS>']):
                    break
                
                # Avoid infinite loop
                if len(output) > 10000:
                    break
        except asyncio.TimeoutError:
            # Timeout is acceptable - we got what we needed
            pass
        
        return output
    
    async def execute_command(self, command: str, wait_for_response: bool = True) -> Tuple[bool, str]:
        """
        Execute a VTY command and return the response
        
        Args:
            command: VTY command to execute
            wait_for_response: Whether to wait for and return response
            
        Returns:
            Tuple of (success: bool, response: str)
        """
        if not self.connected:
            success, msg = await self.connect()
            if not success:
                return False, msg
        
        try:
            # Ensure command ends with newline
            if not command.endswith('\n'):
                command += '\n'
            
            # Send command
            self.writer.write(command)
            await self.writer.drain()
            
            if not wait_for_response:
                return True, "Command sent"
            
            # Read response
            response = await asyncio.wait_for(
                self._read_until_prompt(),
                timeout=self.timeout
            )
            
            return True, response
        
        except asyncio.TimeoutError:
            return False, "Command execution timeout"
        except Exception as e:
            self.connected = False
            return False, f"Failed to execute command: {str(e)}"
    
    async def disconnect(self):
        """Close VTY connection"""
        if self.writer:
            try:
                self.writer.write('exit\n')
                await self.writer.drain()
                self.writer.close()
                await self.writer.wait_closed()
            except Exception:
                pass
        
        self.connected = False
        self.reader = None
        self.writer = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()


class VTYConnectionPool:
    """
    Connection pool for VTY clients
    Manages multiple connections for different Osmocom services
    """
    
    def __init__(self):
        """Initialize connection pool"""
        self.connections = {}
    
    async def get_client(self, service: str) -> VTYClient:
        """
        Get VTY client for a specific service
        
        Args:
            service: Service name ('msc' or 'bts')
            
        Returns:
            VTYClient instance
        """
        if service.lower() == 'msc':
            port = settings.vty_msc_port  # 4242
        elif service.lower() == 'bts':
            port = settings.vty_bts_port  # 4241
        else:
            raise ValueError(f"Unknown service: {service}")
        
        # Create new client each time to avoid connection state issues
        return VTYClient(port=port)
    
    async def close_all(self):
        """Close all connections in pool"""
        for client in self.connections.values():
            await client.disconnect()
        self.connections.clear()


# Global VTY connection pool
vty_pool = VTYConnectionPool()
