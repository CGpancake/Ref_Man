import hou, re, os
import husd.assetutils as assetutils
from typing import Union, List

# Fix paths function
def fix_path(old_path, new_sep='/'):
    _path = old_path.replace('\\', '/')
    _path = _path.replace('\\\\', '/')
    _path = _path.replace('//', '/')

    if _path.endswith('/'):
        _path = _path[:-1]

    _path = _path.replace('/', new_sep)

    new_path = _path

    return new_path


# Error message function
def error(message, severity=hou.severityType.Error):
    print('{severity}: {message}'.format(severity=severity.name(), message=message))
    hou.ui.displayMessage(message, severity=severity)


# Present information
def print_report(header, *body):
    print('\n{header:-^50}'.format(header=header))

    for b in body:
        print('\t{0}'.format(b))

    print('-' * 50)


def node_name(node, base_name):
    name = base_name
    current_name = node.name()

    # Find all node names in the same container
    name_list = [n.name() for n in node.parent().children() if n.name().startswith(str(base_name))
                 and n.name() != current_name]

    # If base does not exist, return it
    if base_name not in name_list:
        return name

    # If base name exists, recursively find the lowest existing suffix number starting from 2
    # and add it if it's not there
    suffix = 2
    while suffix < 100:
        new_name = f'{base_name}_{suffix}'
        if new_name not in name_list:
            return new_name
        suffix += 1

    print('Tried too many times')
    return name

def job_folder():
    jobs = hou.getenv('JOBS')
    client = hou.getenv("CLIENT")
    project = hou.getenv("PROJECT")

    project_folder = os.path.join(jobs, client, project)
    return project_folder


def asset_location():
    return

def update_lightFilters(folder, key):
    filter_loc = '/sasha/3D_LIBRARY/Houdini/Greyscalegorilla/textures'
    os.environ['HOUDINI_ASSETGALLERY_DB_FILE'] = os.path.join(folder,key,'.db')
    for filter in os.listdir(filter_loc):
        elements = filter.split('_')
        name = elements[-1]


import os
import re
import hou


import os
import re
import hou

def load_lightFilters():
    filter_loc = '/sasha/3D_LIBRARY/Houdini/Greyscalegorilla/textures'
    container = hou.node('/stage').createNode('lightfilterlibrary')

    for filter_folder in os.listdir(filter_loc):
        filter_folder_path = os.path.join(filter_loc, filter_folder)
        if not os.path.isdir(filter_folder_path):
            continue

        # Extract the last part of the folder name for the node name
        elements = filter_folder.split('_')
        name = elements[-1]

        # Create a gobo node inside the container with the extracted name
        filter_node = container.createNode('kma_lfilter_gobo', node_name=name)

        # Regex patterns to match .exr and .jpg files with optional frame numbers
        exr_pattern = re.compile(rf'^{re.escape(filter_folder)}(_\d{{3}})?\.exr$')
        jpg_pattern = re.compile(rf'^{re.escape(filter_folder)}(_\d{{3}})?\.jpg$')

        # Check for matching .exr files first, then fall back to .jpg if no .exr found
        matching_files = [f for f in os.listdir(filter_folder_path) if exr_pattern.match(f)]
        file_extension = '.exr'

        if not matching_files:
            matching_files = [f for f in os.listdir(filter_folder_path) if jpg_pattern.match(f)]
            file_extension = '.jpg'

        if matching_files:
            # Check for sequences and get the frame numbers
            sequence_files = [f for f in matching_files if re.match(rf'^{re.escape(filter_folder)}_\d{{3}}{file_extension}$', f)]
            if sequence_files:
                # Extract the frame numbers and find the max frame number
                frame_numbers = [int(re.search(r'_(\d{3})\.', f).group(1)) for f in sequence_files]
                max_frame = max(frame_numbers)

                # Create the file path using $F and padzero with the correct frame range
                map_path = f'{filter_loc}/{filter_folder}/{filter_folder}_`padzero(3,$F%{max_frame + 1})`{file_extension}'
            else:
                # Use the non-sequence file
                map_path = f'{filter_loc}/{filter_folder}/{filter_folder}{file_extension}'

            # Set the 'map' parameter to the constructed path
            filter_node.parm('map').set(map_path)
            print(f'Created gobo filter: {name} with map: {map_path}')


import husd.assetutils as assetutils
import hou


import os
import re
import husd.assetutils as assetutils
import hou

