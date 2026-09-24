from app.extensions import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Flask-Login needs this to load a user from the session
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id         = db.Column(db.Integer, primary_key=True)
    username   = db.Column(db.String(80), unique=True, nullable=False)
    email      = db.Column(db.String(150), unique=True, nullable=False)
    password   = db.Column(db.String(256), nullable=False)
    role       = db.Column(db.String(20), default='user')  # 'admin' or 'user'
   
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def is_admin(self):
        return self.role == 'admin'

    def to_dict(self):
        return {
            'id':       self.id,
            'username': self.username,
            'email':    self.email,
            'role':     self.role
        }


class Employee(db.Model):
    __tablename__ = 'employees'

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), nullable=False)
    email       = db.Column(db.String(150), unique=True, nullable=False)
    position    = db.Column(db.String(100), nullable=False)
    base_salary = db.Column(db.Float, nullable=False)
    bonus       = db.Column(db.Float, default=0.0)
    status      = db.Column(db.String(20), default='active')  # 'active' or 'inactive'
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    payrolls = db.relationship('Payroll', backref='employee',
                               lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id':          self.id,
            'name':        self.name,
            'email':       self.email,
            'position':    self.position,
            'base_salary': self.base_salary,
            'bonus':       self.bonus,
            'status':      self.status
        }


class Payroll(db.Model):
    __tablename__ = 'payroll'

    id           = db.Column(db.Integer, primary_key=True)
    employee_id  = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    month        = db.Column(db.Integer, nullable=False)   # 1-12
    year         = db.Column(db.Integer, nullable=False)
    base_salary  = db.Column(db.Float, nullable=False)
    bonus        = db.Column(db.Float, default=0.0)
    total_salary = db.Column(db.Float, nullable=False)     # base + bonus
    status       = db.Column(db.String(20), default='pending')  # 'pending' or 'approved'
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    # Prevent duplicate payroll for same employee + same month + year
    __table_args__ = (
        db.UniqueConstraint('employee_id', 'month', 'year',
                            name='unique_employee_month_year'),
    )

    def to_dict(self):
        return {
            'id':           self.id,
            'employee_id':  self.employee_id,
            'employee':     self.employee.name,
            'month':        self.month,
            'year':         self.year,
            'base_salary':  self.base_salary,
            'bonus':        self.bonus,
            'total_salary': self.total_salary,
            'status':       self.status
        }