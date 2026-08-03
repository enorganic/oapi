from __future__ import annotations

import os
import typing
import unittest
from collections.abc import Callable
from contextlib import suppress
from copy import deepcopy
from datetime import date, datetime
from itertools import chain
from pathlib import Path
from types import ModuleType
from urllib.error import URLError
from urllib.parse import urljoin
from urllib.request import Request

import pytest
import sob

from oapi.model import (
    ModelModule,
    _append_property_type,
    _get_schema_type,
    _types_from_enum_values,
    get_default_class_name_from_pointer,
)
from oapi.oas.model import Items, OpenAPI, Schema
from oapi.oas.references import Resolver, _urlopen

OPENAPI_EXAMPLE_URL = (
    "https://raw.githubusercontent.com/OAI/OpenAPI-Specification/3.1.1/"
    "examples/"
)
LANGUAGE_TOOL_URL = (
    "https://languagetool.org/http-api/languagetool-swagger.json"
)
TESTS_PATH: Path = Path(__file__).absolute().parent
REGRESSION_DATA_PATH: Path = TESTS_PATH / "regression-data"
INPUT_DATA_PATH: Path = TESTS_PATH / "input-data"
LANGUAGE_TOOL_SWAGGER_PATH: Path = (
    INPUT_DATA_PATH / "languagetool-swagger.json"
)
LANGUAGE_TOOL_PY: Path = REGRESSION_DATA_PATH / "languagetool.py"


class TestModel(unittest.TestCase):
    @staticmethod
    def test_get_default_class_name_from_pointer() -> None:
        assert (
            get_default_class_name_from_pointer(
                pointer=(
                    "#/paths/~1directory~1sub-directory~1name/get/parameters/1"
                ),
                name="argument-name",
            )
            == "DirectorySubDirectoryNameGetArgumentName"
        )
        assert (
            get_default_class_name_from_pointer(
                pointer=(
                    "#/paths/~1directory~1sub-directory~1name/get/parameters/1"
                    "/item"
                ),
                name="argument-name",
            )
            == "DirectorySubDirectoryNameGetArgumentNameItem"
        )

    @staticmethod
    def test_openapi_examples() -> None:
        for relative_path in (
            "v2.0/json/petstore-separate/spec/swagger.json",
            "v3.0/link-example.yaml",
            "v2.0/json/petstore-with-external-docs.json",
            "v3.0/api-with-examples.yaml",
            "v3.0/petstore-expanded.yaml",
            "v3.0/petstore.yaml",
            "v3.0/uspto.yaml",
            "v3.0/callback-example.yaml",
            "v2.0/json/api-with-examples.json",
            "v2.0/json/petstore-expanded.json",
            "v2.0/json/petstore-minimal.json",
            "v2.0/json/petstore-with-external-docs.json",
            "v2.0/json/petstore.json",
            "v2.0/json/uber.json",
            "v2.0/yaml/api-with-examples.yaml",
            "v2.0/yaml/petstore-expanded.yaml",
            "v2.0/yaml/petstore-minimal.yaml",
            "v2.0/yaml/petstore-with-external-docs.yaml",
            "v2.0/yaml/petstore.yaml",
            "v2.0/yaml/uber.yaml",
        ):
            url: str = urljoin(OPENAPI_EXAMPLE_URL, relative_path)
            print(url)  # noqa: T201
            with _urlopen(url) as response:
                openapi: OpenAPI = OpenAPI(response)
                sob.validate(openapi)
                openapi2: OpenAPI = deepcopy(openapi)
                assert sob.get_model_url(openapi) == sob.get_model_url(
                    openapi2
                )
                Resolver(openapi2).dereference()
                try:
                    assert "$ref" not in str(openapi2)
                except AssertionError as assertion_error:
                    if assertion_error.args:
                        assertion_error.args = tuple(
                            chain(
                                (
                                    assertion_error.args[0]
                                    + "\n"
                                    + str(openapi2),
                                ),
                                assertion_error.args[1:],
                            )
                        )
                    else:
                        assertion_error.args = (str(openapi2),)
                    raise
                if openapi2 != openapi:
                    sob.validate(openapi2)

    @staticmethod
    def test_languagetool() -> None:
        if not os.environ.get("CI"):
            with suppress(URLError):  # noqa: SIM117
                with _urlopen(
                    Request(LANGUAGE_TOOL_URL, headers={"User-agent": ""})
                ) as response:
                    with open(
                        LANGUAGE_TOOL_SWAGGER_PATH, "wb"
                    ) as language_tool_io:
                        language_tool_io.write(response.read())  # type: ignore
        with open(LANGUAGE_TOOL_SWAGGER_PATH) as language_tool_io:
            oa = OpenAPI(language_tool_io)
            sob.validate(oa)
            model = ModelModule(oa)
            if LANGUAGE_TOOL_PY.exists():
                with open(LANGUAGE_TOOL_PY) as model_file:
                    model_file_data = model_file.read()
                    if not isinstance(model_file_data, str):
                        model_file_data = str(
                            model_file_data, encoding="utf-8"
                        )
                    assert str(model) == model_file_data
            else:
                if not REGRESSION_DATA_PATH.exists():
                    os.makedirs(REGRESSION_DATA_PATH, exist_ok=True)
                model_string: str = str(model)
                with open(LANGUAGE_TOOL_PY, "w") as model_file:
                    model_file.write(model_string)


