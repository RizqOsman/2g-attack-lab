"""
Osmocom Service Layer
Business logic for interacting with Osmocom stack
Handles service status checks, subscriber queries, and encryption configuration
"""

from typing import Tuple, List, Dict
from app.services.vty_client import vty_pool
from app.models.database import db_manager
from app.utils.helpers import check_systemd_service, check_kernel_module, check_process_running
from app.config import settings


class OsmocomService:
    """
    Service layer for Osmocom operations
    Separates business logic from API routes
    """
    
    @staticmethod
    async def check_system_status() -> Dict:
        """
        Check if PlutoSDR and Osmocom services are running
        
        Returns:
            Dictionary with status information
        """
        # Check PlutoSDR driver
        pluto_active, pluto_details = await check_kernel_module("pluto")
        
        # Alternative: check for iio_usb driver (PlutoSDR uses Industrial I/O)
        if not pluto_active:
            pluto_active, pluto_details = await check_kernel_module("iio")
        
        # Check Osmocom service
        osmocom_active, osmocom_details = await check_systemd_service(
            settings.osmocom_service_name
        )
        
        # If systemd check fails, try process check
        if not osmocom_active:
            # Check for common Osmocom process names
            for process_name in ['osmo-nitb', 'osmo-msc', 'osmo-bsc']:
                osmocom_active, osmocom_details = await check_process_running(process_name)
                if osmocom_active:
                    break
        
        return {
            "pluto_sdr_active": pluto_active,
            "osmocom_active": osmocom_active,
            "details": {
                "pluto_info": pluto_details,
                "osmocom_info": osmocom_details
            }
        }
    
    @staticmethod
    async def get_all_subscribers() -> List[Dict]:
        """
        Retrieve all subscribers from HLR database
        
        Returns:
            List of subscriber dictionaries
        """
        try:
            subscribers = await db_manager.get_all_subscribers()
            return subscribers
        except Exception as e:
            raise Exception(f"Failed to retrieve subscribers: {str(e)}")
    
    @staticmethod
    async def get_subscriber_by_imsi(imsi: str) -> Dict:
        """
        Get specific subscriber by IMSI
        
        Args:
            imsi: IMSI to search for
            
        Returns:
            Subscriber dictionary
        """
        try:
            subscriber = await db_manager.get_subscriber_by_imsi(imsi)
            if not subscriber:
                raise Exception(f"Subscriber with IMSI {imsi} not found")
            return subscriber
        except Exception as e:
            raise Exception(f"Failed to retrieve subscriber: {str(e)}")
    
    @staticmethod
    async def set_encryption_mode(mode: str) -> Tuple[bool, str]:
        """
        Configure BTS encryption mode via VTY
        
        Args:
            mode: "A5/0" (null cipher) or "A5/1" (basic encryption)
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        # Map mode to VTY command
        if mode == "A5/0":
            encryption_cmd = "0"
        elif mode == "A5/1":
            encryption_cmd = "1"
        else:
            return False, f"Invalid encryption mode: {mode}"
        
        # Connect to BTS VTY (port 4241)
        client = await vty_pool.get_client('bts')
        
        try:
            # Connect to VTY
            success, msg = await client.connect()
            if not success:
                return False, msg
            
            # Enter configuration mode
            await client.execute_command("enable")
            await client.execute_command("configure terminal")
            
            # Navigate to BTS configuration
            # Note: This assumes BTS 0, adjust if needed
            await client.execute_command("network")
            await client.execute_command("bts 0")
            
            # Set encryption mode
            success, response = await client.execute_command(f"encryption a5 {encryption_cmd}")
            
            if success:
                # Exit configuration mode
                await client.execute_command("end")
                await client.execute_command("write")  # Save configuration
                
                return True, f"Encryption mode set to {mode}"
            else:
                return False, f"Failed to set encryption: {response}"
        
        except Exception as e:
            return False, f"Error setting encryption mode: {str(e)}"
        finally:
            await client.disconnect()
    
    @staticmethod
    async def execute_vty_command(service: str, command: str) -> Tuple[bool, str]:
        """
        Execute arbitrary VTY command (for advanced use)
        
        Args:
            service: 'msc' or 'bts'
            command: VTY command to execute
            
        Returns:
            Tuple of (success: bool, response: str)
        """
        client = await vty_pool.get_client(service)
        
        try:
            success, msg = await client.connect()
            if not success:
                return False, msg
            
            success, response = await client.execute_command(command)
            return success, response
        
        except Exception as e:
            return False, f"Failed to execute command: {str(e)}"
        finally:
            await client.disconnect()


# Global service instance
osmocom_service = OsmocomService()
