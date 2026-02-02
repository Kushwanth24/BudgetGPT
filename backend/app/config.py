import os
from datetime import timedelta


class Config:
    # -----------------------------
    # App
    # -----------------------------
    APP_NAME = os.getenv("APP_NAME", "BudgetGPT")
    ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = ENV == "development"

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")

    # -----------------------------
    # Database
    # -----------------------------
    # SQLite for MVP, PostgreSQL later
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///app.db",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # -----------------------------
    # JWT
    # -----------------------------
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-secret")

    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MIN", "10080"))  # 7 days
    )

    JWT_TOKEN_LOCATION = ["headers"]
    JWT_HEADER_NAME = "Authorization"
    JWT_HEADER_TYPE = "Bearer"

    # -----------------------------
    # CORS
    # -----------------------------
    FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
    CORS_ORIGINS = [FRONTEND_ORIGIN]

    # -----------------------------
    # Security (future-ready)
    # -----------------------------
    SESSION_COOKIE_SECURE = ENV == "production"
    SESSION_COOKIE_HTTPONLY = True
