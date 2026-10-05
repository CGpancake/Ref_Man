import os
import hou
import absolute.houdini_job_tools.util.util as util
from absolute.session import Session
import re
from pathlib import Path
from pxr import Usd


# Selecting General or Shot explicit USD asset location
def shot_menu(kwargs):
    node = kwargs['node']
    client = hou.getenv("CLIENT")
    project = hou.getenv("PROJECT")

    data = Session(client, project).wip.get_shots()

    menu = ['None', 'None', 'Project', 'Project']

    for s in data:
        menu.append(s)
        menu.append(s)

    return menu

    # Sourcing menu fur available assets

def destination(kwargs):
    node = kwargs['noded']
    stage = node.stage()
    prim = stage.GetPrimAtPath('/_data_')

    attribute_ref = prim.GetAttribute('context')
    attribute = attribute_ref.Get()

    node.parm('destination').set(attribute)

def asset_folder(node, type):
    # Get appropriate asset folder
    jobs = hou.getenv('JOBS')
    client = hou.getenv("CLIENT")
    project = hou.getenv("PROJECT")
    project_folder = os.path.join(jobs, client, project)
    location = ''


    if type == 'assembly':
        asset_type = type
    else:
        asset_type = type + 's'

    if node.evalParm('loc') == 'Project':
        location = node.evalParm('loc')
    else:
        location = 'Shot_' + node.evalParm('loc')


    folder = os.path.join(project_folder, 'assets', 'USD', location, asset_type)
    return folder


def parm_split(parm_name):
    # Get asset and variable index number from multi-parm block naming
    elements = parm_name.split('_')
    asset_type = elements[0]
    index = elements[2]
    return asset_type, index


def asset_menu(kwargs):
    node = kwargs['node']
    name = kwargs['parm'].name()
    elements = name.split('_')
    asset_type = elements[0]
    index = elements[2]

    # Get appropriate asset folder
    folder = asset_folder(node, asset_type)

    menu = ['None', 'None']

    # If folder exists, and they are files, add menu items first and their labels second to the menu
    if folder and os.access(folder, os.F_OK):
        for f in os.listdir(folder):
            if os.path.isdir(util.fix_path(os.path.join(folder, f))):
                menu.append(f)
                menu.append(f)

    # Get asset and variable index number from multi-parm block naming
    elements = name.split('_')
    asset_type = elements[0]
    index = elements[2]

    # Force updating available versions after selecting an asset
    v_menu = node.parm('{0}_version_{1}'.format(asset_type, index))
    v_menu_items = v_menu.menuItems()
    item = node.evalParm('{0}_version_{1}'.format(asset_type, index))
    if item in v_menu_items:
        return menu
    else:
        v_menu.set(v_menu_items[0])
        return menu


def file_list(folder):
    file_list = []
    if folder and os.access(folder, os.F_OK):
        for f in os.listdir(folder):
            if not os.path.isdir(util.fix_path(os.path.join(folder, f))):
                file_list.append(f)
    return file_list


def file_match(files, asset_name, group_name):
    group = []
    for f in files:
        regex = '(?P<name>{0})(?:_V)?(?P<ver>\d+)(?:_W)?(?P<wed>.+)?\.(?P<ext>\w+)'.format(asset_name)
        match = re.match(regex, f)
        if match:
            group.append(match.group(group_name))
    return group

#Verssion menu function is deprecated, Currently used a parameter to set version manually or pick_latest_version function
def version_menu(kwargs):
    node = kwargs['node']
    parm_name = kwargs['parm'].name()

    elements = parm_name.split('_')
    asset_type = elements[0]
    index = elements[2]

    # If asset name is not selected, there would be no versions
    asset_name = node.evalParm('{0}_name_{1}'.format(asset_type, index))
    if asset_name == 'None':
        menu = ['None', 'None']
        return menu

    folder = os.path.join(asset_folder(node, asset_type), asset_name)

    files = []

    if folder and os.access(folder, os.F_OK):
        for f in os.listdir(folder):
            files.append(f)

    group_name = 'ver'
    versions = []

    for f in files:
        regex = f'(?P<name>{asset_name})(?:_V)?(?P<ver>\d+)(?P<wed>_wedge)?\.?(?P<ext>\w+)?'
        match = re.match(regex, f)
        if match:
            versions.append(match.group(group_name))

    versions = list(sorted(set(versions)))

    if len(versions) == 0:
        menu = ['None', 'None']
        return menu

    latest_version = max(versions)
    versions.remove(latest_version)

    menu = [latest_version, 'Latest']

    for v in versions:
        menu.append(v)
        menu.append(v)

    # if node.parm('{0}_wedge_{1}'.format(asset_type, index)):
    #    if node.parm('{0}_wedgeread_{1}'.format(asset_type, index)) == 'explicit':
    #        node.parm('{0}_wedgemenu_{1}'.format(asset_type, index)).pressButton()

    # node.cook(True)
    return menu

