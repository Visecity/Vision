"""
Configuration management for Vision pixel art generation system.

This module provides centralized configuration using Pydantic Settings,
loading values from environment variables with sensible defaults.
"""

from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class RedisSettings(BaseSettings):
    """Redis connection configuration."""

    host: str = Field(default="localhost", description="Redis server host")
    port: int = Field(default=6379, ge=1, le=65535, description="Redis server port")
    password: str = Field(default="", description="Redis password (if required)")
    db: int = Field(default=0, ge=0, description="Redis database number")

    model_config = SettingsConfigDict(
        env_prefix="REDIS_",
        case_sensitive=False,
    )

    @property
    def url(self) -> str:
        """Construct Redis URL for connection."""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


class ModelSettings(BaseSettings):
    """LLM model configuration for different agents."""

    orchestrator_model: str = Field(
        default="claude-3-5-sonnet-20241022",
        description="Model for orchestrator agent",
    )
    design_agent_model: str = Field(
        default="claude-3-5-sonnet-20241022",
        description="Model for design agent",
    )
    palette_agent_model: str = Field(
        default="claude-3-5-sonnet-20241022",
        description="Model for palette agent",
    )
    detail_agent_model: str = Field(
        default="claude-3-5-sonnet-20241022",
        description="Model for detail agent",
    )
    animation_agent_model: str = Field(
        default="claude-3-5-sonnet-20241022",
        description="Model for animation agent",
    )

    model_config = SettingsConfigDict(
        case_sensitive=False,
    )

    @field_validator("*", mode="before")
    @classmethod
    def validate_model_name(cls, v: str) -> str:
        """Validate Claude model names."""
        if not v.startswith("claude-"):
            raise ValueError(f"Invalid Claude model name: {v}")
        return v


class PerformanceSettings(BaseSettings):
    """Performance and caching configuration."""

    enable_caching: bool = Field(
        default=True,
        description="Enable response caching",
    )
    cache_ttl: int = Field(
        default=3600,
        ge=0,
        description="Cache TTL in seconds",
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum retry attempts for API calls",
    )
    timeout: int = Field(
        default=300,
        ge=1,
        description="API call timeout in seconds",
    )
    max_concurrent_agents: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of concurrent agents",
    )

    model_config = SettingsConfigDict(
        case_sensitive=False,
    )


class OutputSettings(BaseSettings):
    """Output directory configuration."""

    output_dir: Path = Field(
        default=Path("./output"),
        description="Main output directory for generated assets",
    )
    asset_dir: Path = Field(
        default=Path("./assets"),
        description="Directory for asset templates and examples",
    )
    temp_dir: Path = Field(
        default=Path("./temp"),
        description="Temporary directory for intermediate files",
    )

    model_config = SettingsConfigDict(
        case_sensitive=False,
    )

    @field_validator("*", mode="before")
    @classmethod
    def validate_path(cls, v: str | Path) -> Path:
        """Convert string to Path and ensure it exists."""
        path = Path(v) if isinstance(v, str) else v
        return path

    def ensure_directories(self) -> None:
        """Create all output directories if they don't exist."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.asset_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    """
    Main application settings.

    Loads configuration from environment variables with fallback to defaults.
    Use Settings() to create an instance, or get_settings() for a cached singleton.
    """

    # Anthropic API
    anthropic_api_key: str = Field(
        description="Anthropic API key for Claude access",
    )

    # Application settings
    debug: bool = Field(
        default=False,
        description="Enable debug mode",
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level",
    )

    # Nested settings
    redis: RedisSettings = Field(
        default_factory=RedisSettings,
        description="Redis configuration",
    )
    models: ModelSettings = Field(
        default_factory=ModelSettings,
        description="LLM model configuration",
    )
    performance: PerformanceSettings = Field(
        default_factory=PerformanceSettings,
        description="Performance settings",
    )
    output: OutputSettings = Field(
        default_factory=OutputSettings,
        description="Output directory settings",
    )

    # Optional integrations
    github_token: str | None = Field(
        default=None,
        description="GitHub API token (optional)",
    )
    github_repo: str | None = Field(
        default=None,
        description="GitHub repository (optional)",
    )
    enable_telemetry: bool = Field(
        default=False,
        description="Enable telemetry/monitoring",
    )
    sentry_dsn: str | None = Field(
        default=None,
        description="Sentry DSN for error tracking (optional)",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def model_post_init(self, __context: object) -> None:
        """Post-initialization hook to ensure directories exist."""
        self.output.ensure_directories()


# Cached settings instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """
    Get cached settings instance.

    Returns:
        Settings: Singleton settings instance

    Example:
        >>> settings = get_settings()
        >>> print(settings.anthropic_api_key)
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    """
    Reset cached settings instance.

    Useful for testing or when environment variables change.
    """
    global _settings
    _settings = None


# TODO: Phase 3 - Add validation for agent-specific settings
# TODO: Phase 3 - Add settings for LangGraph workflow configuration
# TODO: Phase 4 - Add monitoring/telemetry configuration
# TODO: Phase 4 - Add deployment-specific settings (Docker, cloud)