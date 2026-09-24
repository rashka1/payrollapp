from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from app.extensions import db
from werkzeug.security import generate_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('employees.list_employees'))
    if request.method == 'POST':
        data = request.get_json() or request.form
        username = data.get('username')
        password = data.get('password')
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

@auth_bp.route('/users', methods=['GET'])
@login_required
def list_users():
    if not current_user.is_admin():
        return jsonify({'error': 'Admin access required'}), 403
    users = User.query.all()
    return jsonify([u.to_dict() for u in users])

@auth_bp.route('/users', methods=['POST'])
@login_required
def create_user():
    if not current_user.is_admin():
        return jsonify({'error': 'Admin access required'}), 403
    data = request.get_json()
    user = User(username=data['username'], email=data['email'], role=data.get('role', 'user'))
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201

@auth_bp.route('/users-page')
@login_required
def users_page():
    if not current_user.is_admin():
        return redirect(url_for('employees.list_employees'))
    return render_template('users.html', user=current_user.to_dict())

@auth_bp.route('/users/<int:id>', methods=['PUT'])
@login_required
def update_user(id):
    if not current_user.is_admin():
        return jsonify({'error': 'Admin access required'}), 403
    user = User.query.get_or_404(id)
    data = request.get_json()
    user.username = data.get('username', user.username)
    user.email    = data.get('email',    user.email)
    user.role     = data.get('role',     user.role)
    if data.get('password'):
        user.set_password(data['password'])
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