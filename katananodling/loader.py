import importlib
import inspect
import logging
from types import ModuleType
from typing import Dict
from typing import Sequence
from typing import Type

from Katana import NodegraphAPI
from Katana import Callbacks
from Katana import Utils

from . import c
from . import entities

__all__ = (
    "REGISTERED",
    "registerCallbacks",
    "registerTools",
)

logger = logging.getLogger(__name__)


REGISTERED = {}  # type: Dict[str, Type[entities.BaseCustomNode]]
"""
Dictionnary of CUstomTool class registered to be used in Katana.
"""


def registerTools(tools_packages_list):
    # type: (Sequence[str]) -> None
    """
    Register the CustomTool declared in the given locations names.
    Those locations must be python package names registered in the PYTHONPATH, so they
    can be converted to modules and imported.

    Must be called once.

    Args:
        tools_packages_list:
            list of python packages name. Those package must be registered in the PYTHONPATH.
    """
    if REGISTERED:
        raise RuntimeError(
            "REGISTERED global is not empty: this means this function has already been"
            "called. You can only call it once."
        )

    NodegraphAPI.RegisterPythonGroupType(c.KATANA_TYPE_NAME, entities.BaseCustomNode)
    NodegraphAPI.AddNodeFlavor(c.KATANA_TYPE_NAME, "_hide")  # TODO: see if kept
    logger.debug(
        "[registerTools] RegisterPythonGroupType for <{}>".format(c.KATANA_TYPE_NAME)
    )

    for package_id in tools_packages_list:

        try:
            package = importlib.import_module(package_id)  # type: ModuleType
        except Exception as excp:
            logger.exception(
                "[registerTools] Cannot import package <{}>: {}"
                "".format(package_id, excp)
            )
            continue

        registered = _registerToolPackage(package=package)
        # registered tools can be found in REGISTERED global anyway
        continue

    logger.info(
        "[registerTools] Finished. Registered {} custom tools for {} locations."
        "".format(len(REGISTERED), len(tools_packages_list))
    )
    return


def registerCallbacks():
    """
    Register callback for CustomTool nodes events.
    """
    # Callbacks.addCallback(
    #     Callbacks.Type.onNodeCreate,
    #     nodebase.customToolNodeCallback,
    # )
    # logger.debug(
    #     "[_registerCallbackCustomTools] added callback onNodeCreate with"
    #     "<nodebase.customToolNodeCallback>"
    # )

    if not c.Env.get(c.Env.UPGRADE_DISABLE):
        Utils.EventModule.RegisterEventHandler(upgradeOnNodeCreateEvent, "node_create")
        logger.debug(
            '[_registerCallbackCustomTools] registered event handler "node_create" with'
            "<upgradeOnNodeCreateEvent>"
        )
    return


def upgradeOnNodeCreateEvent(*args, **kwargs):
    """
    Called during the ``node_create`` event.

    Perform an upgrade on all the BaseCustomNode instances.

    Exemple of parameters::

        (u'node_create', 1811058784)
        {'node': <RootNode NodegraphAPI_cmodule.GroupNode 'rootNode'>,
         'nodeType': 'Group', 'nodeName': 'Group'}

    Args:
        *args: (event name, event id)
        **kwargs: {node, nodeType, nodeName}
    """
    # remember CustomTool loading is performed in 2 parts:
    #   first a simple CustomTool instanc eis created and then its being assigned
    #   its subclass which will give a different nodeType.
    if kwargs.get("nodeType") == "CustomTool":
        return

    node = kwargs.get("node")
    if not isinstance(node, entities.BaseCustomNode):
        return

    try:
        node.__upgradeapi__()
        node.upgrade()
    except Exception as excp:
        logger.exception(
            "[upgradeOnNodeCreateEvent] Cannot upgrade CustomTool node {}: {}"
            "".format(node, excp),
            exc_info=excp,
        )

    return


