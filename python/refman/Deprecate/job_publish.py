# region Imports
import hou
from utility_scripts import main as util
import os
import sys
import shutil
import re
from absolute.session import Session


def shot_menu(kwargs):
    node = kwargs['node']
    jobs = hou.getenv('JOBS')
    client = hou.getenv("CLIENT")
    project = hou.getenv("PROJECT")

    project_folder = os.path.join(jobs, client, project)
    data = Session(client, project).wip.get_shots()

    menu = ['None', 'None', 'Project', 'Project']

    for s in data:
        menu.append(s)
        menu.append(s)

    node.cook(True)
    return menu


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


def asset_path_switch(kwargs):
    node = kwargs['node']
    node.parm('name').set('None')
    node.parm('name').pressButton()


def asset_path(kwargs):
    node = kwargs['node']
    location = node.evalParm('loc')
    asset_name = node.evalParm('name')
    asset_type = node.evalParm('type')
    construct = node.evalParm('construct')

    node.parm('construct').lock(False)

    if asset_name == 'None' or asset_type == 'None' or location == 'None':
        node.parm('construct').set('None')
        node.parm('construct').lock(True)
        asset_menu(kwargs)
        node.cook(True)
        return

    jobs = hou.getenv('JOBS')
    client = hou.getenv("CLIENT")
    project = hou.getenv("PROJECT")

    project_folder = os.path.join(jobs, client, project)

    version_enable = node.evalParm('enableversion')
    version = ''
    if version_enable:
        version_num = '%02d' % (node.evalParm('version'))
        version = '_V{0}'.format(version_num)

    wedge_enable = node.evalParm('enablewedge')
    wedge = ''
    if wedge_enable:
        wedge_val = node.evalParm('wedge_variable')
        wedge = '_W{0}'.format(wedge_val)
        wedge_subfolder = f'{asset_name}{version}_wedge'
        asset_construct = os.path.join(project_folder, 'assets', 'USD', location, asset_type, asset_name,
                                       wedge_subfolder, asset_name + version + wedge + '.usd')
        # asset_construct = '{0}/assets/USD/{1}/{2}/{3}/{6}/{3}{4}{5}.usd'.format(project_folder, location, asset_type,
        #                                                                    asset_name,
        #                                                                    version, wedge, wedge_subfolder)
    else:
        asset_construct = os.path.join(project_folder, 'assets', 'USD', location, asset_type, asset_name,
                                       asset_name + version + '.usd')
        # asset_construct = '{0}/assets/USD/{1}/{2}/{3}/{3}{4}{5}.usd'.format(project_folder, location, asset_type,
        #                                                                asset_name,
        #                                                                version, wedge)

    # return location
    node.parm('construct').set(asset_construct)
    node.parm('construct').lock(True)
    asset_menu(kwargs)
    node.cook(True)


def create_asset(kwargs):
    node = kwargs['node']
    location = node.evalParm('loc')
    asset_type = node.evalParm('type')

    if location == 'None' or asset_type == 'None':
        message = 'Context and Asset Type need to be selected'
        util.error(message)
        return

    jobs = hou.getenv('JOBS')
    client = hou.getenv("CLIENT")
    project = hou.getenv("PROJECT")

    project_folder = os.path.join(jobs, client, project)
    asset_folder = '{0}/assets/USD/{1}/{2}/'.format(project_folder, location, asset_type)

    if not os.access(asset_folder, os.F_OK):
        os.makedirs(asset_folder)

    input = hou.ui.readInput(message='Enter Asset Name', buttons=('Create', 'Cancel'), title='New Asset')
    if input[0] == 1:
        return

    new_asset = input[1]
    if new_asset == '':
        message = 'You need to enter the Asset Name.'
        hou.ui.displayMessage(message, severity=hou.severityType.Error)
        return

    asset_folder = '{0}/{1}/'.format(asset_folder, new_asset)

    if os.access(asset_folder, os.F_OK):
        message = 'Asset "{0}" already exist'.format(new_asset)
        hou.ui.displayMessage(message, severity=hou.severityType.Error)
        return
    else:
        os.makedirs(asset_folder)
        message = 'asset "{0}" was successfully created'.format(new_asset)
        hou.ui.displayMessage(message)
        return


