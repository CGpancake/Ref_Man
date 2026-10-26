# region Imports
import getpass
import json
import os
import re
import shutil
import subprocess
import tempfile

import hou
import refman.util.util as util
from pxr import Usd, UsdRender
# endregion

def asset_menu(kwargs):
    node = kwargs['node']
    location = node.evalParm('loc')
    asset_type = node.evalParm('type')

    jobs = hou.getenv('JOBS')
    client = hou.getenv("CLIENT")
    project = hou.getenv("PROJECT")

    project_folder = os.path.join(jobs, client, project)

    asset_path = '{0}/assets/USD/{1}/{2}/'.format(project_folder, location, asset_type)

    menu = ['None', 'None']

    if asset_path and os.access(asset_path, os.F_OK):
        for f in os.listdir(asset_path):
            if os.path.isdir(util.fix_path(os.path.join(asset_path, f))):
                menu.append(f)
                menu.append(f)
    return menu


def load_from_disk(kwargs):
    node = kwargs['node']
    load = node.evalParm('load')

def asset_path_switch(kwargs):
    node = kwargs['node']
    node.parm('name').set('None')
    node.parm('name').pressButton()


def openPath(kwargs):
    node = kwargs['node']

    # Reference Manager HDAs expose 'ref_root'; layer HDAs expose 'layer_folder'.
    parm = node.parm('ref_root')
    if parm is None:
        parm = node.parm('layer_folder')
    dir = parm.eval() if parm is not None else ''

    if os.path.exists(dir):
        if dir[-1] != '/':
            dir += '/'
        hou.ui.showInFileBrowser(dir)
    else:
        hou.ui.displayMessage(text="Could not open directory:\n{dir}.".format(dir=dir),
                              severity=hou.severityType.ImportantMessage)

def latest_version(kwargs):
    node = kwargs['node']

    if node.evalParm('enableversion') and node.evalParm('autoversion'):
        # Determine the cache directory

        # Check if asset name is available
        child = hou.node(f'{node.path()}/Distinguish_Role')
        child.cook()

        root = node.evalParm('ref_root')

        if not os.access(root, os.F_OK):
            print("Cache directory does not exist.")
            node.parm('version').set(1)
            return

        # List directories in the cache directory
        items = os.listdir(root)
        dirs = [d for d in items if os.path.isdir(os.path.join(root, d))]
        # Initialize version list
        version_list = []
        # Regex to match directory names with the specific asset name and version pattern
        regex = fr'(V(?P<ver>\d+))$'
        for d in dirs:
            match = re.search(regex, d, re.IGNORECASE)
            if match:
                version_list.append(int(match.group('ver')))

        if not version_list:
            node.parm('version').set(1)
        else:
            # Increment the highest version number found
            version_list.sort()
            new_version = version_list[-1] + 1
            node.parm('version').set(new_version)



def set_default_primitive(kwargs):
    node = kwargs['node']
    stage = node.stage()

    root = stage.GetPseudoRoot()
    children = root.GetChildren()
    prims = []

    for c in children:
        if c.GetName() == 'HoudiniLayerInfo':
            continue
        prims.append(c)

    if len(prims) > 1:
        hou.ui.displayMessage(text='Root contains multiple primitives\n'
                                   'Place all primitives under a single parent.',
                              severity=hou.severityType.Error)
        raise RuntimeError('Root contains multiple primitives')

    elif len(prims) == 0:
        hou.ui.displayMessage(text='Root contains no primitives\n'
                                   'Place primitives under a single parent.',
                              severity=hou.severityType.Error)
        raise RuntimeError('Root contains no primitives')
    elif len(prims) == 1:
        if node.parm('defaultprim').isLocked():
            node.parm('defaultprim').lock(False)

        child_path = f'{node.path()}/Export'
        child = hou.node(child_path)
        child_parm = 'defaultprim'
        child.parm(child_parm).set(str(prims[0].GetPrimPath()))
        node.parm('defaultprim').set(str(prims[0].GetPrimPath()))
        node.parm('defaultprim').lock(True)


