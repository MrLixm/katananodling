import ast
import json
import logging
import re
import sys
import traceback
from abc import abstractmethod
import inspect
from typing import Any
from typing import Optional
from typing import Tuple
from typing import List

from Katana import NodegraphAPI

from katananodling import c
from katananodling import util
from katananodling.util import Version

__all__ = ("BaseCustomNode",)

logger = logging.getLogger(__name__)


class AboutGroupParam:
    """
    A group parameter that provide contextual information on a BaseCustomNode and allow
    to have them stored and persistent on the node.

    Their value is initialized on node creation and should only be updated when the
    node version is upgraded using the ``upgrade()`` method. (where you should call
    the ``__update__()`` method.)

    If the parameter structure is modified or anything that impact the node in katana,
    you would need to implement the changes in :func:`~AboutGroupParam.__upgradeapi__`
    """

    class ParamNames:
        group = "About"
        name = "name"
        version = "version"
        description = "info"
        author = "author"
        path = "path"
        documentation = "open_documentation"
        api_version = "api_version"

        @classmethod
        def getPath(cls, param_name):
            # type: (str) -> str
            if param_name == cls.group:
                return "user.{}".format(cls.group, param_name)
            return "{}.{}".format(cls.getPath(cls.group), param_name)

    def __init__(self, node):
        # type: (BaseCustomNode) -> None

        self.node = node  # type: BaseCustomNode
        self.param = None  # type: Optional[NodegraphAPI.Parameter]
        self.param = node.getParameter(self.ParamNames.getPath(self.ParamNames.group))

    def __build__(self):
        """
        Create and configure the ``About`` parameter on the current node.
        Must be called once in the lifetime on the node.
        """

        parent = self.node.getParameter("user")
        if not parent:
            parent = self.node.getParameters().createChildGroup("user")
            hint = {"hideTitle": True}
            parent.setHintString(repr(hint))

        self.param = parent.createChildGroup(self.ParamNames.group)

        p = self.param.createChildString(self.ParamNames.name, self.node.name)
        p.setHintString(repr({"readOnly": True}))

        p = self.param.createChildString(
            self.ParamNames.version, str(Version(self.node.version))
        )
        p.setHintString(repr({"readOnly": True}))

        p = self.param.createChildString(self.ParamNames.api_version, c.__version__)
        p.setHintString(repr({"readOnly": True, "widget": "null"}))

        p = self.param.createChildString(
            self.ParamNames.description, self.node.description
        )
        p.setHintString(repr({"readOnly": True}))

        p = self.param.createChildString(self.ParamNames.author, self.node.author)
        p.setHintString(repr({"readOnly": True}))

        p = self.param.createChildString(
            self.ParamNames.path, inspect.getfile(self.node.__class__)
        )
        p.setHintString(repr({"readOnly": True, "widget": "null"}))

        script = c.OPEN_DOCUMENTATION_SCRIPT.format(PATH_PARAM=self.ParamNames.path)
        p = self.param.createChildString(self.ParamNames.documentation, script)
        hints = {
            "widget": "scriptButton",
            "scriptText": script,
        }
        p.setHintString(repr(hints))
        return

    def __toggleDebugMode__(self, enable):
        # type: (bool) -> None
        """
        Toggle visibility on hidden parameters for debug purposes.

        You MUST NOT delete / edit paramaters in other way than purely visibility
        ones.

        Args:
            enable: True to enable debug mode, False to make it back to normal
        """

        hidden_param_list = [
            self.node.getParameter(self.ParamNames.getPath(self.ParamNames.path)),
            self.node.getParameter(
                self.ParamNames.getPath(self.ParamNames.api_version)
            ),
        ]
        for param in hidden_param_list:

            hints = ast.literal_eval(param.getHintString())
            if enable:
                del hints["widget"]
            else:
                hints["widget"] = "null"
            param.setHintString(repr(hints))

        return

    def __update__(self):
        """
        Update the values on the parameters with the latest ones defined on the node
        python class.
        """
        p = self.node.getParameter(self.ParamNames.getPath(self.ParamNames.name))
        p.setValue(self.node.name, 0)

        p = self.node.getParameter(self.ParamNames.getPath(self.ParamNames.version))
        p.setValue(str(Version(self.node.version)), 0)

        p = self.node.getParameter(self.ParamNames.getPath(self.ParamNames.description))
        p.setValue(self.node.description, 0)

        p = self.node.getParameter(self.ParamNames.getPath(self.ParamNames.author))
        p.setValue(self.node.author, 0)

        p = self.node.getParameter(self.ParamNames.getPath(self.ParamNames.path))
        p.setValue(inspect.getfile(self.node.__class__), 0)

        script = c.OPEN_DOCUMENTATION_SCRIPT.format(PATH_PARAM=self.ParamNames.path)
        p = self.node.getParameter(self.ParamNames.getPath(self.ParamNames.path))
        p.setValue(script, 0)
        p.setHintString(repr({"scriptText": script}))

        return

    def __upgradeapi__(self):
        """
        This is to update the param following internal API changes on the python package.

        Like for example you changed some parameter names in ``self.ParamNames``, ...

        This is called by the parent :class:`BaseCustomNode`
        """
        p = self.node.getParameter(self.ParamNames.getPath(self.ParamNames.api_version))
        p.setValue(c.__version__, 0)
        return

    def _getValue(self, info_name):
        # type: (str) -> Optional[Any]
        p = self.node.getParameter(self.ParamNames.getPath(info_name))
        if not p:
            return
        return p.getValue(0)

    @property
    def name(self):
        # type: () -> Optional[str]
        return self._getValue(self.ParamNames.name)

    @property
    def version(self):
        # type: () -> Optional[Version]
        v = self._getValue(self.ParamNames.version)
        if not v:
            return
        return Version(v)

    @property
    def api_version(self):
        # type: () -> Optional[Version]
        v = self._getValue(self.ParamNames.api_version)
        if not v:
            return
        return Version(v)

    @property
    def description(self):
        # type: () -> Optional[str]
        return self._getValue(self.ParamNames.description)

    @property
    def author(self):
        # type: () -> Optional[str]
        return self._getValue(self.ParamNames.author)


