# Index

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

> Have a look at [../katananodling/loader.py](../katananodling/loader.py)

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

## Registering result.

The node can then be accessed via the usual `Tab` shortcut, and you will notice
that they all have their own node type.

You can quickly retrieve all the BaseCustomNodes nodes in the scene using :

```python
from Katana import NodegraphAPI
import katananodling.c

NodegraphAPI.GetFlavorNodes(katananodling.c.KATANA_FLAVOR_NAME)
```


# Creating BaseCustomNodes

> You can find a working example in [../demolibrary](../demolibrary)

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
    hint = {"slider": True, "slidermax": 666, "help": "whatever"}
    p.setHintString(repr(hint))

  def upgrade(self):
    if self.version == self.about.version:
      return
    # now do whatever you need to upgrade
    self.about.__update__()

```

## methods

### `BaseCustomNodes.__init__`

Called when the node is created AND when loaded from an existing scene.

You don't need to implement this by default.

If you implement it, do not call the superclass init constructor. *( =no `super()`)*

### `BaseCustomNodes._build`

Called only when the node is created for the first time in the scene. NOT on
previous scene loading. You can create nodes, edit parameters, add attributes, ...

### `BaseCustomNodes.upgrade`

Called when the node is loaded from a previous scene AND when the node is created
for the first time.

You don't need to implement this method unless you have published multiple versions
of your node and one introduce some breaking change like a new parameter. In that
case you can perform a check on the version of the node and then perform the required
upgrade for this version.

Don't forget to call `self.about.__update__()` at the end so the version stored
on the node itself is updated.

## documentation

It is possible to specify a documentation file that can be quickly opened by
the artist from Katana using an automatized button on the tool's node.

There is 2 way to specify the path to the documentation :

### documentation : on python class

Just override the `documentation` class variable :

```python
import os.path
from katananodling.entities import BaseCustomNode

# class can actually be named anything but let's keep it clean :)
class MyToolName(BaseCustomNode):
  
  documentation = os.path.splitext(__file__)[0] + ".md"
  # ...
```

This take priority over the other method, if implemented.

> **Info**
> 
> The path is opened using `webbrowser.open()` so you can actually also specify
> a URL.

But the above example is actually already automatized :

### documentation : on a side-car file

The file just has to be named exactly like the tool's python module/package
and have the `.md` extension.

```
myLibrary/
    __init__.py
    tree_generator.py
    tree_generator.lua
    tree_generator.md
```


# Layered menu

The nodes are accessible via the usual `Tab` shortcut, but they will be 
drowned among the other nodes. To find the CustomNodes quicker, there is a 
pre-made layeredMenu available that you can register :

```python
from Katana import LayeredMenuAPI
import katananodling.menu

layered_menu = katananodling.menu.getLayeredMenuForAllCustomNodes()
LayeredMenuAPI.RegisterLayeredMenu(layered_menu, "katananodling")
```

There is a demo in [../dev/KatanaResources/UIPlugins](../dev/KatanaResources/UIPlugins).
(you can add [../dev/KatanaResources](../dev/KatanaResources) to the `KATANA_RESOURCES` variable to test.)


# Environment variables

Check [../katananodling/c.py](../katananodling/c.py) for an in-depth look.

The available environment variable are :

## `KATANA_NODLING_EXCLUDED_NODES`:

List of CustomNodes **class name** that must be not be registered at all.

Supports Unix shell-style wildcards thanks to the fnmatch python module.

List separator is the system path separator (`;` or `:`):

> ex: `"Lxm*;SceneGenerator[12];PointWidth"`


## `KATANA_NODLING_UPGRADE_DISABLE`: 

Set to 1 (or actually to anythin non-empty)
to disable the upgrading process when BaseCustomNode nodes are loaded
from previous version.

This can be useful when opening archived project or sending scene to the farm.


## `KATANA_NODLING_NODE_PARAM_DEBUG`: 

Set to 1 (or actually to anythin non-empty)
to enable the "debug" mode for BaseCustomNode parameters in the nodegraph.
Params that are usually hidden are made visible.


# Good to know

> Be aware that you cannot open a scene with saved `BaseCustomNode` instance
> if at least the base `BaseCustomNode` class is not registered in Katana.
> But you can open a scene with `BaseCustomNode` subclasses even if they are not registered.
> (so even if you unregister a node-library the scenes will still open)

> This repo has been extracted from [opscripting](https://github.com/MrLixm/opscripting).
> To get all the commit history looks for commit on the previously named
> `customtooling` directory there.
