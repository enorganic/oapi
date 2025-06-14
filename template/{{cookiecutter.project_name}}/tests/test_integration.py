import pytest
import sob
from {{cookiecutter.package}}.client import Client
from {{cookiecutter.package}} import model


def test_client_get_endpoint(client: Client) -> None:
    """
    Replace the content of this test with one which performs a meaningful
    integration test for one of your API endpoints.

    Each method of the client will correspond to an endpoint in the API, and
    will be prefixed with `get_`, `post_`, `put_`, `delete_`, or `path_`
    depending on the HTTP method employed.

    All responses from the client should, minimally, be validated using
    `sob.validate` to verify that the OpenAPI schema defining the
    response is correctly represented in the OpenAPI document. When/if
    validation errors are raised, you will want to either request the API owner
    update their schema (good luck!), or modify your Open API document
    dynamically in scripts/remodel.py in order to create a repeatable
    process for regenerating the code for this API client which has the needed
    corrections *and* can be updated when/if new changes to the Open API
    document are made by the author of the API.

    Typically, at least one test function should be created for each
    method/endpoint in the API/client.

    Example:
        response: model.Endpoint = client.get_endpoint()
        sob.validate(response)
    """

if __name__ == "__main__":
    pytest.main([f"tests/test_integration.py"])
