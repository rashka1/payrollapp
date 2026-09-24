from flask import Blueprint, jsonify, request, render_template
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Employee
from sqlalchemy.exc import IntegrityError

employees_bp = Blueprint('employees', __name__)

@employees_bp.route('/employees')
@login_required
def list_employees():
    return render_template('employees.html', user=current_user.to_dict())

@employees_bp.route('/api/employees', methods=['GET'])
@login_required
def get_employees():
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    query  = Employee.query
    if search:
        query = query.filter(Employee.name.ilike(f'%{search}%'))
    if status:
        if status not in ['active', 'inactive']:
            return jsonify({'error': 'Status must be active or inactive'}), 400
        query = query.filter_by(status=status)
    return jsonify([e.to_dict() for e in query.order_by(Employee.name).all()])

@employees_bp.route('/api/employees/<int:id>', methods=['GET'])
@login_required
def get_employee(id):
    return jsonify(Employee.query.get_or_404(id).to_dict())

@employees_bp.route('/api/employees', methods=['POST'])
@login_required
def create_employee():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    name     = data.get('name', '').strip()
    email    = data.get('email', '').strip()
    position = data.get('position', '').strip()

    if not name:
        return jsonify({'error': 'Name is required'}), 400
    if len(name) > 100:
        return jsonify({'error': 'Name too long (max 100 characters)'}), 400
    if not email or '@' not in email:
        return jsonify({'error': 'Valid email is required'}), 400
    if len(email) > 150:
        return jsonify({'error': 'Email too long (max 150 characters)'}), 400
    if not position:
        return jsonify({'error': 'Position is required'}), 400
    if len(position) > 100:
        return jsonify({'error': 'Position too long (max 100 characters)'}), 400

    try:
        base_salary = float(data.get('base_salary', 0))
        bonus       = float(data.get('bonus', 0))
    except (ValueError, TypeError):
        return jsonify({'error': 'Salary and bonus must be numbers'}), 400

    if base_salary < 0:
        return jsonify({'error': 'Base salary cannot be negative'}), 400
    if bonus < 0:
        return jsonify({'error': 'Bonus cannot be negative'}), 400
    if base_salary > 9999999:
        return jsonify({'error': 'Base salary value is too large'}), 400

    status = data.get('status', 'active')
    if status not in ['active', 'inactive']:
        return jsonify({'error': 'Status must be active or inactive'}), 400

    try:
        emp = Employee(
            name        = name,
            email       = email,
            position    = position,
            base_salary = base_salary,
            bonus       = bonus,
            status      = status
        )
        db.session.add(emp)
        db.session.commit()
        return jsonify(emp.to_dict()), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Email already exists'}), 409

@employees_bp.route('/api/employees/<int:id>', methods=['PUT'])
@login_required
def update_employee(id):
    emp  = Employee.query.get_or_404(id)
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    name     = data.get('name', emp.name).strip()
    email    = data.get('email', emp.email).strip()
    position = data.get('position', emp.position).strip()

    if not name:
        return jsonify({'error': 'Name is required'}), 400
    if len(name) > 100:
        return jsonify({'error': 'Name too long (max 100 characters)'}), 400
    if not email or '@' not in email:
        return jsonify({'error': 'Valid email is required'}), 400
    if len(email) > 150:
        return jsonify({'error': 'Email too long (max 150 characters)'}), 400
    if not position:
        return jsonify({'error': 'Position is required'}), 400
    if len(position) > 100:
        return jsonify({'error': 'Position too long (max 100 characters)'}), 400

    try:
        base_salary = float(data.get('base_salary', emp.base_salary))
        bonus       = float(data.get('bonus', emp.bonus))
    except (ValueError, TypeError):
        return jsonify({'error': 'Salary and bonus must be numbers'}), 400

    if base_salary < 0:
        return jsonify({'error': 'Base salary cannot be negative'}), 400
    if bonus < 0:
        return jsonify({'error': 'Bonus cannot be negative'}), 400
    if base_salary > 9999999:
        return jsonify({'error': 'Base salary value is too large'}), 400

    status = data.get('status', emp.status)
    if status not in ['active', 'inactive']:
        return jsonify({'error': 'Status must be active or inactive'}), 400

    try:
        emp.name        = name
        emp.email       = email
        emp.position    = position
        emp.base_salary = base_salary
        emp.bonus       = bonus
        emp.status      = status
        db.session.commit()
        return jsonify(emp.to_dict())
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Email already exists'}), 409

@employees_bp.route('/api/employees/<int:id>', methods=['DELETE'])
@login_required
def delete_employee(id):
    emp = Employee.query.get_or_404(id)
    db.session.delete(emp)
    db.session.commit()
    return jsonify({'message': 'Employee deleted'})