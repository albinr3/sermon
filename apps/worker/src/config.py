from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    redis_url: str = "redis://localhost:6379/0"
    database_url: str = "postgresql+psycopg2://sermon:sermon@localhost:5432/sermon"

    s3_endpoint: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "sermon"
    s3_region: str = "us-east-1"
    s3_use_ssl: bool = False
    use_llm_for_clip_suggestions: bool = False
    deepseek_api_key: str | None = None
    deepseek_model: str | None = None
    deepseek_base_url: str | None = None


settings = Settings()
