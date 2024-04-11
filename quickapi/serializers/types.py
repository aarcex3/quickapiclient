from typing import TYPE_CHECKING, TypeAlias, TypeVar

if TYPE_CHECKING:
    from _typeshed import DataclassInstance

try:
    import attrs
    import pydantic
except ImportError: ...

DictSerializableT: TypeAlias = (
    "dict | DataclassInstance | attrs.AttrsInstance | pydantic.BaseModel"
)
FromDictSerializableT = TypeVar("FromDictSerializableT")
