import os
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, SecretStr, model_validator


class Settings(BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True)
    token: SecretStr
    namespaces: list[str] = ["veriqta-demo"]
    provider: str = "mock"
    source: str = "fixture"
    model: str = "gpt-4.1-mini"
    api_key: SecretStr = SecretStr("")
    database: str = ".data/investigations.db"
    logs: bool = False
    log_lookback_seconds: int = Field(default=3600, ge=60, le=86400)
    concurrency: int = Field(default=2, ge=1, le=8)
    queue_limit: int = Field(default=20, ge=1, le=100)
    duration: int = Field(default=90, ge=1, le=300)
    tool_timeout: int = Field(default=8, ge=1, le=30)
    max_calls: int = Field(default=8, ge=1, le=16)
    max_turns: int = Field(default=6, ge=1, le=12)
    retention_days: int = Field(default=7, ge=1, le=90)
    max_records: int = Field(default=500, ge=1, le=10000)
    max_db_bytes: int = Field(default=100_000_000, ge=100000)
    session_seconds: int = Field(default=3600, ge=60, le=86400)
    secure_cookie: bool = False

    @model_validator(mode="after")
    def valid(self):
        import re

        if len(self.token.get_secret_value()) < 32:
            raise ValueError(
                "KI_TOKEN must contain at least 32 characters; generate with secrets.token_urlsafe(32)"
            )
        if not self.namespaces or any(
            not re.fullmatch(r"[a-z0-9](?:[-a-z0-9]{0,61}[a-z0-9])?", n) for n in self.namespaces
        ):
            raise ValueError("KI_NAMESPACES must contain explicit namespace names")
        if self.provider not in {"mock", "openai"} or self.source not in {"fixture", "kubernetes"}:
            raise ValueError("Unknown provider or evidence source")
        if self.source == "fixture" and self.provider != "mock":
            raise ValueError("Fixture evidence is restricted to mock provider")
        if self.provider == "openai" and not self.api_key.get_secret_value():
            raise ValueError("KI_API_KEY is required for openai")
        return self

    @classmethod
    def environment(cls):
        data = {}
        for name in cls.model_fields:
            value = os.getenv("KI_" + name.upper())
            if value is not None:
                data[name] = value.split(",") if name == "namespaces" else value
        return cls.model_validate(data)

    def prepare(self):
        Path(self.database).parent.mkdir(parents=True, exist_ok=True, mode=0o700)
