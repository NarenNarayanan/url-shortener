"""
Domain exceptions. Services raise these; routers catch them and translate
them into the appropriate HTTP response. Keeping them out of the service
layer means services can be unit tested without FastAPI in the loop at all,
and the same exception can map to different status codes in different
contexts if that's ever needed.
"""


class AppError(Exception):
    """Base class for all domain-level errors."""


class EmailAlreadyExistsError(AppError):
    pass


class UsernameAlreadyExistsError(AppError):
    pass


class InvalidCredentialsError(AppError):
    pass


class URLNotFoundError(AppError):
    pass


class URLExpiredError(AppError):
    pass
