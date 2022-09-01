"""
Constants
"""
__version_major__ = 0
__version_minor__ = 1
__version_patch__ = 0
__version__ = "{}.{}.{}".format(__version_major__, __version_minor__, __version_patch__)

from typing import Any
from typing import Dict
from typing import Optional
from typing import List


class COLORS:
    """
    Colors for the entries in the LayeredMenu.
    Can also be used to color the node.

    Assumed to be sRGB - Display encoded.
    """

    white = (0.75, 0.75, 0.75)
    grey = (0.5, 0.5, 0.5)
    black = (0.015, 0.015, 0.015)

    green = (0.22, 0.46, 0.27)
    bluelight = (0.27, 0.43, 0.46)
    blue = (0.23, 0.27, 0.46)
    purple = (0.39, 0.35, 0.466)
    pink = (0.46, 0.27, 0.35)
    red = (0.46, 0.16, 0.18)
    yellow = (0.46, 0.41, 0.28)

    default = purple  # fallback if color not specified on subclass


class Env:
    """
    Environment variable used by package.
    """

    _PREFIX = "KATANA_NODLING"

    EXCLUDED_TOOLS = "{}_EXCLUDED_TOOLS".format(_PREFIX)
    """
    Environment variable name that must specify a list of tools name to NOT show in
    the LayeredMenu. Separator is the system path separator (; or :):

    ex: ``"attr_math;xform2P;point_width"``
    """

    UPGRADE_DISABLE = "{}_UPGRADE_DISABLE".format(_PREFIX)
    """
    Set to 1 (or actually to anythin non-empty) to disable the upgrading process
    when BaseCustomNode nodes are loaded from previous version.
    
    This can be useful when opening archived project or sending scene to the farm.
    """

    NODE_PARAM_DEBUG = "{}_NODE_PARAM_DEBUG".format(_PREFIX)
    """
    Set to 1 (or actually to anythin non-empty) to enable the "debug" mode for
    BaseCustomNode parameters. Params that are usually hidden are made visible.
    """

    @classmethod
    def __all__(cls):
        # type: () -> List[str]
        return [
            cls.EXCLUDED_TOOLS,
            cls.NODE_PARAM_DEBUG,
            cls.UPGRADE_DISABLE,
        ]

    @classmethod
    def __asdict__(cls):
        # type: () -> Dict[str, str]
        out = dict()
        for attr in cls.__all__():
            out[attr] = cls.get(attr)
        return out

    @classmethod
    def get(cls, key, default=None):
        # type: (str, Any) -> Optional[str]
        import os  # defer import for the first time we actually need it

        return os.environ.get(key, default)


KATANA_FLAVOR_NAME = "customTool"
"""
As each BaseCustomNode is registered as a separate node type, to quickly find all the custom
tool, they are assigned a flavor using ``NodegraphAPI.AddNodeFlavor()``
"""

KATANA_TYPE_NAME = "CustomTool"
"""
Name used to register the base class for all BaseCustomNodes using 
``NodegraphAPI.RegisterPythonGroupType``.
"""


LAYEREDMENU_SHORTCUT = "O"
"""
Shortcut to use in the Nodegraph to make the LayeredMenu appears.
This is the LayeredMenu for ALL the tools that might be disabled.
"""


OPEN_DOCUMENTATION_SCRIPT = """
import os.path
import webbrowser

tool_path = parameter.getParent().getChild("{PATH_PARAM}").getValue(0)
doc_path = os.path.splitext(tool_path)[0] + ".md"

if os.path.exists(doc_path):
    webbrowser.open(doc_path)
"""