def force_compare(kwargs):
    # Get the current node, parent, and editable stage
    node = kwargs['node']
    load = node.evalParm('load')
    if not load:
        compare = hou.node(f'{node.path()}/Compare_file')
        stage = hou.node(f'{node.path()}/set_customData').stage()

        # Define the path to the prim where the hash is stored
        prim_path = hou.node(f'{node.path()}/Distinguish_Role').evalParm('root')
        if not prim_path:
            raise hou.NodeWarning("No primitives were referenced")

        # Retrieve the prim from the current editable stage
        current_prim = stage.GetPrimAtPath(prim_path)
        if not current_prim.IsValid():
            raise RuntimeError(f"Prim at path {prim_path} does not exist on the current stage")

        # Retrieve the stored hash from the current prim
        current_hash = current_prim.GetCustomDataByKey('asset_hash')

        if current_hash is None:
            print("Current asset hash not found.")
        else:
            print(f"Current asset hash: {current_hash}")
            compare.parm('hash').set(str(current_hash))

        file = None
        if os.path.exists(node.evalParm('usd_file')):
            file = node.evalParm('usd_file')

        if not file:
            print("No valid USD file found.")
            hou.node(f'{node.path()}/Compare_Switch').parm('input').set(1)
            hou.node(f'{node.path()}/Compare_Switch').parm('input').pressButton()
            compare.parm('file').set('')
            compare.parm('file_hash').set('File not found')
            node.parm('message').set('File not found - defaulting to LOP input')
            node.parm('wipup').set(1)
            color = hou.Color(0.8, 0.2, 0.2)
            node.setColor(color)
        else:
            # Open the saved stage from the file
            compare.parm('file').set(file)
            print('testing 02')
            if node.evalParm('check') == 1 and node.evalParm('load') == 0:
                saved_stage = ''
                if os.path.isfile(file):
                    print(f"File path evaluated: {file}, Exists: {os.path.isfile(file)}")
                    saved_stage = Usd.Stage.Open(file)
                else:
                    node.parm('message').set('File was not created yet')
                    node.parm('wipup').set(0)

                # Retrieve the prim from the saved stage
                saved_prim = saved_stage.GetPrimAtPath(prim_path)
                if not saved_prim.IsValid():
                    raise RuntimeError(f"Prim at path {prim_path} does not exist on the saved stage")

                # Retrieve the stored hash from the saved prim
                saved_hash = saved_prim.GetCustomDataByKey('asset_hash')

                if saved_hash is None:
                    print("Saved asset hash not found.")
                else:
                    print(f"Saved asset hash: {saved_hash}")
                    compare.parm('file_hash').set(str(saved_hash))

                # Compare the hashes
                if current_hash != saved_hash:
                    hou.node(f'{node.path()}/Compare_Switch').parm('input').set(1)
                    hou.node(f'{node.path()}/Compare_Switch').parm('input').pressButton()
                    if node.evalParm('autoversion'):
                        node.parm('message').set('Changes Found - Live Check wip up')
                        node.parm('wipup').set(1)
                        color = hou.Color(1.0, 0.6, 0.0)
                        node.setColor(color)
                    else:
                        node.parm('message').set('Warning! Changes Found - autoversion is disabled and file will be overwritten')
                        node.parm('wipup').set(0)
                        color = hou.Color(0.8, 0.2, 0.2)
                        node.setColor(color)

                else:
                    print("No differences found based on asset hash.")
                    hou.node(f'{node.path()}/Compare_Switch').parm('input').set(0)
                    hou.node(f'{node.path()}/Compare_Switch').parm('input').pressButton()
                    color = hou.Color(0.75, 1.0, 0.2)
                    node.setColor(color)
                    node.parm('message').set(
                        'No updates found compared to file on disk - referencing existing file from disk')
                    node.parm('wipup').set(0)
            elif node.evalParm('load') == 1:
                node.parm('message').set(
                    'Node is set to always load files from disk')
                color = hou.Color(0.1, 0.3, 0.75)
                node.setColor(color)
                node.parm('wipup').set(0)
            elif node.evalParm('load') == 0 and node.evalParm('check') == 0 and node.evalParm('autoversion') == 1:
                node.parm('message').set(
                    'Node is set to auto version after manual saving only')
                color = hou.Color(0.2, 0.2, 0.2)
                node.setColor(color)
                node.parm('wipup').set(0)
            else:
                node.parm('message').set(
                    "I don't know what's happening ¯\_(ツ)_/¯")
                color = hou.Color(1.0, 0.2, 0.75)
                node.setColor(color)
                node.parm('wipup').set(0)
    else:
        color = hou.Color(0.3, 0.35, 0.7)
        node.setColor(color)




