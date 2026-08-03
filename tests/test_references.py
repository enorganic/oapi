from __future__ import annotations

import json
import typing
from pathlib import Path
from urllib.error import HTTPError

import pytest
import sob
from servers import Response, http_test_server

from oapi.errors import OAPIReferenceLoopError, OAPIReferencePointerError
from oapi.oas.model import (
    OpenAPI,
    Properties,
    Reference,
    Schema,
)
from oapi.oas.references import Resolver, _Document


def _openapi(data: dict[str, typing.Any]) -> OpenAPI:
    open_api: OpenAPI = OpenAPI(data)
    return open_api


def test_resolver_rejects_non_openapi_root() -> None:
    with pytest.raises(TypeError):
        Resolver(root="not-an-openapi")  # type: ignore[arg-type]


def test_resolver_rejects_non_callable_urlopen() -> None:
    open_api: OpenAPI = _openapi(
        {"openapi": "3.0.3", "info": {"title": "t", "version": "1"}}
    )
    with pytest.raises(TypeError):
        Resolver(open_api, urlopen="not-callable")  # type: ignore[arg-type]


def test_resolver_rejects_non_string_url() -> None:
    open_api: OpenAPI = _openapi(
        {"openapi": "3.0.3", "info": {"title": "t", "version": "1"}}
    )
    with pytest.raises(TypeError):
        Resolver(open_api, url=123)  # type: ignore[arg-type]


def test_document_requires_an_inferable_url() -> None:
    open_api: OpenAPI = _openapi(
        {"openapi": "3.0.3", "info": {"title": "t", "version": "1"}}
    )
    resolver: Resolver = Resolver(
        open_api, url="http://example.com/openapi.json"
    )
    with pytest.raises(ValueError, match="You must provide a URL"):
        _Document(resolver, root=open_api, url=None)


def test_document_rejects_non_resolver_argument() -> None:
    open_api: OpenAPI = _openapi(
        {"openapi": "3.0.3", "info": {"title": "t", "version": "1"}}
    )
    with pytest.raises(TypeError):
        _Document(
            "not-a-resolver",  # type: ignore[arg-type]
            root=open_api,
            url="http://example.com/openapi.json",
        )


def test_document_normalizes_a_path_url_to_str() -> None:
    open_api: OpenAPI = _openapi(
        {"openapi": "3.0.3", "info": {"title": "t", "version": "1"}}
    )
    resolver: Resolver = Resolver(
        open_api, url="http://example.com/openapi.json"
    )
    path: Path = Path("/tmp/openapi.json")
    document: _Document = _Document(resolver, open_api, url=path)
    assert document.url == str(path)
    assert isinstance(document.url, str)


def test_document_infers_url_from_roots_model_url() -> None:
    open_api: OpenAPI = _openapi(
        {"openapi": "3.0.3", "info": {"title": "t", "version": "1"}}
    )
    sob.set_model_url(open_api, "http://example.com/inferred.json")
    resolver: Resolver = Resolver(
        open_api, url="http://example.com/openapi.json"
    )
    document: _Document = _Document(resolver, open_api)
    assert document.url == "http://example.com/inferred.json"


def test_get_absolute_url_and_get_url_pointer() -> None:
    open_api: OpenAPI = _openapi(
        {"openapi": "3.0.3", "info": {"title": "t", "version": "1"}}
    )
    resolver: Resolver = Resolver(
        open_api, url="http://example.com/dir/openapi.json"
    )
    document: _Document = _Document(
        resolver, open_api, url="http://example.com/dir/openapi.json"
    )
    assert document.get_absolute_url("other.json") == (
        "http://example.com/dir/other.json"
    )
    url: str
    pointer: str
    url, pointer = document.get_url_pointer("other.json#/foo/bar")
    assert url == "http://example.com/dir/other.json"
    assert pointer == "#/foo/bar"


def test_dereference_rejects_a_non_model_argument() -> None:
    open_api: OpenAPI = _openapi(
        {"openapi": "3.0.3", "info": {"title": "t", "version": "1"}}
    )
    sob.set_model_url(open_api, "http://example.com/openapi.json")
    resolver: Resolver = Resolver(open_api)
    document: _Document = resolver.documents[""]
    with pytest.raises(TypeError):
        document.dereference("just a string")  # type: ignore[arg-type]


