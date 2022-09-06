from Katana import DrawingModule

from katananodling.entities import OpScriptCustomNode


class PackageDemoNode(OpScriptCustomNode):

    name = "PackageDemo"
    version = (0, 1, 5)
    color = OpScriptCustomNode.Colors.purple
    description = "What the tool does in a few words."
    author = "<FirstName Name email@provider.com>"

    def _build(self):

        script = 'local script = require("{path}")\nscript()'
        script = script.format(path=self.getLuaModuleName())

        opscriptnode = self.getDefaultOpScriptNode()
        opscriptnode.getParameter("CEL").setExpression("=^/user.CEL", True)
        opscriptnode.getParameter("applyWhere").setValue("at locations matching CEL", 0)
        opscriptnode.getParameter("script.lua").setValue(script, 0)

        userparam = self.user_param
        p = userparam.createChildString("CEL", "")
        hint = {"widget": "cel"}
        p.setHintString(repr(hint))

        p = userparam.createChildNumber("amount", 1)
        hint = {"slider": True, "slidermax": 2.0}
        p.setHintString(repr(hint))

        DrawingModule.SetCustomNodeColor(self, *self.color)
        self.moveAboutParamToBottom()
        return
