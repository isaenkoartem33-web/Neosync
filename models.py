from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

db = SQLAlchemy()

class User(db.Model):
    """User model for storing user authentication and profile data"""
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    picture = db.Column(db.String(500))
    
    # Password authentication (for email/password registration)
    password_hash = db.Column(db.String(255))
    
    # OAuth authentication (for Google OAuth)
    google_id = db.Column(db.String(255), unique=True, index=True)
    
    # Yandex OAuth
    yandex_id = db.Column(db.String(255), unique=True, index=True)
    yandex_access_token = db.Column(db.Text)
    yandex_refresh_token = db.Column(db.Text)
    yandex_token_expiry = db.Column(db.DateTime)
    
    # OAuth tokens (encrypted) - for Google
    access_token = db.Column(db.Text)
    refresh_token = db.Column(db.Text)
    token_expiry = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    subscriptions = db.relationship('Subscription', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'picture': self.picture,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Subscription(db.Model):
    """Subscription model for storing user subscriptions"""
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    
    name = db.Column(db.String(255), nullable=False)
    cost = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='USD')
    billing_period = db.Column(db.String(20), nullable=False)  # weekly, monthly, quarterly, yearly
    
    start_date = db.Column(db.Date, nullable=False)
    next_billing_date = db.Column(db.Date, nullable=False)
    
    category = db.Column(db.String(50), default='Other')
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    
    # Gmail import metadata
    imported_from_gmail = db.Column(db.Boolean, default=False)
    gmail_message_id = db.Column(db.String(255))
    
    # Manual addition metadata
    manually_added = db.Column(db.Boolean, default=False)
    
    # Payment URL for redirecting to service payment page
    payment_url = db.Column(db.String(500))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    notifications = db.relationship('Notification', backref='subscription', lazy='dynamic', cascade='all, delete-orphan')
    
    # Indexes
    __table_args__ = (
        db.Index('idx_user_active', 'user_id', 'is_active'),
        db.Index('idx_next_billing', 'next_billing_date'),
    )
    
    def __repr__(self):
        return f'<Subscription {self.name} - ${self.cost}/{self.billing_period}>'
    
    def to_dict(self):
        """Convert subscription to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'cost': self.cost,
            'currency': self.currency,
            'billing_period': self.billing_period,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'next_billing_date': self.next_billing_date.isoformat() if self.next_billing_date else None,
            'category': self.category,
            'notes': self.notes,
            'is_active': self.is_active,
            'imported_from_gmail': self.imported_from_gmail,
            'manually_added': self.manually_added,
            'payment_url': self.payment_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Notification(db.Model):
    """Notification model for storing user notifications"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    subscription_id = db.Column(db.String(36), db.ForeignKey('subscriptions.id'), nullable=False)
    
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), default='billing_reminder')
    is_read = db.Column(db.Boolean, default=False, index=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_user_unread', 'user_id', 'is_read'),
    )
    
    def __repr__(self):
        return f'<Notification {self.notification_type} - Read: {self.is_read}>'
    
    def to_dict(self):
        """Convert notification to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'subscription_id': self.subscription_id,
            'message': self.message,
            'notification_type': self.notification_type,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class EmailVerificationCode(db.Model):
    """Временное хранилище кодов подтверждения email при регистрации"""
    __tablename__ = 'email_verification_codes'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False, index=True)
    code = db.Column(db.String(6), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    user_data = db.Column(db.Text, nullable=False)  # JSON с данными регистрации

    def __repr__(self):
        return f'<EmailVerificationCode {self.email}>'
