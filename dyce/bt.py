__all__ = ("beartype",)


try:
    from beartype import beartype
except ImportError:
    from typing import TypeVar

    T = TypeVar("T")

    def beartype(func: T) -> T:
        return func
