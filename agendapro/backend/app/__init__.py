import os

from flask import Flask, jsonify

from .core.config import get_config
from .core.errors import register_error_handlers
from .core.extensions import bcrypt, cors, db, jwt, migrate


def create_app(config_name=None):
    app = Flask(__name__)
    config_cls = get_config(config_name or os.environ.get("FLASK_ENV", "development"))
    app.config.from_object(config_cls)

    # Extensiones
    db.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})

    # Importa modelos para que Alembic/SQLAlchemy los registre.
    from . import models  # noqa: F401

    # Blocklist de tokens (logout real).
    @jwt.token_in_blocklist_loader
    def _check_blocklist(_header, payload):
        from .models import TokenBlocklist

        return db.session.get(TokenBlocklist, payload["jti"]) is not None

    # Blueprints
    from .api import auth, professional, public

    app.register_blueprint(auth.bp)
    app.register_blueprint(professional.bp)
    app.register_blueprint(public.bp)

    register_error_handlers(app)

    @app.get("/api/v1/health")
    def health():
        return jsonify({"status": "ok"})

    return app
