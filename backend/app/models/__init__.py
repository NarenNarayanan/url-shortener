"""
Importing every model here ensures they're all registered on Base.metadata
before Alembic (or anything else) inspects it. Forgetting to import a model
here is a classic bug: the table silently never gets created by autogenerate.
"""
from app.models.click import Click
from app.models.url import URL
from app.models.user import User

__all__ = ["User", "URL", "Click"]
