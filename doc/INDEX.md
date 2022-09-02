# katananodling

[![root](https://img.shields.io/badge/back_to_root-536362?)](../README.md)
[![INDEX](https://img.shields.io/badge/index-blue?labelColor=blue)](INDEX.md)

Documentation for the `katananodling` python package.

This package allows to register a custom type of node called BaseCustomNode that
allow to quickly create new node to extend Katana. It is similar to SuperTools
with the difference it removes the need of going through Qt to build the interface.

The process of registering is also more flexible where you say which location
to register to a function called at startup. 
Those locations are a usual python package whose namespace list all the
BaseCustomNode subclasses that can be registered.

# Registering BaseCustomNodes

This is achieved via the `registerNodesFor` function of the 
[../katananodling/loader.py](../katananodling/loader.py) module.

This function will expect a list of package name as argument. Those package
must be already registered in the PYTHONPATH, so they can be imported.

```python
from katananodling.loader import registerNodesFor

locations_to_register = ["libStudio", "libProject", "opscriptlibrary"]

registerNodesFor(locations_to_register)
```

Each of this package will be imported and iterated directly to find the 
BaseCustomNode subclasses. To declare a subclass to be registered, you just
need to import it in the `__init__` of your package :

```toml
parentDir/  # <- registered in PYTHONPATH
    libProject/
        __init__.py
            """
            from .myTool import MyTool
            """
        myTool.py
            """
            from katananodling.entities import BaseCustomNode

            class MyTool(BaseCustomNode):
            
                name = "MyToolName"
                ...
                
                def _build(self):
                    ...
            """
```

How you organize the package is up to you but it is recommended to create one
module per subclass.


## Register process in details.

Starting **by the end**, here is the registration process :

- Each tool **class** will be registered in Katana using `NodegraphAPI.RegisterPythonNodeFactory` 
and a callback function when the node is created.
It will also receive a flavor using `NodegraphAPI.AddNodeFlavor` so you can 
quickly retrieve all custom tools.

- To retrieve the tool class we iterate through the given package object in
search for all objects which are subclasses of BaseCustomNode (and whose name
doesn't start with `_`)

- Now how do we retrieve the package as a python module object ? We will simply
do a :
  ```python
  package = importlib.import_module(package_id)  # type: ModuleType
  ```

- But what is `package_id` ? It's simply the name of this package. This mean
it has to be registered in the `PYTHONPATH` so it can be imported.

- And initally we have the `registerNodesFor()` function that will take as argument
a list of package name to import.


# Creating BaseCustomNodes

A custom tool will always be a subclass of `entities.BaseCustomNode`, but
it can also be a subclass of a subclass of BaseCustomNode and so on ...

As it most basic structure, a BaseCustomNode is :

- python :
  - some class variable for information to keep track of it
  - a `_build()` method to do whatever you want on the node.
  - an optional `upgrade()` method to handle porting of older version to newer ones.

```python
from katananodling.entities import BaseCustomNode


# class can actually be named anything but let's keep it clean :)
class MyToolName(BaseCustomNode):
  name = "MyToolName"  # identifier used to register the tool in Katana !
  version = (0, 1, 0)
  color = None
  description = "What the tool does in a few words."
  author = "<FirstName Name email@provider.com>"

  def _build(self):
    p = self.user_param.createChildNumber("amount", 666)
    hint = {
      "slider": True,
      "slidermax": 666,
      "help": "whatever",
    }
    p.setHintString(repr(hint))

  def upgrade(self):
    if self.version == self.about.version:
      return
    # now do whatever you need to upgrade
    self.about.__update__()

```


# Good to know

Be aware that you cannot open a scene with saved BaseCustomNode if at least the base
BaseCustomNode class is not registered in Katana. But you can open a scene
with BaseCustomNode subclass even if they are not registered.