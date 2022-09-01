import logging
from typing import Union
from typing import Tuple
from typing import List


__all__ = (
    "Version",
    "VersionableType",
    "asserting",
)

logger = logging.getLogger(__name__)


def asserting(expression, msg):
    # type: (bool, str) -> None
    """
    It is not recommended to use ``assert`` in CustomTool as the error will not be
    raised in the log. Instead we can use this shortand function that will actually log.

    Args:
        expression: object that must be asserted to true
        msg: message to display in the exception

    Returns:

    """
    if not expression:
        logger.error(msg)
        raise AssertionError(msg)


VersionableType = Union[str, Union[List[int], Tuple[int, int, int]]]


class Version:
    """
    A version represented as a python class object.
    Expressed using semver.org convention: (major, minor, patch)

    Args:
        versionable_object: object that can be converted to a valid version.
    """

    def __init__(self, versionable_object):
        # type: (VersionableType) -> None

        self.version = None  # type: Tuple[int, int, int]

        if isinstance(versionable_object, str):
            self.version = versionable_object.split(".")
            self.version = tuple(map(int, self.version))

        elif (
            isinstance(versionable_object, (tuple, list))
            and len(versionable_object) == 3
            # and len(list(filter(int, versionable_object))) == len(versionable_object)
        ):
            self.version = versionable_object

        else:
            raise TypeError(
                "Can't create a version object from arg <{}> of type {}"
                "".format(repr(versionable_object), type(versionable_object))
            )

        assert len(self.version) == 3, (
            "Given versionable_object <{}> does not produce a version of len==3 once "
            "converted but <{}>".format(versionable_object, self.version)
        )

    def __str__(self):
        version = map(str, self.version)
        return ".".join(version)
