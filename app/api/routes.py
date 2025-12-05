"""
FastAPI Routes for GSM C2 Dashboard
RESTful API endpoints for Osmocom control and monitoring
"""

from fastapi import APIRouter, HTTPException, status
from datetime import datetime
from typing import List

from app.models.schemas import (
    StatusResponse,
    SubscriberResponse,
    SubscriberListResponse,
    EncryptionConfigRequest,
    EncryptionConfigResponse,
    SMSSpoofRequest,
    SMSSpoofResponse,
    ErrorResponse
)
from app.services.osmocom_service import osmocom_service
from app.services.sms_service import sms_service

# Create API router
router = APIRouter()


@router.get(
    "/status",
    response_model=StatusResponse,
    summary="System Status Check",
    description="Check if PlutoSDR driver and Osmocom services are active"
)
async def get_status():
    """
    **System Status Endpoint**
    
    Checks:
    - PlutoSDR kernel module (lsmod for 'pluto' or 'iio')
    - Osmocom service status (systemctl or ps aux)
    
    Returns detailed status information for both components.
    """
    try:
        status_data = await osmocom_service.check_system_status()
        
        return StatusResponse(
            pluto_sdr_active=status_data["pluto_sdr_active"],
            osmocom_active=status_data["osmocom_active"],
            details=status_data["details"],
            timestamp=datetime.utcnow()
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check system status: {str(e)}"
        )


@router.get(
    "/subscribers",
    response_model=SubscriberListResponse,
    summary="List All Subscribers",
    description="Query HLR database for all captured subscribers (IMSI, IMEI, last seen)"
)
async def get_subscribers():
    """
    **Subscribers Endpoint**
    
    Queries the Osmocom HLR SQLite database to retrieve all subscriber records.
    
    Returns:
    - List of subscribers with IMSI, MSISDN, IMEI, and last seen timestamp
    - Total count of subscribers
    
    The database path is configured in .env (HLR_DATABASE_PATH)
    """
    try:
        subscribers_data = await osmocom_service.get_all_subscribers()
        
        # Convert to Pydantic models
        subscribers = [
            SubscriberResponse(
                imsi=sub["imsi"],
                msisdn=sub.get("msisdn"),
                imei=sub.get("imei"),
                last_seen=sub.get("last_seen"),
                authorized=sub.get("authorized", False)
            )
            for sub in subscribers_data
        ]
        
        return SubscriberListResponse(
            subscribers=subscribers,
            total_count=len(subscribers),
            timestamp=datetime.utcnow()
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve subscribers: {str(e)}"
        )


@router.post(
    "/config/encryption",
    response_model=EncryptionConfigResponse,
    summary="Configure BTS Encryption",
    description="Toggle BTS encryption between A5/0 (null cipher/attack mode) and A5/1"
)
async def configure_encryption(config: EncryptionConfigRequest):
    """
    **Encryption Configuration Endpoint**
    
    Connects to Osmocom BTS VTY interface (port 4241) to configure encryption mode.
    
    Modes:
    - **A5/0**: Null cipher (no encryption) - used for security testing
    - **A5/1**: Basic GSM encryption
    
    This endpoint executes VTY commands:
    ```
    enable
    configure terminal
    network
    bts 0
    encryption a5 <0|1>
    end
    write
    ```
    
    ⚠️ **Security Notice**: Only use A5/0 in authorized laboratory environments
    """
    try:
        success, message = await osmocom_service.set_encryption_mode(config.mode)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=message
            )
        
        return EncryptionConfigResponse(
            success=True,
            mode=config.mode,
            message=message,
            timestamp=datetime.utcnow()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to configure encryption: {str(e)}"
        )


@router.post(
    "/attack/sms-spoof",
    response_model=SMSSpoofResponse,
    summary="Inject Spoofed SMS",
    description="Send a spoofed SMS to a target IMSI via Osmocom SMS queue"
)
async def spoof_sms(request: SMSSpoofRequest):
    """
    **SMS Spoofing Endpoint**
    
    Connects to Osmocom MSC VTY interface (port 4242) to inject SMS into the queue.
    
    Parameters:
    - **imsi**: Target IMSI (15 digits)
    - **sender_id**: Spoofed sender (number or alphanumeric, max 11 chars)
    - **message**: SMS content (max 160 characters)
    
    VTY Command format:
    ```
    enable
    subscriber imsi <IMSI> sms sender <sender_id> send <message>
    ```
    
    ⚠️ **Legal Notice**: SMS spoofing is only legal in authorized security research
    environments. Ensure compliance with all applicable laws and regulations.
    """
    try:
        success, message = await sms_service.send_spoofed_sms(
            imsi=request.imsi,
            sender_id=request.sender_id,
            message=request.message
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=message
            )
        
        return SMSSpoofResponse(
            success=True,
            imsi=request.imsi,
            message=message,
            timestamp=datetime.utcnow()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send spoofed SMS: {str(e)}"
        )


@router.get(
    "/health",
    summary="Health Check",
    description="Simple health check endpoint"
)
async def health_check():
    """
    **Health Check Endpoint**
    
    Returns basic application health status.
    """
    return {
        "status": "healthy",
        "service": "GSM C2 Dashboard",
        "timestamp": datetime.utcnow().isoformat()
    }
