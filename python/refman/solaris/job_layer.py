# region Imports
import hou
import Ref_Man.util.util as util
import os
import sys
import shutil
import re
from importlib import reload
from absolute.session import Session
from pxr import Usd

def asset_menu(kwargs):
    node = kwargs['node']
    location = node.evalParm('loc')
    asset_type = node.evalParm('type')

    jobs = hou.getenv('JOBS')
    client = hou.getenv("CLIENT")
    project = hou.getenv("PROJECT")

    project_folder = os.path.join(jobs, client, project)

    asset_path = '{0}/assets/USD/{1}/{2}/'.format(project_folder, location, asset_type)

    menu = ['None', 'None']

    if asset_path and os.access(asset_path, os.F_OK):
        for f in os.listdir(asset_path):
            if os.path.isdir(util.fix_path(os.path.join(asset_path, f))):
                menu.append(f)
                menu.append(f)
    return menu


def load_from_disk(kwargs):
    node = kwargs['node']
    load = node.evalParm('load')

def asset_path_switch(kwargs):
    node = kwargs['node']
    node.parm('name').set('None')
    node.parm('name').pressButton()


def openPath(kwargs):
    node = kwargs['node']

    dir = node.evalParm('layer_folder')

    if os.path.exists(dir):
        if dir[-1] != '/':
            dir += '/'
        hou.ui.showInFileBrowser(dir)
    else:
        hou.ui.displayMessage(text="Could not open directory:\n{dir}.".format(dir=dir),
                              severity=hou.severityType.ImportantMessage)

def latest_version(kwargs):
    node = kwargs['node']

    if node.evalParm('enableversion') and node.evalParm('autoversion'):
        # Determine the cache directory

        # Check if asset name is available
        child = hou.node(f'{node.path()}/Distinguish_Role')
        child.cook()

        root = node.evalParm('ref_root')

        if not os.access(root, os.F_OK):
            print("Cache directory does not exist.")
            node.parm('version').set(1)
            return

        # List directories in the cache directory
        items = os.listdir(root)
        dirs = [d for d in items if os.path.isdir(os.path.join(root, d))]
        # Initialize version list
        version_list = []
        # Regex to match directory names with the specific asset name and version pattern
        regex = fr'(V(?P<ver>\d+))$'
        for d in dirs:
            match = re.search(regex, d, re.IGNORECASE)
            if match:
                version_list.append(int(match.group('ver')))

        if not version_list:
            node.parm('version').set(1)
        else:
            # Increment the highest version number found
            version_list.sort()
            new_version = version_list[-1] + 1
            node.parm('version').set(new_version)



def set_default_primitive(kwargs):
    node = kwargs['node']
    stage = node.stage()

    root = stage.GetPseudoRoot()
    children = root.GetChildren()
    prims = []

    for c in children:
        if c.GetName() == 'HoudiniLayerInfo':
            continue
        prims.append(c)

    if len(prims) > 1:
        hou.ui.displayMessage(text='Root contains multiple primitives\n'
                                   'Place all primitives under a single parent.',
                              severity=hou.severityType.Error)
        raise RuntimeError('Root contains multiple primitives')

    elif len(prims) == 0:
        hou.ui.displayMessage(text='Root contains no primitives\n'
                                   'Place primitives under a single parent.',
                              severity=hou.severityType.Error)
        raise RuntimeError('Root contains no primitives')
    elif len(prims) == 1:
        if node.parm('defaultprim').isLocked():
            node.parm('defaultprim').lock(False)

        child_path = f'{node.path()}/Export'
        child = hou.node(child_path)
        child_parm = 'defaultprim'
        child.parm(child_parm).set(str(prims[0].GetPrimPath()))
        node.parm('defaultprim').set(str(prims[0].GetPrimPath()))
        node.parm('defaultprim').lock(True)


