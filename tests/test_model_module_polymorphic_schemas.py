from __future__ import annotations

from collections.abc import Callable
from types import ModuleType

import pytest
import sob

from oapi.oas.model import OpenAPI


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