def remove_asset(kwargs):
    node = kwargs['node']
    location = node.evalParm('loc')
    asset_type = node.evalParm('type')

    jobs = hou.getenv('JOBS')
    client = hou.getenv("CLIENT")
    project = hou.getenv("PROJECT")

    project_folder = os.path.join(jobs, client, project)

    asset_folder = '{0}/assets/USD/{1}/{2}/'.format(project_folder, location, asset_type)

    assets = []

    if asset_folder and os.access(asset_folder, os.F_OK):
        for f in os.listdir(asset_folder):
            if os.path.isdir(util.fix_path(os.path.join(asset_folder, f))):
                assets.append(f)

    if len(assets) == 0:
        return
    else:
        selection = hou.ui.selectFromList(assets, message='Select Assets to Remove', title='Remove Assets',
                                          column_header='Assets', clear_on_cancel=True)
        for s in selection:
            selected_asset = assets[s]
            selected_folder = '{0}{1}'.format(asset_folder, selected_asset)
            if len(os.listdir(selected_folder)) > 0:
                message = 'Asset {0} contains files inside\n' \
                          'Do you want to proceed removing everything it contains?'.format(selected_asset)
                confirmation = hou.ui.displayConfirmation(message, severity=hou.severityType.Warning,
                                                          title='Removing Asset')
                if not confirmation:
                    return
                else:
                    try:
                        shutil.rmtree(selected_folder)
                    except OSError as e:
                        error_message = "Failed Removing {0} Asset\n" \
                                        "Error: {1} - {2}".format(selected_asset, e.filename, e.strerror)
                        hou.ui.displayMessage(error_message, severity=hou.severityType.Error)
            else:
                try:
                    shutil.rmtree(selected_folder)
                except OSError as e:
                    error_message = "Failed Removing {0} Asset\n" \
                                    "Error: {1} - {2}".format(selected_asset, e.filename, e.strerror)
                    hou.ui.displayMessage(error_message, severity=hou.severityType.Error)


def openPath(kwargs):
    node = kwargs['node']

    jobs = hou.getenv('JOBS')
    client = hou.getenv("CLIENT")
    project = hou.getenv("PROJECT")

    project_folder = os.path.join(jobs, client, project)
    location = node.evalParm('loc')
    asset_type = node.evalParm('type')
    asset_name = node.evalParm('name')

    dir = '{0}/assets/USD/{1}/{2}/{3}'.format(project_folder, location, asset_type, asset_name)

    if os.path.exists(dir):
        if dir[-1] != '/':
            dir += '/'
        hou.ui.showInFileBrowser(dir)
    else:
        hou.ui.displayMessage(text="Could not open directory:\n{dir}.".format(dir=dir),
                              severity=hou.severityType.ImportantMessage)


def auto_version(kwargs):
    node = kwargs['node']
    if node.evalParm('enableversion') and node.evalParm('autoversion'):

        jobs = hou.getenv('JOBS')
        client = hou.getenv("CLIENT")
        project = hou.getenv("PROJECT")

        project_folder = os.path.join(jobs, client, project)

        name = node.evalParm('name')
        location = node.evalParm('loc')
        asset_type = node.evalParm('type')
        version = node.evalParm('version')
        enable_wedge = node.evalParm('enablewedge')

        cache_dir = os.path.join(project_folder, 'assets', 'USD', location, asset_type, name)

        if not os.access(cache_dir, os.F_OK):
            node.parm('version').set(1)
            return

        files = os.listdir(cache_dir)

        version_list = []
        for f in files:
            regex = f'(?P<name>{name})(?:_V)?(?P<ver>\d+)(?P<rest>.+)?'
            match = re.match(regex, f)
            if match:
                version_list.append(match.group('ver'))

        if len(version_list) == 0:
            node.parm('version').set(1)
        else:
            # version_list = list(set(version_list))
            version_list.sort()
            wip_up = int(version_list[-1]) + 1
            node.parm('version').set(wip_up)


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


def latest_version(kwargs):
    try:
        set_default_primitive(kwargs)
    except:
        return

    auto_version(kwargs)
    asset_path(kwargs)
    return
