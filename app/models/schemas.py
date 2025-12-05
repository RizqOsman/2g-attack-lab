"""
Pydantic Schemas for API Request/Response Validation
Ensures type safety and automatic documentation in FastAPI
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Literal
from datetime import datetime
import re


class StatusResponse(BaseModel):
    """Response model for system status check"""
    pluto_sdr_active: bool = Field(description="PlutoSDR driver status")
    osmocom_active: bool = Field(description="Osmocom service status")
    details: dict = Field(default_factory=dict, description="Additional status details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "pluto_sdr_active": True,
                "osmocom_active": True,
                "details": {
                    "pluto_info": "PlutoSDR module loaded",
                    "osmocom_info": "osmo-nitb is running"
                },
                "timestamp": "2025-12-04T10:00:00"
            }
        }


class SubscriberResponse(BaseModel):
    """Response model for subscriber information from HLR"""
    imsi: str = Field(description="International Mobile Subscriber Identity (15 digits)")
    msisdn: Optional[str] = Field(None, description="Mobile phone number / extension")
    imei: Optional[str] = Field(None, description="International Mobile Equipment Identity")
    last_seen: Optional[datetime] = Field(None, description="Last activity timestamp")
    authorized: bool = Field(default=False, description="Authorization status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "imsi": "001010000000001",
                "msisdn": "12345",
                "imei": "353870080123456",
                "last_seen": "2025-12-04T09:30:00",
                "authorized": True
            }
        }


class SubscriberListResponse(BaseModel):
    """Response model for list of subscribers"""
    subscribers: List[SubscriberResponse]
    total_count: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class EncryptionConfigRequest(BaseModel):
    """Request model for encryption configuration"""
    mode: Literal["A5/0", "A5/1"] = Field(
        description="Encryption mode: A5/0 (null cipher/attack mode) or A5/1 (basic encryption)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "mode": "A5/0"
            }
        }


class EncryptionConfigResponse(BaseModel):
    """Response model for encryption configuration"""
    success: bool
    mode: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SMSSpoofRequest(BaseModel):
    """Request model for SMS spoofing attack"""
    imsi: str = Field(
        description="Target IMSI (15 digits)",
        min_length=15,
        max_length=15
    )
    sender_id: str = Field(
        description="Spoofed sender identifier (number or alphanumeric)",
        max_length=11
    )
    message: str = Field(
        description="SMS message content",
        max_length=160
    )
    
    @validator('imsi')
    def validate_imsi(cls, v):
        """Validate IMSI format (15 digits)"""
        if not re.match(r'^\d{15}$', v):
            raise ValueError('IMSI must be exactly 15 digits')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "imsi": "001010000000001",
                "sender_id": "SECURITY",
                "message": "Test message from C2 dashboard"
            }
        }


class SMSSpoofResponse(BaseModel):
    """Response model for SMS spoofing attack"""
    success: bool
    imsi: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class LiveFeedEvent(BaseModel):
    """Model for real-time log events streamed via WebSocket"""
    timestamp: datetime
    event_type: Literal["IMSI_ATTACH", "IMSI_DETACH", "AUTH_REQUEST", "SMS_DELIVERY", "LOCATION_UPDATE", "UNKNOWN"]
    imsi: Optional[str] = None
    details: dict = Field(default_factory=dict)
    raw_log: str = Field(description="Original log line")
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2025-12-04T10:15:00",
                "event_type": "IMSI_ATTACH",
                "imsi": "001010000000001",
                "details": {
                    "location_area": "1",
                    "cell_id": "1"
                },
                "raw_log": "Dec  4 10:15:00 lab osmo-nitb[1234]: Attach request from 001010000000001"
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response model"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
