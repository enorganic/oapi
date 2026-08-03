from __future__ import annotations

from collections.abc import Callable
from types import ModuleType

import pytest
from servers import Response, http_test_server

from oapi.oas.model import OpenAPI


@pytest.fixture
def polymorphic_client(
    generated_client_package: Callable[
        [OpenAPI], tuple[ModuleType, ModuleType]
    ],
) -> tuple[ModuleType, ModuleType]:
    with open("tests/input-data/polymorphic-schemas.json") as f:
        open_api: OpenAPI = OpenAPI(f)
    return generated_client_package(open_api)


def test_array_of_allof_merged_schema_response(
    polymorphic_client: tuple[ModuleType, ModuleType],
) -> None:
    model_module, client_module = polymorphic_client
    with http_test_server(
        responses={
            ("GET", "/pets"): Response(
                status=200,
                body=b'[{"name": "Rex", "species": "dog", "status": "sold"}]',
            )
        }
    ) as server:
        client = client_module.Client(url=server.url)
        pets = client.get_pets()
        assert len(pets) == 1
        pet = pets[0]
        assert isinstance(pet, model_module.Pet)
        assert pet.name == "Rex"
        assert pet.species == "dog"
        assert pet.status == "sold"


def test_oneof_response_infers_the_matching_variant(
    polymorphic_client: tuple[ModuleType, ModuleType],
) -> None:
    model_module, client_module = polymorphic_client
    with http_test_server(
        responses={
            ("GET", "/shapes"): Response(status=200, body=b'{"radius": 5}')
        }
    ) as server:
        client = client_module.Client(url=server.url)
        shape = client.get_shapes()
        assert isinstance(shape, model_module.Circle)
        assert shape.radius == 5


def test_anyof_response_infers_the_matching_variant(
    polymorphic_client: tuple[ModuleType, ModuleType],
) -> None:
    model_module, client_module = polymorphic_client
    with http_test_server(
        responses={
            ("GET", "/contacts"): Response(
                status=200, body=b'{"email": "a@b.com"}'
            )
        }
    ) as server:
        client = client_module.Client(url=server.url)
        contact = client.get_contacts()
        assert isinstance(contact, model_module.EmailContact)
        assert contact.email == "a@b.com"


def test_additional_properties_dictionary_response(
    polymorphic_client: tuple[ModuleType, ModuleType],
) -> None:
    _model_module, client_module = polymorphic_client
    with http_test_server(
        responses={
            ("GET", "/tags"): Response(
                status=200, body=b'{"a": "1", "b": "2"}'
            )
        }
    ) as server:
        client = client_module.Client(url=server.url)
        tags = client.get_tags()
        assert dict(tags) == {"a": "1", "b": "2"}
