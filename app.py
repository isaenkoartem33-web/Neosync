from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from flask_cors import CORS
from authlib.integrations.flask_client import OAuth
from cryptography.fernet import Fernet
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from werkzeug.security import generate_password_hash, check_password_hash
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import base64
import hashlib
import json
import re
import uuid
import hmac
import time
from functools import wraps
from models import db, User, Subscription, Notification
from config import Config
from email_import import import_from_email

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# CORS для Flutter web — разрешаем все localhost порты
CORS(app, resources={r"/mobile/*": {"origins": "*", "allow_headers": ["Content-Type", "Authorization"], "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]}})

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
oauth = OAuth(app)

# Initialize encryption for OAuth tokens
def get_encryption_key():
    """Generate encryption key from config"""
    key = hashlib.sha256(app.config['ENCRYPTION_KEY'].encode()).digest()
    return base64.urlsafe_b64encode(key)

cipher_suite = Fernet(get_encryption_key())

def encrypt_token(token):
    """Encrypt OAuth token"""
    if not token:
        return None
    return cipher_suite.encrypt(token.encode()).decode()

def decrypt_token(encrypted_token):
    """Decrypt OAuth token"""
    if not encrypted_token:
        return None
    return cipher_suite.decrypt(encrypted_token.encode()).decode()

# Configure Google OAuth
google = oauth.register(
    name='google',
    client_id=app.config['GOOGLE_CLIENT_ID'],
    client_secret=app.config['GOOGLE_CLIENT_SECRET'],
    server_metadata_url=app.config['GOOGLE_DISCOVERY_URL'],
    client_kwargs={'scope': ' '.join(app.config['OAUTH_SCOPES'])}
)

# Configure Yandex OAuth
yandex = oauth.register(
    name='yandex',
    client_id=app.config['YANDEX_CLIENT_ID'],
    client_secret=app.config['YANDEX_CLIENT_SECRET'],
    authorize_url=app.config['YANDEX_AUTHORIZE_URL'],
    authorize_params=None,
    access_token_url=app.config['YANDEX_ACCESS_TOKEN_URL'],
    access_token_params=None,
    client_kwargs={'scope': 'login:email login:info'}
)

# Flask-Login user loader
class UserLogin(UserMixin):
    def __init__(self, user_id):
        self.id = user_id

@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(user_id)
    if user:
        return UserLogin(user.id)
    return None

# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@app.route('/')
def index():
    """Main dashboard page"""
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login')
def login():
    """Login page"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    return render_template('reg.html')

@app.route('/auth/google')
def auth_google():
    """Redirect to Google OAuth"""
    redirect_uri = url_for('auth_google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/auth/google/callback')
def auth_google_callback():
    """Handle Google OAuth callback"""
    try:
        token = google.authorize_access_token()
        user_info = token.get('userinfo')
        
        if not user_info:
            return jsonify({'error': 'Failed to get user info'}), 400
        
        # Find user by email first (to link with existing Yandex account)
        user = User.query.filter_by(email=user_info['email']).first()
        
        if not user:
            # Create new user if doesn't exist
            user = User(
                email=user_info['email'],
                name=user_info.get('name', ''),
                picture=user_info.get('picture', '')
            )
            db.session.add(user)
        else:
            # Update existing user info
            user.name = user_info.get('name', user.name)
            user.picture = user_info.get('picture', user.picture)
            user.updated_at = datetime.utcnow()
        
        # Store Google OAuth data
        user.google_id = user_info['sub']
        user.access_token = encrypt_token(token.get('access_token'))
        user.refresh_token = encrypt_token(token.get('refresh_token'))
        user.token_expiry = datetime.utcnow() + timedelta(seconds=token.get('expires_in', 3600))
        
        db.session.commit()
        
        # Login user
        login_user(UserLogin(user.id), remember=True)
        
        return redirect(url_for('index'))
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/auth/yandex')
def auth_yandex():
    """Redirect to Yandex OAuth"""
    redirect_uri = url_for('auth_yandex_callback', _external=True)
    return yandex.authorize_redirect(redirect_uri)

@app.route('/auth/yandex/callback')
def auth_yandex_callback():
    """Handle Yandex OAuth callback"""
    try:
        token = yandex.authorize_access_token()
        
        # Get user info from Yandex
        resp = yandex.get('info', token=token)
        user_info = resp.json()
        
        if not user_info:
            return jsonify({'error': 'Failed to get user info'}), 400
        
        # Find or create user
        user = User.query.filter_by(email=user_info['default_email']).first()
        
        if not user:
            user = User(
                email=user_info['default_email'],
                name=user_info.get('display_name', ''),
                picture=f"https://avatars.yandex.net/get-yapic/{user_info.get('default_avatar_id', '')}/islands-200" if user_info.get('default_avatar_id') else ''
            )
            db.session.add(user)
        else:
            user.name = user_info.get('display_name', user.name)
            if user_info.get('default_avatar_id'):
                user.picture = f"https://avatars.yandex.net/get-yapic/{user_info['default_avatar_id']}/islands-200"
            user.updated_at = datetime.utcnow()
        
        # Store encrypted Yandex OAuth tokens
        user.yandex_id = user_info.get('id', '')
        user.yandex_access_token = encrypt_token(token.get('access_token'))
        user.yandex_refresh_token = encrypt_token(token.get('refresh_token'))
        if token.get('expires_in'):
            user.yandex_token_expiry = datetime.utcnow() + timedelta(seconds=token['expires_in'])
        
        db.session.commit()
        
        # Login user
        login_user(UserLogin(user.id), remember=True)
        
        return redirect(url_for('index'))
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    """Logout user"""
    logout_user()
    return jsonify({'message': 'Logged out successfully'})

@app.route('/api/auth/status', methods=['GET'])
@login_required
def auth_status():
    """Get authentication status for current user"""
    user = User.query.get(current_user.id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Check if there are other users with connected accounts
    all_users = User.query.all()
    google_connected = any(u.google_id for u in all_users)
    yandex_connected = any(u.yandex_id for u in all_users)
    
    return jsonify({
        'authenticated': True,
        'email': user.email,
        'name': user.name,
        'google_connected': google_connected,
        'yandex_connected': yandex_connected,
        'has_password': bool(user.password_hash),
        'current_user_google': bool(user.google_id),
        'current_user_yandex': bool(user.yandex_id)
    })

@app.route('/profile')
@login_required
def profile():
    """Profile page"""
    return render_template('profile.html')

# ============================================================================
# EMAIL/PASSWORD AUTHENTICATION ROUTES
# ============================================================================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register new user with email and password"""
    data = request.get_json()
    
    # Validate input
    if not data.get('email') or not data.get('password') or not data.get('name'):
        return jsonify({'error': 'Email, password and name are required'}), 400
    
    # Check if user already exists
    existing_user = User.query.filter_by(email=data['email']).first()
    if existing_user:
        return jsonify({'error': 'User with this email already exists'}), 400
    
    # Create new user
    user = User(
        email=data['email'],
        name=data['name'],
        picture=data.get('picture', '')
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    # Login user
    login_user(UserLogin(user.id), remember=True)
    
    return jsonify({
        'message': 'User registered successfully',
        'user': user.to_dict()
    }), 201

@app.route('/api/auth/login', methods=['POST'])
def login_email():
    """Login user with email and password"""
    data = request.get_json()
    
    # Validate input
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password are required'}), 400
    
    # Find user
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid email or password'}), 401
    
    # Login user
    login_user(UserLogin(user.id), remember=True)
    
    return jsonify({
        'message': 'Logged in successfully',
        'user': user.to_dict()
    })

# ============================================================================
# SUBSCRIPTION CRUD ROUTES
# ============================================================================

def calculate_next_billing_date(start_date, billing_period):
    """Calculate next billing date based on period"""
    if billing_period == 'weekly':
        return start_date + timedelta(weeks=1)
    elif billing_period == 'monthly':
        return start_date + relativedelta(months=1)
    elif billing_period == 'quarterly':
        return start_date + relativedelta(months=3)
    elif billing_period == 'yearly':
        return start_date + relativedelta(years=1)
    return start_date

def check_duplicate_subscription(user_id, name, cost):
    """
    Check for duplicate subscriptions based on name and cost
    
    Args:
        user_id (str): User ID to check subscriptions for
        name (str): Subscription name to check
        cost (float): Subscription cost to check
    
    Returns:
        dict: Dictionary with duplicate information or None if no duplicate found
    """
    # Normalize name for comparison (case-insensitive)
    name_normalized = name.strip().lower()
    
    # Find existing subscription with same name (case-insensitive)
    existing = Subscription.query.filter_by(user_id=user_id).filter(
        db.func.lower(Subscription.name) == name_normalized
    ).first()
    
    if existing and abs(existing.cost - cost) <= 0.01:  # Allow small floating point differences
        return {
            'duplicate_found': True,
            'existing_subscription': {
                'id': existing.id,
                'name': existing.name,
                'cost': existing.cost,
                'currency': existing.currency,
                'billing_period': existing.billing_period,
                'category': existing.category,
                'start_date': existing.start_date.isoformat() if existing.start_date else None,
                'manually_added': existing.manually_added,
                'imported_from_gmail': existing.imported_from_gmail
            }
        }
    
    return {'duplicate_found': False}

@app.route('/api/subscriptions', methods=['GET'])
@login_required
def get_subscriptions():
    """Get all user subscriptions"""
    subscriptions = Subscription.query.filter_by(user_id=current_user.id).all()
    return jsonify([sub.to_dict() for sub in subscriptions])

@app.route('/api/subscriptions/create-duplicate', methods=['POST'])
@login_required
def create_duplicate_subscription():
    """
    Create subscription even if it's a duplicate (Requirements 3.3)
    This endpoint is called when user confirms they want to create a duplicate subscription
    """
    data = request.get_json()
    
    # Validate required fields
    if not data.get('name') or not data.get('cost') or not data.get('billing_period'):
        return jsonify({'error': 'Missing required fields: name, cost, billing_period'}), 400
    
    # Validate confirmation flag
    if not data.get('confirm_duplicate'):
        return jsonify({'error': 'Duplicate confirmation required'}), 400
    
    # Validate name length (Requirements 2.1)
    name = data['name'].strip()
    if len(name) < 1 or len(name) > 255:
        return jsonify({'error': 'Name must be between 1 and 255 characters'}), 400
    
    # Validate cost (Requirements 2.2)
    try:
        cost = float(data['cost'])
        if cost <= 0:
            return jsonify({'error': 'Cost must be positive'}), 400
        # Check for maximum 2 decimal places
        if round(cost, 2) != cost:
            return jsonify({'error': 'Cost can have maximum 2 decimal places'}), 400
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid cost format'}), 400
    
    # Validate billing period
    valid_periods = ['weekly', 'monthly', 'quarterly', 'yearly']
    if data['billing_period'] not in valid_periods:
        return jsonify({'error': f'Billing period must be one of: {", ".join(valid_periods)}'}), 400
    
    # Validate currency
    valid_currencies = ['RUB', 'USD', 'EUR']
    currency = data.get('currency', 'USD')
    if currency not in valid_currencies:
        return jsonify({'error': f'Currency must be one of: {", ".join(valid_currencies)}'}), 400
    
    # Validate start date (Requirements 2.3)
    try:
        start_date_str = data.get('start_date', date.today().isoformat())
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        
        # Check that start date is not more than 1 year in the future
        max_future_date = date.today() + timedelta(days=365)
        if start_date > max_future_date:
            return jsonify({'error': 'Start date cannot be more than 1 year in the future'}), 400
    except ValueError:
        return jsonify({'error': 'Invalid start date format. Use YYYY-MM-DD'}), 400
    
    # Validate category
    valid_categories = ['Entertainment', 'Software', 'Education', 'Health', 'Finance', 'Other']
    category = data.get('category', 'Other')
    if category not in valid_categories:
        return jsonify({'error': f'Category must be one of: {", ".join(valid_categories)}'}), 400
    
    # Sanitize notes (Requirements 8.2)
    notes = data.get('notes', '').strip()
    if len(notes) > 1000:
        return jsonify({'error': 'Notes cannot exceed 1000 characters'}), 400
    
    # Calculate next billing date (Requirements 6.2)
    next_billing = calculate_next_billing_date(start_date, data['billing_period'])
    
    # Create subscription with proper validation (Requirements 6.1, 6.3, 6.4)
    # Mark as manually added since user confirmed duplicate creation (Requirements 3.3)
    subscription = Subscription(
        user_id=current_user.id,
        name=name,
        cost=cost,
        currency=currency,
        billing_period=data['billing_period'],
        start_date=start_date,
        next_billing_date=next_billing,
        category=category,
        notes=notes,
        is_active=data.get('is_active', True),
        manually_added=True  # Mark as manually added (Requirements 6.1, 3.3)
    )
    
    try:
        db.session.add(subscription)
        db.session.commit()
        
        # Log action for audit (Requirements 8.4)
        app.logger.info(f"Duplicate subscription created: user_id={current_user.id}, subscription_id={subscription.id}, name={name}")
        
        return jsonify({
            'message': 'Duplicate subscription created successfully',
            'subscription': subscription.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating duplicate subscription: {str(e)}")
        return jsonify({'error': 'Failed to create subscription. Please try again.'}), 500

@app.route('/api/subscriptions', methods=['POST'])
@login_required
def create_subscription():
    """Create new subscription"""
    data = request.get_json()
    
    # Validate required fields
    if not data.get('name') or not data.get('cost') or not data.get('billing_period'):
        return jsonify({'error': 'Missing required fields: name, cost, billing_period'}), 400
    
    # Validate name length (Requirements 2.1)
    name = data['name'].strip()
    if len(name) < 1 or len(name) > 255:
        return jsonify({'error': 'Name must be between 1 and 255 characters'}), 400
    
    # Validate cost (Requirements 2.2)
    try:
        cost = float(data['cost'])
        if cost <= 0:
            return jsonify({'error': 'Cost must be positive'}), 400
        # Check for maximum 2 decimal places
        if round(cost, 2) != cost:
            return jsonify({'error': 'Cost can have maximum 2 decimal places'}), 400
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid cost format'}), 400
    
    # Validate billing period
    valid_periods = ['weekly', 'monthly', 'quarterly', 'yearly']
    if data['billing_period'] not in valid_periods:
        return jsonify({'error': f'Billing period must be one of: {", ".join(valid_periods)}'}), 400
    
    # Validate currency
    valid_currencies = ['RUB', 'USD', 'EUR']
    currency = data.get('currency', 'USD')
    if currency not in valid_currencies:
        return jsonify({'error': f'Currency must be one of: {", ".join(valid_currencies)}'}), 400
    
    # Validate start date (Requirements 2.3)
    try:
        start_date_str = data.get('start_date', date.today().isoformat())
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        
        # Check that start date is not more than 1 year in the future
        max_future_date = date.today() + timedelta(days=365)
        if start_date > max_future_date:
            return jsonify({'error': 'Start date cannot be more than 1 year in the future'}), 400
    except ValueError:
        return jsonify({'error': 'Invalid start date format. Use YYYY-MM-DD'}), 400
    
    # Validate category
    valid_categories = ['Entertainment', 'Software', 'Education', 'Health', 'Finance', 'Other']
    category = data.get('category', 'Other')
    if category not in valid_categories:
        return jsonify({'error': f'Category must be one of: {", ".join(valid_categories)}'}), 400
    
    # Sanitize notes (Requirements 8.2)
    notes = data.get('notes', '').strip()
    if len(notes) > 1000:
        return jsonify({'error': 'Notes cannot exceed 1000 characters'}), 400
    
    # Validate payment URL (optional)
    payment_url = data.get('payment_url', '').strip()
    if payment_url:
        if len(payment_url) > 500:
            return jsonify({'error': 'Payment URL cannot exceed 500 characters'}), 400
        # Basic URL validation
        if not payment_url.startswith(('http://', 'https://')):
            return jsonify({'error': 'Payment URL must start with http:// or https://'}), 400
    
    # Check for duplicates (Requirements 3.1, 3.2)
    duplicate_check = check_duplicate_subscription(current_user.id, name, cost)
    
    if duplicate_check['duplicate_found']:
        return jsonify({
            'error': 'Duplicate subscription detected',
            'error_type': 'duplicate',
            'duplicate_info': duplicate_check['existing_subscription']
        }), 409  # Conflict status code for duplicates
    
    # Calculate next billing date (Requirements 6.2)
    next_billing = calculate_next_billing_date(start_date, data['billing_period'])
    
    # Create subscription with proper validation (Requirements 6.1, 6.3, 6.4)
    subscription = Subscription(
        user_id=current_user.id,
        name=name,
        cost=cost,
        currency=currency,
        billing_period=data['billing_period'],
        start_date=start_date,
        next_billing_date=next_billing,
        category=category,
        notes=notes,
        payment_url=payment_url if payment_url else None,
        is_active=data.get('is_active', True),
        manually_added=True  # Mark as manually added (Requirements 6.1)
    )
    
    try:
        db.session.add(subscription)
        db.session.commit()
        
        # Log action for audit (Requirements 8.4)
        app.logger.info(f"Manual subscription created: user_id={current_user.id}, subscription_id={subscription.id}, name={name}")
        
        return jsonify(subscription.to_dict()), 201
    
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating subscription: {str(e)}")
        return jsonify({'error': 'Failed to create subscription. Please try again.'}), 500

@app.route('/api/subscriptions/<subscription_id>', methods=['GET'])
@login_required
def get_subscription(subscription_id):
    """Get subscription by ID"""
    subscription = Subscription.query.get(subscription_id)
    
    if not subscription:
        return jsonify({'error': 'Subscription not found'}), 404
    
    if subscription.user_id != current_user.id:
        return jsonify({'error': 'Forbidden'}), 403
    
    return jsonify(subscription.to_dict())

@app.route('/api/subscriptions/<subscription_id>', methods=['PUT'])
@login_required
def update_subscription(subscription_id):
    """Update subscription"""
    subscription = Subscription.query.get(subscription_id)
    
    if not subscription:
        return jsonify({'error': 'Subscription not found'}), 404
    
    if subscription.user_id != current_user.id:
        return jsonify({'error': 'Forbidden'}), 403
    
    data = request.get_json()
    
    # Validate and update fields
    if 'name' in data:
        name = data['name'].strip()
        if len(name) < 1 or len(name) > 255:
            return jsonify({'error': 'Name must be between 1 and 255 characters'}), 400
        subscription.name = name
    
    if 'cost' in data:
        try:
            cost = float(data['cost'])
            if cost <= 0:
                return jsonify({'error': 'Cost must be positive'}), 400
            if round(cost, 2) != cost:
                return jsonify({'error': 'Cost can have maximum 2 decimal places'}), 400
            subscription.cost = cost
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid cost format'}), 400
    
    if 'currency' in data:
        valid_currencies = ['RUB', 'USD', 'EUR']
        if data['currency'] not in valid_currencies:
            return jsonify({'error': f'Currency must be one of: {", ".join(valid_currencies)}'}), 400
        subscription.currency = data['currency']
    
    if 'billing_period' in data:
        valid_periods = ['weekly', 'monthly', 'quarterly', 'yearly']
        if data['billing_period'] not in valid_periods:
            return jsonify({'error': f'Billing period must be one of: {", ".join(valid_periods)}'}), 400
        subscription.billing_period = data['billing_period']
    
    if 'start_date' in data:
        try:
            start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
            max_future_date = date.today() + timedelta(days=365)
            if start_date > max_future_date:
                return jsonify({'error': 'Start date cannot be more than 1 year in the future'}), 400
            subscription.start_date = start_date
        except ValueError:
            return jsonify({'error': 'Invalid start date format. Use YYYY-MM-DD'}), 400
    
    if 'category' in data:
        valid_categories = ['Entertainment', 'Software', 'Education', 'Health', 'Finance', 'Other']
        if data['category'] not in valid_categories:
            return jsonify({'error': f'Category must be one of: {", ".join(valid_categories)}'}), 400
        subscription.category = data['category']
    
    if 'notes' in data:
        notes = data['notes'].strip()
        if len(notes) > 1000:
            return jsonify({'error': 'Notes cannot exceed 1000 characters'}), 400
        subscription.notes = notes
    
    if 'payment_url' in data:
        payment_url = data['payment_url'].strip()
        if payment_url:
            if len(payment_url) > 500:
                return jsonify({'error': 'Payment URL cannot exceed 500 characters'}), 400
            if not payment_url.startswith(('http://', 'https://')):
                return jsonify({'error': 'Payment URL must start with http:// or https://'}), 400
        subscription.payment_url = payment_url if payment_url else None
    
    if 'is_active' in data:
        subscription.is_active = data['is_active']
    
    # Recalculate next billing date if start_date or billing_period changed
    if 'start_date' in data or 'billing_period' in data:
        subscription.next_billing_date = calculate_next_billing_date(
            subscription.start_date, 
            subscription.billing_period
        )
    
    subscription.updated_at = datetime.utcnow()
    
    try:
        db.session.commit()
        app.logger.info(f"Subscription updated: user_id={current_user.id}, subscription_id={subscription.id}")
        return jsonify(subscription.to_dict())
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating subscription: {str(e)}")
        return jsonify({'error': 'Failed to update subscription'}), 500

@app.route('/api/subscriptions/<subscription_id>', methods=['DELETE'])
@login_required
def delete_subscription(subscription_id):
    """Delete subscription"""
    subscription = Subscription.query.get(subscription_id)
    
    if not subscription:
        return jsonify({'error': 'Subscription not found'}), 404
    
    if subscription.user_id != current_user.id:
        return jsonify({'error': 'Forbidden'}), 403
    
    db.session.delete(subscription)
    db.session.commit()
    
    return jsonify({'message': 'Subscription deleted'})

# ============================================================================
# ANALYTICS ROUTES
# ============================================================================

def normalize_to_monthly(cost, billing_period):
    """Normalize cost to monthly equivalent"""
    if billing_period == 'weekly':
        return cost * 52 / 12
    elif billing_period == 'monthly':
        return cost
    elif billing_period == 'quarterly':
        return cost / 3
    elif billing_period == 'yearly':
        return cost / 12
    return cost

@app.route('/api/analytics/summary', methods=['GET'])
@login_required
def analytics_summary():
    """Get overall spending summary"""
    subscriptions = Subscription.query.filter_by(user_id=current_user.id, is_active=True).all()
    
    total_monthly = sum(normalize_to_monthly(sub.cost, sub.billing_period) for sub in subscriptions)
    total_yearly = total_monthly * 12
    
    return jsonify({
        'total_monthly': round(total_monthly, 2),
        'total_yearly': round(total_yearly, 2),
        'subscription_count': len(subscriptions),
        'average_monthly': round(total_monthly / len(subscriptions), 2) if subscriptions else 0
    })

@app.route('/api/analytics/by-category', methods=['GET'])
@login_required
def analytics_by_category():
    """Get spending by category"""
    subscriptions = Subscription.query.filter_by(user_id=current_user.id, is_active=True).all()
    
    category_totals = {}
    for sub in subscriptions:
        monthly_cost = normalize_to_monthly(sub.cost, sub.billing_period)
        category_totals[sub.category] = category_totals.get(sub.category, 0) + monthly_cost
    
    # Format for Chart.js
    labels = list(category_totals.keys())
    data = [round(v, 2) for v in category_totals.values()]
    
    return jsonify({
        'labels': labels,
        'datasets': [{
            'data': data,
            'backgroundColor': ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40']
        }]
    })

@app.route('/api/analytics/timeline', methods=['GET'])
@login_required
def analytics_timeline():
    """Get spending over time (last 12 months)"""
    subscriptions = Subscription.query.filter_by(user_id=current_user.id, is_active=True).all()
    
    # Calculate monthly expenses for last 12 months
    months = []
    data = []
    
    for i in range(12):
        month_date = date.today() - relativedelta(months=11-i)
        months.append(month_date.strftime('%b %Y'))
        
        # Calculate total for this month
        month_total = sum(normalize_to_monthly(sub.cost, sub.billing_period) 
                         for sub in subscriptions if sub.start_date <= month_date)
        data.append(round(month_total, 2))
    
    return jsonify({
        'labels': months,
        'datasets': [{
            'label': 'Monthly Expenses',
            'data': data,
            'borderColor': '#7B2FDA',
            'backgroundColor': 'rgba(123, 47, 218, 0.1)'
        }]
    })

@app.route('/api/analytics/top-expenses', methods=['GET'])
@login_required
def analytics_top_expenses():
    """Get most expensive subscriptions"""
    subscriptions = Subscription.query.filter_by(user_id=current_user.id, is_active=True).all()
    
    # Sort by monthly cost
    sorted_subs = sorted(subscriptions, 
                        key=lambda s: normalize_to_monthly(s.cost, s.billing_period), 
                        reverse=True)
    
    return jsonify([{
        'name': sub.name,
        'cost': sub.cost,
        'billing_period': sub.billing_period,
        'monthly_cost': round(normalize_to_monthly(sub.cost, sub.billing_period), 2),
        'category': sub.category
    } for sub in sorted_subs[:10]])

# ============================================================================
# NOTIFICATION ROUTES
# ============================================================================

def generate_notifications():
    """Generate notifications for upcoming billing dates"""
    today = date.today()
    
    # Get all active subscriptions
    subscriptions = Subscription.query.filter_by(is_active=True).all()
    
    for subscription in subscriptions:
        days_until_billing = (subscription.next_billing_date - today).days
        
        # Create notification 3 days before
        if days_until_billing == 3:
            existing = Notification.query.filter_by(
                subscription_id=subscription.id,
                notification_type='billing_reminder_3d'
            ).first()
            
            if not existing:
                notification = Notification(
                    user_id=subscription.user_id,
                    subscription_id=subscription.id,
                    message=f"{subscription.name} will charge ${subscription.cost} in 3 days",
                    notification_type='billing_reminder_3d'
                )
                db.session.add(notification)
        
        # Create notification 1 day before
        if days_until_billing == 1:
            existing = Notification.query.filter_by(
                subscription_id=subscription.id,
                notification_type='billing_reminder_1d'
            ).first()
            
            if not existing:
                notification = Notification(
                    user_id=subscription.user_id,
                    subscription_id=subscription.id,
                    message=f"{subscription.name} will charge ${subscription.cost} tomorrow",
                    notification_type='billing_reminder_1d'
                )
                db.session.add(notification)
    
    db.session.commit()

@app.route('/api/notifications', methods=['GET'])
@login_required
def get_notifications():
    """Get user notifications"""
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    return jsonify([notif.to_dict() for notif in notifications])

@app.route('/api/notifications/<notification_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Mark notification as read"""
    notification = Notification.query.get(notification_id)
    
    if not notification or notification.user_id != current_user.id:
        return jsonify({'error': 'Notification not found'}), 404
    
    notification.is_read = True
    db.session.commit()
    
    return jsonify(notification.to_dict())

@app.route('/api/notifications/<notification_id>', methods=['DELETE'])
@login_required
def delete_notification(notification_id):
    """Delete notification"""
    notification = Notification.query.get(notification_id)
    
    if not notification or notification.user_id != current_user.id:
        return jsonify({'error': 'Notification not found'}), 404
    
    db.session.delete(notification)
    db.session.commit()
    
    return jsonify({'message': 'Notification deleted'})

@app.route('/api/notifications/unread-count', methods=['GET'])
@login_required
def unread_notification_count():
    """Get unread notification count"""
    count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return jsonify({'count': count})

# ============================================================================
# FORECAST ROUTES
# ============================================================================

def is_billing_month(subscription, target_month):
    """Check if subscription bills in target month"""
    months_since_start = (target_month.year - subscription.start_date.year) * 12 + \
                         (target_month.month - subscription.start_date.month)
    
    if subscription.billing_period == 'monthly':
        return True
    elif subscription.billing_period == 'quarterly':
        return months_since_start % 3 == 0
    elif subscription.billing_period == 'yearly':
        return months_since_start % 12 == 0
    elif subscription.billing_period == 'weekly':
        return True  # Approximate as monthly
    return False

@app.route('/api/forecast/monthly', methods=['GET'])
@login_required
def forecast_monthly():
    """Get monthly forecast"""
    months = int(request.args.get('months', 12))
    subscriptions = Subscription.query.filter_by(user_id=current_user.id, is_active=True).all()
    
    forecast = []
    start_date = date.today()
    
    for month_offset in range(months):
        month_date = start_date + relativedelta(months=month_offset)
        month_total = 0
        
        for sub in subscriptions:
            if sub.start_date <= month_date and is_billing_month(sub, month_date):
                month_total += sub.cost
        
        forecast.append({
            'month': month_date.strftime('%Y-%m'),
            'total': round(month_total, 2),
            'subscriptions_count': len([s for s in subscriptions if s.start_date <= month_date])
        })
    
    return jsonify(forecast)

@app.route('/api/forecast/yearly', methods=['GET'])
@login_required
def forecast_yearly():
    """Get yearly forecast"""
    subscriptions = Subscription.query.filter_by(user_id=current_user.id, is_active=True).all()
    
    total_yearly = sum(normalize_to_monthly(sub.cost, sub.billing_period) * 12 for sub in subscriptions)
    
    return jsonify({
        'total_yearly': round(total_yearly, 2),
        'average_monthly': round(total_yearly / 12, 2)
    })

# ============================================================================
# RECOMMENDATION ROUTES
# ============================================================================

ALTERNATIVES = {
    'Entertainment': {
        'Netflix': [
            {'name': 'Disney+', 'cost': 7.99, 'features': 'Family content, Marvel, Star Wars'},
            {'name': 'Hulu', 'cost': 7.99, 'features': 'TV shows, movies'},
            {'name': 'Amazon Prime Video', 'cost': 8.99, 'features': 'Movies, TV shows, Prime benefits'}
        ],
        'Spotify': [
            {'name': 'Apple Music', 'cost': 10.99, 'features': 'Music streaming, lossless audio'},
            {'name': 'YouTube Music', 'cost': 9.99, 'features': 'Music streaming, YouTube integration'}
        ]
    },
    'Education': {
        'Coursera': [
            {'name': 'Udemy', 'cost': 19.99, 'features': 'One-time purchase courses'},
            {'name': 'Skillshare', 'cost': 13.99, 'features': 'Creative courses'}
        ]
    }
}

@app.route('/api/recommendations/<subscription_id>', methods=['GET'])
@login_required
def get_recommendations(subscription_id):
    """Get alternative service recommendations"""
    subscription = Subscription.query.get(subscription_id)
    
    if not subscription or subscription.user_id != current_user.id:
        return jsonify({'error': 'Subscription not found'}), 404
    
    category = subscription.category
    name = subscription.name
    
    alternatives = []
    
    if category in ALTERNATIVES and name in ALTERNATIVES[category]:
        for alt in ALTERNATIVES[category][name]:
            savings = subscription.cost - alt['cost']
            alternatives.append({
                'name': alt['name'],
                'cost': alt['cost'],
                'features': alt['features'],
                'savings': round(savings, 2)
            })
        
        # Sort by savings (highest first)
        alternatives.sort(key=lambda x: x['savings'], reverse=True)
    
    return jsonify(alternatives)

# ============================================================================
# PROFILE ROUTES
# ============================================================================

@app.route('/api/profile', methods=['GET'])
@login_required
def get_profile():
    """Get user profile data"""
    user = User.query.get(current_user.id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    subscriptions = Subscription.query.filter_by(user_id=user.id, is_active=True).all()
    total_monthly = sum(normalize_to_monthly(sub.cost, sub.billing_period) for sub in subscriptions)
    
    return jsonify({
        'name': user.name,
        'email': user.email,
        'picture': user.picture,
        'subscription_count': len(subscriptions),
        'total_monthly_expense': round(total_monthly, 2),
        'account_created': user.created_at.isoformat() if user.created_at else None
    })

@app.route('/api/profile', methods=['DELETE'])
@login_required
def delete_profile():
    """Delete user account and all data"""
    user = User.query.get(current_user.id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    db.session.delete(user)
    db.session.commit()
    
    logout_user()
    
    return jsonify({'message': 'Account deleted'})

# ============================================================================
# GMAIL IMPORT ROUTES
# ============================================================================

def parse_subscription_from_email(email_subject, email_body):
    """Parse subscription information from email - IMPROVED WITH KNOWN SERVICES"""
    
    # Known subscription services database
    KNOWN_SERVICES = {
        'netflix': {'name': 'Netflix', 'category': 'Развлечения'},
        'spotify': {'name': 'Spotify', 'category': 'Развлечения'},
        'youtube': {'name': 'YouTube Premium', 'category': 'Развлечения'},
        'яндекс': {'name': 'Яндекс Плюс', 'category': 'Развлечения'},
        'yandex': {'name': 'Yandex Plus', 'category': 'Развлечения'},
        'кинопоиск': {'name': 'Кинопоиск', 'category': 'Развлечения'},
        'apple music': {'name': 'Apple Music', 'category': 'Развлечения'},
        'apple': {'name': 'Apple', 'category': 'Софт'},
        'icloud': {'name': 'iCloud', 'category': 'Софт'},
        'google one': {'name': 'Google One', 'category': 'Софт'},
        'microsoft': {'name': 'Microsoft 365', 'category': 'Софт'},
        'office': {'name': 'Microsoft Office', 'category': 'Софт'},
        'adobe': {'name': 'Adobe', 'category': 'Софт'},
        'chatgpt': {'name': 'ChatGPT Plus', 'category': 'Софт'},
        'github': {'name': 'GitHub', 'category': 'Софт'},
        'dropbox': {'name': 'Dropbox', 'category': 'Софт'},
        'notion': {'name': 'Notion', 'category': 'Софт'},
    }
    
    # Patterns for extracting subscription info
    amount_patterns = [
        r'(?:₽|руб\.?|RUB)\s*(\d+(?:[.,]\d{2})?)',  # Рубли
        r'(\d+(?:[.,]\d{2})?)\s*(?:₽|руб\.?|RUB)',
        r'\$\s*(\d+(?:[.,]\d{2})?)',  # Доллары
        r'(\d+(?:[.,]\d{2})?)\s*(?:USD|\$)',
        r'€\s*(\d+(?:[.,]\d{2})?)',  # Евро
        r'(\d+(?:[.,]\d{2})?)\s*(?:EUR|€)',
        r'(\d+(?:[.,]\d{2})?)\s*(?:рубл|руб)',  # More flexible rubles
    ]
    
    period_patterns = {
        'monthly': r'(?:ежемесячн|месяц|monthly|month|per month|/month|в месяц)',
        'yearly': r'(?:ежегодн|год|yearly|annual|year|per year|/year|в год)',
        'weekly': r'(?:еженедельн|недел|weekly|week|per week|/week|в неделю)',
        'quarterly': r'(?:квартал|quarterly|quarter)'
    }
    
    # Ключевые слова для определения подписок - MORE FLEXIBLE
    subscription_keywords = [
        'subscription', 'подписк', 'membership', 'членство',
        'recurring', 'повторяющ', 'автоплатеж', 'autopay',
        'renewal', 'продление', 'payment', 'оплата',
        'invoice', 'счет', 'receipt', 'квитанц', 'чек',
        'premium', 'plus', 'плюс', 'pro'
    ]
    
    text = (email_subject + ' ' + email_body).lower()
    
    # Debug logging
    print(f"\n=== Parsing Email ===")
    print(f"Subject: {email_subject[:100]}")
    
    # Check if it's from a known service
    detected_service = None
    for service_key, service_info in KNOWN_SERVICES.items():
        if service_key in text:
            detected_service = service_info
            print(f"✓ Detected known service: {service_info['name']}")
            break
    
    # Проверяем, что это письмо о подписке - MORE FLEXIBLE
    is_subscription = any(keyword in text for keyword in subscription_keywords)
    
    # If from known service, more likely to be subscription
    if detected_service:
        is_subscription = True
    
    # If not subscription keywords, check if it has price + period
    if not is_subscription:
        has_price = any(re.search(pattern, text, re.IGNORECASE) for pattern in amount_patterns)
        has_period = any(re.search(pattern, text, re.IGNORECASE) for pattern, _ in period_patterns.items())
        is_subscription = has_price and has_period
    
    if not is_subscription:
        return None
    
    print("✓ Detected as subscription email")
    
    # Extract amount
    amount = None
    currency = 'RUB'  # Default
    
    for pattern in amount_patterns:
        match = re.search(pattern, email_subject + ' ' + email_body, re.IGNORECASE)
        if match:
            amount_str = match.group(1)
            try:
                amount = float(amount_str.replace(',', '.'))
                
                # Determine currency from pattern
                if '₽' in pattern or 'руб' in pattern or 'RUB' in pattern:
                    currency = 'RUB'
                elif '$' in pattern or 'USD' in pattern:
                    currency = 'USD'
                elif '€' in pattern or 'EUR' in pattern:
                    currency = 'EUR'
                
                print(f"✓ Found amount: {amount} {currency}")
                break
            except:
                continue
    
    if not amount:
        print("✗ No amount found")
        return None
    
    # Extract billing period
    billing_period = 'monthly'  # default
    for period, pattern in period_patterns.items():
        if re.search(pattern, text, re.IGNORECASE):
            billing_period = period
            print(f"✓ Found period: {billing_period}")
            break
    
    # Extract service name
    if detected_service:
        service_name = detected_service['name']
        category = detected_service['category']
    else:
        # Try to extract from subject
        subject_parts = re.split(r'[:\-–—]', email_subject)
        if subject_parts:
            service_name = subject_parts[0].strip()
        else:
            service_name = "Подписка"
        
        # Clean up service name
        service_name = re.sub(
            r'\b(payment|оплата|invoice|счет|receipt|квитанция|subscription|подписка|чек)\b',
            '', service_name, flags=re.IGNORECASE
        ).strip()
        
        if len(service_name) < 3:
            service_name = "Подписка"
        
        # Determine category
        category = 'Other'
        category_keywords = {
            'Развлечения': ['music', 'музык', 'video', 'видео', 'film', 'фильм', 'кино'],
            'Софт': ['cloud', 'облако', 'storage', 'хранилище', 'app', 'приложение'],
            'Образование': ['course', 'курс', 'learn', 'обучение'],
            'Фитнес': ['fitness', 'фитнес', 'gym', 'спорт'],
        }
        
        for cat, keywords in category_keywords.items():
            if any(kw in text for kw in keywords):
                category = cat
                break
    
    print(f"✓ Service: {service_name}, Category: {category}")
    print(f"=== Parse Complete ===\n")
    
    return {
        'name': service_name,
        'cost': amount,
        'currency': currency,
        'billing_period': billing_period,
        'category': category,
        'complete': amount is not None
    }

def get_gmail_service(user):
    """Create Gmail API service using user's OAuth token"""
    if not user.access_token:
        return None
    
    try:
        # Decrypt access token
        access_token = decrypt_token(user.access_token)
        refresh_token = decrypt_token(user.refresh_token) if user.refresh_token else None
        
        # Create credentials
        creds = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri='https://oauth2.googleapis.com/token',
            client_id=app.config['GOOGLE_CLIENT_ID'],
            client_secret=app.config['GOOGLE_CLIENT_SECRET'],
            scopes=app.config['OAUTH_SCOPES']
        )
        
        # Build Gmail service
        service = build('gmail', 'v1', credentials=creds)
        return service
    except Exception as e:
        print(f"Error creating Gmail service: {e}")
        return None

def search_subscription_emails(service, max_results=50):
    """Search for subscription-related emails in Gmail - IMPROVED VERSION"""
    try:
        # Get ALL recent emails (last 90 days) - not just with keywords
        results = service.users().messages().list(
            userId='me',
            maxResults=max_results,
            q='newer_than:90d'  # All emails from last 90 days
        ).execute()
        
        messages = results.get('messages', [])
        
        return list(messages)[:max_results]
    
    except Exception as e:
        print(f"Error searching emails: {e}")
        return []

def get_email_content(service, message_id):
    """Get email subject and body"""
    try:
        message = service.users().messages().get(
            userId='me',
            id=message_id,
            format='full'
        ).execute()
        
        # Extract subject
        subject = ''
        headers = message['payload'].get('headers', [])
        for header in headers:
            if header['name'].lower() == 'subject':
                subject = header['value']
                break
        
        # Extract body
        body = ''
        
        def get_body_from_parts(parts):
            text = ''
            for part in parts:
                if part.get('mimeType') == 'text/plain':
                    data = part['body'].get('data', '')
                    if data:
                        text += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                elif part.get('mimeType') == 'text/html':
                    data = part['body'].get('data', '')
                    if data and not text:  # Use HTML only if no plain text
                        html = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                        # Simple HTML tag removal
                        text += re.sub(r'<[^>]+>', ' ', html)
                elif 'parts' in part:
                    text += get_body_from_parts(part['parts'])
            return text
        
        if 'parts' in message['payload']:
            body = get_body_from_parts(message['payload']['parts'])
        else:
            data = message['payload']['body'].get('data', '')
            if data:
                body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        
        return subject, body
    
    except Exception as e:
        print(f"Error getting email content: {e}")
        return '', ''

@app.route('/api/gmail/authorize', methods=['POST'])
@login_required
def gmail_authorize():
    """Request Gmail API access"""
    # For now, we'll use the existing OAuth token
    user = User.query.get(current_user.id)
    
    if not user.access_token:
        return jsonify({'error': 'No OAuth token found. Please login with Google first.'}), 400
    
    return jsonify({
        'message': 'Gmail access authorized',
        'status': 'ready'
    })

@app.route('/api/gmail/import', methods=['GET'])
@login_required
def gmail_import():
    """Import subscriptions from Gmail"""
    try:
        user = User.query.get(current_user.id)
        
        if not user.access_token:
            return jsonify({'error': 'No Gmail access. Please login with Google OAuth first.'}), 400
        
        # Create Gmail service
        service = get_gmail_service(user)
        if not service:
            return jsonify({'error': 'Failed to connect to Gmail API'}), 500
        
        # Search for subscription emails
        messages = search_subscription_emails(service, max_results=50)
        
        if not messages:
            return jsonify({
                'message': 'No subscription emails found',
                'imported_count': 0,
                'subscriptions': []
            })
        
        # Parse emails and extract subscriptions
        extracted_subscriptions = []
        seen_names = set()
        
        for message in messages:
            try:
                subject, body = get_email_content(service, message['id'])
                
                # Parse subscription info
                sub_info = parse_subscription_from_email(subject, body)
                
                if sub_info and sub_info['complete']:
                    # Avoid duplicates in extraction
                    name_lower = sub_info['name'].lower()
                    if name_lower not in seen_names:
                        seen_names.add(name_lower)
                        extracted_subscriptions.append(sub_info)
            except Exception as e:
                print(f"Error parsing email {message['id']}: {e}")
                continue
        
        # Save to database
        imported_count = 0
        saved_subscriptions = []
        
        for sub_data in extracted_subscriptions:
            # Check for duplicates in database
            existing = Subscription.query.filter_by(
                user_id=user.id,
                name=sub_data['name']
            ).first()
            
            if not existing:
                subscription = Subscription(
                    user_id=user.id,
                    name=sub_data['name'],
                    cost=sub_data['cost'],
                    currency='RUB',  # Default to RUB, can be improved
                    billing_period=sub_data['billing_period'],
                    category=sub_data['category'],
                    notes='Импортировано из Gmail',
                    start_date=date.today(),
                    next_billing_date=calculate_next_billing_date(date.today(), sub_data['billing_period']),
                    imported_from_gmail=True
                )
                db.session.add(subscription)
                imported_count += 1
                saved_subscriptions.append(sub_data)
        
        db.session.commit()
        
        return jsonify({
            'message': f'Successfully imported {imported_count} subscriptions from {len(messages)} emails',
            'imported_count': imported_count,
            'emails_scanned': len(messages),
            'subscriptions': saved_subscriptions
        })
    
    except Exception as e:
        return jsonify({'error': f'Gmail import failed: {str(e)}'}), 500

@app.route('/api/gmail/import/status', methods=['GET'])
@login_required
def gmail_import_status():
    """Check Gmail import status"""
    user = User.query.get(current_user.id)
    
    has_gmail_access = user.access_token is not None
    imported_count = Subscription.query.filter_by(user_id=user.id, imported_from_gmail=True).count()
    
    return jsonify({
        'status': 'ready' if has_gmail_access else 'not_authorized',
        'has_access': has_gmail_access,
        'imported_subscriptions': imported_count
    })

@app.route('/api/gmail/test-search', methods=['GET'])
@login_required
def test_gmail_search():
    """Test Gmail search to see what emails are found"""
    try:
        user = User.query.get(current_user.id)
        
        if not user.access_token:
            return jsonify({
                'error': 'No Gmail access',
                'message': 'Нужно войти через Google заново. Нажми кнопку Gmail вверху.',
                'has_token': False
            }), 400
        
        # Try to decrypt token
        try:
            decrypted_token = decrypt_token(user.access_token)
            if not decrypted_token:
                return jsonify({
                    'error': 'Invalid token',
                    'message': 'Токен поврежден. Войди через Google заново.',
                    'has_token': True,
                    'token_valid': False
                }), 400
        except Exception as e:
            return jsonify({
                'error': 'Token decryption failed',
                'message': f'Ошибка расшифровки токена: {str(e)}. Войди заново.',
                'has_token': True,
                'token_valid': False
            }), 400
        
        service = get_gmail_service(user)
        if not service:
            return jsonify({
                'error': 'Failed to create Gmail service',
                'message': 'Не удалось подключиться к Gmail API. Войди заново.',
                'has_token': True,
                'service_created': False
            }), 500
        
        # Search for ALL recent emails (last 7 days)
        results = service.users().messages().list(
            userId='me',
            maxResults=20,
            q='newer_than:7d'
        ).execute()
        
        messages = results.get('messages', [])
        
        email_details = []
        for msg in messages[:10]:  # Check first 10
            try:
                message = service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='full'
                ).execute()
                
                # Get subject
                subject = ''
                headers = message['payload'].get('headers', [])
                for header in headers:
                    if header['name'].lower() == 'subject':
                        subject = header['value']
                        break
                
                email_details.append({
                    'id': msg['id'],
                    'subject': subject
                })
            except:
                continue
        
        return jsonify({
            'success': True,
            'total_found': len(messages),
            'emails': email_details,
            'has_token': True,
            'token_valid': True,
            'service_created': True
        })
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'message': f'Ошибка: {str(e)}'
        }), 500

# ============================================================================
# YANDEX & MAIL.RU IMPORT ROUTES
# ============================================================================

@app.route('/api/subscriptions/refresh-all', methods=['POST'])
@login_required
def refresh_all_subscriptions():
    """Refresh subscriptions from all connected providers - SHOW ALL EMAILS"""
    try:
        user = User.query.get(current_user.id)
        
        results = {
            'gmail': {'checked': False, 'emails': [], 'error': None},
            'yandex': {'checked': False, 'emails': [], 'error': None},
            'mailru': {'checked': False, 'emails': [], 'error': None}
        }
        
        # Check Gmail (if Google OAuth connected)
        if user.google_id and user.access_token:
            results['gmail']['checked'] = True
            try:
                service = get_gmail_service(user)
                if service:
                    # Get last 50 emails from ALL folders (including sent)
                    messages_result = service.users().messages().list(
                        userId='me',
                        maxResults=50,
                        q='newer_than:30d'  # All emails from last 30 days
                    ).execute()
                    
                    messages = messages_result.get('messages', [])
                    
                    for msg in messages:
                        try:
                            message = service.users().messages().get(
                                userId='me',
                                id=msg['id'],
                                format='full'
                            ).execute()
                            
                            # Get subject and sender
                            subject = ''
                            sender = ''
                            headers = message['payload'].get('headers', [])
                            
                            print(f"\n=== Email {msg['id']} ===")
                            print(f"Headers count: {len(headers)}")
                            
                            for header in headers:
                                header_name = header.get('name', '').lower()
                                header_value = header.get('value', '')
                                
                                if header_name == 'subject':
                                    subject = header_value
                                    print(f"Found subject: {subject}")
                                elif header_name == 'from':
                                    sender = header_value
                                    print(f"Found sender: {sender}")
                            
                            # Use sender as fallback if no subject
                            if not subject:
                                subject = f"(Без темы от {sender})" if sender else "(Без темы)"
                            
                            if not sender:
                                sender = "(Неизвестный отправитель)"
                            
                            results['gmail']['emails'].append({
                                'id': msg['id'],
                                'subject': subject,
                                'sender': sender
                            })
                            
                            print(f"Added email: {subject[:50]}")
                            
                        except Exception as e:
                            print(f"Error processing message {msg.get('id', 'unknown')}: {e}")
                            continue
            except Exception as e:
                results['gmail']['error'] = str(e)
        
        # Yandex - note about OAuth limitation
        if user.yandex_id:
            results['yandex']['checked'] = True
            results['yandex']['error'] = 'Yandex OAuth не дает доступ к почте. Используй кнопку Yandex для входа через IMAP (будет добавлено позже)'
        
        return jsonify({
            'success': True,
            'results': results,
            'message': f'Найдено писем: Gmail={len(results["gmail"]["emails"])}'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/email/import', methods=['POST'])
@login_required
def email_import():
    """Import subscriptions from Yandex or Mail.ru"""
    try:
        data = request.get_json()
        
        provider = data.get('provider')  # 'yandex' or 'mailru'
        email_address = data.get('email')
        password = data.get('password')
        
        if not provider or not email_address or not password:
            return jsonify({'error': 'Provider, email and password are required'}), 400
        
        if provider not in ['yandex', 'mailru']:
            return jsonify({'error': 'Invalid provider. Use "yandex" or "mailru"'}), 400
        
        # Import subscriptions
        result = import_from_email(provider, email_address, password, max_results=50)
        
        if 'error' in result:
            return jsonify({'error': result['error']}), 500
        
        subscriptions = result.get('subscriptions', [])
        
        if not subscriptions:
            return jsonify({
                'message': 'No subscription emails found',
                'imported_count': 0,
                'provider': provider
            })
        
        # Save to database
        user = User.query.get(current_user.id)
        imported_count = 0
        saved_subscriptions = []
        
        for sub_data in subscriptions:
            # Check for duplicates
            existing = Subscription.query.filter_by(
                user_id=user.id,
                name=sub_data['name']
            ).first()
            
            if not existing:
                subscription = Subscription(
                    user_id=user.id,
                    name=sub_data['name'],
                    cost=sub_data['cost'],
                    currency=sub_data.get('currency', 'RUB'),
                    billing_period=sub_data['billing_period'],
                    category=sub_data['category'],
                    notes=f'Импортировано из {provider.capitalize()}',
                    start_date=date.today(),
                    next_billing_date=calculate_next_billing_date(date.today(), sub_data['billing_period']),
                    imported_from_gmail=False  # Different source
                )
                db.session.add(subscription)
                imported_count += 1
                saved_subscriptions.append(sub_data)
        
        db.session.commit()
        
        return jsonify({
            'message': f'Successfully imported {imported_count} subscriptions from {provider.capitalize()}',
            'imported_count': imported_count,
            'provider': provider,
            'subscriptions': saved_subscriptions
        })
    
    except Exception as e:
        return jsonify({'error': f'Email import failed: {str(e)}'}), 500

@app.route('/api/email/test-connection', methods=['POST'])
@login_required
def test_email_connection():
    """Test email connection without importing"""
    try:
        data = request.get_json()
        
        provider = data.get('provider')
        email_address = data.get('email')
        password = data.get('password')
        
        if not provider or not email_address or not password:
            return jsonify({'error': 'Provider, email and password are required'}), 400
        
        if provider not in ['yandex', 'mailru']:
            return jsonify({'error': 'Invalid provider'}), 400
        
        # Test connection
        from email_import import YandexImporter, MailRuImporter
        
        if provider == 'yandex':
            importer = YandexImporter(email_address, password)
        else:
            importer = MailRuImporter(email_address, password)
        
        success = importer.connect()
        importer.disconnect()
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Successfully connected to {provider.capitalize()}'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to connect. Check your credentials.'
            }), 401
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

@app.cli.command()
def init_db():
    """Initialize database"""
    db.create_all()
    print('Database initialized!')

@app.cli.command()
def generate_notifs():
    """Generate notifications (run daily)"""
    generate_notifications()
    print('Notifications generated!')

# ============================================================================
# RUN APPLICATION
# ============================================================================

# ============================================================================
# MOBILE API (JWT-based, prefix /mobile)
# ============================================================================

def _jwt_b64(data):
    return base64.urlsafe_b64encode(json.dumps(data, separators=(',',':')).encode()).rstrip(b'=').decode()

def _jwt_b64_decode(s):
    s += '=' * (4 - len(s) % 4)
    return json.loads(base64.urlsafe_b64decode(s))

def make_jwt(user_id):
    header = _jwt_b64({'alg': 'HS256', 'typ': 'JWT'})
    payload = _jwt_b64({'user_id': user_id, 'exp': int(time.time()) + 30 * 86400})
    sig_input = f'{header}.{payload}'.encode()
    sig = hmac.new(app.config['SECRET_KEY'].encode(), sig_input, hashlib.sha256).digest()
    signature = base64.urlsafe_b64encode(sig).rstrip(b'=').decode()
    return f'{header}.{payload}.{signature}'

def verify_jwt(token):
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        header, payload, signature = parts
        sig_input = f'{header}.{payload}'.encode()
        expected_sig = base64.urlsafe_b64encode(
            hmac.new(app.config['SECRET_KEY'].encode(), sig_input, hashlib.sha256).digest()
        ).rstrip(b'=').decode()
        if not hmac.compare_digest(signature, expected_sig):
            return None
        data = _jwt_b64_decode(payload)
        if data.get('exp', 0) < int(time.time()):
            return None
        return data
    except Exception:
        return None

def mobile_jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'Token required'}), 401
        data = verify_jwt(token)
        if not data:
            return jsonify({'error': 'Invalid or expired token'}), 401
        user = User.query.get(data['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 401
        request.mobile_user = user
        return f(*args, **kwargs)
    return decorated


@app.route('/mobile/auth/login', methods=['POST'])
def mobile_login():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email и пароль обязательны'}), 400
    user = User.query.filter_by(email=data['email']).first()
    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Неверный email или пароль'}), 401
    token = make_jwt(user.id)
    return jsonify({'token': token, 'user': user.to_dict()})


@app.route('/mobile/auth/register', methods=['POST'])
def mobile_register():
    import smtplib, random, string
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    data = request.get_json()
    print(f"[REGISTER] Запрос: {data.get('email')}, {data.get('name')}")

    if not data or not data.get('email') or not data.get('password') or not data.get('name'):
        return jsonify({'error': 'Email, пароль и имя обязательны'}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Пользователь с таким email уже существует'}), 400

    # Генерируем 6-значный код
    code = ''.join(random.choices(string.digits, k=6))
    expires_at = datetime.utcnow() + timedelta(minutes=10)

    # Удаляем старые коды для этого email
    from models import EmailVerificationCode
    EmailVerificationCode.query.filter_by(email=data['email']).delete()

    # Сохраняем pending-регистрацию
    import json as _json
    pending = EmailVerificationCode(
        email=data['email'],
        code=code,
        expires_at=expires_at,
        user_data=_json.dumps({'email': data['email'], 'password': data['password'], 'name': data['name']})
    )
    db.session.add(pending)
    db.session.commit()

    # Отправляем письмо
    try:
        smtp_server = 'smtp.gmail.com'
        smtp_port = 587
        sender_email = 'truealex2011@gmail.com'
        sender_password = 'tkrp nozl ygre uxtv'

        print(f"[REGISTER] Отправляем письмо на {data['email']} через {smtp_server}:{smtp_port} от {sender_email}")

        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Код подтверждения NeoSync'
        msg['From'] = sender_email
        msg['To'] = data['email']
        html = f"""
        <div style="font-family:Arial,sans-serif;background:#0f0f0f;color:white;padding:30px;border-radius:12px;max-width:500px">
          <h2 style="color:#a855f7">NeoSync — подтверждение регистрации</h2>
          <p>Привет, <b>{data['name']}</b>!</p>
          <p>Твой код подтверждения:</p>
          <div style="font-size:36px;font-weight:900;color:#a855f7;letter-spacing:8px;text-align:center;padding:20px;background:#1a1a1a;border-radius:8px;margin:20px 0">{code}</div>
          <p style="color:#888;font-size:13px">Код действителен 10 минут. Если ты не регистрировался — просто проигнорируй это письмо.</p>
        </div>
        """
        msg.attach(MIMEText(html, 'html'))

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, data['email'], msg.as_string())

        print(f"[REGISTER] Письмо отправлено! Код: {code}")
    except Exception as e:
        print(f"[REGISTER] Ошибка отправки письма: {e}")
        print(f"[REGISTER] === FALLBACK === Код для {data['email']}: {code} ===")

    return jsonify({'success': True, 'message': 'Код подтверждения отправлен на email'}), 200


@app.route('/mobile/auth/verify-email', methods=['POST'])
def mobile_verify_email():
    import json as _json
    data = request.get_json()
    email = data.get('email', '')
    code = data.get('code', '')

    print(f"[VERIFY] email={email} code={code}")

    if not email or not code:
        return jsonify({'error': 'Email и код обязательны'}), 400

    from models import EmailVerificationCode
    record = EmailVerificationCode.query.filter_by(email=email, code=code).first()

    if not record:
        print(f"[VERIFY] Код не найден для {email}")
        return jsonify({'error': 'Неверный код подтверждения'}), 400

    if datetime.utcnow() > record.expires_at:
        print(f"[VERIFY] Код истёк для {email}")
        db.session.delete(record)
        db.session.commit()
        return jsonify({'error': 'Код истёк, запросите новый'}), 400

    # Создаём пользователя
    user_data = _json.loads(record.user_data)
    print(f"[VERIFY] Создаём пользователя: {user_data['email']}")

    if User.query.filter_by(email=user_data['email']).first():
        db.session.delete(record)
        db.session.commit()
        return jsonify({'error': 'Пользователь уже существует'}), 400

    user = User(email=user_data['email'], name=user_data['name'])
    user.set_password(user_data['password'])
    db.session.add(user)
    db.session.delete(record)
    db.session.commit()

    token = make_jwt(user.id)
    print(f"[VERIFY] Пользователь создан, id={user.id}")
    return jsonify({'token': token, 'user': user.to_dict()}), 201


@app.route('/mobile/auth/me', methods=['GET'])
@mobile_jwt_required
def mobile_me():
    return jsonify(request.mobile_user.to_dict())


@app.route('/mobile/subscriptions', methods=['GET'])
@mobile_jwt_required
def mobile_get_subscriptions():
    subs = Subscription.query.filter_by(user_id=request.mobile_user.id).all()
    return jsonify([s.to_dict() for s in subs])


@app.route('/mobile/subscriptions', methods=['POST'])
@mobile_jwt_required
def mobile_create_subscription():
    data = request.get_json()
    if not data or not data.get('name') or not data.get('cost') or not data.get('billing_period'):
        return jsonify({'error': 'Обязательные поля: name, cost, billing_period'}), 400
    try:
        cost = float(data['cost'])
        start_date = datetime.strptime(data.get('start_date', date.today().isoformat()), '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return jsonify({'error': 'Неверный формат данных'}), 400

    next_billing = calculate_next_billing_date(start_date, data['billing_period'])
    sub = Subscription(
        user_id=request.mobile_user.id,
        name=data['name'].strip(),
        cost=cost,
        currency=data.get('currency', 'RUB'),
        billing_period=data['billing_period'],
        start_date=start_date,
        next_billing_date=next_billing,
        category=data.get('category', 'Other'),
        notes=data.get('notes', ''),
        payment_url=data.get('payment_url'),
        is_active=data.get('is_active', True),
        manually_added=True
    )
    db.session.add(sub)
    db.session.commit()
    return jsonify(sub.to_dict()), 201


@app.route('/mobile/subscriptions/<sub_id>', methods=['GET'])
@mobile_jwt_required
def mobile_get_subscription(sub_id):
    sub = Subscription.query.get(sub_id)
    if not sub or sub.user_id != request.mobile_user.id:
        return jsonify({'error': 'Не найдено'}), 404
    return jsonify(sub.to_dict())


@app.route('/mobile/subscriptions/<sub_id>', methods=['PUT'])
@mobile_jwt_required
def mobile_update_subscription(sub_id):
    sub = Subscription.query.get(sub_id)
    if not sub or sub.user_id != request.mobile_user.id:
        return jsonify({'error': 'Не найдено'}), 404
    data = request.get_json()
    if 'name' in data: sub.name = data['name'].strip()
    if 'cost' in data: sub.cost = float(data['cost'])
    if 'currency' in data: sub.currency = data['currency']
    if 'billing_period' in data: sub.billing_period = data['billing_period']
    if 'category' in data: sub.category = data['category']
    if 'notes' in data: sub.notes = data['notes']
    if 'payment_url' in data: sub.payment_url = data['payment_url']
    if 'is_active' in data: sub.is_active = data['is_active']
    if 'start_date' in data:
        sub.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
    sub.next_billing_date = calculate_next_billing_date(sub.start_date, sub.billing_period)
    sub.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify(sub.to_dict())


@app.route('/mobile/subscriptions/<sub_id>', methods=['DELETE'])
@mobile_jwt_required
def mobile_delete_subscription(sub_id):
    sub = Subscription.query.get(sub_id)
    if not sub or sub.user_id != request.mobile_user.id:
        return jsonify({'error': 'Не найдено'}), 404
    db.session.delete(sub)
    db.session.commit()
    return jsonify({'message': 'Удалено'})


@app.route('/mobile/analytics/summary', methods=['GET'])
@mobile_jwt_required
def mobile_analytics_summary():
    subs = Subscription.query.filter_by(user_id=request.mobile_user.id, is_active=True).all()
    rates = {'RUB': 1, 'USD': 90, 'EUR': 100}

    def to_monthly_rub(s):
        rate = rates.get(s.currency, 1)
        return normalize_to_monthly(s.cost, s.billing_period) * rate

    total_monthly = sum(to_monthly_rub(s) for s in subs)
    return jsonify({
        'total_monthly': round(total_monthly, 2),
        'total_yearly': round(total_monthly * 12, 2),
        'subscription_count': len(subs),
        'average_monthly': round(total_monthly / len(subs), 2) if subs else 0
    })


@app.route('/mobile/analytics/by-category', methods=['GET'])
@mobile_jwt_required
def mobile_analytics_by_category():
    subs = Subscription.query.filter_by(user_id=request.mobile_user.id, is_active=True).all()
    totals = {}
    for s in subs:
        totals[s.category] = totals.get(s.category, 0) + normalize_to_monthly(s.cost, s.billing_period)
    return jsonify({
        'labels': list(totals.keys()),
        'data': [round(v, 2) for v in totals.values()]
    })


@app.route('/mobile/email/scan', methods=['POST'])
@mobile_jwt_required
def mobile_email_scan():
    """Сканирует почту и возвращает найденные подписки БЕЗ сохранения"""
    data = request.get_json()
    provider = data.get('provider', 'mailru')
    email_addr = data.get('email', '')
    password = data.get('password', '')

    print(f"[SCAN] Запрос получен: provider={provider}, email={email_addr}")

    if not email_addr or not password:
        print("[SCAN] Ошибка: email или пароль пустые")
        return jsonify({'error': 'Email и пароль обязательны'}), 400

    try:
        print(f"[SCAN] Вызываем import_from_email...")
        result = import_from_email(provider, email_addr, password)
        print(f"[SCAN] Результат: {result}")
        if 'error' in result and not result.get('success'):
            print(f"[SCAN] Ошибка от import_from_email: {result['error']}")
            return jsonify({'error': result['error']}), 400
        print(f"[SCAN] Успех, найдено подписок: {len(result.get('subscriptions', []))}")
        return jsonify({'success': True, 'subscriptions': result.get('subscriptions', [])})
    except Exception as e:
        print(f"[SCAN] EXCEPTION: {e}")
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/mobile/email/import', methods=['POST'])
@mobile_jwt_required
def mobile_email_import():
    """Сохраняет выбранные пользователем подписки в БД"""
    data = request.get_json()
    subscriptions = data.get('subscriptions', [])

    if not subscriptions:
        return jsonify({'error': 'Нет подписок для импорта'}), 400

    imported_count = 0
    try:
        for sub_data in subscriptions:
            if not sub_data.get('cost') or not sub_data.get('name'):
                continue
            try:
                start_date = date.today()
                next_billing = calculate_next_billing_date(start_date, sub_data.get('billing_period', 'monthly'))
                sub = Subscription(
                    user_id=request.mobile_user.id,
                    name=sub_data['name'],
                    cost=float(sub_data['cost']),
                    currency=sub_data.get('currency', 'RUB'),
                    billing_period=sub_data.get('billing_period', 'monthly'),
                    start_date=start_date,
                    next_billing_date=next_billing,
                    category=sub_data.get('category', 'Other'),
                    is_active=True,
                    manually_added=False,
                )
                db.session.add(sub)
                imported_count += 1
            except Exception:
                continue
        db.session.commit()
        return jsonify({'success': True, 'imported_count': imported_count})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
