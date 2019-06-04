"""
This module provides functionality for resolving references in an instance of `oapi.oas.model.OpenAPI`.
"""

from collections import OrderedDict

import collections
from urllib import request
from urllib.parse import urlparse, urljoin

from sob import meta


from jsonpointer import resolve_pointer

try:
    import typing
    from typing import Union, Any, Sequence, Dict
except ImportError:
    typing = Union = Any = Sequence = Dict = None

from sob.model import Model, Array, Dictionary, Object, unmarshal, detect_format
from sob.properties import Property
from sob.properties.types import NoneType

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

    def dereference(self, model_instance, recursive=False):
        # type: (Model, bool) -> None
        """
        Recursively dereference this objects and all items/properties
        """
        if isinstance(model_instance, Reference):
            raise ReferenceLoopError('A reference cannot be "dereferenced"')
        elif isinstance(model_instance, Object):
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

    def dereference_object_properties(self, object_, recursive=False):
        # type: (Model, bool) -> None
        """
        Replace all references in this object's properties with the referenced object
        """
        object_meta = meta.read(object_)
        for property_name, property_ in object_meta.properties.items():
            value = getattr(object_, property_name)
            if isinstance(value, Reference):
                setattr(
                    object_,
                    property_name,
                    self.resolve(value.ref, types=(property_,), dereference=recursive)
                )
            elif recursive and isinstance(value, Model):
                self.dereference(value)

    def dereference_array_items(self, array, recursive=False):
        # type: (Model, bool) -> None
        """
        Replace all references in this array with the referenced object
        """
        array_meta = meta.read(array)
        for index in range(len(array)):
            item = array[index]
            if isinstance(item, Reference):
                array[index] = self.resolve(
                    item.ref,
                    types=array_meta.item_types,
                    dereference=recursive
                )
            elif recursive and isinstance(item, Model):
                self.dereference(item)

    def dereference_dictionary_values(self, dictionary, recursive=False):
        # type: (Model, bool) -> None
        """
        Replace all references in this dictionary with the referenced object
        """
        dictionary_meta = meta.read(dictionary)
        for key, value in dictionary.items():
            if isinstance(value, Reference):
                dictionary[key] = self.resolve(
                    value.ref,
                    types=dictionary_meta.value_types,
                    dereference=recursive
                )
            elif recursive and isinstance(value, Model):
                self.dereference(value)

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

        if pointer not in self.pointers:

            if pointer[0] == '#':
                # Resolve a reference within the same Open API document
                resolved = resolve_pointer(self.root, pointer[1:])

                # Cast the resolved reference as one of the given types
                resolved = self.unmarshal_resolved_reference(resolved, self.url, pointer, types=types)
            else:
                # Resolve a reference from another Open API document
                url, document_pointer = self.get_url_pointer(pointer)

                # Retrieve the document
                document = self.resolver.get_document(url)

                # Resolve the pointer, if needed
                if document_pointer:
                    resolved = document.resolve(document_pointer, types)
                else:
                    resolved = document.root
                    # Cast the resolved reference as one of the given types
                    resolved = self.unmarshal_resolved_reference(resolved, url, document_pointer, types=types)

            # Recursively dereference
            if dereference and isinstance(resolved, Model):
                self.dereference(resolved)

            # Cache the resolved pointer
            self.pointers[pointer] = resolved

        return self.pointers[pointer]

    def dereference_all(self):
        # type: (OpenAPI) -> None
        self.dereference(self.root)


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
                self.documents[url] = _Document(self, detect_format(response)[0], url)
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