# region ModelModule: naming/schema/type helper functions


def test_get_schema_type_returns_the_explicit_type() -> None:
    assert _get_schema_type(Schema({"type": "string"})) == "string"


def test_get_schema_type_infers_object_from_properties() -> None:
    schema: Schema = Schema({"properties": {"a": {"type": "string"}}})
    assert _get_schema_type(schema) == "object"


def test_get_schema_type_infers_object_from_additional_properties() -> None:
    schema: Schema = Schema({"additionalProperties": {"type": "string"}})
    assert _get_schema_type(schema) == "object"


def test_get_schema_type_infers_array_from_items() -> None:
    schema: Schema = Schema({"items": {"type": "string"}})
    assert _get_schema_type(schema) == "array"


def test_get_schema_type_returns_none_when_nothing_is_inferable() -> None:
    assert _get_schema_type(Schema({})) is None


def test_get_schema_type_accepts_an_items_instance() -> None:
    items: Items = Items({"items": {"type": "string"}})
    assert _get_schema_type(items) == "array"


def test_types_from_enum_values_maps_python_types() -> None:
    types: sob.abc.Types = _types_from_enum_values(["a", "b", 1])
    assert list(types) == [str, int]


def test_types_from_enum_values_maps_date_and_datetime_specially() -> None:
    types: sob.abc.Types = _types_from_enum_values(
        [date(2024, 1, 1), datetime(2024, 1, 1)]
    )
    represented: list[str] = [
        sob.utilities.represent(type_) for type_ in types
    ]
    assert represented == [
        sob.utilities.represent(sob.DateProperty()),
        sob.utilities.represent(sob.DateTimeProperty()),
    ]


def test_types_from_enum_values_deduplicates_by_type() -> None:
    types: sob.abc.Types = _types_from_enum_values(["a", "b", "c"])
    assert list(types) == [str]


def test_append_property_type_adds_a_new_type() -> None:
    property_: sob.abc.Property = sob.Property()
    result: sob.abc.Property = _append_property_type(property_, str)
    assert list(result.types or ()) == [str]


def test_append_property_type_accumulates_distinct_types() -> None:
    property_: sob.abc.Property = _append_property_type(sob.Property(), str)
    property_ = _append_property_type(property_, int)
    assert list(property_.types or ()) == [str, int]


def test_append_property_type_is_idempotent_for_the_same_type() -> None:
    property_: sob.abc.Property = _append_property_type(sob.Property(), str)
    property_ = _append_property_type(property_, str)
    assert list(property_.types or ()) == [str]


