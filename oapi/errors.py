class OAPIError(Exception):

    pass


class ReferenceError(OAPIError):

    pass


class ReferenceLoopError(ReferenceError):

    pass


class ReferencePointerError(ReferenceError):

    pass


class DuplicateClassNameError(OAPIError):

    pass