def pre_render(kwargs):
    print('prerender working!')
    node = kwargs['node']
    node.parm('latest').pressButton()
    elements = hou.node(node.path() + '/Detect_Elements')
    elements.cook()
    configure = hou.node(node.path() + '/configurelayer')
    configure.cook()

#unnecesary cahnge
def onCreated(kwargs):
    node = kwargs['node']

def context_menu(kwargs):
    node = kwargs['node']
    node_type = node.type().name()
    context = ''
    menu = []
    if 'Assets' in node_type:
        type = kwargs['parm'].name().split('_')[0]
        index = kwargs['script_multiparm_index']
        root = node.evalParm(f'{type}_root_{index}')
        name = node.evalParm(f'{type}_name_{index}')
        context = os.path.join(root, name, 'Context')
        menu = ['', 'Asset']
    if 'Reference_Manager' in node_type:
        root = node.evalParm('ref_root')
        context = os.path.join(root, 'Context')
        menu = ['asset','asset','geo','geo','mtl','mtl','agent','agent','clip','clip','groom','groom']

    paths = []
    build_context_menu_items(context, paths)
    for p in paths:
        _relative_path = p.split(f'{context}/', 1)[-1]
        subfolders = _relative_path.split(os.sep)
        cleaned_path = os.sep.join(subfolders[:-1])
        if cleaned_path not in menu:
            menu.append(cleaned_path)
            menu.append(cleaned_path)

    if menu:
        return menu
    else:
        return []


def build_context_menu_items(current_path, paths):
    # Ensure paths is a set for unique collection
    if os.path.isdir(current_path):
        items = os.listdir(current_path)
        file_found = False  # Flag to ensure directory contains at least one file
        for item in items:
            full_path = os.path.join(current_path, item)
            if os.path.isdir(full_path):
                # If it's a directory, recurse into it
                build_context_menu_items(full_path, paths)
            else:
                # If it's a file, set the flag
                file_found = True
        if file_found:
            # Add the directory path once if it contains at least one file
            if current_path not in paths:
                paths.append(current_path)

def generate_inputs(kwargs):
    node = kwargs["node"]

    # --------------------------------------------------
    # Configuration: match these to your HDA
    # --------------------------------------------------
    MULTIPARM_COUNT = "inputs"
    NAME_PARM = "name_{}"
    USD_PATH_PARM = "usd_path_{}"

    FETCH_TYPE = "fetch"
    ROP_TYPE = "usd_rop"

    # Fetch LOP parameter that specifies the source LOP.
    FETCH_PATH_PARM = "loppath"

    # Internal node naming
    FETCH_PREFIX = "fetch_"
    ROP_PREFIX = "rop_"

    # --------------------------------------------------
    # 1. Collect connected inputs by input index
    # --------------------------------------------------
    inputs = []

    for connection in node.inputConnections():
        input_index = connection.inputIndex()
        input_node = connection.inputNode()

        if input_node is not None:
            inputs.append((input_index, input_node))

    inputs.sort(key=lambda item: item[0])

    # --------------------------------------------------
    # 2. Update the multiparm instances
    # --------------------------------------------------
    count_parm = node.parm(MULTIPARM_COUNT)

    if count_parm is None:
        raise hou.Error(
            "Missing multiparm count parameter: "
            + MULTIPARM_COUNT
        )

    count_parm.set(len(inputs))

    for instance, (input_index, input_node) in enumerate(
        inputs, start=1
    ):
        name_parm = node.parm(NAME_PARM.format(instance))

        if name_parm is not None:
            name_parm.set(input_node.name())

        # Preserve existing USD paths when possible.
        # Initialize an empty path for newly created instances.
        usd_parm = node.parm(USD_PATH_PARM.format(instance))

        if usd_parm is not None and not usd_parm.eval():
            usd_parm.set(
                "$HIP/usd/{}.usdc".format(input_node.name())
            )

    # --------------------------------------------------
    # 3. Remove previously generated Fetch and ROP nodes
    # --------------------------------------------------
    for child in list(node.children()):
        child_type = child.type().name()

        if (
            child.name().startswith(FETCH_PREFIX)
            or child.name().startswith(ROP_PREFIX)
        ):
            child.destroy()

    # --------------------------------------------------
    # 4. Create a Fetch/ROP pair for each input
    # --------------------------------------------------
    for instance, (input_index, input_node) in enumerate(
        inputs, start=1
    ):
        # Fetch node
        fetch = node.createNode(
            FETCH_TYPE,
            "{}{}".format(FETCH_PREFIX, instance)
        )

        fetch_path_parm = fetch.parm(FETCH_PATH_PARM)

        if fetch_path_parm is not None:
            fetch_path_parm.set(input_node.path())
        else:
            raise hou.Error(
                "Fetch node '{}' has no parameter '{}'".format(
                    fetch.path(), FETCH_PATH_PARM
                )
            )

        # USD ROP node
        rop = node.createNode(
            ROP_TYPE,
            "{}{}".format(ROP_PREFIX, instance)
        )

        # Match the corresponding multiparm instance.
        usd_parm = node.parm(USD_PATH_PARM.format(instance))
        rop_output_parm = rop.parm("lopoutput")

        if usd_parm is None:
            raise hou.Error(
                "Missing multiparm parameter: {}".format(
                    USD_PATH_PARM.format(instance)
                )
            )

        if rop_output_parm is None:
            raise hou.Error(
                "ROP '{}' has no lopoutput parameter".format(
                    rop.path()
                )
            )

        rop_output_parm.set(usd_parm.evalAsString())

        # Frame range mode follows the HDA's trange / t1 t2 t3.
        _link_rop_to_hda(node, rop)

        # Wire the Fetch output into the ROP if supported.
        if rop.inputConnectors():
            rop.setInput(0, fetch)

        # Organize the generated nodes.
        fetch.setPosition(
            hou.Vector2((instance - 1) * 3, 0)
        )
        rop.setPosition(
            hou.Vector2((instance - 1) * 3, -2)
        )