def test_append_property_type_maps_date_and_datetime_specially() -> None:
    property_: sob.abc.Property = _append_property_type(
        sob.Property(), datetime
    )
    types: list[str] = [
        sob.utilities.represent(type_) for type_ in (property_.types or ())
    ]
    assert types == [sob.utilities.represent(sob.DateTimeProperty())]


def test_get_default_class_name_from_pointer_for_a_named_schema() -> None:
    result: str = get_default_class_name_from_pointer(
        "#/components/schemas/Foo"
    )
    assert result == "Foo"


def test_get_default_class_name_from_pointer_for_a_200_response() -> None:
    result: str = get_default_class_name_from_pointer(
        "#/paths/~1foo/get/responses/200/content/application~1json/schema"
    )
    assert result == "FooGetResponse"


def test_get_default_class_name_from_pointer_for_a_non_200_response() -> None:
    result: str = get_default_class_name_from_pointer(
        "#/paths/~1foo/get/responses/404/schema"
    )
    assert result == "FooGetResponse404"


# endregion

# region ModelModule: empty-schema documents


def test_a_document_with_no_named_schemas_generates_unimportable_source() -> (
    None
):
    """
    Documents a real, verified, currently-unfixed bug: an OpenAPI
    document with no `components/schemas` (every response schema
    inline and primitive-shaped, e.g. bare `{"type": "object"}`)
    generates a `model.py` that cannot actually be imported.
    `ModelModule.get_module_source` builds its `imports` set purely
    from each *generated class's own* source text -- when there are
    zero generated classes, that set stays empty, so neither `from
    __future__ import annotations` nor `import sob` gets emitted. But
    the module's own trailing `_POINTERS_CLASSES: dict[str,
    type[sob.abc.Model]] = {...}` line always references `sob.abc.
    Model` in a variable annotation regardless -- and without `from
    __future__ import annotations` to make that annotation lazy, `sob`
    is genuinely undefined when the module is executed. Not fixed here
    (out of this test-only initiative's scope) -- flagged to the user
    directly as well as documented here.
    """
    open_api_data: dict[str, typing.Any] = {
        "openapi": "3.0.3",
        "info": {"title": "t", "version": "1"},
        "paths": {
            "/foo": {
                "get": {
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {
                                "application/json": {
                                    "schema": {"type": "object"}
                                }
                            },
                        }
                    }
                }
            }
        },
    }
    open_api: OpenAPI = OpenAPI(open_api_data)
    model: ModelModule = ModelModule(open_api)
    source: str = str(model)
    assert "import sob" not in source
    assert "from __future__ import annotations" not in source
    assert "sob.abc.Model" in source
    # `dont_inherit=True` is required here: without it, `compile()`
    # inherits the *calling* module's `__future__` flags -- since this
    # test file itself has `from __future__ import annotations`, that
    # would silently make `_POINTERS_CLASSES`'s annotation lazy (PEP
    # 563) even though the generated source string has no such import
    # of its own, masking the real bug. A real `import`/`importlib`
    # load of this generated file (as every other test in this
    # initiative does) never has this problem, since each file's
    # `__future__` behavior is self-contained -- `dont_inherit=True`
    # makes `exec()` behave the same way, for a faithful reproduction.
    with pytest.raises(NameError, match="sob"):
        exec(  # noqa: S102
            compile(source, "<generated>", "exec", dont_inherit=True), {}
        )


# endregion

# region ModelModule: allOf/oneOf/anyOf/enum/dictionary schema generation


@pytest.fixture
def polymorphic_model(
    generated_client_package: Callable[
        [OpenAPI], tuple[ModuleType, ModuleType]
    ],
) -> ModuleType:
    with open("tests/input-data/polymorphic-schemas.json") as f:
        open_api: OpenAPI = OpenAPI(f)
    model_module, _client_module = generated_client_package(open_api)
    return model_module