class BaseCustomNode(NodegraphAPI.PythonGroupNode):
    """
    Abstract base class to create "BaseCustomNode" nodes.

    That's just a group node with some standards like an "about" param.

    Its default structure correpond to one input and output port, and two dot nodes
    connected together in the inside.
    """

    Colors = c.COLORS  # convenience, to not have to import multiple module for use
    """
    All pre-defined color available to assign to this tool.
    """

    port_in_name = "in"
    port_out_name = "out"

    # MUST be overridden :

    name = c.KATANA_TYPE_NAME  # type: str

    version = (0, 0, 0)  # type: Tuple[int,int,int]
    """
    Specified as (major, minor, patch) and following https://semver.org.
    """

    color = None  # type: Optional[Tuple[float,float,float]]
    """
    Color used on the LayeredMenu but can also be used by the developer to color
    the node itself.
    """

    description = ""  # type: str

    author = ""  # type: str

    documentation = None  # type: Optional[str]
    """
    Path to a documentation "entity" that can be a file path or an URL.
    """

    _registered = False  # type: bool
    """
    True if the class has been registered in Katana.

    **Set at registering time (in Katana).**
    """

    def __init__(self):

        self.about = AboutGroupParam(self)  # type: AboutGroupParam
        self._node_dot_up = None  # type: NodegraphAPI.Node
        self._node_dot_down = None  # type: NodegraphAPI.Node
        return

    def __build__(self):
        """
        Called when the BaseCustomNode subclass is created in the nodegraph.
        """
        try:
            self.about.__build__()
            self._buildDefaultStructure()
            self._build()
        except Exception as excp:
            logger.error(
                "[{}][__build__] {}\n{}"
                "".format(self.__class__.__name__, excp, traceback.format_exc()),
            )
        return

    def __toggleDebugMode__(self, enable):
        # type: (bool) -> None
        """
        Edit some parameters to help at debugging.

        Args:
            enable: True to enable debug mode, False to make it back to normal
        """
        self.about.__toggleDebugMode__(enable=enable)

        pname = "debug__"
        p = self.getParameter(pname)
        if p:
            self.getParameters().deleteChild(p)

        if enable:
            p = self.getParameters().createChildString(pname, "")
            hint = {"widget": "scriptEditor", "readOnly": True}
            p.setHintString(repr(hint))
            v = vars(self)
            v.update(vars(self.__class__))
            p.setValue(json.dumps(v, indent=4, default=str, sort_keys=True), 0)

        return

    def __upgradeapi__(self):
        """
        This is to update the node following internal API changes on the python package.

        Do not confuse it with ``upgrade()`` method made for developers subclasses that
        is call when a node **in the library** must be upgraded.
        """
        if c.Env.get(c.Env.UPGRADE_DISABLE):
            return

        if self.about.api_version == Version(c.__version__):
            return

        versionprev = str(self.about.api_version or "")

        self.about.__upgradeapi__()
        logger.debug(
            "[{}][__upgradeapi__] Finished for <{}>. <{}> -> <{}>"
            "".format(
                self.__class__.__name__, self.getName(), versionprev, c.__version__
            )
        )
        return

    def _buildDefaultStructure(self):
        """
        Create the basic nodegraph representation of a custom tool.
        This is a styled GroupNode with simply 2 connected dots inside.
        """

        self.addInputPort(self.port_in_name)
        self.addOutputPort(self.port_out_name)
        self.setName("{}_0001".format(self.name))

        NodegraphAPI.SetNodeShapeAttr(self, "iconName", "")
        NodegraphAPI.SetNodeShapeAttr(self, "basicDisplay", 1)

        pos = NodegraphAPI.GetNodePosition(self)

        node_dot_up = NodegraphAPI.CreateNode("Dot", self)
        NodegraphAPI.SetNodePosition(node_dot_up, (pos[0], pos[1] + 150))
        node_dot_up.setName("In_{}_0001".format(self.name))

        node_dot_down = NodegraphAPI.CreateNode("Dot", self)
        NodegraphAPI.SetNodePosition(node_dot_down, (pos[0], pos[1] - 150))
        node_dot_down.setName("Out_{}_0001".format(self.name))

        port_a = self.getSendPort(self.port_in_name)
        port_b = node_dot_up.getInputPortByIndex(0)
        port_a.connect(port_b)

        port_a = node_dot_up.getOutputPortByIndex(0)
        port_b = node_dot_down.getInputPortByIndex(0)
        port_a.connect(port_b)

        port_a = node_dot_down.getOutputPortByIndex(0)
        port_b = self.getReturnPort(self.port_out_name)
        port_a.connect(port_b)

        self._node_dot_up = node_dot_up
        self._node_dot_down = node_dot_down
        return

    @classmethod
    def _check(cls):
        """
        Raise an error if the class is malformed.
        """

        util.asserting(
            isinstance(cls.name, str),
            "name=<{}> is not a str".format(cls.name),
        )
        util.asserting(
            False if re.search(r"\W", cls.name) else True,
            "name=<{}> contains unsupported characters".format(cls.name),
        )

        util.asserting(
            isinstance(cls.version, tuple) and len(cls.version) == 3,
            "version=<{}> is not a tuple or of length 3".format(cls.version),
        )
        util.asserting(
            not cls.color or isinstance(cls.color, tuple) and len(cls.color) == 3,
            "color=<{}> is not a tuple or of length 3".format(cls.color),
        )
        util.asserting(
            isinstance(cls.description, str),
            "description=<{}> is not a str".format(cls.description),
        )
        util.asserting(
            isinstance(cls.author, str),
            "author=<{}> is not a str".format(cls.author),
        )
        return

    @classmethod
    def getLibraryPath(cls):
        # type: () -> str
        """
        Absolute path to the top parent directory that act as a library.
        (might NOT be the parent directory of this class' module but the one further
        level above.)
        """
        library_name = cls.__module__.split(".")[0]
        library_module = sys.modules.get(library_name)
        if not library_module:
            logger.warning(
                "[{}][getLibraryPath] Cannot retrieve the module for the parent "
                "library. <{}> not in sys.modules"
                "".format(cls.__name__, library_name)
            )
        return library_module.__path__[0]

    @abstractmethod
    def _build(self):
        """
        Build the interface and the content of the node.

        Abstract method to override by the developper in the subclass.
        """
        pass

    @property
    def user_param(self):
        # type: () -> NodegraphAPI.Parameter
        return self.getParameter("user")

    def moveAboutParamToBottom(self):
        """
        Move the AboutParam parameter to the bottom of the `user` parameter layout.

        To call usually at the end of ``_build()``
        """
        self.user_param.reorderChild(
            self.about.param,
            self.user_param.getNumChildren() - 1,
        )
        return

    def upgrade(self):
        """
        Read the version stored on the node interface and compare it with the version
        specified on this class (latest). If inferior an upgrade is performed
        as specified.

        This is called on existing scene loading AND when a node is created for the
        first time in the scene.

        Must be overriden by developer in subclasses.
        """
        pass

    def wireInsertNodes(self, node_list, vertical_offset=150):
        # type: (List[NodegraphAPI.Node], int) -> None
        """
        Utility method to quickly connect an ORDERED list of node to the internal network.
        The nodes are inserted after the port connected to Output Dot node.

        For convenience, it is assumed that nodes only have one input/output port.

        Args:
            vertical_offset:
                negative offset to apply to each node position in the nodegraph
            node_list:
                node to connect to the internal network and between each other, in
                the expected order.
        """
        # we have to make a big try/except block because Katana is shitty at catching
        # error of creation of registered Nodes.
        try:
            indownport = self._node_dot_down.getInputPortByIndex(0)
            previousOutPort = indownport.getConnectedPort(0)
            previousPos = NodegraphAPI.GetNodePosition(previousOutPort.getNode())
            indownport.disconnect(previousOutPort)

            for node in node_list:
                node.getInputPortByIndex(0).connect(previousOutPort)
                NodegraphAPI.SetNodePosition(
                    node,
                    (previousPos[0], previousPos[1] - vertical_offset),
                )

                previousOutPort = node.getOutputPortByIndex(0)
                previousPos = NodegraphAPI.GetNodePosition(node)
                continue

            indownport.connect(previousOutPort)
            NodegraphAPI.SetNodePosition(
                self._node_dot_down, (previousPos[0], previousPos[1] - vertical_offset)
            )

        except:
            logger.error(
                "[{}][wireInsertNodes] Error while trying to connect {}\n{}"
                "".format(self.__class__.__name__, node_list, traceback.format_exc())
            )
            raise
        return