# region Node callbacks (moved from the HDA module)

def get_root_primitives(file_path):
    try:
        stage = Usd.Stage.Open(file_path)
        return [prim.GetName() for prim in stage.GetPseudoRoot().GetChildren()]
    except Exception as exc:
        print(f"Error reading {file_path}: {exc}")
        return []


def check_roots(kwargs):
    node = kwargs['node']
    file_path = kwargs['script_value']
    if not file_path:
        return

    root_parm = node.parm('root')
    if not os.path.isfile(file_path):
        root_parm.set('')
        return

    root_prims = get_root_primitives(file_path)
    if root_prims and node.evalParm('root') not in root_prims:
        root_parm.set(root_prims[0])


def sequence(kwargs):
    """Sequence toggle callback: push the setting to the legacy Export node
    and to every generated rop_N."""
    node = kwargs['node']
    wanted = 'range' if kwargs['parm'].eval() == 1 else 'current'
    for child in node.children():
        if child.name() == 'Export' or child.name().startswith('rop_'):
            parm = child.parm('trange')
            if parm is not None and not parm.keyframes():  # skip HDA-linked ROPs
                _set_trange(child, wanted)


def openHipfile(kwargs):
    node = kwargs['node']
    usd_file = node.evalParm('usd_file')

    hipfile = None
    if os.path.isfile(usd_file):
        prim = Usd.Stage.Open(usd_file).GetPrimAtPath(node.evalParm('defaultprim'))
        if prim.IsValid():
            hipfile = prim.GetCustomDataByKey('hipfile')

    if not (hipfile and os.path.isfile(hipfile)):
        hou.ui.displayMessage('Hipfile does not exist or is invalid.',
                              severity=hou.severityType.Error)
        return

    try:
        subprocess.Popen(['houdini', hipfile])
    except OSError as exc:
        hou.ui.displayMessage(f'Error opening Houdini: {exc}',
                              severity=hou.severityType.Error)


def onLoaded(kwargs):
    node = kwargs['node']
    node.setColor(hou.Color(0.3, 0.35, 0.7) if node.evalParm('load')
                  else hou.Color(1.0, 0.8, 0.2))


def forceCook(kwargs):
    hou.node(f"{kwargs['node'].path()}/Distinguish_Role").cook()

# endregion


# region Deadline submission: export USD (native progress bar) -> Karma/husk job
#
# Deadline_Submission_Info (JSON env var) keys:
#   all optional: Pool, Group, SecondaryPool, Priority, Whitelist,
#   LimitGroups, BatchName, EnvironmentVariables{}, KarmaVersion
#   (KarmaVersion defaults to the running Houdini major.minor)
# Pool / Group / Priority can be overridden by same-named node parms.

def _deadline_info():
    raw = hou.getenv("Deadline_Submission_Info")
    if not raw:
        raise RuntimeError("Deadline_Submission_Info is empty or missing.")
    info = json.loads(raw)
    if not isinstance(info, dict):
        raise ValueError("Deadline_Submission_Info must be a JSON object.")
    return info