def pick_latest_version(node, type, index):

    name_parm = type + '_' + 'name' + '_' + str(index)
    asset_name = node.evalParm(name_parm)

    # If asset name is not selected, there would be no versions

    if asset_name == 'None':
        latest_version = 0
        return int(latest_version)


    folder = os.path.join(asset_folder(node, type), asset_name)

    files = []

    if folder and os.access(folder, os.F_OK):
        for f in os.listdir(folder):
            files.append(f)

    group_name = 'ver'
    versions = []

    for f in files:
        regex = f'(?P<name>{asset_name})(?:_V)?(?P<ver>\d+)(?P<wed>_wedge)?\.?(?P<ext>\w+)?'
        match = re.match(regex, f)
        if match:
            versions.append(match.group(group_name))

    versions = list(sorted(set(versions)))

    if len(versions)==0:
        latest_version = 0
    else:
        latest_version = int(versions[-1])

    return latest_version
def wedge_menu(kwargs):
    node = kwargs['node']
    parm_name = kwargs['parm'].name()
    parm_path = kwargs['parm'].path()
    parm = kwargs['parm']

    elements = parm_name.split('_')
    asset_type = elements[0]
    index = elements[2]

    enable = node.parm(f'{asset_type}_wedge_{index}')
    if enable == 0:
        enable.set(1)

    asset_name = node.evalParm(f'{asset_type}_name_{index}')

    version = node.evalParm(f'{asset_type}_version_{index}')
    wedge_subfolder = f'{asset_name}_V{version}_wedge'
    folder = os.path.join(asset_folder(node, asset_type), asset_name, wedge_subfolder)

    menu = []
    # Sort files and check if they include wedges
    selected_version = node.evalParm('{0}_version_{1}'.format(asset_type, index))

    name_start = f'{asset_name}_V{selected_version}'
    files = []
    if folder and os.access(folder, os.F_OK):
        for f in os.listdir(folder):
            if not os.path.isdir(os.path.join(folder, f)):
                files.append(f)
    group_name = 'wed'

    for f in files:
        if f.startswith(name_start):
            regex = '(?P<name>{0})_V{1}(?:_W)?(?P<wed>.+)?\.(?P<ext>\w+)'.format(asset_name, selected_version)
            match = re.match(regex, f)
            if match and match.group(group_name) is not None:
                menu.append(match.group(group_name))
                menu.append(match.group(group_name))

    if len(menu) <= 2:
        menu = ['None', 'None']
        # node.cook(True)
        return menu

    # node.cook(True)
    return menu
    # if len(menu) == 2:
    #    node.parm('{0}_wedge_(1)'.format(asset_type, index)).set(0)
    # else:
    #    return menu

def update(kwargs):
    node = kwargs['node']
    parms = node.parms()
    for p in parms:
        if p.name().endswith('_num'):
            p.set(0)
        else:
            return

    # for p in parms:
    #     if '_name_' in p.name():
    #         p.pressButton()


