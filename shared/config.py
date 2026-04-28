"""
Configuration management using Pydantic Settings
Based on: https://docs.pydantic.dev/latest/usage/pydantic_settings/
"""
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import Optional


class Settings(BaseSettings):
    """Application settings with validation"""

    # Gemini AI Configuration
    GEMINI_API_KEY: str = Field(..., description="Gemini API key")
    GEMINI_MODEL: str = Field(default="gemini-2.0-flash-exp", description="Gemini model name")

    # GitHub Configuration
    GITHUB_TOKEN: Optional[str] = Field(default=None, description="GitHub API token")
    GITHUB_REPO_URL: Optional[str] = Field(default=None, description="GitHub repository URL")

    # Database Configuration
    POSTGRES_HOST: str = Field(default="postgres", description="PostgreSQL host")
    POSTGRES_PORT: int = Field(default=5432, description="PostgreSQL port")
    POSTGRES_DB: str = Field(default="qa_multiagent", description="PostgreSQL database name")
    POSTGRES_USER: str = Field(default="qauser", description="PostgreSQL user")
    POSTGRES_PASSWORD: str = Field(..., description="PostgreSQL password")

    # Redis Configuration
    REDIS_HOST: str = Field(default="redis", description="Redis host")
    REDIS_PORT: int = Field(default=6379, description="Redis port")
    REDIS_PASSWORD: str = Field(..., description="Redis password")

    # RabbitMQ Configuration
    RABBITMQ_HOST: str = Field(default="rabbitmq", description="RabbitMQ host")
    RABBITMQ_PORT: int = Field(default=5672, description="RabbitMQ port")
    RABBITMQ_USER: str = Field(default="qarabbit", description="RabbitMQ user")
    RABBITMQ_PASSWORD: str = Field(..., description="RabbitMQ password")

    # Quality Gate Thresholds
    MIN_CODE_COVERAGE: float = Field(default=80.0, ge=0, le=100, description="Minimum code coverage percentage")
    MAX_FAILED_TESTS: int = Field(default=0, ge=0, description="Maximum allowed failed tests")
    MAX_CRITICAL_VULNERABILITIES: int = Field(default=0, ge=0, description="Maximum critical vulnerabilities")
    MIN_PASS_RATE: float = Field(default=95.0, ge=0, le=100, description="Minimum test pass rate")

    # System Configuration
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(default="json", description="Log format (json or standard)")
    DEBUG: bool = Field(default=False, description="Debug mode")
    ENVIRONMENT: str = Field(default="development", description="Environment name")
    MAX_RETRY_ATTEMPTS: int = Field(default=3, ge=1, description="Maximum retry attempts")

    # MCP Configuration
    MCP_PROTOCOL_VERSION: str = Field(default="1.0.0", description="MCP protocol version")
    MCP_TIMEOUT: int = Field(default=30, ge=1, description="MCP request timeout in seconds")

    # Monitoring
    PROMETHEUS_PORT: int = Field(default=9090, description="Prometheus port")
    GRAFANA_PORT: int = Field(default=3000, description="Grafana port")

    # Optional Services
    SONARQUBE_URL: Optional[str] = Field(default=None, description="SonarQube URL")
    SONARQUBE_TOKEN: Optional[str] = Field(default=None, description="SonarQube token")
    SNYK_TOKEN: Optional[str] = Field(default=None, description="Snyk API token")
    SLACK_WEBHOOK_URL: Optional[str] = Field(default=None, description="Slack webhook URL")

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v.upper()

    @property
    def database_url(self) -> str:
        """Get SQLAlchemy database URL"""
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def redis_url(self) -> str:
        """Get Redis connection URL"""
        return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}"

    @property
    def rabbitmq_url(self) -> str:
        """Get RabbitMQ connection URL"""
        return (
            f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASSWORD}"
            f"@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/"
        )

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


# Singleton instance
settings = Settings()
