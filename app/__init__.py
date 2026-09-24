from flask import Flask
from dotenv import load_dotenv
from app.extensions import db, login_manager
import os

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback-secret')

    db.init_app(app)
    login_manager.init_app(app)

    from app.routes.auth import auth_bp
    from app.routes.employees import employees_bp
    from app.routes.payroll import payroll_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(payroll_bp)

    with app.app_context():
        from app.models import User, Employee, Payroll
        db.create_all()
        create_admin()   # create default admin on first run

    return app


def create_admin():
    from app.models import User
    if not User.query.filter_by(role='admin').first():
        admin = User(username='admin', email='admin@payroll.com', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print('Default admin created: admin / admin123')