def _submit_to_deadline(job, plugin):
    """Submit via deadlinecommand (no host config needed) and return the JobID.

    deadlinecommand is found through DEADLINE_PATH (or PATH) and uses the
    repository connection the local Deadline client is already set up with.
    """
    executable = shutil.which("deadlinecommand", path=os.environ.get("DEADLINE_PATH"))
    if not executable:
        raise RuntimeError(
            "deadlinecommand not found. Set DEADLINE_PATH or add Deadline's "
            "bin folder to PATH.")

    with tempfile.TemporaryDirectory(prefix="karma_submit_") as folder:
        files = []
        for filename, values in (("job.job", job), ("plugin.job", plugin)):
            path = os.path.join(folder, filename)
            with open(path, "w", encoding="utf-8", newline="\n") as stream:
                stream.writelines(f"{key}={value}\n" for key, value in values.items())
            files.append(path)

        result = subprocess.run(
            [executable, *files],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            errors="replace",
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),  # no console flash
        )

    output = (result.stdout + result.stderr).strip()
    if result.returncode != 0:
        raise RuntimeError(f"Deadline submission failed:\n{output}")
    for line in result.stdout.splitlines():
        if line.startswith("JobID="):
            return line.partition("=")[2].strip()
    raise RuntimeError(f"Deadline returned no JobID:\n{output}")


def _setting(node, parm_name, info, key, unset=("",)):
    """HDA parm wins; falls back to the JSON settings; None if neither.

    Read with evalAsString(): eval() on a menu parm returns the item *index*
    (0, 1, 2...), not the pool/group name, which is why menu values never
    reached Deadline. Values listed in `unset` count as 'not chosen'.
    """
    parm = node.parm(parm_name)
    value = parm.evalAsString().strip() if parm is not None else ""
    if value.lower() in unset:
        value = ""
    return value if value else info.get(key)


# --- Frame range handling ---------------------------------------------------
# USD ROP 'trange' has four modes (tokens vary by Houdini build, so they are
# classified by token *and* label rather than hard-coded):
#   current : Render Current Frame
#   range   : Render Frame Range / Render Frame Range (Strict)
#   stage   : Render Frame Range From Stage

def _trange_mode(rop):
    """Classify the ROP's trange as 'current', 'range' or 'stage'."""
    parm = rop.parm("trange")
    if parm is None:
        return "current"
    token = parm.evalAsString().lower()
    try:
        label = parm.menuLabels()[parm.eval()].lower()
    except (IndexError, hou.OperationFailed):
        label = ""
    if "stage" in token or "stage" in label:
        return "stage"
    if token == "off" or "current" in label:
        return "current"
    return "range"


def _set_trange(rop, wanted):
    """Set trange to 'current' or 'range', picking the matching menu entry."""
    parm = rop.parm("trange")
    if parm is None:
        return
    tokens = list(parm.menuItems())
    labels = [label.lower() for label in parm.menuLabels()]
    for i, (token, label) in enumerate(zip(tokens, labels)):
        is_current = token == "off" or "current" in label
        is_stage = "stage" in token.lower() or "stage" in label
        strict = "strict" in label or token == "on"
        if wanted == "current" and is_current:
            parm.set(i)
            return
        if wanted == "range" and not is_current and not is_stage and not strict:
            parm.set(i)
            return
    # Fallback: ordinal menu convention 0 = current, 1 = range
    parm.set(0 if wanted == "current" else min(1, len(tokens) - 1))


def _find_parm(node, *names):
    for name in names:
        parm = node.parm(name)
        if parm is not None:
            return parm
    return None


# ROP parm -> HDA parm. Linked with channel references so the ROP always
# follows the HDA (the ROP's parent), including when the HDA is changed later.
_ROP_HDA_LINKS = (
    ("trange", ("trange",)),
    ("f1", ("f1",)),
    ("f2", ("f2",)),
    ("f3", ("f3",)),
)


