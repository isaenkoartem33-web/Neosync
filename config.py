import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///subscriptions.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Google OAuth
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID') or ''
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET') or ''
    GOOGLE_DISCOVERY_URL = 'https://accounts.google.com/.well-known/openid-configuration'
    
    # Yandex OAuth
    YANDEX_CLIENT_ID = os.environ.get('YANDEX_CLIENT_ID') or ''
    YANDEX_CLIENT_SECRET = os.environ.get('YANDEX_CLIENT_SECRET') or ''
    YANDEX_AUTHORIZE_URL = 'https://oauth.yandex.ru/authorize'
    YANDEX_ACCESS_TOKEN_URL = 'https://oauth.yandex.ru/token'
    YANDEX_API_BASE_URL = 'https://login.yandex.ru/'
    
    # OAuth Scopes
    OAUTH_SCOPES = [
        'openid',
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/userinfo.profile',
        'https://www.googleapis.com/auth/gmail.readonly'
    ]
    
    # Encryption key for OAuth tokens
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY') or 'encryption-key-change-in-production'
    
    # Session
    SESSION_COOKIE_SECURE = True  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 604800  # 7 days in seconds

    # Email (для отправки кодов верификации)
    EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
    EMAIL_USER = os.environ.get('EMAIL_USER', '')
    EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD', '')
