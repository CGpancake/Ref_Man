import hou
from absolute.utils import jobconfig
from absolute.houdini.facade import HoudiniFacade
from importlib import reload
import absolute.houdini_job_tools.util.util as util
import os

# from collect_data import shot_menu


conf = jobconfig.JobConfig()


def unset_shot_vars():
    variables = [
        'SHOT', 'PROJ_FPS', 'ASPECT', 'RESX', 'RESY', 'OSCAN', 'HANDLES', 'START', 'END', 'RENDER', 'RENDER_NAME',
        'RENDER_PATH'
    ]
    for v in variables:
        hou.unsetenv(v)
    return


def reload_param(kwargs):
    set_context(kwargs)
    #set_fps(kwargs)
    #set_frame_range(kwargs)
    #set_render(kwargs)
    #set_asset_path(kwargs)

    return


def update(kwargs):
    node = kwargs['node']
    cook = node.evalParm('cook')
    if cook:
        reload_param(kwargs)


def lock_settings(kwargs):
    node = kwargs['node']
    locker = node.evalParm("lock")

    lock = ["frame_rangex", "frame_rangey", "resx", "resy",
            "fps", "pixel_aspect", "overscan"]

    if locker == 1:
        for a in lock:
            node.parm(a).lock(True)
    else:
        for a in lock:
            node.parm(a).lock(False)


def manifest_stage(kwargs):
    node = kwargs['node']
    stage = node.editableStage()

    types = ['components', 'lights', 'cameras']
    context = str(node.evalParm('context'))
    stage.DefinePrim(f'/shot_{context}', 'Scope')

    # for t in types:
    #     prim_path = f'/{t}'
    #     prim_type = 'Xform'
    #     stage.DefinePrim(prim_path, prim_type)


def set_context(kwargs):
    node = kwargs['node']
    context = node.evalParm('context')

    # Set Layer properties
    jobs = hou.getenv('JOBS')
    client = hou.getenv("CLIENT")
    project = hou.getenv("PROJECT")

    if context == 'Project':
        _context = context
    else:
        _context = 'Shot_' + context
    layer_path = os.path.join(jobs, client, project, 'assets', 'USD', _context, 'assembly', _context + '.usd')
    configure = hou.node(node.path() + '/configurelayer')
    configure.parm('savepath').set(layer_path)
    configure.parm('defaultprim').set('/' + _context)

    if context == 'Project':
        if node.evalParm('lock') == 1:
            node.parm('lock').set(0)
            node.parm('lock').pressButton()

        node.parm('frame_rangex').revertToDefaults()
        node.parm('frame_rangey').revertToDefaults()
        node.parm('resy').revertToDefaults()
        node.parm('resx').revertToDefaults()

        base_name = 'JOB_DATA'
        name = util.node_name(node, base_name)



    else:
        conf.reload()
        frame_data = conf.get_shot_info(context)

        if node.evalParm('lock') == 1:
            node.parm('lock').set(0)
            node.parm('lock').pressButton()

        node.parm('frame_rangex').set(int(frame_data[0]))
        node.parm('frame_rangey').set(int(frame_data[0] + frame_data[1]))
        node.parm('resy').set(conf.get_shot_res_height(context))
        node.parm('resx').set(conf.get_shot_res_width(context))
        # Rename
        base_name = f'SHOT_DATA_{context}'
        reload(util)
        name = util.node_name(node, base_name)

        #node.setName(name)

        # job_data_nodes = []
        #
        # for n in hou.node('/stage').children():
        #     if n.name().startswith('SHOT_DATA_' + context):
        #         job_data_nodes.append(n)
        #
        # if len(job_data_nodes)==0:
        #     full_name = 'SHOT_DATA_' + context
        # else:
        #     full_name = 'SHOT_DATA_' + context + '_' + str(len(job_data_nodes)+1)

        node.setName(name)

        node.parm('lock').set(1)
        node.parm('lock').pressButton()

        #manifest_stage(kwargs)

        node.cook(True)
        return


def set_fps(kwargs):
    node = kwargs['node']
    fps = node.evalParm('fps')
    hou.setFps(fps, modify_frame_count=False, preserve_keyframes=True, preserve_frame_start=True)
    hou.putenv('FPS', str(fps))
    node.cook(True)
    return


def set_frame_range(kwargs):
    node = kwargs['node']
    frame_range = node.evalParmTuple('frame_range')
    handles = node.evalParmTuple('handles')
    preroll = node.evalParm('preroll')
    enable_handles = node.evalParm('enable_handles')
    enable_preroll = node.evalParm('enable_preroll')

    cook = node.evalParm('cook')
    if enable_handles == 1:
        frame_start = frame_range[0] - handles[0]
        frame_end = frame_range[1] + handles[1]
    else:
        frame_start = frame_range[0]
        frame_end = frame_range[1]

    if enable_preroll == 1:
        hou.playbar.setFrameRange(frame_start - preroll, frame_end)
    else:
        hou.playbar.setFrameRange(frame_start, frame_end)

    hou.putenv('START', str(frame_start))
    hou.putenv('END', str(frame_end))
    node.cook(True)
    return


def set_render(kwargs):
    node_name = str('placeholder')
    scene_file = HoudiniFacade.get_current_file()
    scene_name, scene_ext = os.path.splitext(os.path.basename(scene_file))
    render_name = "%s_%s.$F4.exr" % (scene_name, node_name)
    hou.putenv('RENDER_NAME', render_name)
    hou.putenv('RENDER_PATH', os.path.join(HoudiniFacade.get_render_path("arnold")))
    hou.putenv('RENDER', os.path.join(HoudiniFacade.get_render_path("arnold"), render_name))


def set_asset_path(kwargs):
    job = hou.getenv('JOB')
    _asset_path: str = str(job + '/USD')
    hou.putenv("ASSET_PATH", _asset_path)

def aov_name_presets(kwargs):
    node = kwargs['node']
    setting = node.evalParm('aov_name_presets')
    if setting == 'arnold':
        node.parm('aovs').set(3)
        #Set explicit names
        node.parm('currentName1').set('MotionVectors')
        node.parm('newName1').set('motionvector')
        node.parm('currentName2').set('Depth')
        node.parm('newName2').set('Pz')
        node.parm('currentName3').set('CombinedVolume')
        node.parm('newName3').set('volume')
    elif setting == 'karma':
        node.parm('aovs').set(0)
    else:
        return
def aov_name_custom(kwargs):
    node = kwargs['node']
    node.parm('aov_name_presets').set('custom')

def onLoaded(kwargs):
    node = kwargs['node']

    node.parm('context').pressButton()

    lock_settings(kwargs)


def onCreated(kwargs):
    node = kwargs['node']

    node.setUserData('nodeshape', 'trapezoid_down')
    node.setColor(hou.Color(0, 0.5, 0.3))
    node.setGenericFlag(hou.nodeFlag.Display, False)
    node.setGenericFlag(hou.nodeFlag.Selectable, False)
    node.parm('context').set('Project')
    node.parm('context').pressButton()

    #Enable arnold AOV presets
    node.parm('aov_name_presets').set('arnold')
    node.parm('aov_name_presets').pressButton()


def test():
    print('module is working')
