import os
import hou


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


def save_snap(kwargs):
    node = kwargs['node']

    path = node.evalParm('snap_path')
    name = node.evalParm('snap_name')

    source_path = node.evalParm('snap_source')
    source = hou.node(source_path)
    items = source.children()

    ext: str = '.cpio'

    file = path + name + ext

    source.saveItemsToFile(items, file)


def load_snap(kwargs):
    node = kwargs['node']

    destination_path = node.evalParm('destination')
    destination = hou.node(destination_path)

    file = node.evalParm('file')

    destination.loadItemsFromFile(file, ignore_load_warnings=False)
