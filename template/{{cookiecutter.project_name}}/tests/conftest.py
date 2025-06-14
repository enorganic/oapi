import pytest
from {{cookiecutter.package}}.client import Client


@pytest.fixture(name="client", autouse=True, scope="session")
def get_client() -> Client:
    return Client(
        # Provide client parameters for testing here
    )
