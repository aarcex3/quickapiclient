from abc import ABC, abstractmethod


class BaseHttpClient(ABC):
    """Base interface for all HTTP clients."""

    @abstractmethod
    def __init__(self, *args, **kwargs): ...  # type: ignore [no-untyped-def]

    @abstractmethod
    def get(self, *args, **kwargs):  # type: ignore [no-untyped-def]
        raise NotImplementedError

    @abstractmethod
    def options(self, *args, **kwargs):  # type: ignore [no-untyped-def]
        raise NotImplementedError

    @abstractmethod
    def head(self, *args, **kwargs):  # type: ignore [no-untyped-def]
        raise NotImplementedError

    @abstractmethod
    def post(self, *args, **kwargs):  # type: ignore [no-untyped-def]
        raise NotImplementedError

    @abstractmethod
    def put(self, *args, **kwargs):  # type: ignore [no-untyped-def]
        raise NotImplementedError

    @abstractmethod
    def patch(self, *args, **kwargs):  # type: ignore [no-untyped-def]
        raise NotImplementedError

    @abstractmethod
    def delete(self, *args, **kwargs):  # type: ignore [no-untyped-def]
        raise NotImplementedError
