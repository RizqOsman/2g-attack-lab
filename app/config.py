"""
Configuration Management for GSM C2 Dashboard
Centralized settings using Pydantic Settings for type safety and validation
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables or .env file
    """
    
    # VTY Connection Settings
    vty_host: str = Field(default="localhost", description="Osmocom VTY host address")
    vty_msc_port: int = Field(default=4242, description="Osmo-MSC/NITB VTY port")
    vty_bts_port: int = Field(default=4241, description="Osmo-BTS VTY port")
    vty_timeout: int = Field(default=10, description="VTY connection timeout in seconds")
    
    # Database Settings
    hlr_database_path: str = Field(
        default="/var/lib/osmocom/hlr.sqlite3",
        description="Path to Osmocom HLR SQLite database"
    )
    
    # Log Monitoring Settings
    osmocom_log_path: str = Field(
        default="/var/log/osmocom/osmo-nitb.log",
        description="Path to Osmocom log file for monitoring"
    )
    
    # Application Settings
    app_host: str = Field(default="0.0.0.0", description="Application host address")
    app_port: int = Field(default=8000, description="Application port")
    debug_mode: bool = Field(default=False, description="Enable debug mode")
    
    # Service Check Settings
    pluto_sdr_check_cmd: str = Field(
        default="lsmod | grep -i pluto",
        description="Command to check PlutoSDR driver status"
    )
    osmocom_service_name: str = Field(
        default="osmo-nitb",
        description="Osmocom service name for status checks"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
