# region Imports
import hou
import Ref_Man.util.util as util
import os
import sys
import shutil
import re
from importlib import reload
from absolute.session import Session
def component_paths(kwargs):
    node = kwargs['node']
    name = node.evalParm('name')

    #Rename Node
    base_name = f'{name}_component'
    node_name = util.node_name(node, base_name)
    node.setName(node_name)

    version = str(node.evalParm('component_version'))

    jobs = hou.getenv('JOBS')
    client = hou.getenv("CLIENT")
    project = hou.getenv("PROJECT")

    job_folder = os.path.join(jobs, client, project)
    #job_folder = util.job_folder()

    asset_folder = os.path.join(job_folder,'assets','USD','components',name)
    asset_path = os.path.join(asset_folder, 'v_' + version, name + '.usd')
    mtl_path = os.path.join(asset_folder, 'v_' + version, name + 'mtl', name + 'mtl' + '.usdc')
    geo_path = os.path.join(asset_folder, 'v_' + version, name + 'geo', name + 'geo' + '.usdc')
    payload_path = os.path.join(asset_folder, 'v_' + version, name + 'payload' + '.usda')


    node.parm('asset_path').set(asset_path)
    node.parm('geo_path').set(geo_path)
    node.parm('mtl_path').set(mtl_path)
    node.parm('payload_path').set(payload_path)
    node.parm('asset_folder').set(asset_folder)
    print(job_folder)