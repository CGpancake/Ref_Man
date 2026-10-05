import hou
import os
import json
from utility_scripts import main as util
from importlib import reload

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


def manage_job():
    sel = hou.ui.displayMessage('Select an action', buttons=('Add', 'Remove', 'Details', 'Cancel'))
    print(sel)

    if sel == 0:
        add_job()
    elif sel == 1:
        remove_job()
    elif sel == 2:
        job_details()
    else:
        return


# Add JOB function
def add_job():
    data = read_json()

    # Initialising Variables
    _job_name = None
    path = None
    job_name = None
    job_code = None
    fps = None
    start_frame = None
    end_frame = None

    # Select JOB Path
    repeat = True
    while repeat:
        repeat = False
        _path = hou.ui.selectFile(title='Select JOB Directory', file_type=hou.fileType.Directory)
        path = os.path.dirname(_path)

        if path == '':
            return

        # Check if JOB already exist
        for k, v in data.items():
            if util.fix_path(path) == util.fix_path(v['PATH']):
                util.error('JOB path is already used by JOB {0}\nPlease, select a different path'.format(k))

                repeat = True
                break
        # If JOB exists, stop here
        if repeat:
            continue

    _job_name = os.path.split(path)[-1]

    # Select JOB Path, Code, FPS
    repeat = True

    while repeat:

        repeat = False

        inputs = hou.ui.readMultiInput(message='Enter JOB Data',
                                       input_labels=('JOB Name', 'JOB Code', 'FPS', 'Start Frame', 'End Frame'),
                                       buttons=('OK', 'Cancel'), initial_contents=(_job_name, '', '24'))

        # Return if clicked cancel
        if inputs[0] == 1:
            return

        # Set data
        job_name = inputs[1][0]
        job_code = inputs[1][1]
        fps = inputs[1][2]
        start_frame = inputs[1][3]
        end_frame = inputs[1][4]

        # Loop if data is missing
        if job_name == '' or job_code == '' or fps == '' or start_frame  == '' or end_frame  == '':
            util.error('Fill in all fields')

            repeat = True
            continue

        # Check if FPS is a float
        try:
            float(fps)
        except ValueError:
            util.error('FPS is not set as number')
            repeat = True
            continue

        # Check if START is int
        try:
            int(start_frame)
        except ValueError:
            util.error('Start Frame is not set as integer number')
            repeat = True
            continue

        # Check if END is int
        try:
            int(end_frame)
        except ValueError:
            util.error('Start END is not set as integer number')
            repeat = True
            continue

        # Check if JOB name exist
        for k, v in data.items():
            if job_name == k:
                util.error('JOB Name already exist')
                repeat = True
                break
            if job_code == v['CODE']:
                util.error('JOB Code already exist')
                repeat = True
                break
        if repeat:
            continue

    # Check if data was updated
    if job_name and job_code and fps:
        job_data = {
            'CODE': job_code,
            'PATH': path,
            'FPS': fps,
            'START_FRAME': start_frame,
            'END_FRAME': end_frame
        }
        data[job_name] = job_data

    # If data was updated, write it
    if data:
        with open(job_list, 'w') as f:
            json.dump(data, f, sort_keys=True, indent=4)


# Remove JOB function
def remove_job():
    data = read_json()
    # jobs = data.keys()
    jobs = list(data.keys())

    # print(jobs)
    sel = hou.ui.selectFromList(jobs, message='Select JOBs to remove', title='Remove JOBs', column_header='JOBs',
                                clear_on_cancel=True)
    if len(sel) == 0:
        return

    for i in sel:
        key = jobs[i]
        del data[key]

    with open(job_list, 'w') as f:
        json.dump(data, f, sort_keys=True, indent=4)


