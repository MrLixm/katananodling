# Index

[![root](https://img.shields.io/badge/back_to_root-536362?)](../README.md)
[![INDEX](https://img.shields.io/badge/index-blue?labelColor=blue)](INDEX.md)

Documentation for the `katananodling` python package.

# What

This package allows to register a custom type of node called BaseCustomNode that
allow to quickly create new node to extend Katana. It is similar to SuperTools
with the difference it removes the need of going through Qt to build the interface.

The process of registering is also more flexible where you say which location
to register to a function called at startup. 
Those locations are a usual python package whose namespace list all the
BaseCustomNode subclasses that can be registered.

As for SuperTools, CustomNode are version tracked and can be upgraded which
made maintenance much easier. They work well in a version-controlled pipeline.

Their biggest issue is that they are defined in Python. While Macro made easy
for non-technical artist to create tools, CustomNodes will prevent this and will
imply some basic python knowledge to iterate tools.

A solution to this is currently being investigated in issue https://github.com/MrLixm/katananodling/issues/1, where we would
let users create their node in Katana as usual and just have them run a command
to convert them to python.

# Installation

`katananodling` is a traditional python package and just need its parent directory
to be added to `PYTHONPATH`

```ini
/z/stuff/
    katananodling/
        README.md
        katananodling/
        doc/
        ...
```

```shell
export PYTHONPATH="$PYTHONPATH;/z/stuff/katananodling"
```

It has a single dependencies which is the official python `typing` module.
It is only needed if your Katana version is on a Python version <3.5.

To install it you can 
```shell
cd /z/stuff
mkdir typing
python2 -m pip install typing --target=typing/
```
and then just add it to `PYTHONPATH`
```shell
export PYTHONPATH="$PYTHONPATH;/z/stuff/typing"
```

# Registering BaseCustomNodes

Let's start by the end and see what is the entry point in Katana :

This is achieved via the `registerNodesFor` function of the 
[../katananodling/loader.py](../katananodling/loader.py) module.

This function will expect a list of python package names as argument. Those package
must be already registered in the PYTHONPATH, so they can be imported.

We will call those packages "node libraries".

```python
from katananodling.loader import registerNodesFor

locations_to_register = ["libStudio", "libProject", "opscriptlibrary"]

registerNodesFor(locations_to_register)
```

## Libraries

> A library is a python package that defined a bunch of BaseCustomNode 
> subclasses inside.

Each of this library will be imported and iterated directly to find the 
BaseCustomNode subclasses. To declare a subclass to be registered, you just
need to import it in the `__init__` of your package :

```ini
parentDir/  # <- registered in PYTHONPATH
    libProject/  # <- the library
        __init__.py
            """
            import sys  # <- will be ignored
            
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

So the library only care about what is defined in the `__init__.py` of the package.
(not 100% true as some "utility" functions expect a certain hierarchy)

How you organize it is up to you, but consider the following conventions :

### Libraries Structure suggestion

#### Modules

For small libraries with few nodes, one module per node subclass.

```ini
library/
    __init__.py
    nodeAlpha.py
    nodeBeta.py
    nodeBeta.md
```

#### Packages

(Recommended) For medium to big libraries. One package per node subclass.

```ini

library/
    __init__.py
    nodeAlpha/
        __init__.py
    nodeBeta/
        __init__.py
        __init__.md
        img.jpg
        # ...
```

We use the `__init__.py` to directly declare the node and avoid the need to create
a new module.

Have a look at the [demolibrary](../demolibrary) to see some examples.


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

## Registering's result.

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

- some class variable for information to keep track of it
- a `_build()` method to do whatever you want on the node.
- an optional `upgrade()` method to handle porting of older version to newer ones.

```python
from katananodling.entities import BaseCustomNode

# class can actually be named anything but its name is used as identifier
# so don't change it later.
class MyToolNameNode(BaseCustomNode):
  
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

It's up to you to name the class but here is some hints :

- Ends the name with `Node` ex: `TreeGeneratorNode`
- Once the node has been released in the pipeline, do not change it. The class
name is used  by the `KATANA_NODLING_EXCLUDED_NODES` env variable to filter out
node you don't want to register.

## class variables

These are the public variables you have to set on each new subclass.

### ![str](https://img.shields.io/badge/str-4f4f4f) BaseCustomNode.name

Unique name used to register the node in Katana.

Changing it later will break references to nodes in previous scenes.

### ![tuple[int, int, int]](https://img.shields.io/badge/tuple[int,_int,_int]-4f4f4f) BaseCustomNode.version

Specified as (major, minor, patch) and following https://semver.org.

### ![tuple[float, float, float] or None](https://img.shields.io/badge/tuple[float,float,float]_or_None-4f4f4f) BaseCustomNode.color

Color used on the LayeredMenu but can also be used by the developer to color
the node itself.

Tips: you can used the `Colors` class attribute to access pre-defined colors
(editable in the `c.py` module)

```python
from katananodling.entities import BaseCustomNode

class MyNode(BaseCustomNode):
    color = BaseCustomNode.Colors.purple
```

Set to None to use the default color.


### ![str](https://img.shields.io/badge/str-4f4f4f) BaseCustomNode.description

Short text describing what the node does.

### ![str](https://img.shields.io/badge/str-4f4f4f) BaseCustomNode.author

Name of the author of the node with a potential email adress like `<FirstName Name email@provider>`

### ![str](https://img.shields.io/badge/str-4f4f4f) BaseCustomNode.documentation

See [documentation section](#documentation)

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

The version to compare are the version stored in the class attribute, and
the version stored on the node parameters :

```python
def upgrade(self):
    if self.version == self.about.version:
      return
    # reaching here means we have a version difference
    
    version = self.about.version  # just to get less characters to type :^)
    
    if version.major < 2 and version.minor < 2:
        # whatever
        pass
        
    self.about.__update__()
```


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

> **Note**:
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

# BaseCustomNode subclasses to subclass

Yeah that title is not very clear : In some cases you might want to create 
multiple custom nodes that share the same features. To avoid duplicated code
it can be smart to create a first subclass of `BaseCustomNode` that is implemented
here, in this package, and then subclassed by the custom nodes in the libraries.

There is currently one example of this which is the `OpScriptCustomNode` class
in [entities/opscript](../katananodling/entities/opscript.py).

It is recommended to create on new module in `entities/` per new subclass.

## OpScriptCustomNode

Convenient class to create a custom node whose main feature is based around
an OpScript. It creates a default OpScript node that can then be configured as
wished.

It's `getLuaModuleName` function assume that the OpScript lua script used is
an actual file living next to the python module of the subclass, and not code
directly stored in the OpScript node. This is the principle of the 
[opscripting](https://github.com/MrLixm/opscripting) package.


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

The shortcut to open this layeredMenu in katana is `O` by default but can be
changed in `c.py`.


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

This can be useful when opening archived project or sending scene to a render farm.


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

> Some utility function make use of `sys.modules` to work. So be aware that 
> monkey patching or other weird path manipulation may affect them.
> 
> Those are `entities.opscript.OpScriptCustomNode.getLuaModuleName` and
> `entities.opscript.BaseCustomNode.getLibraryPath`