import fnmatch
import importlib
import inspect
import json
import logging
import traceback
from types import ModuleType
from typing import Dict
from typing import Optional
from typing import Sequence
from typing import Type

from Katana import NodegraphAPI
from Katana import Utils

from . import c
from . import entities

__all__ = (
    "REGISTERED",
    "registerCallbacks",
    "registerNodesFor",
)

logger = logging.getLogger(__name__)


REGISTERED = {}  # type: Dict[str, Type[entities.BaseCustomNode]]
"""
Dictionnary of BaseCustomNode class registered to be used in Katana.
"""


def registerNodesFor(tools_packages_list):
    # type: (Sequence[str]) -> None
    """
    Register the BaseCustomNode declared in the given locations names.
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
    logger.debug("[registerNodesFor] Started...")
    logger.debug(
        "[registerNodesFor] c.Env={}".format(json.dumps(c.Env.__asdict__(), indent=4))
    )

    NodegraphAPI.RegisterPythonGroupType(c.KATANA_TYPE_NAME, entities.BaseCustomNode)
    NodegraphAPI.AddNodeFlavor(c.KATANA_TYPE_NAME, "_hide")  # TODO: see if kept
    logger.debug(
        "[registerNodesFor] RegisterPythonGroupType for <{}>".format(c.KATANA_TYPE_NAME)
    )

    for package_id in tools_packages_list:

        try:
            package = importlib.import_module(package_id)  # type: ModuleType
        except Exception as excp:
            logger.exception(
                "[registerNodesFor] Cannot import package <{}>: {}"
                "".format(package_id, excp)
            )
            continue

        registered = _registerNodePackage(package=package)
        # registered tools can be found in REGISTERED global anyway
        continue

    logger.info(
        "[registerNodesFor] Finished. Registered {} custom tools for {} locations."
        "".format(len(REGISTERED), len(tools_packages_list))
    )
    return


def registerCallbacks():
    """
    Register callback for BaseCustomNode nodes events.
    """

    if not c.Env.get(c.Env.UPGRADE_DISABLE):
        Utils.EventModule.RegisterEventHandler(upgradeOnNodeCreateEvent, "node_create")
        logger.debug(
            '[registerCallbacks] registered event handler "node_create" with'
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
    # remember BaseCustomNode loading is performed in 2 parts:
    #   first a simple BaseCustomNode instanc eis created and then its being assigned
    #   its subclass which will give a different nodeType.
    if kwargs.get("nodeType") == c.KATANA_TYPE_NAME:
        return

    node = kwargs.get("node")
    if not isinstance(node, entities.BaseCustomNode):
        return

    try:
        node.__upgradeapi__()
        node.upgrade()
    except Exception as excp:
        logger.exception(
            "[upgradeOnNodeCreateEvent] Cannot upgrade BaseCustomNode node {}: {}"
            "".format(node, excp),
            exc_info=excp,
        )

    try:
        node.__toggleDebugMode__(True if c.Env.get(c.Env.NODE_PARAM_DEBUG) else False)
    except Exception as excp:
        logger.exception(
            "[upgradeOnNodeCreateEvent] Error while calling __toggleDebugMode__ "
            "on node {}: {}".format(node, excp),
            exc_info=excp,
        )

    return


def _createCustomNode(class_name):
    # type: (str) -> Optional[NodegraphAPI.Node]
    """

    Args:
        class_name: name of the tool to create, must be previously registered.

    Returns:
        Instance of the node created in the Nodegraph.
    """
    custom_tool_class = REGISTERED[class_name]
    node = None  # type: entities.BaseCustomNode

    Utils.UndoStack.DisableCapture()

    try:

        node = NodegraphAPI.CreateNode(c.KATANA_TYPE_NAME)

        node.__class__ = custom_tool_class
        node.setType(class_name)
        if not NodegraphAPI.NodegraphGlobals.IsLoading():
            node.setName(class_name)
            node.__build__()

    except Exception as excp:
        logger.exception(
            '[_createCustomNode] Error creating BaseCustomNode of type "{}": {}'
            "".format(class_name, excp)
        )
        if node:
            node.delete()

    finally:
        Utils.UndoStack.EnableCapture()

    return node


def _registerNodePackage(package):
    # type: (ModuleType) ->  Dict[str, Type[entities.BaseCustomNode]]
    """

    Args:
        package: python <module> object to import the custom tools from

    Returns:
        all the custom tools loaded as dict[tool_name, tool_class]
    """

    customnodes_dict = _getAvailableNodesInPackage(package=package)

    for tool_module_name, tool_class in customnodes_dict.items():

        if tool_class.name in REGISTERED:
            logger.warning(
                "[_registerNodePackage] tool from module <{}> from package {} is "
                "already registered as <{}>."
                "".format(tool_module_name, package, tool_class.name)
            )
            continue

        NodegraphAPI.RegisterPythonNodeFactory(tool_class.name, _createCustomNode)
        NodegraphAPI.AddNodeFlavor(tool_class.name, c.KATANA_FLAVOR_NAME)
        REGISTERED[tool_class.name] = tool_class

        logger.debug(
            "[_registerNodePackage] registered ({}){}"
            "".format(tool_module_name, tool_class)
        )
        continue

    logger.debug(
        "[_registerNodePackage] Finished registering package {}, {} tools found."
        "".format(package, len(customnodes_dict))
    )
    return customnodes_dict


def _getAvailableNodesInPackage(package):
    # type: (ModuleType) -> Dict[str, Type[entities.BaseCustomNode]]
    """
    _getAllNodesInPackage() but filtered to remove the tools that have been asked to be
    ignored using an environment variable.

    Returns:
        dict of module_name, BaseCustomNode class defined in the module
    """
    import os  # defer import to get the latest version of os.environ

    all_nodes = _getAllNodesInPackage(package)

    excluded_nodes_var = c.Env.get(c.Env.EXCLUDED_NODES)
    if not excluded_nodes_var:
        return all_nodes

    excluded_dict = dict()
    excluded_keys = list()
    # this is a list of Class names as fnmatch expressions !
    class_names_to_exclude = excluded_nodes_var.split(os.pathsep)

    for module_name, basecustomnode in all_nodes.items():

        for namepattern in class_names_to_exclude:

            if fnmatch.fnmatch(basecustomnode.__name__, namepattern):
                excluded_keys.append(module_name)
                excluded_dict[basecustomnode.__name__] = "excluded by: {}".format(
                    namepattern
                )
                continue

    # as we can't delete key in a dict we are iterating over :
    for excluded in excluded_keys:
        del all_nodes[excluded]

    logger.debug(
        "[_getAvailableNodesInPackage] Finished. Excluded {} nodes: {}".format(
            len(excluded_dict),
            json.dumps(excluded_dict, indent=4, default=str, sort_keys=True),
        )
    )
    return all_nodes


def _getAllNodesInPackage(package):
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
                "[_getAllNodesInPackage] InvalidNodeClass: class <{}> for package {}:\n"
                "   {}".format(objectData, package, excp)
            )
            continue

        out[objectName] = objectData
        logger.debug(
            "[_getAllNodesInPackage] Found [{}]={}".format(objectName, objectData)
        )

    return out
