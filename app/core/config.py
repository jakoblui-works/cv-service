import urllib.parse

from pydantic import BaseModel, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class RedisSettings(BaseModel):
    host: str = "localhost"
    port: int = 6379
    password: SecretStr

    @property
    def url(self) -> str:
        password = urllib.parse.quote(self.password.get_secret_value(), safe="")
        return f"redis://:{password}@{self.host}:{self.port}/0"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        extra="ignore",
        hide_input_in_errors=True,
    )
    log_level: str = "INFO"

    app_name: str = "cv-service"
    debug: bool = False

    redis: RedisSettings


settings = Settings()
