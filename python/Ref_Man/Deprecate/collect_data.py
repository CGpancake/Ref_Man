import hou
import os
from absolute.utils import projects
from absolute.utils import jobconfig
from absolute.session import Session

conf: jobconfig._JobConfig = jobconfig.JobConfig()


def shot_menu(kwargs):
    node = kwargs['node']

    client = hou.getenv("CLIENT")
    project = hou.getenv("PROJECT")

    data = Session(client, project).wip.get_shots()

    menu = ['Project', 'Project']

    for s in data:
        menu.append(s)
        menu.append(s)

    node.cook(True)
    return menu


def shot_menu_deprecated(kwargs):
    node = kwargs['node']
    client = hou.getenv("CLIENT")
    project = hou.getenv("PROJECT")
    data = Session(client, project).wip.get_shots()

    menu = ['-', '-']

    if client == '-':
        main.unset_shot_vars()
        node.cook(True)
        return menu
    if project == '-':
        main.unset_shot_vars()
        node.cook(True)
        return menu

    for s in data:
        menu.append(s)
        menu.append(s)

    node.cook(True)
    return menu


def set_render(kwargs):
    node_name = str('placeholder')
    scene_file = HoudiniFacade.get_current_file()
    scene_name, scene_ext = os.path.splitext(os.path.basename(scene_file))
    render_name = "%s_%s.$F4.exr" % (scene_name, node_name)
    hou.putenv('RENDER_NAME', render_name)
    hou.putenv('RENDER_PATH', os.path.join(HoudiniFacade.get_render_path("arnold")))
    hou.putenv('RENDER', os.path.join(HoudiniFacade.get_render_path("arnold"), render_name))


def asset_path(kwargs):
    job = hou.getenv('JOB')
    _asset_path: str = str(job + '/USD')
    hou.putenv(asset_path)