def test_dereference_object_properties_rejects_an_empty_ref() -> None:
    open_api: OpenAPI = _openapi(
        {"openapi": "3.0.3", "info": {"title": "t", "version": "1"}}
    )
    sob.set_model_url(open_api, "http://example.com/openapi.json")
    resolver: Resolver = Resolver(open_api)
    document: _Document = resolver.documents[""]
    schema: Schema = Schema()
    schema.items = Reference({"$ref": ""})
    with pytest.raises(ValueError, match=r'\{"\$ref": ""\}'):
        document.dereference_object_properties(schema)


def test_dereference_array_items_rejects_an_empty_ref() -> None:
    open_api: OpenAPI = _openapi(
        {"openapi": "3.0.3", "info": {"title": "t", "version": "1"}}
    )
    sob.set_model_url(open_api, "http://example.com/openapi.json")
    resolver: Resolver = Resolver(open_api)
    document: _Document = resolver.documents[""]
    schema: Schema = Schema()
    schema.all_of = [Reference({"$ref": ""})]
    all_of: typing.Sequence[Reference | Schema] | None = schema.all_of
    assert isinstance(all_of, sob.abc.Array)
    with pytest.raises(ValueError, match=r'\{"\$ref": ""\}'):
        document.dereference_array_items(all_of)


def test_dereference_dictionary_values_rejects_an_empty_ref() -> None:
    open_api: OpenAPI = _openapi(
        {"openapi": "3.0.3", "info": {"title": "t", "version": "1"}}
    )
    sob.set_model_url(open_api, "http://example.com/openapi.json")
    resolver: Resolver = Resolver(open_api)
    document: _Document = resolver.documents[""]
    schema: Schema = Schema()
    schema.properties = Properties({"x": Reference({"$ref": ""})})
    properties: Properties | None = schema.properties
    assert isinstance(properties, sob.abc.Dictionary)
    with pytest.raises(ValueError, match=r'\{"\$ref": ""\}'):
        document.dereference_dictionary_values(properties)


def test_dereference_raises_loop_error_for_self_referencing_array() -> None:
    """
    `Schema.items` is a direct `Reference | Schema` attribute (not nested
    inside a dict/list container), so a schema whose `items` refers back
    to itself is visited directly by `dereference_object_properties` --
    unlike a self-reference nested inside `properties`, which would only
    be reached with `recursive=True`, and `recursive=True` is exactly
    the setting under which `dereference()` catches and suppresses
    `OAPIReferenceLoopError` (see the module docstring/`dereference`
    implementation: `except OAPIReferenceLoopError: if not recursive:
    raise`). Calling `_Document.dereference` directly with
    `recursive=False` is therefore the only way to observe this real,
    reachable error -- no public caller currently passes
    `recursive=False`, but the code path is real production code, not
    dead code invented for this test.
    """
    open_api: OpenAPI = _openapi(
        {
            "openapi": "3.0.3",
            "info": {"title": "t", "version": "1"},
            "paths": {},
            "components": {
                "schemas": {
                    "Node": {
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/Node"},
                    }
                }
            },
        }
    )
    sob.set_model_url(open_api, "http://example.com/openapi.json")
    resolver: Resolver = Resolver(open_api)
    document: _Document = resolver.documents[""]
    assert open_api.components is not None
    assert open_api.components.schemas is not None
    node: Schema = open_api.components.schemas["Node"]
    with pytest.raises(OAPIReferenceLoopError):
        document.dereference(node, recursive=False)


def test_dereference_with_recursive_true_silently_absorbs_the_loop() -> None:
    """
    Contrasts with the test above: the real, public-facing behavior for
    `recursive=True` (what every public caller actually uses) is to
    swallow the loop error rather than raise it, leaving the
    self-referencing structure as-is. This is current, real behavior,
    not something this test judges as correct or incorrect.
    """
    open_api: OpenAPI = _openapi(
        {
            "openapi": "3.0.3",
            "info": {"title": "t", "version": "1"},
            "paths": {},
            "components": {
                "schemas": {
                    "Node": {
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/Node"},
                    }
                }
            },
        }
    )
    sob.set_model_url(open_api, "http://example.com/openapi.json")
    resolver: Resolver = Resolver(open_api)
    resolver.dereference()


