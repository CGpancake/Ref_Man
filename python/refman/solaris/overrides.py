from pxr import Usd, UsdGeom
import hou, json, os
from typing import Optional, Any
import toolutils


def _createNode(container: hou.Node, node_name: str, node_type: str) -> hou.Node:
    """
    Returns the node with name node_name.
    """
    return container.createNode(node_type, node_name=node_name, force_valid_node_name=True)

def custom_fileAssetPlacementHandler(
    container: hou.Node,
    asset_info: dict[str, Any],
    primpath: str,
    prev_item: Optional[hou.NetworkMovableItem],
    next_node: Optional[hou.Node],
    force_gen: bool = False) -> Optional[hou.Node]:
    """ Generate a set of nodes that import an asset from a file.

    file_path : str describing the file path to the asset.
    name: str name for the node, might be modified to be a valid variable name.
    primpath: str describing the primitive path for the referenced asset.
    data: bytestring encoding a dictionary holding the primpath for the specific
          primitive being referenced from the file.
    """

    file_path = asset_info['srcpath']
    name = asset_info['label']
    data = asset_info['data']
    data_dict = json.loads(data.decode()) if data else {}
    node_name = hou.text.variableName(name)

    # Create an asset reference node
    new_node = container.node(node_name)
    if not force_gen and new_node is not None:
        # If the node already exists just return that node.
        return new_node
    if file_path.startswith('/sasha/3D_LIBRARY/Houdini/Lights/HDRIs'):
        # Get Required Metadata
        base_name = file_path.split('/')[-1].split('.')[0]
        stage = Usd.Stage.Open(file_path)
        primitive_path = f'/{base_name}'
        primitive = stage.GetPrimAtPath(primitive_path)
        hdri_metadata = primitive.GetCustomData().get('hdri')
        new_node = _createNode(container, node_name, "domelight")


        desired_params = [parm for parm in new_node.parms() if
                          'inputstexturefile' in parm.name() and 'control' not in parm.name()]
        for parm in desired_params:
            try:
                parm.set(hdri_metadata)
            except hou.OperationFailed as e:
                print(f"Failed to set {parm.name()}: {e}")

        if prev_item is not None and next_node is None:
            new_node.setInput(0, prev_item)
        if next_node is not None:
            toolutils.insertNodeAbove(next_node, new_node)
        new_node.moveToGoodPosition()
        return new_node
    elif file_path.startswith('/sasha/3D_LIBRARY/Houdini/Lights/LightFilters'):
        # Otherwise generate the node as usual
        new_node = _createNode(container, node_name, "lightfilterlibrary")
        gobo = _createNode(new_node, node_name, 'kma_lfilter_gobo')
        base_name = file_path.split('/')[-1].split('.')[0].split('_')[-1]
        stage = Usd.Stage.Open(file_path)
        primitive_path = f'/{base_name}'
        primitive = stage.GetPrimAtPath(primitive_path)
        lightfilter_metadata = primitive.GetCustomData().get('LightFilter')
        # open usd from file_path and get texture file location
        gobo.parm("map").set(lightfilter_metadata)


        if prev_item is not None and next_node is None:
            new_node.setInput(0, prev_item)
        if next_node is not None:
            toolutils.insertNodeAbove(next_node, new_node)
        new_node.moveToGoodPosition()
        return new_node
    else:
        # Otherwise generate the node as usual
        new_node = _createNode(container, node_name, "assetreference")
        new_node.parm("filepath").set(file_path)
        new_node.parm("instanceable").set(1)
        # Warn on missing files instead of error.
        new_node.parm("handlemissingfiles").set("warn")
        new_node.parm("primpath").set(primpath)
        new_node.parm("filerefprim").set("")
        new_node.parm("filerefprimpath").set(data_dict.get("refprimpath", ""))

        # Set variant selections.
        variants_dict = data_dict.get('variants', {})
        new_node.parm("num_variants").set(len(variants_dict))
        for (i, (vset, value)) in enumerate(variants_dict.items()):
            new_node.parm("variantset{}".format(i + 1)).set(vset)
            new_node.parm("variantname{}".format(i + 1)).set(value)

        if prev_item is not None and next_node is None:
            new_node.setInput(0, prev_item)
        if next_node is not None:
            toolutils.insertNodeAbove(next_node, new_node)
        new_node.moveToGoodPosition()
        return new_node


def override_drag_drop():
    print('trying to overwrite')
    from layout import assetlayoutinterface as ali
    orig_register_asset = ali.registerAsset

    def register_asset_override(id_, asset):
        orig_register_asset(id_, asset)

        if id_ == "sidefx_usd_database_source":
            ali.__asset_defns["sidefx_usd_database_source"].generator = custom_fileAssetPlacementHandler

    ali.registerAsset = register_asset_override