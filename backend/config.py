from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    gmail_user: str = "ready4industry@gmail.com"
    gmail_app_password: str = ""
    backend_host: str = "127.0.0.1"
    backend_port: int = 8000
    database_url: str = "sqlite+aiosqlite:///./collegemarketingai.db"
    templates_dir: str = "../templates"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
