"""
This module provides functionality for resolving references within an instance
of `oapi.oas.model.OpenAPI`.

For example, the following will replace all references in the Open API
document `open_api_document` with the objects targeted by the `ref` property
of the reference:

```python
from urllib.request import urlopen
from oapi.oas.model import OpenAPI

with urlopen(
    'https://raw.githubusercontent.com/OAI/OpenAPI-Specification/master/'
    'examples/v3.0/callback-example.yaml'
) as response:
    open_api_document = OpenAPI(response)

resolver = Resolver(open_api_document)
resolver.dereference()
```
"""
import sob
from typing import Any, Callable, Dict, Optional, Sequence, Tuple, Union
from urllib.error import HTTPError
from urllib.parse import ParseResult, urljoin, urlparse
from urllib.request import urlopen as _urlopen
from jsonpointer import resolve_pointer  # type: ignore
from .model import OpenAPI, Reference
from ..errors import ReferenceLoopError


def _unmarshal_resolved_reference(
    resolved_reference: sob.abc.MarshallableTypes,
    url: Optional[str],
    pointer: str,
    types: Union[Sequence[Union[sob.abc.Property, type]], sob.abc.Types] = (),
) -> sob.abc.Model:
    if types or (not isinstance(resolved_reference, sob.abc.Model)):
        resolved_reference = sob.model.unmarshal(
            resolved_reference, types=types
        )
        # Re-assign the URL and pointer
        assert isinstance(resolved_reference, sob.abc.Model)
        sob.meta.url(resolved_reference, url)
        sob.meta.pointer(resolved_reference, pointer)
    return resolved_reference


class _Document:
    def __init__(
        self,
        resolver: "Resolver",
        root: sob.abc.Model,
        url: Optional[str] = None,
    ) -> None:
        assert isinstance(url, str)
        assert isinstance(resolver, Resolver)
        # Infer the document URL
        if (url is None) and isinstance(root, sob.abc.Model):
            url = sob.meta.get_url(root)
        self.resolver: Resolver = resolver
        self.root: sob.abc.Model = root
        self.pointers: Dict[str, Optional[sob.abc.Model]] = {}
        self.url: str = url

    def get_url_pointer(self, pointer: str) -> Tuple[str, str]:
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
        self, model: sob.abc.Model, recursive: bool = True
    ) -> None:
        """
        Recursively dereference this objects and all items/properties
        """
        try:
            if isinstance(model, sob.abc.Object):
                self.dereference_object_properties(model, recursive=recursive)
            elif isinstance(model, sob.abc.Array):
                self.dereference_array_items(model, recursive=recursive)
            elif isinstance(model, sob.abc.Dictionary):
                self.dereference_dictionary_values(model, recursive=recursive)
            else:
                raise TypeError(
                    "The argument must be an instance of "
                    f"`{sob.utilities.qualified_name(sob.model.Model)}`, "
                    f"not {repr(model)}"
                )
        except ReferenceLoopError:
            if not recursive:
                raise

    def prevent_infinite_recursion(
        self, model: sob.abc.Model
    ) -> Tuple[Optional[str], Optional[sob.abc.Model]]:
        """
        Prevent recursion errors by putting a placeholder `None` in place of
        the parent object in the `pointer` cache
        """
        pointer = sob.meta.get_pointer(model)
        existing_value: Optional[sob.abc.Model] = None
        if pointer:
            if pointer in self.pointers:
                existing_value = self.pointers[pointer]
            self.pointers[pointer] = None
        return pointer, existing_value

    def reset_recursion_placeholder(
        self, pointer: str, previous_value: Optional[sob.abc.Model]
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
        self, object_: sob.abc.Model, recursive: bool = True
    ) -> None:
        """
        Replace all references in this object's properties with the referenced
        object
        """
        object_meta = sob.meta.read(object_)
        # Prevent recursion errors
        pointer: Optional[str]
        existing: Optional[sob.abc.Model]
        pointer, existing = self.prevent_infinite_recursion(object_)
        for property_name, property_ in object_meta.properties.items():
            value = getattr(object_, property_name)
            if isinstance(value, Reference):
                assert value.ref
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
        self, array: sob.abc.Array, recursive: bool = True
    ) -> None:
        """
        Replace all references in this array with the referenced object
        """
        array_meta = sob.meta.read(array)
        # Prevent recursion errors
        pointer: Optional[str]
        existing: Optional[sob.abc.Model]
        pointer, existing = self.prevent_infinite_recursion(array)
        index: int
        item: Any
        for index, item in enumerate(array):
            if isinstance(item, Reference):
                assert item.ref
                array[index] = self.resolve(
                    item.ref,
                    types=array_meta.item_types or (),
                    dereference=recursive,
                )
            elif recursive and isinstance(item, sob.abc.Model):
                self.dereference(item, recursive=recursive)
        if pointer:
            self.reset_recursion_placeholder(pointer, existing)

    def dereference_dictionary_values(
        self, dictionary: sob.abc.Dictionary, recursive: bool = True
    ) -> None:
        """
        Replace all references in this dictionary with the referenced object
        """
        dictionary_meta = sob.meta.read(dictionary)

        # Prevent recursion errors
        pointer, existing = self.prevent_infinite_recursion(dictionary)
        key: str
        value: Any
        for key, value in dictionary.items():
            if isinstance(value, Reference):
                assert value.ref
                dictionary[key] = self.resolve(
                    value.ref,
                    types=dictionary_meta.value_types or (),
                    dereference=recursive,
                )
            elif recursive and isinstance(value, sob.abc.Model):
                self.dereference(value, recursive=recursive)
        if pointer:
            self.reset_recursion_placeholder(pointer, existing)

    def resolve(
        self,
        pointer: str,
        types: Union[
            sob.abc.Types, Sequence[Union[sob.abc.Property, type]]
        ] = (),
        dereference: bool = False,
    ) -> sob.abc.Model:
        """
        Return the object referenced by a pointer
        """
        if pointer in self.pointers:
            # This catches recursion errors
            if self.pointers[pointer] is None:
                raise ReferenceLoopError(pointer)
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
                    raise RuntimeError()
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
        model: Optional[sob.abc.Model] = self.pointers[pointer]
        assert model
        # The following is necessary in order to apply pointers to
        # dereferenced elements
        sob.meta.set_pointer(model, pointer)
        return model

    def dereference_all(self) -> None:
        self.dereference(self.root, recursive=True)


