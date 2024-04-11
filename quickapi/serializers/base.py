from collections.abc import Sequence
from typing import Protocol

from quickapi.exceptions import (
    DictDeserializationError,
    DictSerializationError,
)
from quickapi.serializers.attrs import AttrsDeserializer, AttrsSerializer
from quickapi.serializers.dataclass import DataclassDeserializer, DataclassSerializer
from quickapi.serializers.pydantic import PydanticDeserializer, PydanticSerializer
from quickapi.serializers.types import DictSerializableT, FromDictSerializableT


class BaseSerializer(Protocol):
    @classmethod
    def can_apply(cls, klass: type[FromDictSerializableT]) -> bool:
        raise NotImplementedError

    @classmethod
    def from_dict(
        cls, klass: type[FromDictSerializableT], values: dict
    ) -> FromDictSerializableT:
        raise NotImplementedError


class BaseDeserializer(Protocol):
    @classmethod
    def can_apply(cls, instance: DictSerializableT) -> bool:
        raise NotImplementedError

    @classmethod
    def to_dict(cls, instance: DictSerializableT) -> dict | None:
        raise NotImplementedError


class DictSerializable:
    """
    Convert to/from dictionaries to the appropriate class/instance.

    @TODO: Maybe make the (de)serializer pluggable and configurable
        instead of checking which one can apply.
    """

    serializers: Sequence[type[BaseSerializer]] = (
        DataclassSerializer,
        AttrsSerializer,
        PydanticSerializer,
    )
    deserializers: Sequence[type[BaseDeserializer]] = (  # type: ignore [assignment]
        DataclassDeserializer,
        AttrsDeserializer,
        PydanticDeserializer,
    )

    @classmethod
    def from_dict(
        cls, klass: type[FromDictSerializableT], values: dict
    ) -> FromDictSerializableT:
        for serializer in cls.serializers:
            if serializer.can_apply(klass):
                return serializer.from_dict(klass, values)
        raise DictSerializationError(expected_type=klass.__name__)

    @classmethod
    def to_dict(cls, instance: DictSerializableT) -> dict | None:
        for deserializer in cls.deserializers:
            if deserializer.can_apply(instance):
                return deserializer.to_dict(instance)
        raise DictDeserializationError(expected_type=str(DictSerializableT))
