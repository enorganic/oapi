"""
This module provides functionality for resolving references within an instance
of `oapi.oas.OpenAPI`.

The following will replace all references in the Open API
document `open_api_document` with the objects targeted by the `ref` property
of the reference.

Example:

    import yaml
    from urllib.request import urlopen
    from oapi.oas import OpenAPI
    from oapi.oas.references import Resolver


    with urlopen(
        "https://raw.githubusercontent.com/OAI/OpenAPI-Specification/3.1.1/"
        "examples/v3.0/callback-example.yaml"
    ) as response:
        open_api_document = OpenAPI(
            yaml.safe_load(response)
        )

    resolver = Resolver(open_api_document)
    resolver.dereference()
"""

from __future__ import annotations

import json
from functools import wraps
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, cast
from urllib.error import HTTPError
from urllib.parse import ParseResult, urljoin, urlparse
from urllib.request import Request
from urllib.request import urlopen as urllib_request_urlopen

import sob
from jsonpointer import resolve_pointer  # type: ignore

from oapi.errors import OAPIReferenceLoopError, OAPIReferencePointerError
from oapi.oas.model import OpenAPI, Reference

if TYPE_CHECKING:
    from collections.abc import Sequence


def _unmarshal_resolved_reference(
    resolved_reference: sob.abc.MarshallableTypes,
    url: str | None,
    pointer: str,
    types: Sequence[sob.abc.Property | type] | sob.abc.Types = (),
) -> sob.abc.Model:
    if types or (not isinstance(resolved_reference, sob.abc.Model)):
        resolved_reference = sob.unmarshal(resolved_reference, types=types)
        # Re-assign the URL and pointer
        if not isinstance(resolved_reference, sob.abc.Model):
            raise TypeError(resolved_reference)
        sob.set_model_url(resolved_reference, url)
        sob.set_model_pointer(resolved_reference, pointer)
    return resolved_reference


@wraps(urllib_request_urlopen)
def _urlopen(
    url: str | Request, *args: Any, **kwargs: Any
) -> sob.abc.Readable:
    response: sob.abc.Readable = urllib_request_urlopen(  # noqa: S310
        url, *args, **kwargs
    )
    response_url: str = response.url  # type: ignore
    if response_url.lower().endswith(("yaml", "yml")):
        # Use pyyaml to parse yaml files, if it is installed
        try:
            import yaml  # type: ignore
        except ImportError:
            pass
        else:
            response = cast(
                sob.abc.Readable,
                BytesIO(
                    json.dumps(
                        yaml.safe_load(response)  # type: ignore
                    ).encode("utf-8")
                ),
            )
            response.url = response_url  # type: ignore
    return response


