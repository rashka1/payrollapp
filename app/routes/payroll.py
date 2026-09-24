from flask import Blueprint, jsonify, request, render_template
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Payroll, Employee
from sqlalchemy.exc import IntegrityError

payroll_bp = Blueprint('payroll', __name__)

# Serve the frontend
@payroll_bp.route('/payroll')
@login_required
def payroll_page():
    return render_template('payroll.html', user=current_user.to_dict())

# GET all payroll records (with optional search)
@payroll_bp.route('/api/payroll', methods=['GET'])
@login_required
def get_payroll():
    search     = request.args.get('search', '')
    status     = request.args.get('status', '')
    month      = request.args.get('month', '')
    year       = request.args.get('year', '')

    query = Payroll.query.join(Employee)
    if search:
        query = query.filter(Employee.name.ilike(f'%{search}%'))
    if status:
        query = query.filter(Payroll.status == status)
    if month:
        query = query.filter(Payroll.month == int(month))
    if year:
        query = query.filter(Payroll.year == int(year))

    records = query.order_by(Payroll.year.desc(), Payroll.month.desc()).all()
    return jsonify([p.to_dict() for p in records])

# POST generate payroll for an employee
@payroll_bp.route('/api/payroll', methods=['POST'])
@login_required
def generate_payroll():
    data = request.get_json()
    employee_id = data.get('employee_id')
    month       = int(data.get('month'))
    year        = int(data.get('year'))

    # Rule 1: employee must exist
    emp = Employee.query.get_or_404(employee_id)

    # Rule 2: employee must be ACTIVE
    if emp.status != 'active':
        return jsonify({'error': 'Cannot generate payroll for inactive employee'}), 400

    # Rule 3: calculate total (never trust the frontend)
    base_salary  = emp.base_salary
    bonus        = emp.bonus
    total_salary = base_salary + bonus

    try:
        payroll = Payroll(
            employee_id  = emp.id,
            month        = month,
            year         = year,
            base_salary  = base_salary,
            bonus        = bonus,
            total_salary = total_salary,
            status       = 'pending'   # always starts as pending
        )
        db.session.add(payroll)
        db.session.commit()
        return jsonify(payroll.to_dict()), 201

    except IntegrityError:
        db.session.rollback()
        # Rule 4: duplicate blocked by UniqueConstraint
        return jsonify({'error': f'Payroll for this employee in {month}/{year} already exists'}), 409

# PUT update a payroll record
@payroll_bp.route('/api/payroll/<int:id>', methods=['PUT'])
@login_required
def update_payroll(id):
    payroll = Payroll.query.get_or_404(id)

    # Rule 5: cannot edit approved payroll
    if payroll.status == 'approved':
        return jsonify({'error': 'Cannot edit an approved payroll record'}), 403

    data = request.get_json()
    payroll.base_salary  = float(data.get('base_salary', payroll.base_salary))
    payroll.bonus        = float(data.get('bonus',       payroll.bonus))
    payroll.total_salary = payroll.base_salary + payroll.bonus  # recalculate
    db.session.commit()
    return jsonify(payroll.to_dict())

# DELETE a payroll record
@payroll_bp.route('/api/payroll/<int:id>', methods=['DELETE'])
@login_required
def delete_payroll(id):
    payroll = Payroll.query.get_or_404(id)

    # Rule 6: cannot delete approved payroll
    if payroll.status == 'approved':
        return jsonify({'error': 'Cannot delete an approved payroll record'}), 403

    db.session.delete(payroll)
    db.session.commit()
    return jsonify({'message': 'Payroll record deleted'})

# PUT approve payroll — ADMIN ONLY
@payroll_bp.route('/api/payroll/<int:id>/approve', methods=['PUT'])
@login_required
def approve_payroll(id):
    # Rule 7: only admin can approve
    if not current_user.is_admin():
        return jsonify({'error': 'Admin access required to approve payroll'}), 403

    payroll = Payroll.query.get_or_404(id)

    if payroll.status == 'approved':
        return jsonify({'error': 'Payroll is already approved'}), 400

    payroll.status = 'approved'
    db.session.commit()
    return jsonify(payroll.to_dict())