def load_lightFilters():
    filter_loc = '/sasha/3D_LIBRARY/Houdini/Greyscalegorilla/textures'
    container = hou.node('/stage').createNode('lightfilterlibrary')

    for filter_folder in os.listdir(filter_loc):
        filter_folder_path = os.path.join(filter_loc, filter_folder)
        if not os.path.isdir(filter_folder_path):
            continue

        # Extract the last part of the folder name for the node name
        elements = filter_folder.split('_')
        name = elements[-1]

        # Create a gobo node inside the container with the extracted name
        filter_node = container.createNode('kma_lfilter_gobo', node_name=name)

        # Regex patterns to match .exr and .jpg files with optional frame numbers
        exr_pattern = re.compile(rf'^{re.escape(filter_folder)}(_\d{{3}})?\.exr$')
        jpg_pattern = re.compile(rf'^{re.escape(filter_folder)}(_\d{{3}})?\.jpg$')

        # Check for matching .exr files first, then fall back to .jpg if no .exr found
        matching_files = [f for f in os.listdir(filter_folder_path) if exr_pattern.match(f)]
        file_extension = '.exr'

        if not matching_files:
            matching_files = [f for f in os.listdir(filter_folder_path) if jpg_pattern.match(f)]
            file_extension = '.jpg'

        if matching_files:
            # Check for sequences and get the frame numbers
            sequence_files = [f for f in matching_files if re.match(rf'^{re.escape(filter_folder)}_\d{{3}}{file_extension}$', f)]
            if sequence_files:
                # Extract the frame numbers and find the max frame number
                frame_numbers = [int(re.search(r'_(\d{3})\.', f).group(1)) for f in sequence_files]
                max_frame = max(frame_numbers)

                # Create the file path using $F and padzero with the correct frame range
                map_path = f'{filter_loc}/{filter_folder}/{filter_folder}_`padzero(3,$F%{max_frame + 1})`{file_extension}'
            else:
                # Use the non-sequence file
                map_path = f'{filter_loc}/{filter_folder}/{filter_folder}{file_extension}'

            # Set the 'map' parameter to the constructed path
            filter_node.parm('map').set(map_path)
            print(f'Created gobo filter: {name} with map: {map_path}')

    # After processing all filters, add them to the asset gallery
    gallery_path = '/sasha/3D_LIBRARY/Houdini/Lights/Area_Lights'
    for usd_file in os.listdir(gallery_path):
        usd_file_path = os.path.join(gallery_path, usd_file)
        if os.path.isfile(usd_file_path) and usd_file.endswith('.usdc'):
            # Use the filename (without extension) as the asset name
            asset_name = os.path.splitext(usd_file)[0]
            assetutils.AssetGallery.addAsset(
                asset_file_or_dir_path=usd_file_path,
                asset_name=asset_name
            )
            print(f'Added asset: {asset_name} from {usd_file_path}')


def add_to_gallery(usd_folder, gallery):
    search_dir = '/sasha/3D_LIBRARY/Houdini/Greyscalegorilla/textures'

    for usd in os.listdir(usd_folder):
        if not usd.endswith('.usdc'):
            continue

        # Extract the base name without the extension
        base_name = os.path.splitext(usd)[0]
        suffix = f'{base_name}_Preview.jpg'

        match_found = False
        for root, _, files in os.walk(search_dir):
            for file in files:
                if file.endswith(suffix):
                    match_found = True
                    file_path = os.path.join(root, file)
                    usd_file_path = os.path.join(usd_folder, usd)

                    try:
                        gallery.addAsset(
                            asset_file_or_dir_path=usd_file_path,
                            thumbnail_file_path=file_path,
                            asset_name=base_name
                        )
                        print(f'Added {base_name} to gallery with preview {file_path}')
                    except Exception as e:
                        print(f'Failed to add {base_name}: {e}')

        if not match_found:
            print(f'{base_name} preview not found.')


def get_thumbnail(base_dir):
    """Return the first file ending with '_preview.jpg' in the directory."""
    try:
        files = os.listdir(base_dir)
        print(f"Files in {base_dir}: {files}")
        for file_name in files:
            if file_name.endswith('_preview.jpg'):
                return os.path.join(base_dir, file_name)
    except FileNotFoundError:
        print(f"Directory not found: {base_dir}")
    return None


def loadAssets(destination_folder, db, thumb_path):
    """Load assets and their thumbnails into an asset gallery."""
    os.environ['HOUDINI_ASSETGALLERY_DB_FILE'] = db

    # List only .usdc files
    file_list = [f for f in os.listdir(destination_folder) if f.endswith('.usdc')]

    increment = float(100) / len(file_list)
    completion = 0.0
    failed_list = []

    asset_gallery = assetutils.AssetGallery()

    for usd_file in file_list:
        print(f'Completion: {completion:.2f}%')
        print(f'Evaluating: {usd_file}')

        file_path = os.path.join(destination_folder, usd_file)
        base_name = os.path.splitext(usd_file)[0]

        # Construct the directory where thumbnails are located
        thumbnail_dir = os.path.join(thumb_path, base_name)

        # Get a thumbnail from the directory
        thumbnail = get_thumbnail(thumbnail_dir)

        # Format asset name with spaces between capital letters
        asset_name = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', base_name.split('_')[-1])

        if thumbnail:
            try:
                print(f'Adding asset with thumbnail: {file_path}, {thumbnail}')
                asset_gallery.addAsset(file_path, thumbnail_file_path=thumbnail, asset_name=asset_name)
            except Exception as e:
                print(f"Error adding asset {usd_file} with thumbnail {thumbnail}: {e}")
                failed_list.append(usd_file)
        else:
            print(f"No suitable thumbnail found for: {usd_file}")
            failed_list.append(usd_file)

        completion += increment

    if failed_list:
        print(f"Number of failed assets: {len(failed_list)}")
        print(failed_list)
        return len(failed_list), failed_list


def build_parm_name(prefix: 'str | None' = None,
                    affix: 'str | None' = None,
                    index: 'int | list[int] | None' = None,
                    suffix: 'str | None' = None) -> str:
    parts = []

    if prefix is not None:
        parts.append(prefix)

    if affix is not None:
        parts.append(affix)

    if index is not None:
        # Check if index is a single integer or a list
        if isinstance(index, list):
            parts.extend(map(str, index))  # Convert each index in the list to a string and extend the list
        else:
            parts.append(str(index))  # Convert single index to a string

    if suffix is not None:
        parts.append(suffix)

    return '_'.join(parts)





