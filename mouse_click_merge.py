# <pep8-80 compliant>

# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
import bmesh
import mathutils
import math

from bpy.props import *

__author__ = "Nutti <nutti.metro@gmail.com>"
__status__ = "In Feature Review"
__version__ = "0.3"
__date__ = "9 May 2015"

bl_info = {
    "name" : "Mouse Click Merge",
    "author" : "Nutti",
    "version" : (0,3),
    "blender" : (2, 7, 0),
    "location" : "3D View > Properties Panel > Mouse Click Merge",
    "description" : "Merge by clicking mouse. This add-on is inspired by modeling tool 'Metasequoia'.",
    "warning" : "",
    "wiki_url" : "",
    "tracker_url" : "",
    "category" : "3D View"
}

addon_keymaps = []

def get_allowed_operation(scene, context):
    items = []

    items.append(("MERGE", "Merge", "Merge nearest-neighbor vertex."))
    items.append(("FLIP DIAGONAL EDGE", "Flip Diagonal Edge", "Flip diagonal edge."))
    
    return items


# properties used by "merge" operation
class MCMMergeProperties(bpy.types.PropertyGroup):
    running = BoolProperty(
        name = "Is Running",
        description = "Is merge operation running now?",
        default = False)
    left_mouse_down = BoolProperty(
        name = "Left Mouse Down",
        description = "Is left mouse down?",
        default = False)
    right_mouse_down = BoolProperty(
        name = "Right Mouse Down",
        description = "Is right mouse down?",
        default = False)
    merged = BoolProperty(
        name = "Merged",
        description = "Already merged?",
        default = True)
    merged_count = IntProperty(
        name = "Merged count",
        description = "Merged count",
        default = 0)

# properties used by "flip diagonal edge" operation
class MCMFlipDiagonalProperties(bpy.types.PropertyGroup):
    running = BoolProperty(
        name = "Is Running",
        description = "Is flip diagonal operation running now?",
        default = False)
    left_mouse_down = BoolProperty(
        name = "Left Mouse Down",
        description = "Is left mouse down?",
        default = False)
    right_mouse_down = BoolProperty(
        name = "Right Mouse Down",
        description = "Is right mouse down?",
        default = False)
    fliped = BoolProperty(
        name = "Fliped",
        description = "Already fliped?",
        default = True)

# skeleton strategy
class MCMStrategySkel():
    def modal(self, ops, context, event):
        pass
    def invoke(self, ops, context, event):
        pass