def _link_rop_to_hda(node, rop):
    """Make the ROP's trange and frame range reference the HDA's parms.

    Called when the ROPs are generated and again at submit time (it is
    idempotent), so ROPs built by an older version are fixed up as well.
    The HDA's trange menu must list the same items in the same order as the
    USD ROP's, because the reference passes the menu index.
    """
    for rop_name, hda_names in _ROP_HDA_LINKS:
        rop_parm = rop.parm(rop_name)
        hda_name = next((n for n in hda_names if node.parm(n) is not None), None)
        if rop_parm is None or hda_name is None:
            print(f"Cannot link {rop.name()}.{rop_name}: no HDA parm named "
                  f"{' or '.join(hda_names)}.")
            continue
        rop_parm.setExpression(f'ch("../{hda_name}")', hou.exprLanguage.Hscript)

    hda_menu = node.parm("trange")
    rop_menu = rop.parm("trange")
    if hda_menu is not None and rop_menu is not None \
            and list(hda_menu.menuItems()) != list(rop_menu.menuItems()):
        print(f"WARNING: HDA trange menu {list(hda_menu.menuItems())} differs from "
              f"{rop.name()} trange menu {list(rop_menu.menuItems())}; the frame "
              f"range mode may not match.")


def _frames_for_job(rop, usd_path):
    """Deadline frame string matching what the ROP just exported."""
    mode = _trange_mode(rop)

    if mode == "current":
        return str(hou.intFrame())

    if mode == "stage":
        # Range comes from the stage's own metadata, i.e. the exported file.
        stage = Usd.Stage.Open(usd_path, Usd.Stage.LoadNone)
        if stage.HasAuthoredTimeCodeRange():
            return f"{int(stage.GetStartTimeCode())}-{int(stage.GetEndTimeCode())}"
        return str(hou.intFrame())

    start, end, step = rop.evalParmTuple("f")
    frames = f"{int(start)}-{int(end)}"
    return frames if step <= 1 else f"{frames}x{int(step)}"


# --- Render settings preflight ----------------------------------------------

DEFAULT_RENDER_SETTINGS = "/Render/rendersettings"


def _find_render_settings(stage):
    settings = UsdRender.Settings.GetStageRenderSettings(stage)
    if not settings:
        settings = UsdRender.Settings(stage.GetPrimAtPath(DEFAULT_RENDER_SETTINGS))
    return settings or None


def _validate_render_settings(usd_path):
    """Check the exported USD can be rendered by husk/Karma before submitting.

    Husk falls back to the stage's render settings for everything not passed
    on the command line (camera, resolution, products, AOVs), so the file
    must carry a complete RenderSettings -> Products -> Vars chain. Raises
    RuntimeError listing every problem found.
    """
    stage = Usd.Stage.Open(usd_path, Usd.Stage.LoadNone)

    settings = _find_render_settings(stage)
    if settings is None:
        raise RuntimeError(
            f"No RenderSettings prim in the exported USD (looked at stage "
            f"metadata and {DEFAULT_RENDER_SETTINGS}). Add a Karma Render "
            f"Settings LOP upstream of the node being fetched.")
    settings_path = settings.GetPath()
    problems = []

    products = settings.GetProductsRel().GetTargets()
    if not products:
        problems.append(f"{settings_path} has no render products.")

    for product_path in products:
        prim = stage.GetPrimAtPath(product_path)
        if not prim.IsValid():
            problems.append(f"{settings_path} lists product {product_path}, "
                            f"which is not in the exported USD.")
            continue
        product = UsdRender.Product(prim)

        if not product.GetProductNameAttr().Get():
            problems.append(f"Product {product_path} has no productName (output path).")

        var_paths = product.GetOrderedVarsRel().GetTargets()
        if not var_paths:
            problems.append(f"Product {product_path} has no render vars (AOVs).")
        for var_path in var_paths:
            if not stage.GetPrimAtPath(var_path).IsValid():
                problems.append(
                    f"Bad orderedVar path {var_path} for product {product_path}: "
                    f"the render var prim is not in the exported USD (are the "
                    f"Render Var LOPs upstream of the fetched node, and not "
                    f"above a layer break?).")

    for camera_path in settings.GetCameraRel().GetTargets():
        if not stage.GetPrimAtPath(camera_path).IsValid():
            problems.append(f"Render settings camera {camera_path} is not in the exported USD.")

    if problems:
        raise RuntimeError("\n    ".join(problems))


IMAGE_EXTENSIONS = (".exr", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".dpx")


