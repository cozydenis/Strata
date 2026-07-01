from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = ""
    cors_origins: str = "http://localhost:3000"
    environment: str = "dev"
    pipeline_api_key: str = ""
    supabase_url: str = ""
    supabase_service_key: str = ""
    supabase_jwt_secret: str = ""
    # Fallback current Referenzzinssatz (%) when the reference_rates table is empty.
    # Verify against bwo.admin.ch; 1.25% as of June 2026.
    default_reference_rate: float = 1.25
    # Email notifications (watch-event digests). When smtp_host is unset the
    # ConsoleSender is used (logs the email), so this works with zero config.
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    mail_from: str = "Strata <no-reply@strata.homes>"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
