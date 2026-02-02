from flask import Flask, jsonify
from app.config import Config
from app.extensions import db, migrate, jwt, cors
from app.utils.errors import AppError, error_response
from app.controllers.auth_controller import auth_bp
from app.controllers.health_controller import health_bp
from app.controllers.group_controller import group_bp
from app.controllers.expense_controller import expense_bp
from app.controllers.category_controller import category_bp
from app.controllers.budget_controller import budget_bp



def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, resources={
                  r"/*": {"origins": app.config["CORS_ORIGINS"]}}, supports_credentials=True)

    # Blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(group_bp)
    app.register_blueprint(expense_bp)
    app.register_blueprint(category_bp)
    app.register_blueprint(budget_bp)



    # Error handling
    @app.errorhandler(AppError)
    def handle_app_error(err: AppError):
        payload, code = error_response(
            err.message, err.status_code, err.details)
        return jsonify(payload), code

    @app.errorhandler(404)
    def handle_404(_):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def handle_500(err):
        return jsonify({"error": "Internal server error"}), 500

    return app