def test_resolve_raises_pointer_error_for_a_falsy_but_existing_target() -> (
    None
):
    """
    `resolve_pointer` (the `jsonpointer` library) raises its own
    `JsonPointerException` for a pointer path that doesn't exist at
    all -- that is a different, real failure mode, not this one.
    `OAPIReferencePointerError` is specifically for a pointer that
    *does* resolve, but to a falsy value (e.g. a real, empty
    `sob.Array`), which the `if not model:` check at the end of
    `resolve()` treats as "not found."
    """
    open_api: OpenAPI = _openapi(
        {
            "openapi": "3.0.3",
            "info": {"title": "t", "version": "1"},
            "paths": {},
            "components": {
                "schemas": {"Color": {"type": "string", "enum": []}}
            },
        }
    )
    sob.set_model_url(open_api, "http://example.com/openapi.json")
    resolver: Resolver = Resolver(open_api)
    with pytest.raises(OAPIReferencePointerError):
        resolver.resolve("#/components/schemas/Color/enum")


def test_resolve_raises_type_error_for_a_null_valued_target() -> None:
    """
    Resolving a pointer to a location whose real, unmarshalled value is
    `None` hits `_unmarshal_resolved_reference`'s own `TypeError` guard
    (it only accepts already-`sob.abc.Model` results, or something
    `sob.unmarshal` can turn into one) before `resolve()`'s own
    falsy-value check is ever reached.
    """
    open_api: OpenAPI = _openapi(
        {
            "openapi": "3.0.3",
            "info": {"title": "t", "version": "1", "description": None},
            "paths": {},
        }
    )
    sob.set_model_url(open_api, "http://example.com/openapi.json")
    resolver: Resolver = Resolver(open_api)
    with pytest.raises(TypeError):
        resolver.resolve("#/info/description")


def test_resolve_reference_follows_a_chain_to_the_real_target() -> None:
    open_api: OpenAPI = _openapi(
        {
            "openapi": "3.0.3",
            "info": {"title": "t", "version": "1"},
            "paths": {},
            "components": {
                "schemas": {
                    "A": {"type": "string"},
                    "B": {"$ref": "#/components/schemas/A"},
                }
            },
        }
    )
    sob.set_model_url(open_api, "http://example.com/openapi.json")
    resolver: Resolver = Resolver(open_api)
    assert open_api.components is not None
    assert open_api.components.schemas is not None
    b_reference: Reference = open_api.components.schemas["B"]
    resolved: sob.abc.Model = resolver.resolve_reference(b_reference)
    assert isinstance(resolved, Schema)
    assert resolved.type_ == "string"


def test_resolve_reference_recurses_through_a_two_level_chain() -> None:
    """
    `B` above resolves to a real `Schema` in one hop, so it never
    exercises `resolve_reference`'s own recursive
    `self.resolve_reference(resolved_model, types=types)` call (that
    branch only fires when the *result* of resolving one reference is
    itself still a `Reference`). This test adds one more hop
    (`C -> B -> A`) specifically to reach that recursive call for real.
    """
    open_api: OpenAPI = _openapi(
        {
            "openapi": "3.0.3",
            "info": {"title": "t", "version": "1"},
            "paths": {},
            "components": {
                "schemas": {
                    "A": {"type": "string"},
                    "B": {"$ref": "#/components/schemas/A"},
                    "C": {"$ref": "#/components/schemas/B"},
                }
            },
        }
    )
    sob.set_model_url(open_api, "http://example.com/openapi.json")
    resolver: Resolver = Resolver(open_api)
    assert open_api.components is not None
    assert open_api.components.schemas is not None
    c_reference: Reference = open_api.components.schemas["C"]
    resolved: sob.abc.Model = resolver.resolve_reference(c_reference)
    assert isinstance(resolved, Schema)
    assert resolved.type_ == "string"


def test_resolve_reference_rejects_an_empty_ref() -> None:
    open_api: OpenAPI = _openapi(
        {"openapi": "3.0.3", "info": {"title": "t", "version": "1"}}
    )
    sob.set_model_url(open_api, "http://example.com/openapi.json")
    resolver: Resolver = Resolver(open_api)
    empty_reference: Reference = Reference({"$ref": ""})
    with pytest.raises(ValueError, match=r'\{"\$ref": ""\}'):
        resolver.resolve_reference(empty_reference)


