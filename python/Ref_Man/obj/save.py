import hou
from utility_scripts import main as util

def save():
    #find data node
    shot_data = None
    shot_data_nodes = []
    for n in hou.node('/obj').children():
        if n.type().nameComponents()[2].startswith('shot_data'):
            shot_data_nodes.append(n)
    if len(shot_data_nodes) > 1:
        util.error('Shot Data node already exist\nAborting operation')
        return
    elif len(shot_data_nodes) == 1:
        shot_data = shot_data_nodes[0]
    else:
        util.error('Shot Data node does not exist\nPlease create one and select a scene before saving')
        return