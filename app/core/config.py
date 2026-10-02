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


class S3Settings(BaseModel):
    endpoint_url: str = "http://localhost:3900"
    region: str = "garage"
    access_key_id: str
    secret_access_key: SecretStr
    bucket: str


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
    s3: S3Settings


settings = Settings()  # pyright: ignore[reportCallIssue]  # required fields are loaded from the environment
