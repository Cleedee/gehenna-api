import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-prod')
    API_BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost:8002')
    SESSION_COOKIE_NAME = 'gehenna_session'
    PERMANENT_SESSION_LIFETIME = 3600 * 24 * 7