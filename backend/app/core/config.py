"""
ShieldPay AI — Application Configuration
"""
import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "ShieldPay AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # MongoDB
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    MONGODB_DB_NAME: str = "shieldpay"

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "shieldpay-dev-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 1440  # 24 hours

    # External APIs
    WEATHER_API_KEY: str = os.getenv("WEATHER_API_KEY", "demo-key")
    WEATHER_API_URL: str = "https://api.openweathermap.org/data/2.5"
    TRAFFIC_API_KEY: str = os.getenv("TRAFFIC_API_KEY", "demo-key")
    TRAFFIC_API_URL: str = "https://api.tomtom.com/traffic/services"

    # Premium Pricing
    BASE_PREMIUM_MIN: float = 15.0   # ₹15/week minimum
    BASE_PREMIUM_MAX: float = 50.0   # ₹50/week maximum
    RISK_MULTIPLIER_CAP: float = 3.0

    # Trust Score Thresholds
    TRUST_INSTANT_PAYOUT: float = 0.85
    TRUST_SOFT_VERIFY: float = 0.50
    # Below 0.50 → delayed review

    # Payout Limits
    MAX_WEEKLY_PAYOUT: float = 2000.0  # ₹2000 max per week
    LIQUIDITY_RESERVE_RATIO: float = 0.30  # 30% reserve

    # Scheduler
    TRIGGER_SCAN_INTERVAL_MINUTES: int = 20

    # CORS
    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"


settings = Settings()
