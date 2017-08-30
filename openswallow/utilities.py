def bases(t):
    # type: (type) -> Set[type]
    """
    Retrieves a set containing all classes (`type` instances) from which the given class inherits.

        :param t: An instance type.

        :return: A set containing all types from which this type inherits (directly and indirectly).
    """
    bs = set()
    for b in t.__bases__:
        for bb in bases(b):  # type: Set[type]
            bs.add(bb)
        bs.add(b)
    return bs