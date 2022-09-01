import logging
from abc import abstractmethod
from typing import Optional

from Katana import NodegraphAPI

from .base import BaseCustomNode

__all__ = ("OpScriptCustomNode",)

logger = logging.getLogger(__name__)


class OpScriptCustomNode(BaseCustomNode):
    """
    Abstract class to create a custom node based on at least one OpScript node.
    The OpScript configuration (OpArg) is accessible to the user via parameters
    declared in the ``_build()`` method that must be overriden.
    """

    luamodule = NotImplemented
    """
    Every OpScript must live in a .lua registered in the LUA_PATH.
    This means the OpScript.script will only import it using ``require()``

    This is not used by default and its up to the developer subclassing this to use it.
    """

    def _buildDefaultStructure(self):
        super(OpScriptCustomNode, self)._buildDefaultStructure()

        self._node_opscript = NodegraphAPI.CreateNode("OpScript", self)
        self._node_opscript.setName("OpScript_{}_0001".format(self.name))
        self._node_opscript.getParameters().createChildGroup("user")

        self.wireInsertNodes([self._node_opscript])
        return

    @abstractmethod
    def _build(self):
        pass

    def getDefaultOpScriptNode(self):
        # type: () -> Optional[NodegraphAPI.Node]
        """
        Return the OpScript node created at init.

        But be aware the node might have other OpScript node inside.
        """
        return self._node_opscript