def force_compare(kwargs):
    # Get the current node, parent, and editable stage
    node = kwargs['node']
    load = node.evalParm('load')
    if not load:
        compare = hou.node(f'{node.path()}/Compare_file')
        stage = hou.node(f'{node.path()}/set_customData').stage()

        # Define the path to the prim where the hash is stored
        prim_path = hou.node(f'{node.path()}/Distinguish_Role').evalParm('root')
        if not prim_path:
            raise hou.NodeWarning("No primitives were referenced")

        # Retrieve the prim from the current editable stage
        current_prim = stage.GetPrimAtPath(prim_path)
        if not current_prim.IsValid():
            raise RuntimeError(f"Prim at path {prim_path} does not exist on the current stage")

        # Retrieve the stored hash from the current prim
        current_hash = current_prim.GetCustomDataByKey('asset_hash')

        if current_hash is None:
            print("Current asset hash not found.")
        else:
            print(f"Current asset hash: {current_hash}")
            compare.parm('hash').set(str(current_hash))

        file = None
        if os.path.exists(node.evalParm('usd_file')):
            file = node.evalParm('usd_file')

        if not file:
            print("No valid USD file found.")
            hou.node(f'{node.path()}/Compare_Switch').parm('input').set(1)
            hou.node(f'{node.path()}/Compare_Switch').parm('input').pressButton()
            compare.parm('file').set('')
            compare.parm('file_hash').set('File not found')
            node.parm('message').set('File not found - defaulting to LOP input')
            node.parm('wipup').set(1)
            color = hou.Color(0.8, 0.2, 0.2)
            node.setColor(color)
        else:
            # Open the saved stage from the file
            compare.parm('file').set(file)
            print('testing 02')
            if node.evalParm('check') == 1 and node.evalParm('load') == 0:
                saved_stage = ''
                if os.path.isfile(file):
                    print(f"File path evaluated: {file}, Exists: {os.path.isfile(file)}")
                    saved_stage = Usd.Stage.Open(file)
                else:
                    node.parm('message').set('File was not created yet')
                    node.parm('wipup').set(0)

                # Retrieve the prim from the saved stage
                saved_prim = saved_stage.GetPrimAtPath(prim_path)
                if not saved_prim.IsValid():
                    raise RuntimeError(f"Prim at path {prim_path} does not exist on the saved stage")

                # Retrieve the stored hash from the saved prim
                saved_hash = saved_prim.GetCustomDataByKey('asset_hash')

                if saved_hash is None:
                    print("Saved asset hash not found.")
                else:
                    print(f"Saved asset hash: {saved_hash}")
                    compare.parm('file_hash').set(str(saved_hash))

                # Compare the hashes
                if current_hash != saved_hash:
                    hou.node(f'{node.path()}/Compare_Switch').parm('input').set(1)
                    hou.node(f'{node.path()}/Compare_Switch').parm('input').pressButton()
                    if node.evalParm('autoversion'):
                        node.parm('message').set('Changes Found - Live Check wip up')
                        node.parm('wipup').set(1)
                        color = hou.Color(1.0, 0.6, 0.0)
                        node.setColor(color)
                    else:
                        node.parm('message').set('Warning! Changes Found - autoversion is disabled and file will be overwritten')
                        node.parm('wipup').set(0)
                        color = hou.Color(0.8, 0.2, 0.2)
                        node.setColor(color)

                else:
                    print("No differences found based on asset hash.")
                    hou.node(f'{node.path()}/Compare_Switch').parm('input').set(0)
                    hou.node(f'{node.path()}/Compare_Switch').parm('input').pressButton()
                    color = hou.Color(0.75, 1.0, 0.2)
                    node.setColor(color)
                    node.parm('message').set(
                        'No updates found compared to file on disk - referencing existing file from disk')
                    node.parm('wipup').set(0)
            elif node.evalParm('load') == 1:
                node.parm('message').set(
                    'Node is set to always load files from disk')
                color = hou.Color(0.1, 0.3, 0.75)
                node.setColor(color)
                node.parm('wipup').set(0)
            elif node.evalParm('load') == 0 and node.evalParm('check') == 0 and node.evalParm('autoversion') == 1:
                node.parm('message').set(
                    'Node is set to auto version after manual saving only')
                color = hou.Color(0.2, 0.2, 0.2)
                node.setColor(color)
                node.parm('wipup').set(0)
            else:
                node.parm('message').set(
                    "I don't know what's happening ¯\_(ツ)_/¯")
                color = hou.Color(1.0, 0.2, 0.75)
                node.setColor(color)
                node.parm('wipup').set(0)
    else:
        color = hou.Color(0.3, 0.35, 0.7)
        node.setColor(color)




def pre_render(kwargs):
    print('prerender working!')
    node = kwargs['node']
    node.parm('latest').pressButton()
    elements = hou.node(node.path() + '/Detect_Elements')
    elements.cook()
    configure = hou.node(node.path() + '/configurelayer')
    configure.cook()

#unnecesary cahnge
def onCreated(kwargs):
    node = kwargs['node']

def context_menu(kwargs):
    node = kwargs['node']
    node_type = node.type().name()
    context = ''
    menu = []
    if 'Assets' in node_type:
        type = kwargs['parm'].name().split('_')[0]
        index = kwargs['script_multiparm_index']
        root = node.evalParm(f'{type}_root_{index}')
        name = node.evalParm(f'{type}_name_{index}')
        context = os.path.join(root, name, 'Context')
        menu = ['', 'Asset']
    if 'Reference_Manager' in node_type:
        root = node.evalParm('ref_root')
        context = os.path.join(root, 'Context')
        menu = ['asset','asset','geo','geo','mtl','mtl','agent','agent','clip','clip','groom','groom']

    paths = []
    build_context_menu_items(context, paths)
    for p in paths:
        _relative_path = p.split(f'{context}/', 1)[-1]
        subfolders = _relative_path.split(os.sep)
        cleaned_path = os.sep.join(subfolders[:-1])
        if cleaned_path not in menu:
            menu.append(cleaned_path)
            menu.append(cleaned_path)

    if menu:
        return menu
    else:
        return []


def build_context_menu_items(current_path, paths):
    # Ensure paths is a set for unique collection
    if os.path.isdir(current_path):
        items = os.listdir(current_path)
        file_found = False  # Flag to ensure directory contains at least one file
        for item in items:
            full_path = os.path.join(current_path, item)
            if os.path.isdir(full_path):
                # If it's a directory, recurse into it
                build_context_menu_items(full_path, paths)
            else:
                # If it's a file, set the flag
                file_found = True
        if file_found:
            # Add the directory path once if it contains at least one file
            if current_path not in paths:
                paths.append(current_path)