def test_resolve_reference_raises_a_real_loop_error_for_self_reference() -> (
    None
):
    open_api: OpenAPI = _openapi(
        {
            "openapi": "3.0.3",
            "info": {"title": "t", "version": "1"},
            "paths": {},
            "components": {
                "schemas": {
                    "SelfRef": {"$ref": "#/components/schemas/SelfRef"}
                }
            },
        }
    )
    sob.set_model_url(open_api, "http://example.com/openapi.json")
    resolver: Resolver = Resolver(open_api)
    assert open_api.components is not None
    assert open_api.components.schemas is not None
    self_reference: Reference = open_api.components.schemas["SelfRef"]
    with pytest.raises(OAPIReferenceLoopError):
        resolver.resolve_reference(self_reference)


def test_get_relative_url_for_the_root_document_itself() -> None:
    open_api: OpenAPI = _openapi(
        {"openapi": "3.0.3", "info": {"title": "t", "version": "1"}}
    )
    resolver: Resolver = Resolver(
        open_api, url="http://example.com/docs/openapi.json"
    )
    assert (
        resolver.get_relative_url("http://example.com/docs/openapi.json") == ""
    )


def test_get_relative_url_for_a_different_absolute_url() -> None:
    open_api: OpenAPI = _openapi(
        {"openapi": "3.0.3", "info": {"title": "t", "version": "1"}}
    )
    resolver: Resolver = Resolver(
        open_api, url="http://example.com/docs/openapi.json"
    )
    assert (
        resolver.get_relative_url("http://example.com/docs/other.json")
        == "other.json"
    )


def test_get_relative_url_passes_through_a_relative_looking_url() -> None:
    open_api: OpenAPI = _openapi(
        {"openapi": "3.0.3", "info": {"title": "t", "version": "1"}}
    )
    resolver: Resolver = Resolver(
        open_api, url="http://example.com/docs/openapi.json"
    )
    assert resolver.get_relative_url("other.json") == "other.json"


def test_get_relative_url_for_an_empty_url() -> None:
    open_api: OpenAPI = _openapi(
        {"openapi": "3.0.3", "info": {"title": "t", "version": "1"}}
    )
    resolver: Resolver = Resolver(
        open_api, url="http://example.com/docs/openapi.json"
    )
    assert resolver.get_relative_url("") == ""


def test_resolver_resolves_a_reference_in_a_real_external_http_document() -> (
    None
):
    external_document: dict[str, object] = {
        "openapi": "3.0.3",
        "info": {"title": "external", "version": "1"},
        "paths": {},
        "components": {
            "schemas": {
                "Widget": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                }
            }
        },
    }
    with http_test_server(
        responses={
            ("GET", "/external.json"): Response(
                status=200,
                body=json.dumps(external_document).encode(),
                headers={"Content-type": "application/json"},
            )
        }
    ) as server:
        open_api: OpenAPI = _openapi(
            {
                "openapi": "3.0.3",
                "info": {"title": "t", "version": "1"},
                "paths": {},
                "components": {
                    "schemas": {
                        "Local": {
                            "$ref": (
                                f"{server.url}/external.json"
                                "#/components/schemas/Widget"
                            )
                        }
                    }
                },
            }
        )
        sob.set_model_url(open_api, f"{server.url}/openapi.json")
        resolver: Resolver = Resolver(open_api)
        assert open_api.components is not None
        assert open_api.components.schemas is not None
        local_reference: Reference = open_api.components.schemas["Local"]
        resolved: sob.abc.Model = resolver.resolve_reference(local_reference)
        assert isinstance(resolved, sob.abc.Dictionary)
        assert resolved["type"] == "object"


def test_get_document_raises_a_real_http_error_for_a_404() -> None:
    with http_test_server(
        responses={("GET", "/missing.json"): Response(status=404, body=b"n/a")}
    ) as server:
        open_api: OpenAPI = _openapi(
            {"openapi": "3.0.3", "info": {"title": "t", "version": "1"}}
        )
        sob.set_model_url(open_api, f"{server.url}/openapi.json")
        resolver: Resolver = Resolver(open_api)
        with pytest.raises(HTTPError):
            resolver.get_document(f"{server.url}/missing.json")


def test_get_document_raises_a_real_file_not_found_error() -> None:
    open_api: OpenAPI = _openapi(
        {"openapi": "3.0.3", "info": {"title": "t", "version": "1"}}
    )
    sob.set_model_url(open_api, "/tmp/openapi.json")
    resolver: Resolver = Resolver(open_api, urlopen=open)
    with pytest.raises(FileNotFoundError):
        resolver.get_document("/tmp/does-not-exist-oapi-test.json")
