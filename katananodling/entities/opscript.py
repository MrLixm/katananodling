import logging
import sys
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

    @classmethod
    def getLuaModuleName(cls):
        # type: () -> Optional[str]
        """
        This return the "import path" of the lua module for this node. To be used by
        the lua ``require()`` function.

        It is free to the user to use this function or manually specify the module name
        in the OpScript.

        ex: "demolibrary.packageDemo.init" for a "package"
        ex: "demolibrary.demo" for a module
        """
        module_name = cls.__module__
        module = sys.modules[module_name]
        # if module has __path__ attribute = this is a package.
        # package means we use "init" files,
        if hasattr(module, "__path__"):
            # and in lua init module doesn't have the underscores
            module_name = module_name + ".init"

        return module_name

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
