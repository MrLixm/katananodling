import logging

from Katana import NodegraphAPI
from Katana import LayeredMenuAPI

from . import c
from .loader import REGISTERED


__all__ = ("getLayeredMenuForAllCustomTool",)

logger = logging.getLogger(__name__)


def getLayeredMenuForAllCustomTool():
    # type: () -> LayeredMenuAPI.LayeredMenu
    """
    Get a LayeredMenu instance to display that list all the CustomTool registered in
    Katana.
    """

    layeredMenu = LayeredMenuAPI.LayeredMenu(
        _populateCallback,
        _actionCallback,
        keyboardShortcut=c.LAYEREDMENU_SHORTCUT,
        alwaysPopulate=False,
        onlyMatchWordStart=False,
        sortAlphabetically=True,
        checkAvailabilityCallback=None,
    )

    logger.debug("[getLayeredMenu] Finished.")
    return layeredMenu


def _populateCallback(layered_menu):
    # type: (LayeredMenuAPI.LayeredMenu) -> None
    """
    Called when the shortcut to raise the layeredMenu is pressed.

    This is called usually once and cached in memory unless specified otherwise
    on the LayeredMenu instance.

    Args:
        layered_menu:
    """

    available_tools = NodegraphAPI.GetFlavorNodes(
        c.KATANA_FLAVOR_NAME, filterExists=True
    )
    for tool_name in available_tools:  # type: str

        tool = REGISTERED.get(tool_name)
        entry_color = c.COLORS.default

        if tool:
            try:
                entry_color = tool.color or c.COLORS.default
            except AttributeError as excp:
                pass

        else:
            logger.warning(
                "[_populateCallback] tool name <{}> doesn't seems to be registered "
                "which shouldn't happens.".format(tool_name)
            )

        layered_menu.addEntry(
            tool_name,
            text=tool_name,
            color=entry_color,
        )

        continue

    return


def _actionCallback(key):
    # type: (str) -> NodegraphAPI.Node
    """
    Called when an entry is clicked by the user.

    Args:
        key: value of the entry clicked

    Returns:
        created node corresponding ot the given key
    """

    available_tools = NodegraphAPI.GetFlavorNodes(
        c.KATANA_FLAVOR_NAME, filterExists=True
    )
    for tool_name in available_tools:  # type: str

        if key != tool_name:
            continue

        try:
            node = NodegraphAPI.CreateNode(tool_name, NodegraphAPI.GetRootNode())
        except Exception as excp:
            logger.error(
                "[__actionCallback] Error when trying to create node <{}>: {}"
                "".format(tool_name, excp),
            )
            raise

        if node is None:
            logger.error(
                "[_actionCallback] CreateNode({}) returned None. This might comes "
                "from any error in the class registered for this tool so check the "
                "code.".format(key)
            )

        return node

    return
