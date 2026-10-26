# region Imports
import hou
import os
import re
from utility_scripts import main as util


# endregion

def prerender(node):
    auto_version(hou.node('..'))


def preframe(node):
    print("preframe")


def postframe(node):
    print("postframe")


def prewrite(node):
    print("prewrite")


def postwrite(node):
    print("postwrite")


def postrender(node):
    print("postrender")


def wedge_parm_val(wedge_num, parm_num):
    return '{0} > {1}'.format(wedge_num, parm_num)
    wedge = hou.parm('wedge_{0}'.format(wedge_num))
    parameter_name = hou.evalParm('parm_{0}_{1}'.format(wedge_num, parm_num))
    parameter_value = hou.evalParm('val_{0}_{1}'.format(wedge_num, parm_num))


def wedge_action(kwargs):
    node = kwargs['node']

    parent_num = kwargs['script_multiparm_index2']
    parent_parm = node.parm('wedge_{0}'.format(parent_num))
    parent_node = parent_parm.evalAsNode()

    if not parent_node:
        util.error('invalind node selected')
        return

    parm_list = []
    for p in parent_node.parms():
        template = p.parmTemplate()
        parm_type = template.type()
        if parm_type == hou.parmTemplateType.Folder or parm_type == hou.parmTemplateType.FolderSet:
            continue

        parm_list.append(p)

    tree_list = []
    for p in parm_list:
        hierarchy = list(p.containingFolders())
        hierarchy.append('{0} ({1})'.format(p.parmTemplate().label(), p.name()))
        tree_list.append('/'.join(hierarchy))

    choice = hou.ui.selectFromTree(tree_list, exclusinve=True , message='select a parameter to watch', title='Wedges',
                          clear_on_cancel=True)
    if len(choice) > 0:
        idx = tree_list.index(choice[0])
        parm = parm_list[idx]

        val_parm = kwargs['parmtuple'][0]
        name_parm = node.parm(val_parm.name()[:-4])
        name_parm.set(parm.name)



def auto_version(node, forced=False):
    if node.evalParm('enableversion') and node.evalParm('autoversion') or forced:
        # `chs("basedir") + "/" + chs("basename")``
        cache_dir = node.evalParm('basedir') + '/' + node.evalParm('basename')
        # cache_dir = node.evalParm('cachedir')

        if not os.access(cache_dir, os.F_OK):
            node.parm('version').set(1)
            return

        files = os.listdir(cache_dir)
        version_list = []
        for f in files:
            if os.path.isdir(os.path.join(cache_dir, f)):
                regex = 'v(?P<ver>\\d+)'.format(node.evalParm('basename'))
                match = re.match(regex, f)
                if match:
                    version_list.append(int(match.group('ver')))
        print(len(version_list))
        if len(version_list) == 0:
            node.parm('version').set(1)

        else:
            version_list = list(set(version_list))
            version_list.sort()

            latest_version = version_list[-1]
            if forced:
                node.parm('version').set(latest_version)
            else:
                node.parm('version').set(latest_version + 1)

    return


def latest_version(kwargs):
    node = kwargs['node']
    auto_version(node, forced=True)
    node.parm('reload').pressButton()
    return


# region Snapshot functions
def cache_snap(kwargs):
    node = kwargs['node']

    basedir = node.evalParm('basedir')
    basename = node.evalParm('basename')
    versioning = node.evalParm('enableversion')
    version = node.evalParm('versionstr')

    name = basename
    path = basedir + '/' + basename + '/'
    if versioning:
        name += '_' + version
        path += version + '/'

    ext: str = '.cpio'

    if not os.path.exists(path):
        os.makedirs(path)

    parent = node.parent()
    items = parent.children()

    file = path + name + ext

    # Write files.
    parent.saveItemsToFile(items, file)


def cache_snap_to_clip(kwargs):
    node = kwargs['node']

    destination_path = node.evalParm('destination')
    destination = hou.node(destination_path)
    destination_items = destination.children()

    destination.copyItemsToClipboard(destination_items)
    # hou.copyNodesToClipboard(_nodes)
    # hou.ui.copyTextToClipboard(_data)


def snap_to_dest(kwargs):
    node = kwargs['node']

    basedir = node.evalParm('basedir')
    basename = node.evalParm('basename')
    versioning = node.evalParm('enableversion')
    version = node.evalParm('versionstr')
    destination_path = node.evalParm('destination')
    destination = hou.node(destination_path)

    name = basename
    path = basedir + '/' + basename + '/'
    if versioning:
        name += '_' + version
        path += version + '/'

    ext: str = '.cpio'

    file = path + name + ext

    destination.loadItemsFromFile(file, ignore_load_warnings=False)
# endregion