def set_path(kwargs):
    node = kwargs['node']
    name = kwargs['parm'].name()

    elements = name.split('_')

    asset_type = elements[0]
    index = elements[2]
    asset_name = node.evalParm('{0}_name_{1}'.format(asset_type, index))
    destination = node.evalParm('dest')
    prim_path = destination
    hou.node(node.path() + f'/{asset_type}').parm(f'primpath{index}').set(prim_path)

    version_mode = node.evalParm('{0}_version_{1}'.format(asset_type, index))
    version : int = 0


    if version_mode == 'Manual':
        version = node.evalParm('{0}_vernumManual_{1}'.format(asset_type, index))
    elif version_mode == 'Latest':
        version = node.evalParm('{0}_vernumLatest_{1}'.format(asset_type, index))

    ext = 'usd'

    # Version conditions
    version_write = '_V' + str(f'{version:02}')

    # Wedge conditions
    wedge = ''
    wedge_enable = node.evalParm(f'{asset_type}_wedge_{index}')
    if wedge_enable:
        wedge_read = node.evalParm(f'{asset_type}_wedgeread_{index}')

        if wedge_read == 'explicit':
            wedge_menu = node.evalParm('{0}_wedgemenu_{1}'.format(asset_type, index))
            if wedge_menu != 'None':
                wedge = '_W{0}'.format(node.evalParm('{0}_wedgemenu_{1}'.format(asset_type, index)))
        elif wedge_read == 'attribute':
            if node.evalParm('{0}_wedgeparm_{1}'.format(asset_type, index)) == '':
                wedge = ''
            else:
                wedge_index = node.evalParm(f'{asset_type}_wedgeparm_{index}')
                wedge = f'_W{int(wedge_index):02}'

    file_name = f'{asset_name}{version_write}{wedge}.{ext}'
    wedge_subfolder = f'{asset_name}_{wedge}'

    if wedge_enable:
        asset_path = os.path.join(asset_folder(node, asset_type), asset_name, wedge_subfolder)
    else:
        asset_path = os.path.join(asset_folder(node, asset_type), asset_name)

    asset_file = os.path.join(asset_path, file_name)

    #Adjust reference nodes inside HDA
    child_path = f'{node.path()}/{asset_type}'
    child = hou.node(child_path)
    child_parm = f'filepath{index}'
    # child_prim_path = f'primpath{index}'

    reference = f'{asset_type}_filereference_{index}'
    file_name_parm = f'{asset_type}_filename_{index}'

    if node.parm(reference).isLocked():
        node.parm(reference).lock(False)

    if node.parm(file_name_parm).isLocked():
        node.parm(file_name_parm).lock(False)

    owner_parm = node.parm('{0}_owner_{1}'.format(asset_type, index))

    if owner_parm.isLocked():
        owner_parm.lock(False)

    if os.access(asset_file, os.F_OK):
        if not os.path.isdir(asset_file):
            if asset_name != 'None':
                node.parm(reference).set(asset_path)
                node.parm(reference).lock(True)
                node.parm(file_name_parm).set(file_name)
                node.parm(file_name_parm).lock(True)
                child.parm(child_parm).set(asset_file)
                # if asset_type != 'assembly':
                #     child.parm(child_prim_path).set(prim_path)
                # else:
                #     child.parm(child_prim_path).set(prim_path)
            else:
                node.parm(reference).set(asset_path)
                node.parm(reference).lock(True)
                node.parm(file_name_parm).set('')
                child.parm(child_parm).set('')
                # if asset_type != 'assembly':
                #     child.parm(child_prim_path).set(prim_path)
                # else:
                #     child.parm(child_prim_path).set(prim_path)

            path = Path(asset_file)
            file_owner = path.owner()

            owner_parm.set(file_owner)
            owner_parm.lock(True)

            #Set comment

            # Create a stage object from the USD file
            stage = Usd.Stage.Open(asset_file)

            # Access the root layer of the stage
            root_layer = stage.GetRootLayer()
            comment_parm = node.parm(f'comment_{index}')
            if comment_parm.isLocked:
                comment_parm.lock(False)

            if root_layer:
                # Check if customLayerData exists in the file
                if root_layer.customLayerData:
                    # Get the customLayerData dictionary
                    custom_layer_data = root_layer.customLayerData

                    # Access specific data within customLayerData
                    comment = custom_layer_data['Comment']
                    if comment:
                        comment_parm.set(comment)
                        comment_parm.lock(True)
                    else:
                        print("No Comment found in customLayerData.")
                        comment_parm.set('')
                else:
                    print("No customLayerData found in the USD file.")
                    comment_parm.set('')
            else:
                print("Failed to open the USD file or retrieve customLayerData.")
                comment_parm.set('')


    else:
        node.parm(reference).set(asset_path)
        node.parm(reference).lock(True)
        child.parm(child_parm).set('')
        #child.parm(child_prim_path).set('')

        owner_parm.set('')
        owner_parm.lock(True)
        node.parm(file_name_parm).set('File Not Found')
        node.parm(file_name_parm).lock(True)
    return


def openPath(kwargs):
    node = kwargs['node']
    parm_name = kwargs['parm_name']
    elements = parm_name.split('_')

    if elements[0] == 'assembly':
        asset_type = elements[0]
    else:
        asset_type = elements[0] + 's'


    index = elements[2]

    jobs = hou.getenv('JOBS')
    client = hou.getenv("CLIENT")
    project = hou.getenv("PROJECT")

    project_folder = os.path.join(jobs, client, project)

    if node.evalParm('loc') == 'Project':
        location = node.evalParm('loc')
    else:
        location = 'Shot_' + node.evalParm('loc')

    asset_name = node.evalParm(f'{elements[0]}_name_{index}')

    folder = os.path.join(project_folder, 'assets', 'USD', location, asset_type, asset_name)

    if os.path.exists(folder):
        if folder[-1] != '/':
            folder += '/'
        hou.ui.showInFileBrowser(folder)
    else:
        hou.ui.displayMessage(text=f"Could not open directory:\n{folder}.",
                              severity=hou.severityType.ImportantMessage)


