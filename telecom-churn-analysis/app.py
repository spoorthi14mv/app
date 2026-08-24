import os
from flask import Flask, jsonify, redirect, url_for
from config import Config
from extensions import db, csrf
from flask_wtf.csrf import CSRFError

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure necessary directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['MODELS_DIR'], exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'instance'), exist_ok=True)

    db.init_app(app)
    csrf.init_app(app)

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        return jsonify({"error": "CSRF token missing or invalid", "details": e.description}), 400

    @app.route('/')
    def index():
        return redirect(url_for('dashboard.index'))

    # Import and register blueprints
    from routes.dashboard import dashboard_bp
    from routes.data import data_bp
    from routes.analysis import analysis_bp
    from routes.prediction import prediction_bp
    from routes.insights import insights_bp
    from routes.reports import reports_bp

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
        print("Initialized the database.")

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
