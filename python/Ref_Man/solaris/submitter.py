import hou, os, sys

import os


def auto_version(kwargs):
    node = kwargs['node']
    inputs = node.inputConnections()
    index = kwargs['parm'].name().split('/')[-1]
    new_version = 1  # Default version

    highest = []

    for index, input in enumerate(inputs):
        if node.evalParm(f'auto_version{index}'):
            # Determine directories
            name = node.evalParm(f'asset_name_{index}')
            usd = node.evalParm(f'usd_path_{index}')
            exr = node.evalParm(f'exr_path_{index}')
            dirs = [usd, exr]

            # Initial version list
            version_list = []

            # Check if EXR path does not exist and USD does
            if not os.access(exr, os.F_OK) and os.access(usd, os.F_OK):
                print("Submission does not exist.")
                node.parm('version').set(1)
                return

            for d in dirs:
                if os.path.exists(d):
                    # List subdirectories in the current directory `d`
                    items = os.listdir(d)
                    subfolders = [s for s in items if os.path.isdir(os.path.join(d, s))]

                    # Filter and find version numbers
                    for folder in subfolders:
                        if folder.startswith('v') and folder[1:].isdigit():
                            # Convert the folder name from 'vXXX' to int XXX
                            version_number = int(folder[1:])  # Extract the numeric part and convert to int
                            version_list.append(version_number)

            # Check if there are any found versions
            if version_list:
                highest_version = max(version_list)
                highest.append(highest_version)

    if not highest:
        node.parm('version').set(1)
    else:
        # Increment the highest version number found
        new_version = max(highest) + 1
        node.parm(f'ver_{index}').set(new_version)
        print(f"New version set to: v{new_version:03}")
