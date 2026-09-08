from datetime import datetime, timedelta, timezone

from flask import Blueprint, current_app, jsonify, request
from flask_bcrypt import check_password_hash, generate_password_hash
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)
from sqlalchemy import select

from ..core.errors import AuthenticationError, ConflictError, ForbiddenError, ValidationError
from ..core.extensions import bcrypt, db
from ..core.validation import require, require_email, require_password
from ..models import TokenBlocklist, User

bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")


def _issue_tokens(user: User):
    access = create_access_token(identity=user.id, additional_claims={"type": "access"})
    refresh = create_refresh_token(identity=user.id, additional_claims={"type": "refresh"})
    return access, refresh


@bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    email = require_email(data).lower()
    name = require(data, "name")
    password = require_password(data)
    confirm = require(data, "confirm_password")
    if password != confirm:
        raise ValidationError(details=[{"field": "confirm_password", "message": "Las contraseñas no coinciden."}])

    # Regla #8: unicidad del profesional por instancia.
    existing = db.session.execute(select(User)).scalars().first()
    if existing:
        raise ConflictError(
            "Esta instancia ya tiene un profesional registrado. Inicia sesión.",
            code="PROFESSIONAL_EXISTS",
        )
    if db.session.execute(select(User).where(User.email == email)).scalars().first():
        raise ConflictError(
            "El email ya está registrado. Inicia sesión o usa otro email.",
            code="EMAIL_ALREADY_REGISTERED",
        )

    user = User(email=email, name=name, password=bcrypt.generate_password_hash(password).decode())
    db.session.add(user)
    db.session.commit()

    access, refresh = _issue_tokens(user)
    return jsonify({"user": user.to_public_dict(), "access_token": access, "refresh_token": refresh}), 201


@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = require(data, "email")
    password = require(data, "password")

    user = db.session.execute(select(User).where(User.email == email.strip().lower())).scalars().first()
    generic = "Credenciales inválidas. Verifica tu email y contraseña."

    if user and user.locked_until and user.locked_until > datetime.now(timezone.utc):
        remaining = int((user.locked_until - datetime.now(timezone.utc)).total_seconds() // 60) + 1
        raise ForbiddenError(
            f"Cuenta bloqueada temporalmente por intentos fallidos. Reintenta en {remaining} min.",
            code="ACCOUNT_LOCKED",
        )

    if not user or not check_password_hash(user.password, password):
        if user:
            _register_failed_login(user)
            db.session.commit()
        raise AuthenticationError(generic)

    # Éxito: reinicia contadores.
    user.failed_login_count = 0
    user.locked_until = None
    db.session.commit()

    access, refresh = _issue_tokens(user)
    return jsonify(
        {"access_token": access, "refresh_token": refresh, "user": user.to_public_dict()}
    )


def _register_failed_login(user: User):
    user.failed_login_count = (user.failed_login_count or 0) + 1
    if user.failed_login_count >= current_app.config["MAX_FAILED_LOGINS"]:
        user.locked_until = datetime.now(timezone.utc) + timedelta(
            minutes=current_app.config["LOCKOUT_MINUTES"]
        )
        user.failed_login_count = 0


@bp.post("/refresh-token")
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    access = create_access_token(identity=identity, additional_claims={"type": "access"})
    return jsonify({"access_token": access})


@bp.post("/logout")
@jwt_required()
def logout():
    data = request.get_json(silent=True) or {}
    jtis = [get_jwt()["jti"]]
    # Si llega un refresh_token, también se revoca.
    refresh_token = data.get("refresh_token")
    if refresh_token:
        from flask_jwt_extended import decode_token

        try:
            decoded = decode_token(refresh_token)
            jtis.append(decoded["jti"])
        except Exception:  # noqa: BLE001
            pass

    now = datetime.now(timezone.utc)
    for jti in jtis:
        db.session.add(TokenBlocklist(jti=jti, user_id=get_jwt_identity(), expires=now + timedelta(days=30)))
    db.session.commit()
    return jsonify({"message": "Logged out successfully"})
