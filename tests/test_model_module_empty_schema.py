from __future__ import annotations

import typing

import pytest

from oapi.model import ModelModule
from oapi.oas.model import OpenAPI


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
