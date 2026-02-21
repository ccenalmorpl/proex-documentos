"""Application configuration module.

All settings are loaded from environment variables or .env file.
"""

from functools import lru_cache
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with validation and environment variable support."""

    # HubSpot Configuration
    proex_access_token: str = Field(
        ...,
        description="HubSpot private app access token (required)",
        min_length=10
    )

    # CORS Configuration
    cors_origins: str = Field(
        default="http://localhost:3000,https://app.hubspot.com,https://app-eu1.hubspot.com",
        description="Comma-separated list of allowed CORS origins"
    )

    # App Configuration
    debug: bool = Field(default=False)
    app_name: str = Field(default="Documentos Proex Microservice")
    version: str = Field(default="1.0.0")

    # Server Configuration
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000, ge=1, le=65535)

    # AWS Configuration
    aws_region: Optional[str] = Field(default=None)
    lambda_function_name: Optional[str] = Field(default=None)
    aws_account_id: Optional[str] = Field(default=None)
    ecr_repo_name: Optional[str] = Field(default=None)
    function_name: Optional[str] = Field(default=None)

    # Logging Configuration
    log_level: str = Field(default="INFO")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Performance
    request_timeout: int = Field(default=30, ge=1, le=300)

    # Documentos - Sanitario
    sanitario_empresa_direccion: str = Field(
        default="",
        description="Texto fijo 'empresa + dirección' para certificado sanitario"
    )

    # HubSpot File Manager
    files_folder: str = Field(
        default="/documentos-proex",
        description="Carpeta en HubSpot File Manager donde se suben los PDFs"
    )

    @field_validator('proex_access_token')
    @classmethod
    def validate_hubspot_token(cls, v: str) -> str:
        if not v:
            raise ValueError("HubSpot access token is required")
        if not (v.startswith('pat-') or v.startswith('HUBSPOT_')):
            raise ValueError("Invalid HubSpot token format")
        return v

    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level. Must be one of: {valid_levels}")
        return v.upper()

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return not self.debug

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        validate_assignment = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
