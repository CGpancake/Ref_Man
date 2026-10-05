import hou
import json
import os
import sys
from importlib import reload
from utility_scripts import main as util
from absolute.utils import jobconfig

os.path.join(os.getenv("JOBS"), os.getenv("CLIENT"), os.getenv("PROJECT"))

conf:jobconfig._JobConfig = jobconfig.JobConfig()

reload(util)

# Set Config File
job_list = '/home/domantas.lukosius/Desktop/HOUDINI/CONFIG/proj_list.json'


# Read json file
def read_json():
    try:
        with open(job_list, 'r') as f:
            data = json.load(f)
    except ValueError:
        data = {}

    return data


def create_folder_and_var(var, path):
    path = util.fix_path(path)
    hou.putenv(var, path)

    if not os.access(path, os.F_OK):
        os.makedirs(path)
        print('Creating variable {0} and folder [{1}]'.format(var, path))

    return


def unset_shot_vars():
    variables = [
        'ABS_SHOT',
        'ABS_SHOT_PATH',
        'ABS_OUTPUT_PATH',
        'ABS_CACHE_PATH',
        'ABS_RENDER_PATH',
        'ABS_PLAYBLAST_PATH',
    ]
    for v in variables:
        hou.unsetenv(v)
    return


def job_menu(kwargs):
    data = read_json()
    menu = ['-', '-']
    for k in data.keys():
        menu.append(k)
        menu.append(k)

    return menu


def shot_menu():
    # import pdb
    # pdb.set_trace()
    menu = []
    shots_path = os.path.expandvars(hou.getenv("ABS_SHOTS_PATH"))
    if shots_path and os.access(shots_path, os.F_OK):
        for f in os.listdir(shots_path):
            if os.path.isdir(util.fix_path(os.path.join(shots_path, f))):
                menu.append(f)
                menu.append(f)
    return menu


def set_job(kwargs):
    node = kwargs['node']
    job_name = node.evalParm('job')
    # job_name = kwargs['script_value']
    node.parm('shot').set('')
    unset_shot_vars()

    data = read_json()

    # Doesn't work
    if job_name == '-':
        hou.unsetenv('ABS_JOB_NAME')
        hou.unsetenv('ABS_CODE')
        hou.unsetenv('ABS_JOB_FPS')
        hou.unsetenv('ABS_JOB_START')
        hou.unsetenv('ABS_JOB_END')
        hou.unsetenv('ABS_JOB_PATH')
        hou.unsetenv('ABS_SHOTS_PATH')
        hou.unsetenv('ABS_HDA_PATH')
        hou.unsetenv('ABS_SCRIPTS_PATH')
        node.cook(True)
        return

    try:
        job_data = data[job_name]
    except KeyError:
        util.error('JOB Data not Found')
        return

    hou.putenv('ABS_JOB_NAME', job_name)
    hou.putenv('ABS_CODE', job_data['CODE'])

    fps = float(job_data['FPS'])
    hou.putenv('ABS_JOB_FPS', str(fps))
    # setFps function seems broken for some reason
    hou.setFps(fps, modify_frame_count=False, preserve_keyframes=True, preserve_frame_start=False)

    ### looking into hou.playbar.setPlaybackRange(start, end)

    start_frame = int(job_data['START_FRAME'])
    end_frame = int(job_data['END_FRAME'])
    hou.putenv('ABS_JOB_START', str(start_frame))
    hou.putenv('ABS_JOB_END', str(end_frame))

    hou.playbar.setFrameRange(start_frame, end_frame)

    job_path = job_data['PATH']
    create_folder_and_var('ABS_JOB_PATH', job_path)

    create_folder_and_var('ABS_SHOTS_PATH', os.path.join(job_path, 'shots'))

    hda_path = os.path.join(job_path, 'hda')
    create_folder_and_var('ABS_HDA_PATH', hda_path)

    scripts_path = os.path.join(job_path, 'scripts')
    create_folder_and_var('ABS_SCRIPTS_PATH', scripts_path)

    # Append project paths
    hda_paths = [hda_path, ]
    scan_path = hou.getenv('HOUDINI_OTLSCAN_PATH')
    if scan_path:
        hda_paths += scan_path.split(';')
    hda_paths = list(set(hda_paths))
    hou.putenv('HOUDINI_OTLSCAN_PATH', ';'.join(hda_paths))
    hou.hda.reloadAllFiles()

    sys.path.append(scripts_path)

    node.cook(True)


def set_shot(kwargs):
    node = kwargs['node']
    shot_name = node.evalParm('shot')

    # if null > unset all
    if shot_name == '':
        unset_shot_vars()
        node.cook(True)
        return

    # if no PROJECT_PATH; SHOTS_PATH; var

    job_path = hou.getenv('ABS_JOB_PATH')
    if not job_path or not os.access(job_path, os.F_OK):
        util.error('JOB path is invalid')
        return

    shots_path = hou.getenv('ABS_SHOTS_PATH')
    if not job_path:
        util.error('SHOTS path variable not found')
        return

    # If SHOTS_PATH var exists but no folder

    if not os.access(shots_path, os.F_OK):
        os.makedirs(scenes_path)

    shot_path = util.fix_path(os.path.join(shots_path, shot_name))
    if not os.access(shot_path, os.F_OK):
        message = 'Shot folder "{0}" does not exist\n' \
                  'Do you want to create it now?'.format(shot_name)
        choice = hou.ui.displayMessage(message, severity=hou.severityType.ImportantMessage, buttons=('Yes', 'No'))
        if choice == 0:
            os.makedirs(shot_path)
        else:
            return

    hou.putenv('ABS_SHOT', str(shot_name))
    hou.putenv('ABS_SHOT_PATH', str(shot_path))

    create_folder_and_var('SAVE_PATH', os.path.join(shot_path, 'wip'))

    output_path = os.path.join(shot_path, 'output')
    create_folder_and_var('ABS_OUTPUT_PATH', output_path)
    create_folder_and_var('ABS_CACHE_PATH', os.path.join(output_path, 'cache'))
    create_folder_and_var('ABS_RENDER_PATH', os.path.join(output_path, 'render'))
    create_folder_and_var('ABS_PLAYBLAST_PATH', os.path.join(output_path, 'playblast'))

    node.cook(True)


def onLoaded(kwargs):
    node = kwargs['node']
    curr_shot = node.evalParm('shot')

    node.parm('job').pressButton()
    if not curr_shot == '':
        node.parm('shot').set(curr_shot)
        if curr_shot in shot_menu({}):
            node.parm('shot').pressButton()


def onCreated(kwargs):
    node = kwargs['node']

    node.setName('SHOT_DATA')

    node.setUserData('nodeshape', 'trapezoid_down')
    node.setColor(hou.Color(0,0.5,0.3))
    node.setGenericFlag(hou.nodeFlag.Display, False)
    node.setGenericFlag(hou.nodeFlag.Selectable, False)

    job_name = str(hou.getenv('ABS_JOB_NAME'))
    shot_name = str(hou.getenv('ABS_SHOT'))
    if not job_name == 'None':
        node.parm('job').set(hou.getenv('ABS_JOB_NAME'))
    if not shot_name == 'None':
        node.parm('shot').set(hou.getenv('ABS_SHOT'))