class Resolver:
    """
    This class should be used, with an instance of `oapi.oas.model.OpenAPI`, to
    resolve references.

    Parameters:

        - root (oapi.oas.model.OpenAPI): The OpenAPI document against which
          pointers will be resolved.

        - url (str): The URL or file path from where `root` was retrieved. The
          base URL for relative paths will be the directory above this URL.
          This will not typically be needed, as it can be inferred from most
          `Model` instances.

        - urlopen (collections.Callable): If provided, this should be a
          function taking one argument (a `str`), which can be used in lieu
          of `urllib.request.urlopen` to retrieve a document and return an
          instance of a sub-class of `IOBase` (such as
          `http.client.HTTPResponse`). This should be used if authentication is
          needed in order to retrieve external references in the document,
          or if local file paths will be referenced instead of web URL's (use
          `open` as the value for the `urlopen` parameter
          in this case).
    """

    def __init__(
        self,
        root: OpenAPI,
        url: str = None,
        urlopen: Callable = _urlopen,
    ) -> None:
        # Ensure arguments are of the correct types
        assert callable(urlopen)
        assert isinstance(root, OpenAPI)
        assert isinstance(url, (str, sob.utilities.types.NoneType))
        # This is the function used to open external pointer references
        self.urlopen = urlopen
        # Infer the URL from the `OpenAPI` document, if not explicitly provided
        if url is None:
            url = sob.meta.url(root) or ""
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
                        self, sob.model.detect_format(response)[0], url=url
                    )
            except (HTTPError, FileNotFoundError) as error:
                sob.errors.append_exception_text(error, ": {url}")
                raise error
        return self.documents[url]

    def dereference(self) -> None:
        """
        Dereference the primary document
        """
        self.documents[""].dereference_all()

    def resolve(
        self,
        pointer: str,
        types: Union[
            sob.abc.Types, Sequence[Union[type, sob.abc.Property]]
        ] = (),
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
        types: Union[
            sob.abc.Types, Sequence[Union[type, sob.abc.Property]]
        ] = (),
    ) -> sob.abc.Model:
        """
        Retrieve a referenced object.

        Parameters:

        - reference (oapi.oas.model.Reference)
        - types ([Union[type, sob.abc.Property]]) = ()
        """
        url: str = sob.meta.get_url(reference) or ""
        assert reference.ref
        pointer: str = urljoin(
            sob.meta.get_pointer(reference) or "",
            reference.ref,
        )
        resolved_model: sob.abc.Model = self.get_document(url).resolve(
            pointer, types
        )
        if resolved_model is reference or (
            isinstance(resolved_model, Reference)
            and resolved_model.ref == reference.ref
        ):
            raise ReferenceLoopError(
                f"`Reference` instance is self-referential: {pointer}"
            )
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
                    relative_url = sob.utilities.string.url_relative_to(
                        url, self.url
                    )
            else:
                relative_url = url
        return relative_url
