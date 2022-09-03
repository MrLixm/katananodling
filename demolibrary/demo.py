from Katana import NodegraphAPI

from katananodling.entities import BaseCustomNode


class DemoNode(BaseCustomNode):

    name = "Demo"
    version = (0, 1, 0)
    color = BaseCustomNode.Colors.green
    description = "What the tool does in a few words."
    author = "<FirstName Name email@provider.com>"

    def _build(self):

        prunenode = NodegraphAPI.CreateNode("Prune", self)
        p = prunenode.getParameter("CEL")
        p.setExpression("^/user.CEL")
        self.wireInsertNodes([prunenode])

        userparam = self.user_param
        p = userparam.createChildString("CEL", "")
        hint = {"widget": "cel"}
        p.setHintString(repr(hint))

        p = userparam.createChildNumber("amount", 1)
        hint = {"slider": True, "slidermax": 2.0}
        p.setHintString(repr(hint))

        self.moveAboutParamToBottom()
        return