def _apply_output_path(node, index, usd_path, name, is_sequence, info):
    """Write the HDA's exr_path_N into the product's productName.

    The HDA's output path only exists on the HDA; husk reads productName from
    the USD. If the HDA path is a folder, '<name>.$F4.exr' (sequence) or
    '<name>.exr' is appended. Only done when there is exactly one product,
    since one path cannot be mapped onto several.
    """
    parm = node.parm(f"exr_path_{index}")
    path = str(parm.eval() or "").strip().replace("\\", "/") if parm is not None else ""
    if not path:
        return
    if os.path.splitext(path)[1].lower() not in IMAGE_EXTENSIONS:
        path = f"{path.rstrip('/')}/{name}" + (".$F4.exr" if is_sequence else ".exr")
    _check_farm_path(path, "The output path", info)

    stage = Usd.Stage.Open(usd_path, Usd.Stage.LoadNone)
    settings = _find_render_settings(stage)
    if settings is None:
        return
    products = settings.GetProductsRel().GetTargets()
    if len(products) != 1:
        return
    prim = stage.GetPrimAtPath(products[0])
    if not prim.IsValid():
        return

    stage.SetEditTarget(stage.GetRootLayer())
    UsdRender.Product(prim).GetProductNameAttr().Set(path)
    stage.GetRootLayer().Save()


USD_EXTENSIONS = (".usd", ".usda", ".usdc", ".usdz")


def _check_farm_path(path, what, info):
    """Refuse paths on the local C: drive: render workers cannot see them.

    A job that points at C:/Houdini/... starts on the worker, which has no
    such folder, and fails with 'Unable to load USD file'. Use a UNC/network
    path (e.g. \\\\GFS\\jobs\\...). Set "AllowLocalPaths": true in
    Deadline_Submission_Info if your workers really do share that path.
    """
    if info.get("AllowLocalPaths"):
        return
    if os.path.splitdrive(os.path.normpath(path))[0].upper() == "C:":
        raise RuntimeError(
            f"{what} is on the local C: drive ({path}), which farm workers "
            f"cannot see. Point it at a network location such as \\\\GFS\\jobs\\...")


def _normalize_usd_path(path, fallback_name):
    """Make sure the export path is a file path USD can determine a format for.

    A path like C:/Houdini/USD/Render/Test_1010 has no extension, so USD
    cannot pick a file format and both the export and the later open fail.
    """
    if os.path.isdir(path) or path.endswith(("/", "\\")):
        path = os.path.join(path, fallback_name)
    if os.path.splitext(path)[1].lower() not in USD_EXTENSIONS:
        path += ".usd"
    return path


def _deadline_safe_path(path):
    """Keep a trailing number out of the USD file name.

    Deadline's Karma plugin treats a number at the end of the file name as a
    frame number and swaps it for the task's frame: Test_1010.usd was
    requested as Test_1001.usd on frame 1001, which does not exist.
    """
    stem, ext = os.path.splitext(path)
    if stem[-1:].isdigit():
        stem += "_usd"
    return stem + ext


def _frame_count(frames):
    """Number of frames in a Deadline frame string like '1001', '1-10', '1-10x2'."""
    span, _, step = frames.partition("x")
    start, _, end = span.partition("-")
    first = int(start)
    last = int(end) if end else first
    return (last - first) // max(int(step or 1), 1) + 1


def _rop_report(node, index, rop):
    """Everything useful for working out why a ROP wrote nothing."""
    lines = [f"{rop.path()}: lopoutput = {rop.evalParm('lopoutput')}, "
             f"trange = {rop.parm('trange').evalAsString()}"]
    for target in (rop, hou.node(f"{node.path()}/fetch_{index}")):
        if target is None:
            continue
        lines += [f"{target.name()} error: {m}" for m in target.errors()]
        lines += [f"{target.name()} warning: {m}" for m in target.warnings()]
    return "\n    ".join(lines)


def _batch_name(info):
    """Deadline batch name: the hip file name, so one click = one group."""
    name = hou.getenv("HIPNAME") or ""
    if not name or name.lower() == "untitled":
        name = info.get("BatchName") or "untitled"
    return name


