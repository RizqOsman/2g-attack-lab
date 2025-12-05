"""
Helper Utilities for GSM C2 Dashboard
Common utility functions for validation, formatting, and system checks
"""

import re
import asyncio
from typing import Optional, Tuple
from datetime import datetime


def validate_imsi(imsi: str) -> bool:
    """
    Validate IMSI format (15 digits)
    
    Args:
        imsi: IMSI string to validate
        
    Returns:
        True if valid, False otherwise
    """
    return bool(re.match(r'^\d{15}$', imsi))


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """
    Format datetime to ISO 8601 string
    
    Args:
        dt: Datetime object (defaults to current time)
        
    Returns:
        Formatted timestamp string
    """
    if dt is None:
        dt = datetime.utcnow()
    return dt.isoformat()


async def check_process_running(process_name: str) -> Tuple[bool, str]:
    """
    Check if a process is running using ps command
    
    Args:
        process_name: Name of the process to check
        
    Returns:
        Tuple of (is_running: bool, details: str)
    """
    try:
        process = await asyncio.create_subprocess_exec(
            'ps', 'aux',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            output = stdout.decode()
            lines = [line for line in output.split('\n') if process_name in line and 'grep' not in line]
            if lines:
                return True, f"{process_name} is running (PID found)"
            else:
                return False, f"{process_name} is not running"
        else:
            return False, f"Failed to check process: {stderr.decode()}"
    except Exception as e:
        return False, f"Error checking process: {str(e)}"


async def check_systemd_service(service_name: str) -> Tuple[bool, str]:
    """
    Check if a systemd service is active
    
    Args:
        service_name: Name of the systemd service
        
    Returns:
        Tuple of (is_active: bool, details: str)
    """
    try:
        process = await asyncio.create_subprocess_exec(
            'systemctl', 'is-active', service_name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        status = stdout.decode().strip()
        if status == 'active':
            return True, f"{service_name} is active"
        else:
            return False, f"{service_name} status: {status}"
    except FileNotFoundError:
        # systemctl not available, fall back to process check
        return await check_process_running(service_name)
    except Exception as e:
        return False, f"Error checking service: {str(e)}"


async def check_kernel_module(module_name: str) -> Tuple[bool, str]:
    """
    Check if a kernel module is loaded using lsmod
    
    Args:
        module_name: Name of the kernel module
        
    Returns:
        Tuple of (is_loaded: bool, details: str)
    """
    try:
        process = await asyncio.create_subprocess_exec(
            'lsmod',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            output = stdout.decode().lower()
            if module_name.lower() in output:
                return True, f"{module_name} module is loaded"
            else:
                return False, f"{module_name} module is not loaded"
        else:
            return False, f"Failed to check module: {stderr.decode()}"
    except Exception as e:
        return False, f"Error checking module: {str(e)}"


def parse_log_event(log_line: str) -> Optional[dict]:
    """
    Parse Osmocom log line to extract relevant event information
    
    Args:
        log_line: Raw log line from Osmocom
        
    Returns:
        Parsed event dictionary or None if not relevant
    """
    # Common patterns in Osmocom logs
    patterns = {
        'IMSI_ATTACH': r'(attach|location.*update).*imsi[:\s]+(\d{15})',
        'IMSI_DETACH': r'detach.*imsi[:\s]+(\d{15})',
        'AUTH_REQUEST': r'auth.*request.*imsi[:\s]+(\d{15})',
        'SMS_DELIVERY': r'sms.*deliver.*imsi[:\s]+(\d{15})',
        'LOCATION_UPDATE': r'location.*update.*imsi[:\s]+(\d{15})'
    }
    
    log_lower = log_line.lower()
    
    for event_type, pattern in patterns.items():
        match = re.search(pattern, log_lower)
        if match:
            # Extract IMSI (typically last group in pattern)
            imsi = match.groups()[-1] if len(match.groups()) > 0 else None
            
            return {
                'event_type': event_type,
                'imsi': imsi,
                'raw_log': log_line.strip(),
                'timestamp': datetime.utcnow()
            }
    
    # Check for other relevant keywords
    if any(keyword in log_lower for keyword in ['imsi', 'subscriber', 'mobile']):
        # Generic event
        imsi_match = re.search(r'\d{15}', log_line)
        return {
            'event_type': 'UNKNOWN',
            'imsi': imsi_match.group(0) if imsi_match else None,
            'raw_log': log_line.strip(),
            'timestamp': datetime.utcnow()
        }
    
    return None


def sanitize_sms_message(message: str) -> str:
    """
    Sanitize SMS message content
    
    Args:
        message: Raw SMS message
        
    Returns:
        Sanitized message
    """
    # Remove potentially dangerous characters
    # Keep alphanumeric, spaces, and basic punctuation
    sanitized = re.sub(r'[^\w\s\.,!?\-]', '', message)
    # Limit length to GSM SMS standard
    return sanitized[:160]


def format_vty_command(command: str) -> str:
    """
    Format VTY command to ensure proper termination
    
    Args:
        command: Raw VTY command
        
    Returns:
        Formatted command with line ending
    """
    command = command.strip()
    if not command.endswith('\n'):
        command += '\n'
    return command
