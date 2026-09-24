from flask import Blueprint, jsonify, request, render_template
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Payroll, Employee
from sqlalchemy.exc import IntegrityError

payroll_bp = Blueprint('payroll', __name__)

@payroll_bp.route('/payroll')
@login_required
def payroll_page():
    return render_template('payroll.html', user=current_user.to_dict())

@payroll_bp.route('/api/payroll', methods=['GET'])
@login_required
def get_payroll():
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    query  = Payroll.query.join(Employee)
    if search:
        query = query.filter(Employee.name.ilike(f'%{search}%'))
    if status:
        if status not in ['pending', 'approved']:
            return jsonify({'error': 'Status must be pending or approved'}), 400
        query = query.filter(Payroll.status == status)
    records = query.order_by(Payroll.year.desc(), Payroll.month.desc()).all()
    return jsonify([p.to_dict() for p in records])

@payroll_bp.route('/api/payroll', methods=['POST'])
@login_required
def generate_payroll():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    employee_id = data.get('employee_id')
    if not employee_id:
        return jsonify({'error': 'Employee is required'}), 400

    try:
        month = int(data.get('month'))
        year  = int(data.get('year'))
    except (ValueError, TypeError):
        return jsonify({'error': 'Month and year must be numbers'}), 400

    if month < 1 or month > 12:
        return jsonify({'error': 'Month must be between 1 and 12'}), 400
    if year < 2000 or year > 2100:
        return jsonify({'error': 'Year must be between 2000 and 2100'}), 400

    emp = Employee.query.get_or_404(employee_id)

    if emp.status != 'active':
        return jsonify({'error': 'Cannot generate payroll for inactive employee'}), 400

    try:
        payroll = Payroll(
            employee_id  = emp.id,
            month        = month,
            year         = year,
            base_salary  = emp.base_salary,
            bonus        = emp.bonus,
            total_salary = emp.base_salary + emp.bonus,
            status       = 'pending'
        )
        db.session.add(payroll)
        db.session.commit()
        return jsonify(payroll.to_dict()), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': f'Payroll for this employee in {month}/{year} already exists'}), 409

@payroll_bp.route('/api/payroll/bulk', methods=['POST'])
@login_required
def bulk_generate_payroll():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    try:
        month = int(data.get('month'))
        year  = int(data.get('year'))
    except (ValueError, TypeError):
        return jsonify({'error': 'Month and year must be numbers'}), 400

    if month < 1 or month > 12:
        return jsonify({'error': 'Month must be between 1 and 12'}), 400
    if year < 2000 or year > 2100:
        return jsonify({'error': 'Year must be between 2000 and 2100'}), 400

    active = Employee.query.filter_by(status='active').all()
    if not active:
        return jsonify({'error': 'No active employees found'}), 400

    generated = []
    skipped   = []
    for emp in active:
        try:
            payroll = Payroll(
                employee_id  = emp.id,
                month        = month,
                year         = year,
                base_salary  = emp.base_salary,
                bonus        = emp.bonus,
                total_salary = emp.base_salary + emp.bonus,
                status       = 'pending'
            )
            db.session.add(payroll)
            db.session.commit()
            generated.append(emp.name)
        except IntegrityError:
            db.session.rollback()
            skipped.append(emp.name)

    return jsonify({
        'message':   f'Generated {len(generated)}, skipped {len(skipped)} (already exist)',
        'generated': generated,
        'skipped':   skipped
    }), 201

@payroll_bp.route('/api/payroll/<int:id>', methods=['PUT'])
@login_required
def update_payroll(id):
    payroll = Payroll.query.get_or_404(id)
    if payroll.status == 'approved':
        return jsonify({'error': 'Cannot edit an approved payroll record'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    try:
        base_salary = float(data.get('base_salary', payroll.base_salary))
        bonus       = float(data.get('bonus',       payroll.bonus))
    except (ValueError, TypeError):
        return jsonify({'error': 'Salary and bonus must be numbers'}), 400

    if base_salary < 0:
        return jsonify({'error': 'Base salary cannot be negative'}), 400
    if bonus < 0:
        return jsonify({'error': 'Bonus cannot be negative'}), 400

    payroll.base_salary  = base_salary
    payroll.bonus        = bonus
    payroll.total_salary = base_salary + bonus
    db.session.commit()
    return jsonify(payroll.to_dict())

@payroll_bp.route('/api/payroll/<int:id>', methods=['DELETE'])
@login_required
def delete_payroll(id):
    payroll = Payroll.query.get_or_404(id)
    if payroll.status == 'approved':
        return jsonify({'error': 'Cannot delete an approved payroll record'}), 403
    db.session.delete(payroll)
    db.session.commit()
    return jsonify({'message': 'Payroll record deleted'})

@payroll_bp.route('/api/payroll/<int:id>/approve', methods=['PUT'])
@login_required
def approve_payroll(id):
    if not current_user.is_admin():
        return jsonify({'error': 'Admin access required to approve payroll'}), 403
    payroll = Payroll.query.get_or_404(id)
    if payroll.status == 'approved':
        return jsonify({'error': 'Payroll is already approved'}), 400
    payroll.status = 'approved'
    db.session.commit()
    return jsonify(payroll.to_dict())