class _Document:
    def __init__(
        self,
        resolver: Resolver,
        root: sob.abc.Model,
        url: str | Path | None = None,
    ) -> None:
        message: str
        # Attempt to Infer the document URL
        if (url is None) and isinstance(root, sob.abc.Model):
            url = sob.get_model_url(root)
        if isinstance(url, Path):
            url = str(url)
        if url is None:
            message = (
                "You must provide a URL or file path to the OpenAPI document "
                "in order to resolve references"
            )
            raise ValueError(message)
        if not isinstance(resolver, Resolver):
            raise TypeError(resolver)
        self.resolver: Resolver = resolver
        self.root: sob.abc.Model = root
        self.pointers: dict[str, sob.abc.Model | None] = {}
        self.url: str = url

    def get_url_pointer(self, pointer: str) -> tuple[str, str]:
        """
        Get an absolute URL + relative pointer
        """
        url: str
        separator: str
        url, separator, pointer = pointer.partition("#")
        url = self.get_absolute_url(url)
        return url, f"{separator}{pointer}"

    def get_absolute_url(self, url: str) -> str:
        """
        Get an absolute URL from a (possibly relative) URL
        """
        parse_result = urlparse(url)
        if not parse_result.scheme:
            url = urljoin(self.url, url.lstrip("/ "))
        return url

    def dereference(
        self, model: sob.abc.Model, *, recursive: bool = True
    ) -> None:
        """
        Recursively dereference this objects and all items/properties
        """
        message: str
        try:
            if isinstance(model, sob.abc.Object):
                self.dereference_object_properties(model, recursive=recursive)
            elif isinstance(model, sob.abc.Array):
                self.dereference_array_items(model, recursive=recursive)
            elif isinstance(model, sob.abc.Dictionary):
                self.dereference_dictionary_values(model, recursive=recursive)
            else:
                message = (
                    "The argument must be an instance of "
                    f"`{sob.utilities.get_qualified_name(sob.Model)}`, "
                    f"not {model!r}"
                )
                raise TypeError(message)
        except OAPIReferenceLoopError:
            if not recursive:
                raise

    def prevent_infinite_recursion(
        self, model: sob.abc.Model
    ) -> tuple[str | None, sob.abc.Model | None]:
        """
        Prevent recursion errors by putting a placeholder `None` in place of
        the parent object in the `pointer` cache
        """
        pointer: str | None = sob.get_model_pointer(model)
        existing_value: sob.abc.Model | None = None
        if pointer:
            if pointer in self.pointers:
                existing_value = self.pointers[pointer]
            self.pointers[pointer] = None
        return pointer, existing_value

    def reset_recursion_placeholder(
        self, pointer: str, previous_value: sob.abc.Model | None
    ) -> None:
        """
        Cleanup a placeholder created by the `prevent_infinite_recursion`
        method
        """
        if pointer and (pointer in self.pointers):
            if previous_value is None:
                del self.pointers[pointer]
            else:
                self.pointers[pointer] = previous_value

    def dereference_object_properties(
        self, object_: sob.abc.Object, *, recursive: bool = True
    ) -> None:
        """
        Replace all references in this object's properties with the referenced
        object
        """
        message: str
        object_meta: sob.abc.ObjectMeta | None = sob.read_object_meta(object_)
        if object_meta is None:
            message = f"No metadata found for the object:\n{object_!r}\n"
            raise ValueError(message)
        if TYPE_CHECKING:
            assert object_meta.properties is not None
        # Prevent recursion errors
        pointer: str | None
        existing: sob.abc.Model | None
        pointer, existing = self.prevent_infinite_recursion(object_)
        property_name: str
        property_: sob.abc.Property
        for property_name, property_ in object_meta.properties.items():
            value = getattr(object_, property_name)
            if isinstance(value, Reference):
                if not value.ref:
                    raise ValueError(value)
                setattr(
                    object_,
                    property_name,
                    self.resolve(
                        value.ref, types=(property_,), dereference=recursive
                    ),
                )
            elif recursive and isinstance(value, sob.abc.Model):
                self.dereference(value, recursive=recursive)
        if pointer:
            self.reset_recursion_placeholder(pointer, existing)

    def dereference_array_items(
        self, array: sob.abc.Array, *, recursive: bool = True
    ) -> None:
        """
        Replace all references in this array with the referenced object
        """
        message: str
        array_meta: sob.abc.ArrayMeta | None = sob.read_array_meta(array)
        # Prevent recursion errors
        pointer: str | None
        existing: sob.abc.Model | None
        pointer, existing = self.prevent_infinite_recursion(array)
        index: int
        item: Any
        for index, item in enumerate(array):
            if isinstance(item, Reference):
                if not item.ref:
                    raise ValueError(item)
                array[index] = self.resolve(
                    item.ref,
                    types=(array_meta.item_types or () if array_meta else ()),
                    dereference=recursive,
                )
            elif recursive and isinstance(item, sob.abc.Model):
                self.dereference(item, recursive=recursive)
        if pointer:
            self.reset_recursion_placeholder(pointer, existing)

    def dereference_dictionary_values(
        self, dictionary: sob.abc.Dictionary, *, recursive: bool = True
    ) -> None:
        """
        Replace all references in this dictionary with the referenced object
        """
        message: str
        dictionary_meta: sob.abc.DictionaryMeta | None = (
            sob.read_dictionary_meta(dictionary)
        )
        # Prevent recursion errors
        pointer, existing = self.prevent_infinite_recursion(dictionary)
        key: str
        value: Any
        for key, value in dictionary.items():
            if isinstance(value, Reference):
                if not value.ref:
                    raise ValueError(value)
                dictionary[key] = self.resolve(
                    value.ref,
                    types=(
                        dictionary_meta.value_types or ()
                        if dictionary_meta
                        else ()
                    ),
                    dereference=recursive,
                )
            elif recursive and isinstance(value, sob.abc.Model):
                self.dereference(value, recursive=recursive)
        if pointer:
            self.reset_recursion_placeholder(pointer, existing)

    def resolve(
        self,
        pointer: str,
        types: sob.abc.Types | Sequence[sob.abc.Property | type] = (),
        *,
        dereference: bool = False,
    ) -> sob.abc.Model:
        """
        Return the object referenced by a pointer
        """
        if pointer in self.pointers:
            # This catches recursion errors
            if self.pointers[pointer] is None:
                raise OAPIReferenceLoopError(pointer)
        else:
            self.pointers[pointer] = None
            if pointer.startswith("#"):
                # Resolve a reference within the same Open API document
                resolved = resolve_pointer(self.root, pointer[1:])
                # Cast the resolved reference as one of the given types
                resolved = _unmarshal_resolved_reference(
                    resolved, self.url, pointer, types=types
                )
                if resolved is None:
                    raise RuntimeError
            else:
                # Resolve a reference from another Open API document
                url, document_pointer = self.get_url_pointer(pointer)
                # Retrieve the document
                document = self.resolver.get_document(
                    urljoin(self.url, url.lstrip("/"))
                )
                # Resolve the pointer, if needed
                if document_pointer:
                    resolved = document.resolve(document_pointer, types)
                else:
                    resolved = document.root
                    # Cast the resolved reference as one of the given types
                    resolved = _unmarshal_resolved_reference(
                        resolved, url, document_pointer, types=types
                    )
            # Recursively dereference
            if dereference and isinstance(resolved, sob.abc.Model):
                self.dereference(resolved, recursive=dereference)
            # Cache the resolved pointer
            self.pointers[pointer] = resolved
        model: sob.abc.Model | None = self.pointers[pointer]
        if not model:
            raise OAPIReferencePointerError(pointer)
        # The following is necessary in order to apply pointers to
        # dereferenced elements
        sob.set_model_pointer(model, pointer)
        return model

    def dereference_all(self) -> None:
        self.dereference(self.root, recursive=True)


