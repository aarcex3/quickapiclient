from quickapi.exceptions import DictSerializationError
from quickapi.serializers.types import FromDictSerializableT

try:
    import msgspec
except ImportError:
    msgspec_installed = False
else:
    msgspec_installed = True


class MsgspecSerializer:
    """
    Convert from dict to msgspec.Struct.
    """

    @classmethod
    def can_apply(cls, klass: type[FromDictSerializableT]) -> bool:
        return msgspec_installed and issubclass(klass, msgspec.Struct)

    @classmethod
    def from_dict(
        cls, klass: type[FromDictSerializableT], values: dict
    ) -> FromDictSerializableT:
        try:
            return msgspec.convert(values, klass)
        except msgspec.ValidationError as e:
            raise DictSerializationError(expected_type=klass.__name__) from e


class MsgspecDeserializer:
    """Convert from msgspec.Struct to dict."""

    @classmethod
    def can_apply(cls, instance: "msgspec.Struct") -> bool:
        return msgspec_installed and isinstance(instance, msgspec.Struct)

    @classmethod
    def to_dict(cls, instance: "msgspec.Struct") -> dict | None:
        data = msgspec.structs.asdict(instance)

        def convert_nested(data):
            if isinstance(data, list):
                return [convert_nested(item) for item in data]
            elif isinstance(data, dict):
                return {key: convert_nested(value) for key, value in data.items()}
            elif isinstance(data, msgspec.Struct):
                return cls.to_dict(data)
            return data

        return convert_nested(data)