def load(kwargs):
    node = kwargs['node']
    parm_name = kwargs['parm'].name()
    elements = parm_name.split('_')
    asset_type = elements[0]
    index = elements[2]

    asset_name = node.evalParm('{0}_name_{1}'.format(asset_type, index))

    folder = '{0}/{1}'.format(asset_folder(node, asset_type), asset_name)

    menu = []
    # Sort files and check if they include wedges
    selected_version = node.evalParm('{0}_version_{1}'.format(asset_type, index))

    name_start = '{0}_V{1}'.format(asset_name, selected_version)

    files = file_list(folder)

    group_name = 'wed'

    for f in files:
        if f.startswith(name_start):
            regex = '(?P<name>{0})_V{1}(?:_W)?(?P<wed>.+)?\.(?P<ext>\w+)'.format(asset_name, selected_version)
            match = re.match(regex, f)
            if match and match.group(group_name) is not None:
                menu.append(match.group(group_name))

    if len(menu) > 0:
        node.parm('{0}_wedge_{1}'.format(asset_type, index)).set(1)
    else:
        node.parm('{0}_wedge_{1}'.format(asset_type, index)).set(0)


def owner(kwargs):
    node = kwargs['node']
    parm = kwargs['parm']
    parm_name = kwargs['parm'].name()
    elements = parm_name.split('_')
    asset_type = elements[0]
    index = elements[2]

    path_eval = node.evalParm('{0}_filereference_{1}'.format(asset_type, index))
    path = Path(path_eval)
    file_owner = path.owner()
    parm.set(file_owner)
    return file_owner


def enable_wedge(kwargs):
    node = kwargs['node']
    parm_name = kwargs['parm_name']
    elements = parm_name.split('_')
    asset_type = elements[0]
    index = elements[2]
    asset_name = node.evalParm(f'{asset_type}_name_{index}')
    folder = os.path.join(asset_folder(node, asset_type), asset_name)
    # Force updating available wedges after enabling
    version = node.evalParm(f'{asset_type}_version_{index}')
    wedge = node.evalParm(f'{asset_type}_wedge_{index}')
    starts_with = f'{asset_name}_V{version}'

    if folder and os.access(folder, os.F_OK):
        has_wedge = os.path.isdir(f'{folder}/{starts_with}_wedge')
        has_file = os.path.isfile(f'{folder}/{starts_with}.usd')

        if has_wedge and has_file:

            response = hou.ui.displayMessage(text=f"V{version} contains files with and without wedging:\n"
                                                  f"Do you want to enable wedging?.",
                                             buttons=('Yes', 'No'),
                                             severity=hou.severityType.Message)
            if response == 0:
                node.parm(f'{asset_type}_wedge_{index}').set(1)
                if node.evalParm(f'{asset_type}_wedgeread_{index}') == 'explicit':
                    wedge_list = node.parm(f'{asset_type}_wedgemenu_{index}').menuItems()
                    node.parm(f'{asset_type}_wedgemenu_{index}').set(wedge_list[0])
                    node.parm(f'{asset_type}_wedgemenu_{index}').pressButton()
                set_path(kwargs)
            if response == 1:
                node.parm(f'{asset_type}_wedge_{index}').set(0)
                set_path(kwargs)

        elif has_wedge:
            node.parm(f'{asset_type}_wedge_{index}').set(1)
            set_path(kwargs)

        elif has_file:
            node.parm(f'{asset_type}_wedge_{index}').set(0)
            set_path(kwargs)
        else:
            node.parm(f'{asset_type}_version_{index}').pressButton()
            set_path(kwargs)
            return


def reference_primitive(kwargs):
    node = kwargs['node']
    parm_name = kwargs['parm'].name()
    elements = parm_name.split('_')
    asset_type = elements[0]
    index = elements[2]
    selection = node.evalParm(parm_name)

    #Set value to reference node inside HDA
    child_path = f'{node.path()}/{asset_type}'
    child = hou.node(child_path)
    child_parm = f'filerefprim{index}'
    child.parm(child_parm).set(selection)

def reference_specific_primitive(kwargs):
    node = kwargs['node']
    parm_name = kwargs['parm'].name()
    elements = parm_name.split('_')
    asset_type = elements[0]
    index = elements[2]
    selection = node.evalParm(parm_name)

    #Set value to reference node inside HDA
    child_path = f'{node.path()}/{asset_type}'
    child = hou.node(child_path)
    child_parm = f'filerefprimpath{index}'
    child.parm(child_parm).set(selection)


def onCreated(kwargs):
    node = kwargs['node']
    node.parm('loc').set('Project')
    node.parm('loc').pressButton()


