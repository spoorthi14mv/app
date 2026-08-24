import os
from flask import Flask
from config import Config
from models import db
from flask_login import LoginManager

# Initialize extensions
login = LoginManager()
login.login_view = 'auth.login'
login.login_message_category = 'info'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure necessary directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['MODELS_DIR'], exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'instance'), exist_ok=True)

    db.init_app(app)
    login.init_app(app)

    # Import and register blueprints
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.data import data_bp
    from routes.analysis import analysis_bp
    from routes.prediction import prediction_bp
    from routes.insights import insights_bp
    from routes.reports import reports_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(data_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(prediction_bp)
    app.register_blueprint(insights_bp)
    app.register_blueprint(reports_bp)

    @app.cli.command("init-db")
    def init_db_command():
        """Clear the existing data and create new tables."""
        db.create_all()
        # Initialize default admin user if not exists
        from models.user import User
        from werkzeug.security import generate_password_hash
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@telecom.com',
                password_hash=generate_password_hash('admin123')
            )
            db.session.add(admin)
            db.session.commit()
            print("Initialized default admin user (admin/admin123)")
        print("Initialized the database.")

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
