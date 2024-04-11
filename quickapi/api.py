from dataclasses import dataclass
from typing import Generic, TypeVar, get_args

from quickapi.exceptions import (
    ClientSetupError,
    DictDeserializationError,
    DictSerializationError,
    HTTPError,
    RequestSerializationError,
    ResponseSerializationError,
)
from quickapi.http_clients import (
    BaseHttpClient,
    BaseHttpClientAuth,
    BaseHttpClientResponse,
    HTTPxClient,
)
from quickapi.http_clients.types import BaseHttpMethod
from quickapi.serializers import (
    DictSerializable,
    DictSerializableT,
)

USE_DEFAULT = object()

ResponseBodyT = TypeVar("ResponseBodyT")


@dataclass
class BaseResponse(Generic[ResponseBodyT]):
    client_response: BaseHttpClientResponse
    body: ResponseBodyT


class BaseApi(Generic[ResponseBodyT]):
    """
    Base class for all API endpoints.

    Subclass from `BaseApi` and define appropriate attributes from
    the list below to create your own API client endpoint.

    Make sure to add in the generic type for the expected response body, so that
    you can get a fully typed response object.

    Attributes:
        url: The URL of the API endpoint.
        method: The HTTP method to be used for the request.
        request_params: The request parameters type defines the expected format
            for any parameters that will be added to the URL as query strings.
        request_body: The request body type (for POST, PUT, PATCH requests)
            defines the expected format the request body will need to be in.
        response_body: The expected response body type. The HTTP response body
            will be serialized to this type.
        auth: Optional authentication to be used. Can be any class supported
            by the HTTP client.
        http_client: Optional HTTP client to be used if not using the
            default (HTTPx). Or if wanting to customize the default client.

    Raises:
        ClientSetupError: If the class attributes are not correctly defined.

    Examples:
        A very basic example of a Cat Facts API definition:

        ```python
        import quickapi


        @dataclass
        class ResponseBody:
            current_page: int
            data: list[str]


        class MyApi(quickapi.BaseApi[ResponseBody]):
            url = "https://catfact.ninja/facts"
            response_body = ResponseBody
        ```

        Which can be used like this:

        ```python
        api = MyApi()
        response = api.execute()
        assert isinstance(response.body, ResponseBody)
        ```

    """

    url: str
    method: BaseHttpMethod = BaseHttpMethod.GET
    auth: BaseHttpClientAuth = None
    request_params: type[DictSerializableT] | None = None
    request_body: type[DictSerializableT] | None = None
    response_body: type[ResponseBodyT]
    http_client: BaseHttpClient | None = None

    _http_client: BaseHttpClient = HTTPxClient()
    _request_params: "DictSerializableT | None" = None
    _request_body: "DictSerializableT | None" = None
    _response_body_cls: type[ResponseBodyT]
    _response: BaseResponse[ResponseBodyT] | None = None

    @classmethod
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        cls._validate_subclass()

        if cls.request_params is not None:
            cls._request_params = cls.request_params()

        if cls.request_body is not None:
            cls._request_body = cls.request_body()

        cls._response_body_cls = cls.response_body  # pyright: ignore [reportGeneralTypeIssues]

        if cls.http_client is not None:
            cls._http_client = cls.http_client

    @classmethod
    def _validate_subclass(cls) -> None:
        if getattr(cls, "url", None) is None:
            raise ClientSetupError(attribute="url")

        if getattr(cls, "response_body", None) is None:
            raise ClientSetupError(attribute="response_body")

        if (
            getattr(cls, "method", None) is not None
            and cls.method not in BaseHttpMethod.values()
        ):
            raise ClientSetupError(attribute="method")

        if getattr(cls, "http_client", None) is not None and not (
            isinstance(cls.http_client, BaseHttpClient)
        ):
            raise ClientSetupError(attribute="http_client")

        if getattr(cls, "__orig_bases__", None) is not None:
            response_body_generic_type = get_args(cls.__orig_bases__[0])[0]  # type: ignore [attr-defined]
            if (
                isinstance(response_body_generic_type, TypeVar)
                and response_body_generic_type.__name__ == "ResponseBodyT"
            ):
                raise ClientSetupError(attribute="ResponseBodyT")

    def __init__(
        self,
        request_params: "DictSerializableT | None" = None,
        request_body: "DictSerializableT | None" = None,
        http_client: BaseHttpClient | None = None,
        auth: BaseHttpClientAuth = USE_DEFAULT,
    ) -> None:
        self._load_overrides(request_params, request_body, http_client, auth)

    def _load_overrides(
        self,
        request_params: "DictSerializableT | None" = None,
        request_body: "DictSerializableT | None" = None,
        http_client: BaseHttpClient | None = None,
        auth: BaseHttpClientAuth = USE_DEFAULT,
    ) -> None:
        self._request_params = request_params or self._request_params
        self._request_body = request_body or self._request_body
        self._http_client = http_client or self._http_client
        self.auth = auth if auth != USE_DEFAULT else self.auth

    def execute(
        self,
        request_params: "DictSerializableT | None" = None,
        request_body: "DictSerializableT | None" = None,
        http_client: BaseHttpClient | None = None,
        auth: BaseHttpClientAuth = USE_DEFAULT,
    ) -> BaseResponse[ResponseBodyT]:
        """
        Validate and execute the API request, then validate and return the typed response.

        You can optionally override the request parameters, request body, HTTP client
        and authentication. Otherwise, default values from the class attributes (if
        defined) will be used.

        Args:
            request_params: Optional request parameters to be sent with the request.
                They will need to be of the same type as the configured
                `BaseApi.request_params`.
            request_body: Optional request body to be sent with the request.
                They will need to be of the same type as the configured
                `BaseApi.request_body`.
            http_client: Optional HTTP client to be used for sending the request.
            auth: Optional authentication to be used for the request.

        Returns:
            Response object containing the client response and the parsed response body.

        Raises:
            HTTPError: If the response status code is not 200.
            RequestSerializationError: If the request parameters or body cannot be serialized.
            ResponseSerializationError: If the response body cannot be serialized.

        """

        self._load_overrides(request_params, request_body, http_client, auth)
        request_params = self._parse_request_params(self._request_params)
        request_body = self._parse_request_body(self._request_body)

        client_response = self._http_client.send_request(
            method=self.method,
            url=self.url,
            auth=self.auth,
            params=request_params,
            json=request_body,
        )
        self._check_response_for_errors(client_response)

        body = self._parse_response_body(
            klass=self._response_body_cls, body=client_response.json()
        )
        self._response = BaseResponse(client_response=client_response, body=body)

        return self._response

    def _check_response_for_errors(
        self, client_response: BaseHttpClientResponse
    ) -> None:
        # TODO: Add support for handling different response status codes
        if client_response.status_code != 200:
            raise HTTPError(client_response.status_code)

    def _parse_request_params(self, params: "DictSerializableT | None") -> dict | None:
        try:
            params = DictSerializable.to_dict(params) if params else {}
        except DictDeserializationError as e:
            raise RequestSerializationError(expected_type=e.expected_type) from e
        else:
            return params

    def _parse_request_body(self, body: "DictSerializableT | None") -> dict | None:
        try:
            body = DictSerializable.to_dict(body) if body else {}
        except DictDeserializationError as e:
            raise RequestSerializationError(expected_type=e.expected_type) from e
        else:
            return body

    def _parse_response_body(
        self, klass: type[ResponseBodyT], body: dict
    ) -> ResponseBodyT:
        try:
            return DictSerializable.from_dict(klass, body)
        except DictSerializationError as e:
            raise ResponseSerializationError(expected_type=e.expected_type) from e
