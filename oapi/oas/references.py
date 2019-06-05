"""
This module provides functionality for resolving references within an instance of `oapi.oas.model.OpenAPI`.

For example, the following will replace all references in the Open API document `open_api_document` with the objects
targeted by the `ref` property of the reference:

```python
from urllib.request import urlopen
from oapi.oas.model import OpenAPI

with urlopen(
    'https://raw.githubusercontent.com/OAI/OpenAPI-Specification/master/examples/v3.0/callback-example.yaml'
) as response:
    open_api_document = OpenAPI(response)

resolver = Resolver(open_api_document)
resolver.dereference()
```
"""

from collections import OrderedDict

import collections
from urllib import request
from urllib.parse import urlparse, urljoin

from sob import meta


from jsonpointer import resolve_pointer
from sob.utilities import qualified_name

try:
    import typing
    from typing import Union, Any, Sequence, Dict
except ImportError:
    typing = Union = Any = Sequence = Dict = None

from sob.model import Model, Array, Dictionary, Object, unmarshal, detect_format
from sob.properties import Property
from sob.properties.types import NoneType
from sob.errors import get_exception_text

from .model import Reference, OpenAPI
from ..errors import ReferenceLoopError


class _Document(object):

    def __init__(
        self,
        resolver,  # type: Resolver
        root,  # type: Union[Sequence, Dict, Array, Dictionary]
        url=None,  # type: Optional[str]
    ):
        # type: (...) -> None

        assert isinstance(url, str)
        assert isinstance(resolver, Resolver)

        # Infer the document URL
        if (url is None) and isinstance(root, Model):
            url = meta.url(root)

        self.resolver = resolver
        self.root = root
        self.pointers = {}
        self.url = url

    def get_url_pointer(self, pointer):
        # type: (str) -> Tuple[str, str]
        """
        Get an absolute URL + relative pointer
        """
        pointer_split = pointer.split('#')
        url = self.get_absolute_url(pointer_split[0])

        if len(pointer_split) > 1:
            pointer = '#'.join(pointer_split[1:])
            if pointer[0] != '#':
                pointer = '#' + pointer
        else:
            pointer = None

        return url, pointer

    def get_absolute_url(self, url):
        # type: (str) -> str
        """
        Get an absolute URL from a (possibly relative) URL
        """
        parse_result = urlparse(url)

        if not parse_result.scheme:
            url = urljoin(
                self.url,
                url.lstrip('/ ')
            )

        return url

    def dereference(self, model_instance, recursive=True):
        # type: (Model, bool) -> None
        """
        Recursively dereference this objects and all items/properties
        """

        try:
            if isinstance(model_instance, Object):
                self.dereference_object_properties(model_instance, recursive=recursive)
            elif isinstance(
                model_instance,
                (Array, collections.Sequence, collections.Set)
            ) and not isinstance(
                model_instance,
                (str, bytes)
            ):
                self.dereference_array_items(model_instance, recursive=recursive)
            elif isinstance(model_instance, (Dictionary, dict, OrderedDict)):
                self.dereference_dictionary_values(model_instance, recursive=recursive)
            else:
                raise TypeError(
                    'The argument must be an instance of `%s`, not %s' % (
                        qualified_name(Model),
                        repr(model_instance)
                    )
                )
        except (ReferenceLoopError, RecursionError):
            if not recursive:
                raise

    def prevent_infinite_recursion(self, model_instance):
        # type: (Model) -> Model
        """
        Prevent recursion errors by putting a placeholder `None` in place of the parent object in the `pointer` cache
        """
        pointer = meta.pointer(model_instance)
        existing_value = None  # type: Model
        if pointer:
            if pointer in self.pointers:
                existing_value = self.pointers[pointer]
            self.pointers[pointer] = None
        return pointer, existing_value

    def reset_recursion_placeholder(self, pointer, previous_value):
        # type: (Optional[str], Optional[Model]) -> None
        """
        Cleanup a placeholder created by the `prevent_infinite_recursion` method
        """
        if pointer and (pointer in self.pointers):
            if previous_value is None:
                del self.pointers[pointer]
            else:
                self.pointers[pointer] = previous_value

    def dereference_object_properties(self, object_, recursive=True):
        # type: (Model, bool) -> None
        """
        Replace all references in this object's properties with the referenced object
        """
        object_meta = meta.read(object_)

        # Prevent recursion errors
        pointer, existing = self.prevent_infinite_recursion(object_)

        for property_name, property_ in object_meta.properties.items():
            value = getattr(object_, property_name)
            if isinstance(value, Reference):
                setattr(
                    object_,
                    property_name,
                    self.resolve(value.ref, types=(property_,), dereference=recursive)
                )
            elif recursive and isinstance(value, Model):
                self.dereference(value, recursive=recursive)

        self.reset_recursion_placeholder(pointer, existing)

    def dereference_array_items(self, array, recursive=True):
        # type: (Model, bool) -> None
        """
        Replace all references in this array with the referenced object
        """
        array_meta = meta.read(array)

        # Prevent recursion errors
        pointer, existing = self.prevent_infinite_recursion(array)

        for index in range(len(array)):
            item = array[index]
            if isinstance(item, Reference):
                array[index] = self.resolve(
                    item.ref,
                    types=array_meta.item_types,
                    dereference=recursive
                )
            elif recursive and isinstance(item, Model):
                self.dereference(item, recursive=recursive)

        self.reset_recursion_placeholder(pointer, existing)

    def dereference_dictionary_values(self, dictionary, recursive=True):
        # type: (Model, bool) -> None
        """
        Replace all references in this dictionary with the referenced object
        """
        dictionary_meta = meta.read(dictionary)

        # Prevent recursion errors
        pointer, existing = self.prevent_infinite_recursion(dictionary)

        for key, value in dictionary.items():
            if isinstance(value, Reference):
                dictionary[key] = self.resolve(
                    value.ref,
                    types=dictionary_meta.value_types,
                    dereference=recursive
                )
            elif recursive and isinstance(value, Model):
                self.dereference(value, recursive=recursive)

        self.reset_recursion_placeholder(pointer, existing)

    @staticmethod
    def unmarshal_resolved_reference(resolved_reference, url, pointer, types=None):
        # type: (Model, Optional[str], str, Sequence[Property, type]) -> Model
        if types or (not isinstance(resolved_reference, Model)):
            resolved_reference = unmarshal(resolved_reference, types=types)
            # Re-assign the URL and pointer
            meta.url(resolved_reference, url)
            meta.pointer(resolved_reference, pointer)
        return resolved_reference

    def resolve(self, pointer, types=None, dereference=False):
        # type: (str, Sequence[Property, type], bool) -> Model
        """
        Return the object referenced by a pointer
        """

        if pointer in self.pointers:
            # This catches
            if self.pointers[pointer] is None:
                raise ReferenceLoopError(pointer)

        else:

            if pointer[0] == '#':
                # Resolve a reference within the same Open API document
                try:
                    resolved = resolve_pointer(self.root, pointer[1:])
                except RecursionError:
                    raise RecursionError(
                        pointer + '\n' + get_exception_text()
                    )

                # Cast the resolved reference as one of the given types
                resolved = self.unmarshal_resolved_reference(resolved, self.url, pointer, types=types)
            else:
                # Resolve a reference from another Open API document
                url, document_pointer = self.get_url_pointer(pointer)

                # Retrieve the document
                document = self.resolver.get_document(urljoin(self.url, url.lstrip('/')))

                # Resolve the pointer, if needed
                if document_pointer:
                    resolved = document.resolve(document_pointer, types)
                else:
                    resolved = document.root
                    # Cast the resolved reference as one of the given types
                    resolved = self.unmarshal_resolved_reference(resolved, url, document_pointer, types=types)

            # Recursively dereference
            if dereference and isinstance(resolved, Model):
                self.dereference(resolved, recursive=dereference)

            # Cache the resolved pointer
            self.pointers[pointer] = resolved

        return self.pointers[pointer]

    def dereference_all(self):
        # type: (OpenAPI) -> None
        self.dereference(self.root, recursive=True)


