import os
import hou
import absolute.houdini_job_tools.util.util as util
from absolute.session import Session
import re
from pprint import pprint
from pathlib import Path


def unset_hdri_path(kwargs):
    node = kwargs['node']
    node.parm('lookdev_light').set('None')
    if node.parm('hdri').isLocked():
        node.parm('hdri').lock(False)
    node.parm('hdri').set('')
    node.parm('hdri').lock(True)
    child_path = f'{node.path()}/Lookdev_Dome'
    child = hou.node(child_path)
    child.bypass(True)

def set_hdri_path(kwargs):
    node = kwargs['node']
    path = node.parm('lookdev_light').evalAsString()

    child_path = f'{node.path()}/Lookdev_Dome'
    child = hou.node(child_path)
    child.bypass(False)

    if path == 'None':
        child.bypass(True)
        return
    if node.parm('hdri').isLocked():
        node.parm('hdri').lock(False)

    node.parm('hdri').set(path)
    node.parm('hdri').lock(True)

def lookdev_light_menu(kwargs):
    node = kwargs['node']
    collection = node.parm('hdri_collection').evalAsString()

    root = '/sharon/JOBS/absolute/look_dev_5001721/assets/hdr/'
    path = os.path.join(root, collection)

    menu = ['None', 'None']

    if path and os.access(path, os.F_OK):
        for f in os.listdir(path):
            if not os.path.isdir(os.path.join(path, f)):
                if f.endswith('.exr'):
                    menu.append(os.path.join(path, f))
                    menu.append(f.rstrip('.exr'))
                    # menu.append(label[0])

    return menu

def lookdev_cam(kwargs):
    node = kwargs['node']
    child_path = f'{node.path()}/Lookdev_Cam'
    child = hou.node(child_path)
    if node.evalParm('lookdev_cam'):
        child.bypass(False)
    else:
        child.bypass(True)

def onCreated(kwargs):
    node = kwargs['node']

    #set initial state
    node.parm('hdri_collection').set('LOOKDEV')
    node.parm('hdri_collection').pressButton()
    node.parm('set_type').set('None')
    node.parm('set_type').pressButton()
    node.parm('set').set('None')
    node.parm('set').pressButton()

    light_rot = node.parm('light_rot')
    prim_rot = node.parm('prim_rot')
    degrees = (0, 360)
    frames = (1001, 1100)
    i=0

    for v in degrees:
        i+=1
        key = hou.Keyframe()
        key.setFrame(frames[i-1])
        key.setValue(degrees[i-1])
        light_rot.setKeyframe(key)
        prim_rot.setKeyframe(key)