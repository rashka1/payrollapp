from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from app.extensions import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('employees.list_employees'))
    if request.method == 'POST':
        data = request.get_json() or request.form
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        username = data.get('username', '').strip()
        password = data.get('password', '')
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return jsonify({'message': 'Login successful', 'user': user.to_dict()})
        return jsonify({'error': 'Invalid username or password'}), 401
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/users-page')
@login_required
def users_page():
    if not current_user.is_admin():
        return redirect(url_for('employees.list_employees'))
    return render_template('users.html', user=current_user.to_dict())

@auth_bp.route('/users', methods=['GET'])
@login_required
def list_users():
    if not current_user.is_admin():
        return jsonify({'error': 'Admin access required'}), 403
    return jsonify([u.to_dict() for u in User.query.all()])

@auth_bp.route('/users', methods=['POST'])
@login_required
def create_user():
    if not current_user.is_admin():
        return jsonify({'error': 'Admin access required'}), 403
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    username = data.get('username', '').strip()
    email    = data.get('email', '').strip()
    password = data.get('password', '')
    role     = data.get('role', 'user')

    if not username:
        return jsonify({'error': 'Username is required'}), 400
    if len(username) > 80:
        return jsonify({'error': 'Username too long (max 80 characters)'}), 400
    if not email or '@' not in email:
        return jsonify({'error': 'Valid email is required'}), 400
    if not password:
        return jsonify({'error': 'Password is required'}), 400
    if len(password) < 4:
        return jsonify({'error': 'Password must be at least 4 characters'}), 400
    if role not in ['admin', 'user']:
        return jsonify({'error': 'Role must be admin or user'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 409
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already exists'}), 409

    user = User(username=username, email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201

@auth_bp.route('/users/<int:id>', methods=['PUT'])
@login_required
def update_user(id):
    if not current_user.is_admin():
        return jsonify({'error': 'Admin access required'}), 403
    user = User.query.get_or_404(id)
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    username = data.get('username', user.username).strip()
    email    = data.get('email',    user.email).strip()
    role     = data.get('role',     user.role)
    password = data.get('password', '')

    if not username:
        return jsonify({'error': 'Username is required'}), 400
    if not email or '@' not in email:
        return jsonify({'error': 'Valid email is required'}), 400
    if role not in ['admin', 'user']:
        return jsonify({'error': 'Role must be admin or user'}), 400
    if password and len(password) < 4:
        return jsonify({'error': 'Password must be at least 4 characters'}), 400

    existing = User.query.filter_by(username=username).first()
    if existing and existing.id != id:
        return jsonify({'error': 'Username already exists'}), 409
    existing_email = User.query.filter_by(email=email).first()
    if existing_email and existing_email.id != id:
        return jsonify({'error': 'Email already exists'}), 409

    user.username = username
    user.email    = email
    user.role     = role
    if password:
        user.set_password(password)
    db.session.commit()
    return jsonify(user.to_dict())

@auth_bp.route('/users/<int:id>', methods=['DELETE'])
@login_required
def delete_user(id):
    if not current_user.is_admin():
        return jsonify({'error': 'Admin access required'}), 403
    if id == current_user.id:
        return jsonify({'error': 'Cannot delete your own account'}), 400
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted'})