def _createCustomTool(class_name):
    # type: (str) -> NodegraphAPI.Node
    """

    Args:
        class_name: name of the tool to create, must be previously registered.

    Returns:
        Instance of the node created in the Nodegraph.
    """
    custom_tool_class = REGISTERED[class_name]

    Utils.UndoStack.DisableCapture()

    try:

        try:
            node = NodegraphAPI.CreateNode(
                c.KATANA_TYPE_NAME
            )  # type: nodebase.BaseCustomNode
        except Exception:
            logger.exception(
                '[_createCustomTool] Error creating CustomTool of type "{}"'.format(
                    class_name
                )
            )
            return

        try:

            node.__class__ = custom_tool_class
            node.setType(class_name)
            if not NodegraphAPI.NodegraphGlobals.IsLoading():
                node.setName(class_name)
                node.__build__()

        except Exception:
            logger.exception(
                '[_createCustomTool] Error creating CustomTool of type "{}"'
                "".format(class_name)
            )
            node.delete()
            return

    finally:
        Utils.UndoStack.EnableCapture()

    return node


def _registerToolPackage(package):
    # type: (ModuleType) ->  Dict[str, Type[nodebase.BaseCustomNode]]
    """

    Args:
        package: python <module> object to import the custom tools from

    Returns:
        all the custom tools loaded as dict[tool_name, tool_class]
    """

    customtool_dict = _getAvailableToolsInPackage(package=package)

    for tool_module_name, tool_class in customtool_dict.items():

        if tool_class.name in REGISTERED:
            logger.warning(
                "[_registerToolPackage] tool from module <{}> from package {} is "
                "already registered as <{}>."
                "".format(tool_module_name, package, tool_class.name)
            )
            continue

        NodegraphAPI.RegisterPythonNodeFactory(tool_class.name, _createCustomTool)
        NodegraphAPI.AddNodeFlavor(tool_class.name, c.KATANA_FLAVOR_NAME)
        REGISTERED[tool_class.name] = tool_class

        logger.debug(
            "[_registerToolPackage] registered ({}){}"
            "".format(tool_module_name, tool_class)
        )
        continue

    logger.debug(
        "[_registerToolPackage] Finished registering package {}, {} tools found."
        "".format(package, len(customtool_dict))
    )
    return customtool_dict


def _getAvailableToolsInPackage(package):
    # type: (ModuleType) -> Dict[str, Type[entities.BaseCustomNode]]
    """
    _getAllToolsInPackage() but filtered to remove the tools that have been asked to be
    ignored using an environment variable.

    Returns:
        dict of module_name, BaseCustomNode class defined in the module
    """
    import os  # defer import to get the latest version of os.environ

    all_tools = _getAllToolsInPackage(package)

    excluded_tool_var = c.Env.get(c.Env.EXCLUDED_TOOLS)
    if not excluded_tool_var:
        return all_tools

    tools_to_exclude = excluded_tool_var.split(os.pathsep)
    nexcluded = 0
    for excluded_tool_name in tools_to_exclude:
        if excluded_tool_name in all_tools:
            del all_tools[excluded_tool_name]
            nexcluded += 1

    logger.debug(
        "[_getAvailableToolsInPackage] Finished. Excluded {} tools.".format(nexcluded)
    )
    return all_tools


def _getAllToolsInPackage(package):
    # type: (ModuleType) -> Dict[str, Type[entities.BaseCustomNode]]
    """
    Get a list of all the "tools" modules available in the given package.

    Not recommended to use as the "final" function. See ``getAvailableTools()`` instead.

    SRC: https://stackoverflow.com/a/1310912/13806195

    Returns:
        dict of module_name, BaseCustomNode class defined in the module
    """

    out = dict()

    for objectName, objectData in package.__dict__.items():

        if objectName.startswith("_"):
            continue

        if not inspect.isclass(objectData):
            continue

        if not issubclass(objectData, entities.BaseCustomNode):
            continue

        try:
            objectData._check()
        except AssertionError as excp:
            logger.exception(
                "[getAllToolsInPackage] InvalidNodeClass: class <{}> for package {}:\n"
                "   {}".format(objectData, package, excp)
            )
            continue

        out[objectName] = objectData
        logger.debug(
            "[_getAllToolsInPackage] Found [{}]={}".format(objectName, objectData)
        )

    return out