# strategy: merge
class MCMMerge(MCMStrategySkel):
    def modal(self, ops, context, event):
        mcm_props = bpy.context.scene.mcm_merge_props
        merge_type = bpy.context.scene.mcm_merge_type
        merge_uv = bpy.context.scene.mcm_merge_uv
        
        if mcm_props.running is False:
            return {'PASS_THROUGH'}
        
        # update key state
        if event.type == 'LEFTMOUSE':
            if event.value == 'PRESS':
                mcm_props.left_mouse_down = True
            elif event.value == 'RELEASE':
                mcm_props.left_mouse_down = False
        elif event.type == 'RIGHTMOUSE':
            if event.value == 'PRESS':
                mcm_props.right_mouse_down = True
            elif event.value == 'RELEASE':
                mcm_props.right_mouse_down = False
        
        # merge vertex
        if mcm_props.right_mouse_down is True and mcm_props.left_mouse_down is True and mcm_props.merged is False:
            # get adjacent vertex
            obj = bpy.context.edit_object
            me = obj.data
            bm = bmesh.from_edit_mesh(me)
            selected_vert = None
            adj_verts = []
            for v in bm.verts:
                if v.select is True:
                    selected_vert = v
                    for e in v.link_edges:
                        adj_verts.append(e.other_vert(v))
                    break
            nearest_vert = None
            min_distance = 1000000000.0
            for av in adj_verts:
                if nearest_vert is None:
                    nearest_vert = av
                    diff = mathutils.Vector()
                    diff = av.co - selected_vert.co
                    min_distance = math.sqrt(diff.x * diff.x + diff.y * diff.y + diff.z * diff.z)
                else:
                    diff = mathutils.Vector()
                    diff = av.co - selected_vert.co
                    distance = math.sqrt(diff.x * diff.x + diff.y * diff.y + diff.z * diff.z)
                    if distance < min_distance:
                        nearest_vert = av
                        min_distance = distance
            
            # merge adjacent vertex
            if nearest_vert is not None:
                nearest_vert.select_set(True)
                bpy.ops.mesh.merge(type=merge_type, uvs=merge_uv)
                mcm_props.merged_count = mcm_props.merged_count + 1
            mcm_props.merged = True
        
        # restrain merge operation processed more than twice
        if mcm_props.right_mouse_down is False or mcm_props.left_mouse_down is False:
            mcm_props.merged = False
        
        return {'PASS_THROUGH'}
    def invoke(self, ops, context, event):
        sc = context.scene
        mcm_props = bpy.context.scene.mcm_merge_props
        if context.area.type == 'VIEW_3D':
            # start merge
            if mcm_props.running is False:
                mcm_props.running = True
                mcm_props.merged = False
                mcm_props.left_mouse_down = False
                mcm_props.right_mouse_down = False
                mcm_props.merged_count = 0
                context.window_manager.modal_handler_add(ops)
                return {'RUNNING_MODAL'}
            # stop merge
            else:
                mcm_props.running = False
                ops.report({'INFO'}, "Merged: %d vertices." % (mcm_props.merged_count))
                return {'FINISHED'}
        else:
            return {'CANCELLED'}
        

# strategy: flip diagonal
class MCMFlipDiagonal(MCMStrategySkel):
    def modal(self, ops, context, event):
        mcm_props = bpy.context.scene.mcm_flip_diag_props
        merge_type = bpy.context.scene.mcm_merge_type
        merge_uv = bpy.context.scene.mcm_merge_uv
        
        if mcm_props.running is False:
            return {'PASS_THROUGH'}
        
        # update key state
        if event.type == 'LEFTMOUSE':
            if event.value == 'PRESS':
                mcm_props.left_mouse_down = True
            elif event.value == 'RELEASE':
                mcm_props.left_mouse_down = False
        elif event.type == 'RIGHTMOUSE':
            if event.value == 'PRESS':
                mcm_props.right_mouse_down = True
            elif event.value == 'RELEASE':
                mcm_props.right_mouse_down = False

        if mcm_props.right_mouse_down is True and mcm_props.left_mouse_down is True and mcm_props.fliped is False:
            bpy.ops.mesh.edge_rotate(use_ccw=False)
            mcm_props.fliped = True
        
        # restrain flip operation processed more than twice
        if mcm_props.right_mouse_down is False or mcm_props.left_mouse_down is False:
            mcm_props.fliped = False
        
        return {'PASS_THROUGH'}
    
    def invoke(self, ops, context, event):
        sc = context.scene
        mcm_props = bpy.context.scene.mcm_flip_diag_props
        if context.area.type == 'VIEW_3D':
            # start merge
            if mcm_props.running is False:
                mcm_props.running = True
                mcm_props.left_mouse_down = False
                mcm_props.right_mouse_down = False
                mcm_props.fliped = False
                context.window_manager.modal_handler_add(ops)
                return {'RUNNING_MODAL'}
            # stop merge
            else:
                mcm_props.running = False
                return {'FINISHED'}
        else:
            return {'CANCELLED'}

