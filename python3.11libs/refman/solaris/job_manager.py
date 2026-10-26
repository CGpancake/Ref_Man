import hou, os
#from absolute.session import Session

def shot_num(kwargs):
    node = kwargs['node']
    mode = node.evalParm('shot_selection')

    shot_list = ''

    if mode == 'Pattern':
        pattern = node.evalParm('shot_pattern')
        shot_list = hou.node('/stage').glob(pattern)

    elif mode == 'Input':
        shot_list = node.inputs()

    num = int(len(shot_list))
    return num
    #shotnum = node.parm('shotnum')
    #if shotnum.isLocked():
    #    shotnum.lock(False)
    #node.parm('shotnum').set(num)



def shot_name(node, index):
    mode = node.evalParm('shot_selection')

    shot_list = ''

    if mode == 'Pattern':
        pattern = node.evalParm('shot_pattern')
        shot_list = hou.node('/stage').glob(pattern)

    elif mode == 'Input':
        shot_list = node.inputs()

    return shot_list[index]

def create_ropfetch(kwargs):
    node = kwargs['node']
    multiparm = kwargs['script_value']
    path = node.path()

    top_network = hou.node(os.path.join(path, 'top'))
    rop_pattern = 'ropfetch*'
    available_rops = top_network.glob(rop_pattern)
    #Clear
    for rop in available_rops:
        rop.destroy()

    if int(multiparm) == 0:
        hou.node(os.path.join(path,'top/Update_and_Send')).setInput(0, hou.node(os.path.join(path, 'top/Wedges')))
    else:
        requested_rops = range(0,int(multiparm))

        for rop in requested_rops:
            ropfetch = top_network.createNode('ropfetch')
            print(rop)
            if rop == 0:
                ropfetch.setInput(0,hou.node(os.path.join(path,'top','Wedges')),0)
            else:
                ropfetch.setInput(0,hou.node(os.path.join(path,'top',f'ropfetch{rop}')),0)


        final_rop = hou.node(os.path.join(path, f'top/ropfetch{int(multiparm)}'))
        hou.node(os.path.join(path,'top/Update_and_Send')).setInput(0,final_rop,0)

        top_network.layoutChildren()
        return

def set_rops(kwargs):
    node = kwargs['node']
    pattern = 'rop*'
    parms = node.globParms(pattern)

    for parm in parms:
        path = parm.eval()
        ropfetch = hou.node(f'{node.path()}/top/{parm.name()}')
        ropfetch.parm('roppath').set(path)

def evaluate_using(kwargs):
    node = kwargs['node']
    pattern = 'framegeneration_*'
    parms = node.globParms(pattern)

    for parm in parms:
        selection = parm.eval()
        elements = parm.name().split('_')
        target = elements[0]
        index = elements[1]

        ropfetch = hou.node(f'{node.path()}/top/ropfetch{index}')
        ropfetch.parm(target).set(selection)

def set_range(kwargs):
    node = kwargs['node']
    pattern = 'range_*'
    parms = node.globParms(pattern)

    for parm in parms:
        elements = parm.name().split('_')
        target = elements[0]
        index = elements[1]
        path = f'{node.path()}/{target}_{index}_'

        selection = hou.evalParmTuple(path)

        Tuple = hou.parmTuple(f'{node.path()}/top/ropfetch{index}/{target}')
        Tuple.deleteAllKeyframes()
        hou.parmTuple(f'{node.path()}/top/ropfetch{index}/{target}').set(selection)

def single_item(kwargs):
    node = kwargs['node']
    pattern = 'singletask_*'
    parms = node.globParms(pattern)

    for parm in parms:
        selection = parm.eval()
        elements = parm.name().split('_')
        target = elements[0]
        index = elements[1]

        ropfetch = hou.node(f'{node.path()}/top/ropfetch{index}')
        ropfetch.parm(target).set(selection)

def batch_all(kwargs):
    node = kwargs['node']
    pattern = 'batchall_*'
    parms = node.globParms(pattern)

    for parm in parms:
        selection = parm.eval()
        elements = parm.name().split('_')
        target = elements[0]
        index = elements[1]

        ropfetch = hou.node(f'{node.path()}/top/ropfetch{index}')
        ropfetch.parm(target).set(selection)

def frames_per_batch(kwargs):
    node = kwargs['node']
    pattern = 'framesperbatch_*'
    parms = node.globParms(pattern)

    for parm in parms:
        selection = parm.eval()
        elements = parm.name().split('_')
        target = elements[0]
        index = elements[1]

        ropfetch = hou.node(f'{node.path()}/top/ropfetch{index}')
        ropfetch.parm(target).set(selection)

def cook_when(kwargs):
    node = kwargs['node']
    pattern = 'cookwhen_*'
    parms = node.globParms(pattern)

    for parm in parms:
        selection = parm.eval()
        elements = parm.name().split('_')
        target = elements[0]
        index = elements[1]

        ropfetch = hou.node(f'{node.path()}/top/ropfetch{index}')
        ropfetch.parm(target).set(selection)

def update_assets(item):
    nodes = hou.node('/stage').glob('*ASSET*')
    #node_paths = list(str(hda.evalParm('asset_node_paths')).split(' '))

    pattern = '*wedgeparm*'

    for asset_node in nodes:
        parm_list = asset_node.globParms(pattern)
        for parm in parm_list:
            parm.set(str(item))
            parm.pressButton()

def generate_inputs(kwargs):
    node = kwargs['node']
    client = hou.getenv("CLIENT")
    project = hou.getenv("PROJECT")
    shots = Session(client, project).wip.get_shots()
    nulls = []
    network = node.parent()
    for shot in enumerate(shots):
        node_name = 'shot_' + str(shot[1])
        node_index = int(shot[0])
        print(node_name)
        print(node_index)
        null = network.createNode('null', node_name=node_name)
        nulls.append(null)
        node.setInput(node_index, null, 0)
        null.moveToGoodPosition()

    #for n in nulls:
        #n.moveToGoodPosition()