# def resolve(
#     data,  # type: model.Model
#     url = None,  # type: Optional[str]
#     urlopen = request.urlopen,  # type: Union[typing.Callable, Sequence[typing.Callable]]
#     recursive = True, # type: bool
#     root = None,  # type: Optional[Union[model.Model, dict, Sequence]]
#     _references = None,  # type: Optional[typing.Dict[str, Union[Object, Dictionary, Array]]]
#     _recurrence = False  # type: bool
# ):
#     # type: (...) -> Model
#     """
#     Replaces `oapi.model.Reference` instances with the material referenced.
#
#     Arguments:
#
#         - data (Object|Dictionary|Array): A deserialized object or array.
#
#         - url (str): The URL from where `data` was retrieved. The base URL for relative paths will be the directory
#           above this URL, and this URL will be used to index _references in order to prevent cyclic recursion when
#           mapping (external) bidirectional _references between two (or more) documents. For `Object` instances, if the
#           URL is not provided, it will be inferred from the object's metadata where possible. Objects created from an
#           instance of `http.client.HTTPResponse` will have had the source URL stored with it's metadata when the
#           object was instantiated.
#
#         - urlopen (`collections.Callable`): If provided, this should be a function taking one argument (a `str`),
#           which can be used in lieu of `request.urlopen` to retrieve a document and return an instance of a sub-class
#           of `IOBase` (such as `http.client.HTTPResponse`). This should be used if authentication is needed in order
#           to retrieve external _references in the document, or if local file paths will be referenced instead of web
#           URL's.
#
#         - root (Object|Dictionary|Array): The root document to be used for resolving inline references. This argument
#           is only needed if `data` is not a "root" object/element in a document (an object resulting from
#           deserializing a document, as opposed to one of the child objects of that deserialized root object).
#     """
#     if not isinstance(data, sob.abc.model.Model):
#         raise TypeError(
#             'The parameter `data` must be an instance of `%s`, not %s.' % (
#                 qualified_name(sob.abc.model.Model),
#                 repr(data)
#             )
#         )
#
#     if _references is None:
#         _references = {}
#
#     def resolve_ref(
#         ref,  # type: str
#         types=None  # type: tuple
#     ):
#         # type: (...) -> typing.Any
#         ref_root = root
#         ref_document_url = url
#         if ref[0] == '#':
#             ref_document = ref_root
#             ref_pointer = ref[1:]
#         else:
#             ref_parts = ref.split('#')
#             ref_parts_url = ref_parts[0]
#             if ref_document_url:
#                 parse_result = urlparse(ref_parts_url)
#                 if parse_result.scheme:
#                     ref_document_url = ref_parts_url
#                 else:
#                     ref_document_url = urljoin(
#                         ref_document_url,
#                         ref_parts_url.lstrip('/ ')
#                     )
#             else:
#                 ref_document_url = ref_parts_url
#             if len(ref_parts) < 2:
#                 ref_pointer = None
#             else:
#                 ref_pointer = '#'.join(ref_parts[1:])
#             if ref_document_url in _references:
#                 if _references[ref_document_url] is None:
#                     raise ReferenceLoopError()
#                 ref_document = _references[ref_document_url]
#             else:
#                 try:
#                     ref_document, f = detect_format(urlopen(ref_document_url))
#                 except HTTPError as http_error:
#                     http_error.msg = http_error.msg + ': ' + ref_document_url
#                     raise http_error
#         if ref_pointer is None:
#             ref_data = ref_document
#             #if types:
#             ref_data = unmarshal(ref_data, types=types)
#             ref_url_pointer = ref_document_url
#             if recursive:
#                 if ref_url_pointer not in _references:
#                     _references[ref_url_pointer] = None
#                     try:
#                         ref_data = resolve(
#                             ref_data,
#                             root=ref_document,
#                             urlopen=urlopen,
#                             url=ref_document_url,
#                             recursive=recursive,
#                             _references=_references,
#                             _recurrence=True
#                         )
#                         _references[ref_url_pointer] = ref_data
#                     except ReferenceLoopError:
#                         pass
#         else:
#             ref_url_pointer = '%s#%s' % (ref_document_url or '', ref_pointer)
#             if ref_url_pointer in _references:
#                 if _references[ref_url_pointer] is None:
#                     raise ReferenceLoopError()
#                 else:
#                     ref_data = _references[ref_url_pointer]
#             else:
#                 ref_data = resolve_pointer(ref_document, ref_pointer)
#                 # if types:
#                 ref_data = unmarshal(ref_data, types)
#                 if recursive:
#                     _references[ref_url_pointer] = None
#                     try:
#                         ref_data = resolve(
#                             ref_data,
#                             root=ref_document,
#                             urlopen=urlopen,
#                             url=ref_document_url,
#                             recursive=recursive,
#                             _references=_references,
#                             _recurrence=True
#                         )
#                         _references[ref_url_pointer] = ref_data
#                     except ReferenceLoopError:
#                         pass
#         return ref_data
#     if url is None:
#         r = root or data
#         if isinstance(r, sob.abc.model.Model):
#             url = meta.url(r)
#     if not _recurrence:
#         data = deepcopy(data)
#     if root is None:
#         root = deepcopy(data)
#     if isinstance(data, Reference):
#         data = resolve_ref(data.ref)
#     elif isinstance(data, Object):
#         m = meta.read(data)
#         for pn, p in m.properties.items():
#             v = getattr(data, pn)
#             if isinstance(v, Reference):
#                 v = resolve_ref(v.ref, types=(p,))
#                 setattr(data, pn, v)
#             elif recursive and isinstance(v, sob.abc.model.Model):
#                 try:
#                     v = resolve(
#                         v,
#                         root=root,
#                         urlopen=urlopen,
#                         url=url,
#                         recursive=recursive,
#                         _references=_references,
#                         _recurrence=True
#                     )
#                 except ReferenceLoopError:
#                     pass
#                 setattr(data, pn, v)
#     elif isinstance(data, (Dictionary, dict, OrderedDict)):
#         for k, v in data.items():
#             if isinstance(v, sob.abc.model.Model):
#                 try:
#                     data[k] = resolve(
#                         v,
#                         root=root,
#                         urlopen=urlopen,
#                         url=url,
#                         recursive=recursive,
#                         _references=_references,
#                         _recurrence=True
#                     )
#                 except ReferenceLoopError:
#                     pass
#     elif isinstance(data, (Array, collections.Sequence, collections.Set)) and not isinstance(data, (str, bytes)):
#         if not isinstance(data, collections.MutableSequence):
#             data = list(data)
#         for i in range(len(data)):
#             if isinstance(data[i], sob.abc.model.Model):
#                 try:
#                     data[i] = resolve(
#                         data[i],
#                         root=root,
#                         urlopen=urlopen,
#                         url=url,
#                         recursive=recursive,
#                         _references=_references,
#                         _recurrence=True
#                     )
#                 except ReferenceLoopError:
#                     pass
#     return data