# Operation.
class MCMOperator(bpy.types.Operator):
    """Merge by Mouse Click."""
    
    bl_idname = "view3d.mouse_click_merge"
    bl_label = "Merge by Mouse Click"
    bl_description = "Merge by Mouse Click"
    bl_options = {'REGISTER', 'UNDO'}
    
    strategy = None
    
    def __init__(self):
        pass
    
    def __del__(self):
        pass
    
    def modal(self, context, event):
        if context.area:
            context.area.tag_redraw()
        
        if self.strategy == None:
            return {'CANCELLED'}
        else:
            return self.strategy.modal(self, context, event)
    
    def invoke(self, context, event):
        sc = context.scene
        if sc.mcm_operation == "MERGE":
            self.strategy = MCMMerge()
        elif sc.mcm_operation == "FLIP DIAGONAL EDGE":
            self.strategy = MCMFlipDiagonal()
        
        if self.strategy == None:
            return {'CANCELLED'}
        else:
            return self.strategy.invoke(self, context, event)
        
# UI view
class OBJECT_PT_MCM(bpy.types.Panel):
    bl_label = "Mouse Click Merge"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    
    def draw(self, context):
        sc = context.scene
        layout = self.layout
        merge_props = bpy.context.scene.mcm_merge_props
        flip_diag_props = bpy.context.scene.mcm_flip_diag_props
        layout.prop(sc, "mcm_operation", text="")
        if sc.mcm_operation == "MERGE":
            if merge_props.running is False:
                layout.operator(MCMOperator.bl_idname, text="Start", icon="PLAY")
            else:
                layout.operator(MCMOperator.bl_idname, text="Stop", icon="PAUSE")
            layout.label(text="Merge Type:")
            layout.prop(sc, "mcm_merge_type", text="")
            layout.prop(sc, "mcm_merge_uv", text="UV")
        elif sc.mcm_operation == "FLIP DIAGONAL EDGE":
            if flip_diag_props.running is False:
                layout.operator(MCMOperator.bl_idname, text="Start", icon="PLAY")
            else:
                layout.operator(MCMOperator.bl_idname, text="Stop", icon="PAUSE")


def get_allowed_merge_type(scene, context):
    items = []
    
    # FIRST and LAST are allowed when selection mode is VERT
    if bpy.context.tool_settings.mesh_select_mode[0] is True:
        items.append(("FIRST", "First", "Merge into first selected vertex."))
        items.append(("LAST", "Last", "Merge into nearest neighbor vertex."))

    items.append(("CENTER", "Center", "Merge into center of merged vertices."))
    items.append(("CURSOR", "Cursor", "Merge and move merged vertex to cursor."))
    
    return items


def init_properties():
    sc = bpy.types.Scene
    sc.mcm_operation = EnumProperty(
        items=get_allowed_operation,
        name="Operation",
        description="Operation")
    sc.mcm_merge_type = EnumProperty(
        items=get_allowed_merge_type,
        name="Merge Type",
        description="Merge Type")
    sc.mcm_merge_uv = BoolProperty(
        name="UV",
        description="Merge with UV.",
        default=False)
    sc.mcm_merge_props = PointerProperty(
        name = "MCM merge operation internal data",
        description = "MCM merge operation internal data",
        type = MCMMergeProperties)
    sc.mcm_flip_diag_props = PointerProperty(
        name = "MCM flip diagonal operation internal data",
        description = "MCM flip diagonal operation internal data",
        type = MCMFlipDiagonalProperties)

def clear_properties():
    del bpy.types.Scene.mcm_merge_type
    del bpy.types.Scene.mcm_merge_uv
    del bpy.types.Scene.mcm_merge_props
    del bpy.types.Scene.mcm_flip_diag_props

def register():
    bpy.utils.register_module(__name__)
    init_properties()
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name="3D View", space_type="VIEW_3D")
        kmi = km.keymap_items.new(MCMOperator.bl_idname, "M", "PRESS", shift=True, alt=False)
        addon_keymaps.append((km, kmi))


def unregister():
    bpy.utils.unregister_module(__name__)
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    clear_properties()


if __name__ == "__main__":
    register()
    
