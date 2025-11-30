"""
Configuration Management
Handles environment variables and application settings
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # LLM Configuration
    openai_api_key: Optional[str] = None
    ollama_base_url: str = "http://localhost:11434"
    # ollama_model: str = "llama3.1:latest"
    ollama_model: str = "gemma2:9b"
   
    
    # Database Configuration
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = "mysql_password_here"
    mysql_database: str = "tcs_forecast"
    
    # Application Settings
    log_level: str = "INFO"
    max_document_size: int = 10485760  # 10MB
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @property
    def database_url(self) -> str:
        """Generate MySQL connection URL"""
        return (
            f"mysql+mysqlconnector://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
        )
    
    @property
    def use_openai(self) -> bool:
        """Check if OpenAI API key is provided"""
        return bool(self.openai_api_key)


# Global settings instance
settings = Settings()
