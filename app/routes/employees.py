from flask import Blueprint, jsonify, request, render_template
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Employee
from sqlalchemy.exc import IntegrityError

employees_bp = Blueprint('employees', __name__)

# Serve the frontend
@employees_bp.route('/employees')
@login_required
def list_employees():
    return render_template('employees.html',
                           user=current_user.to_dict())

# GET all employees (with optional search)
@employees_bp.route('/api/employees', methods=['GET'])
@login_required
def get_employees():
    search = request.args.get('search', '')
    status = request.args.get('status', '')

    query = Employee.query
    if search:
        query = query.filter(Employee.name.ilike(f'%{search}%'))
    if status:
        query = query.filter_by(status=status)

    employees = query.order_by(Employee.name).all()
    return jsonify([e.to_dict() for e in employees])

# GET one employee
@employees_bp.route('/api/employees/<int:id>', methods=['GET'])
@login_required
def get_employee(id):
    emp = Employee.query.get_or_404(id)
    return jsonify(emp.to_dict())

# POST create employee
@employees_bp.route('/api/employees', methods=['POST'])
@login_required
def create_employee():
    data = request.get_json()
    try:
        emp = Employee(
            name=data['name'],
            email=data['email'],
            position=data['position'],
            base_salary=float(data['base_salary']),
            bonus=float(data.get('bonus', 0)),
            status=data.get('status', 'active')
        )
        db.session.add(emp)
        db.session.commit()
        return jsonify(emp.to_dict()), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Email already exists'}), 409

# PUT update employee
@employees_bp.route('/api/employees/<int:id>', methods=['PUT'])
@login_required
def update_employee(id):
    emp = Employee.query.get_or_404(id)
    data = request.get_json()
    emp.name        = data.get('name',        emp.name)
    emp.email       = data.get('email',       emp.email)
    emp.position    = data.get('position',    emp.position)
    emp.base_salary = float(data.get('base_salary', emp.base_salary))
    emp.bonus       = float(data.get('bonus',       emp.bonus))
    emp.status      = data.get('status',      emp.status)
    db.session.commit()
    return jsonify(emp.to_dict())

# DELETE employee
@employees_bp.route('/api/employees/<int:id>', methods=['DELETE'])
@login_required
def delete_employee(id):
    emp = Employee.query.get_or_404(id)
    db.session.delete(emp)
    db.session.commit()
    return jsonify({'message': 'Employee deleted'})