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
    print(f"Processing file path: {file_path}")

    # Otherwise generate the node as usual
    new_node = _createNode(container, node_name, "null")

    if prev_item is not None and next_node is None:
        new_node.setInput(0, prev_item)
    if next_node is not None:
        toolutils.insertNodeAbove(next_node, new_node)
    new_node.moveToGoodPosition()
    return new_node


def override_drag_drop():
    from layout import assetlayoutinterface as ali
    orig_register_asset = ali.registerAsset

    def register_asset_override(id_, asset):
        orig_register_asset(id_, asset)

        if id_ == "sidefx_usd_database_source":
            ali.__asset_defns["sidefx_usd_database_source"].generator = custom_fileAssetPlacementHandler

    ali.registerAsset = register_asset_override