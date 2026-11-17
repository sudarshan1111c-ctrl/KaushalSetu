"""Configuration settings for KaushalSetu application.

Only simple settings are defined here; more can be added as needed.
"""
import os

class Config:
    # Secret key for session management – override via environment variable
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    # Database URI – can be overridden via DATABASE_URL env var
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///kaushalsetu.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
