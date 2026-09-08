from flask import jsonify

from .extensions import jwt


class APIError(Exception):
    """Error de API con el formato estandarizado de api.md §3."""

    def __init__(self, status, code, message, details=None):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.details = details or []

    def to_response(self):
        return (
            jsonify(
                {
                    "status": self.status,
                    "code": self.code,
                    "message": self.message,
                    "details": self.details,
                }
            ),
            self.status,
        )


class ValidationError(APIError):
    def __init__(self, message="Los datos de la petición son inválidos.", details=None):
        super().__init__(400, "VALIDATION_ERROR", message, details)


class AuthenticationError(APIError):
    def __init__(self, message="Credenciales inválidas.", code="AUTHENTICATION_FAILED"):
        super().__init__(401, code, message)


class ForbiddenError(APIError):
    def __init__(self, message="No tienes permisos para esta acción.", code="ACCESS_DENIED"):
        super().__init__(403, code, message)


class NotFoundError(APIError):
    def __init__(self, message="El recurso solicitado no existe.", code="RESOURCE_NOT_FOUND"):
        super().__init__(404, code, message)


class ConflictError(APIError):
    def __init__(self, message="Conflicto con el estado actual.", code="CONFLICT_ERROR"):
        super().__init__(409, code, message)


class BusinessRuleError(APIError):
    def __init__(self, message, code="BUSINESS_RULE_VIOLATION"):
        super().__init__(422, code, message)


def register_error_handlers(app):
    @app.errorhandler(APIError)
    def _handle_api_error(err):
        return err.to_response()

    @app.errorhandler(404)
    def _handle_404(_err):
        return NotFoundError("Recurso no encontrado.").to_response()

    @app.errorhandler(405)
    def _handle_405(_err):
        return APIError(405, "METHOD_NOT_ALLOWED", "Método no permitido.").to_response()

    @app.errorhandler(Exception)
    def _handle_unexpected(err):
        # No exponer detalles internos (agents.md §2).
        app.logger.exception("Error interno no controlado")
        return APIError(
            500, "INTERNAL_ERROR", "Ocurrió un error inesperado. Inténtelo más tarde."
        ).to_response()

    # Mapeo de errores de JWT al formato estándar.
    @jwt.expired_token_loader
    def _expired(_h, _p):
        return APIError(401, "TOKEN_EXPIRED", "El token ha expirado.").to_response()

    @jwt.invalid_token_loader
    def _invalid(reason):
        return APIError(401, "AUTHENTICATION_FAILED", f"Token inválido: {reason}").to_response()

    @jwt.unauthorized_loader
    def _missing(reason):
        return APIError(401, "AUTHENTICATION_FAILED", "Falta el token de autenticación.").to_response()

    @jwt.revoked_token_loader
    def _revoked(_h, _p):
        return APIError(401, "TOKEN_EXPIRED", "El token ha sido revocado.").to_response()