def _submit_input(node, index, info, pool, group, priority):
    """Export one USD and submit it as a Karma job. Returns (name, job_id)."""
    raw_path = hou.text.expandString(
        str(node.evalParm(f"usd_path_{index}") or "")).strip()
    if not raw_path:
        raise ValueError("USD path is empty.")
    fallback_name = (node.evalParm(f"name_{index}") or "").strip() or f"input_{index}"
    usd_path = os.path.abspath(_normalize_usd_path(raw_path, fallback_name))
    usd_path = _deadline_safe_path(usd_path)
    _check_farm_path(usd_path, "The USD path", info)
    os.makedirs(os.path.dirname(usd_path), exist_ok=True)

    rop = hou.node(f"{node.path()}/rop_{index}")
    if rop is None:
        raise RuntimeError(f"Could not find USD ROP: rop_{index}")

    _link_rop_to_hda(node, rop)

    # Point the ROP at the path explicitly (it was set when the inputs were
    # generated and may be stale), then run a blocking export.
    rop.parm("lopoutput").set(usd_path.replace("\\", "/"))
    rop.render()

    if not os.path.isfile(usd_path):
        raise RuntimeError(
            f"The USD ROP did not write {usd_path}.\n    "
            + _rop_report(node, index, rop))

    output_name = (node.evalParm(f"name_{index}") or "").strip() or fallback_name
    _apply_output_path(node, index, usd_path, output_name,
                       is_sequence=_trange_mode(rop) != "current", info=info)

    # Fail here, with a readable message, rather than on the farm.
    _validate_render_settings(usd_path)

    name = (node.evalParm(f"name_{index}") or "").strip() or \
        os.path.splitext(os.path.basename(usd_path))[0]

    frames = _frames_for_job(rop, usd_path)
    job = {
        "Plugin": "Karma",
        "Name": name,
        "UserName": getpass.getuser(),
        "Frames": frames,
        # One USD holds the whole range, so one task must render all of it;
        # smaller chunks make the Karma plugin look for per-frame USD files.
        "ChunkSize": _frame_count(frames),
        "Priority": priority,
    }
    optional = {
        "Pool": pool,
        "Group": group,
        "SecondaryPool": info.get("SecondaryPool"),
        "BatchName": info.get("BatchName"),
        "Whitelist": info.get("Whitelist"),
        "LimitGroups": info.get("LimitGroups"),
    }
    job.update({key: value for key, value in optional.items() if value})
    for n, (key, value) in enumerate(info.get("EnvironmentVariables", {}).items()):
        job[f"EnvironmentKeyValue{n}"] = f"{key}={value}"

    plugin = {
        "SceneFile": os.path.normpath(usd_path),
        "Version": info.get("KarmaVersion")
        or "{}.{}".format(*hou.applicationVersion()[:2]),
    }

    return name, _submit_to_deadline(job, plugin)


def _export_and_submit_all(node, info, pool, group, priority):
    """Export and submit every input under one Houdini progress dialog.

    Lives in its own function so the dialog is released on return, before
    the result message box is shown.
    """
    count = node.evalParm("inputs")
    submitted, errors, cancelled = [], [], False

    try:
        with hou.InterruptableOperation(
            "Submitting USD to Deadline", "Exporting USD", open_interrupt_dialog=True
        ) as op:
            for i in range(1, count + 1):
                label = (node.evalParm(f"name_{i}") or "").strip() or f"input {i}"
                op.updateLongProgress((i - 1) / count, f"Exporting {label} ({i}/{count})")
                try:
                    submitted.append(
                        _submit_input(node, i, info, pool, group, priority))
                except hou.OperationInterrupted:
                    raise
                except Exception as exc:
                    errors.append(f"{label}: {exc}")
                op.updateLongProgress(i / count, f"Finished {label} ({i}/{count})")
    except hou.OperationInterrupted:
        cancelled = True

    return submitted, errors, cancelled


def submit(kwargs):
    node = kwargs["node"]

    try:
        info = _deadline_info()
        info["BatchName"] = _batch_name(info)
        pool = _setting(node, "pool", info, "Pool")
        group = _setting(node, "group", info, "Group")
        info["SecondaryPool"] = _setting(
            node, "sec_pool", info, "SecondaryPool",
            unset=("", "none", "<none>", "-"))
        priority_value = _setting(node, "priority", info, "Priority")
        priority = int(float(priority_value)) if priority_value not in (None, "") else 50
    except Exception as exc:
        hou.ui.displayMessage(f"Deadline setup failed:\n{exc}")
        return []

    submitted, errors, cancelled = _export_and_submit_all(
        node, info, pool, group, priority)

    message = f"Submitted {len(submitted)} of {node.evalParm('inputs')} USD jobs."
    message += (f"\nBatch: {info['BatchName']}  Pool: {pool}  "
                f"Secondary: {info.get('SecondaryPool')}  Group: {group}  "
                f"Priority: {priority}")
    if cancelled:
        message += "\nCancelled by user."
    if errors:
        message += "\n\nIssues:\n" + "\n".join(errors)
    hou.ui.displayMessage(message)
    return submitted

# endregion