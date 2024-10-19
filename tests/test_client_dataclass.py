import dataclasses

import httpx_auth
import pytest
from pytest_httpx import HTTPXMock

import quickapi


@dataclasses.dataclass
class Fact:
    fact: str
    length: int


@dataclasses.dataclass
class RequestParams:
    max_length: int = 100
    limit: int = 10


@dataclasses.dataclass
class RequestBody:
    some_data: str | None = None


@dataclasses.dataclass
class ResponseBody:
    current_page: int
    data: list[Fact] = dataclasses.field(default_factory=list)


class GetDataClassApi(quickapi.BaseApi[ResponseBody]):
    url = "/facts"
    response_body = ResponseBody


class PostDataclassApi(quickapi.BaseApi[ResponseBody]):
    url = "/facts"
    method = quickapi.BaseHttpMethod.POST
    request_params = RequestParams
    request_body = RequestBody
    response_body = ResponseBody


class ExampleClient(quickapi.BaseClient):
    base_url = "https://example.com"
    fetch = quickapi.ApiEndpoint(GetDataClassApi)
    submit = quickapi.ApiEndpoint(PostDataclassApi)


class TestExampleClient:
    def test_api_client_fetch(self, httpx_mock: HTTPXMock):
        mock_json = {"current_page": 1, "data": [{"fact": "Some fact", "length": 9}]}
        httpx_mock.add_response(
            url=f"{ExampleClient.base_url}{ExampleClient.fetch.url}",
            match_headers={"X-Api-Key": "my_api_key"},
            json=mock_json,
        )

        client = ExampleClient(
            auth=httpx_auth.HeaderApiKey(header_name="X-Api-Key", api_key="my_api_key")
        )
        response = client.fetch()
        assert response.body.current_page == 1
        assert response.body.data[0] == Fact(fact="Some fact", length=9)

    def test_api_client_submit(self, httpx_mock: HTTPXMock):
        mock_json = {"current_page": 1, "data": [{"fact": "Some fact", "length": 9}]}
        client = ExampleClient(
            auth=httpx_auth.HeaderApiKey(header_name="X-Api-Key", api_key="my_api_key")
        )

        httpx_mock.add_response(
            url=f"{ExampleClient.base_url}{ExampleClient.submit.url}?max_length={RequestParams().max_length}&limit={RequestParams().limit}",
            match_headers={"X-Api-Key": "my_api_key"},
            json=mock_json,
        )

        response = client.submit()
        assert response.body.current_page == 1
        assert response.body.data[0] == Fact(fact="Some fact", length=9)


class TestClientSetupError:
    def test_if_invalid_api_endpoint_cls(self, httpx_mock: HTTPXMock):
        with pytest.raises(quickapi.ClientSetupError):

            class _(quickapi.BaseClient):
                invalid_endpoint = quickapi.ApiEndpoint(object)  # type: ignore [reportArgumentType]

    def test_if_api_endpoint_not_part_of_base_client(self, httpx_mock: HTTPXMock):
        lone_api_endpoint = quickapi.ApiEndpoint(GetDataClassApi)
        with pytest.raises(AttributeError):
            lone_api_endpoint()

    def test_if_api_endpoint_descriptor_set(self, httpx_mock: HTTPXMock):
        client = ExampleClient()
        with pytest.raises(AttributeError):
            client.fetch = "invalid"

    def test_if_api_endpoint_descriptor_del(self, httpx_mock: HTTPXMock):
        client = ExampleClient()
        with pytest.raises(AttributeError):
            del client.fetch
