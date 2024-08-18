import os

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseConfig(BaseModel):
    dsn: str = 'postgresql://user:password@host:port/dbname'


class Config(BaseSettings):
    database: DatabaseConfig = DatabaseConfig()
    # token_key: str = ''

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        env_prefix='GEHENNA_',
        env_nested_delimiter='__',
        case_sensitive=False,
    )


config = Config()