class Resolver(object):
    """
    This class should be used, with an instance of `oapi.oas.model.OpenAPI`, to resolve references.

    Parameters:

        - root (oapi.oas.model.OpenAPI): The OpenAPI document against which pointers will be resolved.

        - url (str): The URL or file path from where `root` was retrieved. The base URL for relative paths will be the
          directory above this URL. This will not typically be needed, as it can be inferred from most `Model`
          instances.

        - urlopen (collections.Callable): If provided, this should be a function taking one argument (a `str`),
          which can be used in lieu of `urllib.request.urlopen` to retrieve a document and return an instance of a
          sub-class of `IOBase` (such as `http.client.HTTPResponse`). This should be used if authentication is needed
          in order to retrieve external references in the document, or if local file paths will be referenced instead
          of web URL's (use `open` as the value for the `urlopen` parameter in this case).
    """

    def __init__(self, root, url=None, urlopen = request.urlopen):
        # type: (OpenAPI, Optional[str], typing.Callable, bool) -> None

        # Ensure arguments are of the correct types
        assert callable(urlopen)
        assert isinstance(root, OpenAPI)
        assert isinstance(url, (str, NoneType))

        self.url = url

        # This is the function used to open external pointer references
        self.urlopen = urlopen

        # Infer the URL from the `OpenAPI` document, if not explicitly provided
        if url is None:
            url = meta.url(root) or '#'

        # This is the primary document--the one we are resolving
        document = _Document(self, root, url)

        # Store the primary document both by URL and under the key "#" (for convenient reference)
        self.documents = {
            url: document
        }
        if url != '#':
            self.documents['#'] = document

    def get_document(self, url):
        # type: (str) -> Model
        """
        Retrieve a document by URL, or use the cached document if previously retrieved
        """

        if url not in self.documents:

            with self.urlopen(url) as response:
                self.documents[url] = _Document(self, detect_format(response)[0], url=url)

        return self.documents[url]

    def dereference(self):
        # type: (...) -> None
        """
        Dereference the primary document
        """
        self.documents['#'].dereference_all()

    def resolve(self, pointer, types=None, dereference=False):
        # type: (str, Sequence[Property, type], bool) -> Model
        return self.documents['#'].resolve(pointer, types, dereference=dereference)
