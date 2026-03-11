from pydantic_settings import BaseSettings


class EnvSettings(BaseSettings):
    # App
    environment: str = "development"
    port: int = 3333
    allowed_origins: str = ""

    # Database
    db_host: str = "localhost"
    db_port: int = 5432
    db_user: str = "postgres"
    db_password: str = "postgres"
    db_name: str = "spock"

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 0
    redis_tls: str = ""

    # Proxy
    proxy_url: str = ""
    proxy_secret: str = ""

    # Investidor10
    investidor10_base_url: str = "https://investidor10.com.br"
    investidor10_timeout_ms: int = 30000

    # Analysis
    analysis_algorithm_version: str = "1.0.0"
    analysis_rolling_window_months: int = 12

    # Scoring
    scoring_weight_regularity: float = 0.4
    scoring_weight_timeliness: float = 0.3
    scoring_weight_quality: float = 0.3
    scoring_timeliness_limit_days: int = 30

    # Sentry
    sentry_dsn: str = ""
    sentry_environment: str = "development"
    sentry_traces_sample_rate: float = 0.1

    # Auth
    api_keys: str = ""

    @property
    def _requires_ssl(self) -> bool:
        return self.db_host != "localhost"

    @property
    def database_url(self) -> str:
        base = f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        if self._requires_ssl:
            return f"{base}?ssl=require"
        return base

    @property
    def sync_database_url(self) -> str:
        base = f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        if self._requires_ssl:
            return f"{base}?sslmode=require"
        return base

    @property
    def redis_url(self) -> str:
        scheme = "rediss" if self.redis_tls else "redis"
        auth = f":{self.redis_password}@" if self.redis_password else ""
        base = f"{scheme}://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"
        if self.redis_tls:
            return f"{base}?ssl_cert_reqs=none"
        return base

    @property
    def api_key_list(self) -> list[str]:
        if not self.api_keys:
            return []
        return [k.strip() for k in self.api_keys.split(",") if k.strip()]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}
