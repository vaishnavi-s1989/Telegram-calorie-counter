"""
Configuration module for the Telegram Calorie Tracker Bot
Supports local development (SQLite + polling) and
IBM Cloud / Code Engine production (PostgreSQL + webhook).
"""
import os
from dotenv import load_dotenv

# Load .env only in local development; on IBM Code Engine env vars are
# injected directly by the platform so load_dotenv() is a no-op there.
load_dotenv()


class Config:
    """Application configuration"""

    # ------------------------------------------------------------------
    # Telegram Bot
    # ------------------------------------------------------------------
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")

    # ------------------------------------------------------------------
    # Webhook vs Polling mode
    #   - Set WEBHOOK_MODE=true on IBM Code Engine (required — Code Engine
    #     does not support long-running polling processes well, and the
    #     container must respond to HTTP on PORT).
    #   - Leave unset / false for local development (polling mode).
    # ------------------------------------------------------------------
    WEBHOOK_MODE: bool = os.getenv("WEBHOOK_MODE", "false").lower() == "true"

    # The public HTTPS URL that IBM Code Engine assigns to your application.
    # Format: https://<app-name>.<random>.<region>.codeengine.appdomain.cloud
    # Set this after first deployment.
    WEBHOOK_URL: str = os.getenv("WEBHOOK_URL", "")

    # Secret token Telegram will send in X-Telegram-Bot-Api-Secret-Token header
    # Generate with: python -c "import secrets; print(secrets.token_hex(32))"
    WEBHOOK_SECRET: str = os.getenv("WEBHOOK_SECRET", "")

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------
    APP_ENV: str = os.getenv("APP_ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"

    # IBM Code Engine always routes traffic to PORT 8080
    PORT: int = int(os.getenv("PORT", "8080"))

    # ------------------------------------------------------------------
    # Database
    #   - Local dev  : SQLite (default)
    #   - IBM Cloud  : IBM Databases for PostgreSQL
    #                  Set DATABASE_URL to the PostgreSQL connection string
    #                  from the IBM Cloud service credentials, e.g.:
    #                  postgresql://user:pass@host:port/dbname?sslmode=require
    # ------------------------------------------------------------------
    # SQLAlchemy 2.x dropped the legacy "postgres://" scheme — only
    # "postgresql://" is accepted.  ElephantSQL and some other providers
    # still emit the old scheme, so we normalise it here at load time.
    #
    # IBM Databases for PostgreSQL (private endpoint) issues URLs with
    # sslmode=verify-full, which requires the server's CA certificate.
    # IBM Cloud uses its own internal CA that is NOT in the standard OS
    # trust store, so verify-full always fails inside the container.
    # We downgrade to sslmode=require, which still enforces TLS encryption
    # but skips CA verification — safe because both Code Engine and IBM
    # Databases for PostgreSQL run inside IBM Cloud's private network.
    @staticmethod
    def _normalise_db_url(url: str) -> str:
        # 1. Fix legacy scheme
        url = url.replace("postgres://", "postgresql://", 1)
        # 2. Downgrade verify-full -> require for IBM Cloud private endpoints
        if url.startswith("postgresql"):
            url = url.replace("sslmode=verify-full", "sslmode=require")
        return url

    DATABASE_URL: str = _normalise_db_url.__func__(  # type: ignore[attr-defined]
        os.getenv("DATABASE_URL", "sqlite:///./calorie_tracker.db")
    )

    # Detect which database engine is in use
    @classmethod
    def is_postgres(cls) -> bool:
        return cls.DATABASE_URL.startswith("postgresql")

    # ------------------------------------------------------------------
    # IBM Cloud — Container Registry
    #   Used only during the build/push phase (ibmcloud CLI commands).
    #   Not needed at runtime.
    # ------------------------------------------------------------------
    IBM_CLOUD_REGION: str = os.getenv("IBM_CLOUD_REGION", "us-south")
    IBM_CR_NAMESPACE: str = os.getenv("IBM_CR_NAMESPACE", "")
    IBM_CR_IMAGE: str = os.getenv(
        "IBM_CR_IMAGE",
        "us.icr.io/<namespace>/calorie-tracker-bot:latest"
    )

    # ------------------------------------------------------------------
    # External APIs
    # ------------------------------------------------------------------
    # USDA FoodData Central API
    # Get your API key from: https://fdc.nal.usda.gov/api-key-signup.html
    USDA_API_KEY: str = os.getenv("USDA_API_KEY", "")
    USDA_API_URL: str = os.getenv(
        "USDA_API_URL",
        "https://api.nal.usda.gov/fdc/v1"
    )
    
    OPEN_FOOD_FACTS_API_URL: str = os.getenv(
        "OPEN_FOOD_FACTS_API_URL",
        "https://world.openfoodfacts.org/api/v0"
    )

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration at startup"""
        errors = []

        if not cls.TELEGRAM_BOT_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN is required")

        if cls.WEBHOOK_MODE and not cls.WEBHOOK_URL:
            errors.append(
                "WEBHOOK_URL is required when WEBHOOK_MODE=true. "
                "Set it to your IBM Code Engine application URL."
            )

        if cls.WEBHOOK_MODE and not cls.WEBHOOK_SECRET:
            errors.append(
                "WEBHOOK_SECRET is required when WEBHOOK_MODE=true. "
                "Generate with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )

        if errors:
            raise ValueError("\n".join(errors))

        return True

    @classmethod
    def summary(cls) -> str:
        """Return a human-readable config summary (no secrets)"""
        return (
            f"APP_ENV={cls.APP_ENV} | "
            f"DEBUG={cls.DEBUG} | "
            f"PORT={cls.PORT} | "
            f"WEBHOOK_MODE={cls.WEBHOOK_MODE} | "
            f"DB={'PostgreSQL' if cls.is_postgres() else 'SQLite'}"
        )


# Singleton config instance
config = Config()

# Made with Bob