def test_allof_merges_properties_from_every_member_schema(
    polymorphic_model: ModuleType,
) -> None:
    """
    `Pet` is `allOf: [NamedEntity, {species, status}]` -- the generated
    class should have properties from both member schemas merged into
    one, including `NamedEntity`'s `required: [name]`.
    """
    meta: sob.abc.ObjectMeta | None = sob.read_object_meta(
        polymorphic_model.Pet
    )
    assert meta is not None
    assert meta.properties is not None
    assert set(meta.properties.keys()) == {"name", "species", "status"}
    assert meta.properties["name"].required is True


def test_allof_merged_class_enforces_the_merged_required_property(
    polymorphic_model: ModuleType,
) -> None:
    pet: sob.abc.Object = polymorphic_model.Pet({"species": "dog"})
    with pytest.raises(sob.errors.ValidationError, match="name"):
        sob.validate(pet)


def test_allof_merged_class_accepts_a_fully_populated_instance(
    polymorphic_model: ModuleType,
) -> None:
    pet: sob.abc.Object = polymorphic_model.Pet(
        {"name": "Rex", "species": "dog", "status": "sold"}
    )
    sob.validate(pet)


def test_enum_schema_generates_an_enumerated_property_with_real_values(
    polymorphic_model: ModuleType,
) -> None:
    meta: sob.abc.ObjectMeta | None = sob.read_object_meta(
        polymorphic_model.Pet
    )
    assert meta is not None
    assert meta.properties is not None
    status_property: sob.abc.Property = meta.properties["status"]
    assert isinstance(status_property, sob.EnumeratedProperty)
    assert status_property.values == {"available", "pending", "sold"}


def test_enum_schema_rejects_an_unlisted_value_at_construction(
    polymorphic_model: ModuleType,
) -> None:
    with pytest.raises(sob.errors.UnmarshalValueError, match="unknown"):
        polymorphic_model.Pet({"name": "x", "status": "unknown"})


def test_oneof_generates_independent_non_merged_classes(
    polymorphic_model: ModuleType,
) -> None:
    """
    `Shape` is `oneOf: [Circle, Square]` -- unlike `allOf`, this should
    *not* merge `Circle` and `Square` into one class; each keeps only
    its own properties.
    """
    circle_meta: sob.abc.ObjectMeta | None = sob.read_object_meta(
        polymorphic_model.Circle
    )
    square_meta: sob.abc.ObjectMeta | None = sob.read_object_meta(
        polymorphic_model.Square
    )
    assert circle_meta is not None
    assert square_meta is not None
    assert circle_meta.properties is not None
    assert square_meta.properties is not None
    assert set(circle_meta.properties.keys()) == {"radius"}
    assert set(square_meta.properties.keys()) == {"side"}


def test_oneof_member_schemas_validate_independently(
    polymorphic_model: ModuleType,
) -> None:
    circle: sob.abc.Object = polymorphic_model.Circle({"radius": 5})
    sob.validate(circle)
    square: sob.abc.Object = polymorphic_model.Square({"side": 3})
    sob.validate(square)


def test_anyof_generates_independent_non_merged_classes(
    polymorphic_model: ModuleType,
) -> None:
    email_meta: sob.abc.ObjectMeta | None = sob.read_object_meta(
        polymorphic_model.EmailContact
    )
    phone_meta: sob.abc.ObjectMeta | None = sob.read_object_meta(
        polymorphic_model.PhoneContact
    )
    assert email_meta is not None
    assert phone_meta is not None
    assert email_meta.properties is not None
    assert phone_meta.properties is not None
    assert set(email_meta.properties.keys()) == {"email"}
    assert set(phone_meta.properties.keys()) == {"phone"}


def test_additional_properties_schema_generates_a_dictionary_subclass(
    polymorphic_model: ModuleType,
) -> None:
    assert issubclass(polymorphic_model.TagsGetResponse, sob.Dictionary)
    tags: sob.abc.Dictionary = polymorphic_model.TagsGetResponse(
        {"a": "1", "b": "2"}
    )
    sob.validate(tags)
    assert dict(tags) == {"a": "1", "b": "2"}


# endregion


if __name__ == "__main__":
    # unittest.main()
    TestModel.test_get_default_class_name_from_pointer()
