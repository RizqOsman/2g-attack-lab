"""
SMS Service Layer
Handles SMS spoofing/injection via Osmocom VTY interface
"""

from typing import Tuple
from app.services.vty_client import vty_pool
from app.utils.helpers import validate_imsi, sanitize_sms_message


class SMSService:
    """
    SMS injection service for GSM laboratory
    Interfaces with Osmocom SMS queue via VTY commands
    """
    
    @staticmethod
    async def send_spoofed_sms(imsi: str, sender_id: str, message: str) -> Tuple[bool, str]:
        """
        Inject a spoofed SMS into Osmocom SMS queue
        
        Args:
            imsi: Target IMSI (15 digits)
            sender_id: Spoofed sender identifier
            message: SMS message content
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        # Validate IMSI
        if not validate_imsi(imsi):
            return False, "Invalid IMSI format (must be 15 digits)"
        
        # Sanitize message
        safe_message = sanitize_sms_message(message)
        
        # Connect to MSC VTY (port 4242)
        client = await vty_pool.get_client('msc')
        
        try:
            # Connect to VTY
            success, msg = await client.connect()
            if not success:
                return False, msg
            
            # Enter enable mode
            await client.execute_command("enable")
            
            # Construct SMS injection command
            # Format: subscriber imsi <IMSI> sms sender <sender_id> send <message>
            sms_command = f"subscriber imsi {imsi} sms sender {sender_id} send {safe_message}"
            
            # Execute SMS command
            success, response = await client.execute_command(sms_command)
            
            if success:
                # Check response for success indicators
                if "error" in response.lower() or "fail" in response.lower():
                    return False, f"SMS injection failed: {response}"
                
                return True, f"SMS injected to IMSI {imsi}"
            else:
                return False, f"Failed to execute SMS command: {response}"
        
        except Exception as e:
            return False, f"Error sending SMS: {str(e)}"
        finally:
            await client.disconnect()
    
    @staticmethod
    async def send_sms_to_extension(extension: str, sender_id: str, message: str) -> Tuple[bool, str]:
        """
        Send SMS to a subscriber by extension number (alternative method)
        
        Args:
            extension: Extension/MSISDN number
            sender_id: Sender identifier
            message: SMS message content
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        safe_message = sanitize_sms_message(message)
        
        client = await vty_pool.get_client('msc')
        
        try:
            success, msg = await client.connect()
            if not success:
                return False, msg
            
            await client.execute_command("enable")
            
            # Alternative command format using extension
            sms_command = f"subscriber extension {extension} sms sender {sender_id} send {safe_message}"
            
            success, response = await client.execute_command(sms_command)
            
            if success and "error" not in response.lower():
                return True, f"SMS sent to extension {extension}"
            else:
                return False, f"SMS send failed: {response}"
        
        except Exception as e:
            return False, f"Error sending SMS: {str(e)}"
        finally:
            await client.disconnect()


# Global SMS service instance
sms_service = SMSService()
