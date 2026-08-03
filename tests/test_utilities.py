from __future__ import annotations

import warnings
from pathlib import Path

import pytest
import sob

from oapi._utilities import (
    get_string_format_property,
    get_type_format_property,
    iter_distinct,
    rename_parameters,
)
from oapi.client import ClientModule
from oapi.client import Module as ClientModuleAlias
from oapi.model import ModelModule
from oapi.model import Module as ModelModuleAlias
from oapi.oas.model import Link_, LinkObject, OpenAPI

TESTS_PATH: Path = Path(__file__).absolute().parent
MULTIPART_FIXTURE_PATH: Path = (
    TESTS_PATH / "input-data" / "multipart-request-body.json"
)


@rename_parameters(old_name="new_name")
def _greet(new_name: str, other: str = "x") -> str:
    return f"{new_name}-{other}"


def test_rename_parameters_translates_old_kwarg_to_new() -> None:
    assert _greet(old_name="a") == "a-x"


def test_rename_parameters_passes_through_new_kwarg_unchanged() -> None:
    assert _greet(new_name="b") == "b-x"


def test_rename_parameters_passes_through_other_kwargs() -> None:
    assert _greet(old_name="a", other="y") == "a-y"


@pytest.mark.parametrize(
    ("type_", "expected_class"),
    [
        ("number", sob.NumberProperty),
        ("integer", sob.IntegerProperty),
        ("boolean", sob.BooleanProperty),
        ("file", sob.BytesProperty),
        ("array", sob.ArrayProperty),
        ("object", sob.Property),
    ],
)
def test_get_type_format_property_maps_simple_types(
    type_: str, expected_class: type[sob.abc.Property]
) -> None:
    property_: sob.abc.Property = get_type_format_property(type_)
    assert type(property_) is expected_class


@pytest.mark.parametrize(
    ("format_", "content_encoding", "expected_class"),
    [
        ("date-time", None, sob.DateTimeProperty),
        ("date", None, sob.DateProperty),
        ("byte", None, sob.BytesProperty),
        ("binary", None, sob.BytesProperty),
        ("base64", None, sob.BytesProperty),
        (None, None, sob.StringProperty),
        (None, "base64", sob.BytesProperty),
    ],
)
def test_get_string_format_property_maps_formats(
    format_: str | None,
    content_encoding: str | None,
    expected_class: type[sob.abc.Property],
) -> None:
    property_: sob.abc.Property = get_string_format_property(
        format_, content_encoding
    )
    assert type(property_) is expected_class


def test_get_type_format_property_string_delegates() -> None:
    property_: sob.abc.Property = get_type_format_property(
        "string", "date-time"
    )
    assert type(property_) is sob.DateTimeProperty


def test_get_type_format_property_none_type_without_media_or_encoding() -> (
    None
):
    property_: sob.abc.Property = get_type_format_property(None)
    assert type(property_) is sob.Property


def test_get_type_format_property_none_type_uses_default_type() -> None:
    property_: sob.abc.Property = get_type_format_property(
        None, default_type=sob.StringProperty
    )
    assert type(property_) is sob.StringProperty


def test_get_type_format_property_none_type_with_content_media_type() -> None:
    property_: sob.abc.Property = get_type_format_property(
        None, content_media_type="application/json"
    )
    assert type(property_) is sob.BytesProperty


def test_get_type_format_property_none_type_with_content_encoding() -> None:
    property_: sob.abc.Property = get_type_format_property(
        None, content_encoding="base64"
    )
    assert type(property_) is sob.BytesProperty


def test_get_type_format_property_unknown_type_raises() -> None:
    with pytest.raises(ValueError, match="Unknown schema type: bogus"):
        get_type_format_property("bogus")


def test_get_type_format_property_required_is_propagated() -> None:
    property_: sob.abc.Property = get_type_format_property(
        "string", required=True
    )
    assert property_.required is True


def test_iter_distinct_deduplicates_preserving_order() -> None:
    assert list(iter_distinct([1, 2, 1, 3, 2, 4])) == [1, 2, 3, 4]


def test_iter_distinct_empty_iterable() -> None:
    assert list(iter_distinct([])) == []


def test_deprecated_link_alias_warns_and_returns_link_object() -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        link: LinkObject = Link_()
    assert len(caught) == 1
    assert issubclass(caught[0].category, DeprecationWarning)
    assert "oapi.oas.model.Link_" in str(caught[0].message)
    assert "oapi.oas.model.LinkObject" in str(caught[0].message)
    assert isinstance(link, LinkObject)


def test_deprecated_model_module_alias_warns_and_returns_model_module() -> (
    None
):
    with open(MULTIPART_FIXTURE_PATH) as io_:
        open_api: OpenAPI = OpenAPI(io_)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        model_module: ModelModule = ModelModuleAlias(open_api)
    assert len(caught) == 1
    assert issubclass(caught[0].category, DeprecationWarning)
    assert "oapi.model.Module" in str(caught[0].message)
    assert "oapi.ModelModule" in str(caught[0].message)
    assert isinstance(model_module, ModelModule)


def test_deprecated_client_module_alias_warns_and_returns_client_module(
    tmp_path: Path,
) -> None:
    with open(MULTIPART_FIXTURE_PATH) as io_:
        open_api: OpenAPI = OpenAPI(io_)
    model_module: ModelModule = ModelModule(open_api)
    model_path: Path = tmp_path / "model.py"
    model_path.write_text(str(model_module))
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        client_module: ClientModule = ClientModuleAlias(
            open_api, model_path=str(model_path)
        )
    assert len(caught) == 1
    assert issubclass(caught[0].category, DeprecationWarning)
    assert "oapi.client.Module" in str(caught[0].message)
    assert "oapi.ClientModule" in str(caught[0].message)
    assert isinstance(client_module, ClientModule)


if __name__ == "__main__":
    test_rename_parameters_translates_old_kwarg_to_new()
