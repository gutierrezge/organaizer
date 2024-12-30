from functools import wraps
from typing import Callable, Optional
from pydantic import BaseModel
from src import log

logger = log.configure()


def rest_api(func: Callable) -> Callable:
    """
    Decorator that ensures the route always returns a ResponseEntity
    and handles jsonification of Pydantic models.
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> tuple[str, int, dict[str,str]]:
        response:Optional[BaseModel] = func(*args, **kwargs)
        return response.model_dump(exclude_none=True) if response is not None else {}

    return wrapper