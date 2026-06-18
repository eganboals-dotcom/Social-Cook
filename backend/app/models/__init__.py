"""ORM models. Importing this package registers every model on `Base.metadata`
(used by Alembic and by the test harness's create_all)."""
from app.models.purchase import Purchase
from app.models.recipe import Recipe
from app.models.user import User

__all__ = ["User", "Recipe", "Purchase"]