class Resolver:
    """
    This class should be used, with an instance of `oapi.oas.OpenAPI`, to
    resolve references.

    Parameters:
        root: The OpenAPI document against which
            pointers will be resolved.
        url: The URL or file path from where `root` was retrieved. The
            base URL for relative paths will be the directory above this
            URL. This will not typically be needed, as it can be inferred
            from most `Model` instances.
        urlopen: If provided, this should be a
            function taking one argument (a `str`), which can be used in
            lieu of `urllib.request.urlopen` to retrieve a document and
            return an instance of a sub-class of `IOBase` (such as
            `http.client.HTTPResponse`). This should be used if
            authentication is needed in order to retrieve external
            references in the document, or if local file paths will be
            referenced instead of web URL's (use `open` as the value for
            the `urlopen` parameter in this case).
    """

    def __init__(
        self,
        root: OpenAPI,
        url: str | None = None,
        urlopen: Callable = _urlopen,
    ) -> None:
        # Ensure arguments are of the correct types
        if not callable(urlopen):
            raise TypeError(urlopen)
        if not isinstance(root, OpenAPI):
            raise TypeError(root)
        if not ((url is None) or isinstance(url, str)):
            raise TypeError(url)
        # This is the function used to open external pointer references
        self.urlopen = urlopen
        # Infer the URL from the `OpenAPI` document, if not explicitly provided
        if url is None:
            url = sob.get_model_url(root) or ""
        self.url = url
        # This is the primary document--the one we are resolving
        document: _Document = _Document(self, root, url)
        # Store the primary document both by URL and under the key "#" (for
        # convenient reference)
        self.documents = {url: document}
        if url != "":
            self.documents[""] = document

    def get_document(self, url: str) -> _Document:
        """
        Retrieve a document by URL, or use the cached document if previously
        retrieved
        """
        if url not in self.documents:
            try:
                with self.urlopen(url) as response:
                    self.documents[url] = _Document(
                        self, sob.unmarshal(sob.deserialize(response)), url=url
                    )
            except (HTTPError, FileNotFoundError) as error:
                sob.errors.append_exception_text(error, f": {url}")
                raise
        return self.documents[url]

    def dereference(self) -> None:
        """
        Dereference the primary document
        """
        self.documents[""].dereference_all()

    def resolve(
        self,
        pointer: str,
        types: sob.abc.Types | Sequence[type | sob.abc.Property] = (),
        *,
        dereference: bool = False,
    ) -> sob.abc.Model:
        """
        Retrieve an object at the specified pointer
        """
        url, pointer = self.documents[""].get_url_pointer(pointer)
        return self.documents[url].resolve(
            pointer, types, dereference=dereference
        )

    def resolve_reference(
        self,
        reference: Reference,
        types: sob.abc.Types | Sequence[type | sob.abc.Property] = (),
    ) -> sob.abc.Model:
        """
        Retrieve a referenced object.

        Parameters:
            reference:
            types:
        """
        message: str
        url: str = sob.get_model_url(reference) or ""
        if not reference.ref:
            raise ValueError(reference)
        pointer: str = urljoin(
            sob.get_model_pointer(reference) or "",
            reference.ref,
        )
        resolved_model: sob.abc.Model = self.get_document(url).resolve(
            pointer, types
        )
        if resolved_model is reference or (
            isinstance(resolved_model, Reference)
            and resolved_model.ref == reference.ref
        ):
            message = f"`Reference` instance is self-referential: {pointer}"
            raise OAPIReferenceLoopError(message)
        if isinstance(resolved_model, Reference):
            resolved_model = self.resolve_reference(
                resolved_model, types=types
            )
        return resolved_model

    def get_relative_url(self, url: str) -> str:
        """
        Given a URL, return that URL relative to the base document
        """
        relative_url: str = ""
        if url:
            parse_result: ParseResult = urlparse(url)
            # Determine if the URL is absolute or relative
            if parse_result.netloc or parse_result.scheme == "file":
                # Only include the relative URL if it is not the root document
                if url == self.url:
                    relative_url = ""
                else:
                    relative_url = sob.utilities.get_url_relative_to(
                        url, self.url
                    )
            else:
                relative_url = url
        return relative_url
