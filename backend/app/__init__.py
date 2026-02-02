from flask import Flask
from app.config import Config
from app.extensions import db, migrate, jwt, cors
from app.utils.responses import error_response
from app.utils.errors import AppError

# Controllers
from app.controllers.auth_controller import auth_bp
from app.controllers.group_controller import group_bp
from app.controllers.expense_controller import expense_bp
from app.controllers.category_controller import category_bp
from app.controllers.budget_controller import budget_bp
from app.controllers.health_controller import health_bp
from app.controllers.ai_controller import ai_bp



def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # -----------------------------
    # Initialize extensions
    # -----------------------------
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    cors.init_app(
        app,
        resources={r"/*": {"origins": app.config["CORS_ORIGINS"]}},
        supports_credentials=True,
    )

    # -----------------------------
    # Register blueprints
    # -----------------------------
    app.register_blueprint(auth_bp)
    app.register_blueprint(group_bp)
    app.register_blueprint(expense_bp)
    app.register_blueprint(category_bp)
    app.register_blueprint(budget_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(ai_bp)
    

    # -----------------------------
    # Global error handling
    # -----------------------------
    @app.errorhandler(AppError)
    def handle_app_error(err: AppError):
        return error_response(
            message=err.message,
            status=err.status,
            code=err.code,
        )

    @app.errorhandler(404)
    def not_found(_):
        return error_response("Not found", 404, "NOT_FOUND")

    @app.errorhandler(500)
    def server_error(err):
        app.logger.exception(err)
        return error_response("Internal server error", 500, "SERVER_ERROR")

    return app