def job_details():
    data = read_json()
    jobs = list(data.keys())
    sel = hou.ui.selectFromList(jobs, exclusive=True, message='Select JOB to view details', title='JOB Details',
                                column_header='JOBs', clear_on_cancel=True)
    if len(sel) == 0:
        return

    job = jobs[sel[0]]
    job_data = data[job]

    util.print_report(' Project Details ',
                      'Name: {0}'.format(job),
                      'Code: {0}'.format(job_data['CODE']),
                      'Path: {0}'.format(job_data['PATH']),
                      'FPS: {0}'.format(job_data['FPS']),
                      'START_FRAME: {0}'.format(job_data['START_FRAME']),
                      'END_FRAME: {0}'.format(job_data['END_FRAME']),

                      )

def edit_job():
    data = read_json()
    jobs = list(data.keys())
    sel = hou.ui.selectFromList(jobs, exclusive=True, message='Select JOB to Edit', title='Edit JOB',
                                column_header='JOBs', clear_on_cancel=True)
    if len(sel) == 0:
        return

    job = jobs[sel[0]]
    job_data = data[job]

    # Initialising Variables

    path = None
    _job_path = job_data['PATH']
    job_name = None
    _job_name = job_data
    job_code = None
    _job_code = job_data['CODE']
    fps = None
    _fps = job_data['FPS']
    start_frame = None
    _start_frame = job_data['START_FRAME']
    end_frame = None
    _end_frame = job_data['END_FRAME']

    # Select JOB Path
    repeat = True
    while repeat:
        repeat = False
        _path = hou.ui.selectFile(start_directory=_job_path, title='Select JOB Directory',
                                  file_type=hou.fileType.Directory)
        path = os.path.dirname(_path)

        if path == '':
            return

        # Check if JOB already exist
        for k, v in data.items():
            if util.fix_path(path) == util.fix_path(v['PATH']):
                util.error('JOB path is already used by JOB {0}\nPlease, select a different path'.format(k))

                repeat = True
                break
        # If JOB exists, stop here
        if repeat:
            continue

    _job_name = os.path.split(path)[-1]

    # Select JOB Path, Code, FPS
    repeat = True

    while repeat:

        repeat = False

        inputs = hou.ui.readMultiInput(message='Enter JOB Data',
                                       input_labels=('JOB Name', 'JOB Code', 'FPS', 'Start Frame', 'End Frame'),
                                       buttons=('OK', 'Cancel'), initial_contents=(_job_name, _job_code, _fps,
                                                                                   _start_frame, _end_frame))

        # Return if clicked cancel
        if inputs[0] == 1:
            return



        # Set data
        job_name = inputs[1][0]
        job_code = inputs[1][1]
        fps = inputs[1][2]
        start_frame = inputs[1][3]
        end_frame = inputs[1][4]

        # Loop if data is missing
        if job_name == '' or job_code == '' or fps == '' or start_frame == '' or end_frame == '':
            util.error('Fill in all fields')

            repeat = True
            continue

        # Check if FPS is a float
        try:
            float(fps)
        except ValueError:
            util.error('FPS is not set as number')
            repeat = True
            continue

        # Check if START is int
        try:
            int(start_frame)
        except ValueError:
            util.error('Start Frame is not set as integer number')
            repeat = True
            continue

        # Check if END is int
        try:
            int(end_frame)
        except ValueError:
            util.error('Start END is not set as integer number')
            repeat = True
            continue

        # # Check if JOB name exist
        # for k, v in data.items():
        #     if job_name == k:
        #         util.error('JOB Name already exist')
        #         repeat = True
        #         break
        #     if job_code == v['CODE']:
        #         util.error('JOB Code already exist')
        #         repeat = True
        #         break

        if repeat:
            continue

    for i in sel:
        key = jobs[i]
        del data[key]

    with open(job_list, 'w') as f:
        json.dump(data, f, sort_keys=True, indent=4)

    # Check if data was updated
    if job_name and job_code and fps:
        job_data = {
            'CODE': job_code,
            'PATH': path,
            'FPS': fps,
            'START_FRAME': start_frame,
            'END_FRAME': end_frame
        }
        data[job_name] = job_data

    # If data was updated, write it
    if data:
        with open(job_list, 'w') as f:
            json.dump(data, f, sort_keys=True, indent=4)