"""Configuration management using Pydantic Settings."""

from functools import lru_cache
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All settings are optional to support different tool combinations.
    Individual tools will validate their required settings.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Primo settings
    primo_api_key: Optional[str] = Field(default=None, description="Ex Libris Primo API key")
    primo_base_url: str = Field(
        default="https://api-na.hosted.exlibrisgroup.com/primo/v1/search",
        description="Primo API base URL"
    )
    primo_vid: Optional[str] = Field(default=None, description="Primo view ID (e.g., 01INST:VIEW)")
    primo_scope: Optional[str] = Field(default=None, description="Primo search scope")

    # OpenAlex settings
    openalex_email: Optional[str] = Field(
        default=None,
        description="Email for OpenAlex polite pool (recommended for better rate limits)"
    )

    # LibGuides settings
    libguides_site_id: Optional[str] = Field(default=None, description="LibGuides site ID")
    libguides_client_id: Optional[str] = Field(default=None, description="LibGuides OAuth client ID")
    libguides_client_secret: Optional[str] = Field(default=None, description="LibGuides OAuth client secret")
    libguides_base_url: Optional[str] = Field(
        default=None,
        description="LibGuides API base URL (default: https://lgapi-us.libapps.com/1.2)"
    )

    # Repository settings (bePress/Digital Commons)
    repository_base_url: Optional[str] = Field(
        default=None,
        description="Repository API base URL (e.g., https://content-out.bepress.com/v2/institution.edu)"
    )
    repository_api_key: Optional[str] = Field(default=None, description="Repository API security token")

    def validate_primo(self) -> None:
        """Validate that required Primo settings are present."""
        if not self.primo_api_key:
            raise ValueError("PRIMO_API_KEY is required for Primo tool")
        if not self.primo_vid:
            raise ValueError("PRIMO_VID is required for Primo tool")

    def validate_libguides(self) -> None:
        """Validate that required LibGuides settings are present."""
        if not self.libguides_site_id:
            raise ValueError("LIBGUIDES_SITE_ID is required for LibGuides tool")
        if not self.libguides_client_id:
            raise ValueError("LIBGUIDES_CLIENT_ID is required for LibGuides tool")
        if not self.libguides_client_secret:
            raise ValueError("LIBGUIDES_CLIENT_SECRET is required for LibGuides tool")

    def validate_repository(self) -> None:
        """Validate that required repository settings are present."""
        if not self.repository_base_url:
            raise ValueError("REPOSITORY_BASE_URL is required for repository tool")
        if not self.repository_api_key:
            raise ValueError("REPOSITORY_API_KEY is required for repository tool")


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Singleton Settings instance loaded from environment
    """
    return Settings()
