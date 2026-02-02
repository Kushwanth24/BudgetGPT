import os


class Config:
    APP_NAME = os.getenv("APP_NAME", "BudgetGPT")
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-secret")

    # SQLite MVP default (relative file app.db in backend folder)
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # CORS: allow Next.js dev + prod; set FRONTEND_ORIGIN to lock down later
    FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
    CORS_ORIGINS = [FRONTEND_ORIGIN]

    # JWT
    JWT_ACCESS_TOKEN_EXPIRES_MIN = int(
        os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MIN", "10080"))  # 7 days
