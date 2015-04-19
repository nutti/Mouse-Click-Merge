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
__version__ = "0.1"
__date__ = "20 April 2015"

bl_info = {
    "name" : "Mouse Click Merge",
    "author" : "Nutti",
    "version" : (0,1),
    "blender" : (2, 7, 0),
    "location" : "3D View > Properties Panel > Mouse Click Merge",
    "description" : "Merge by clicking mouse. This add-on is inspired by modeling tool 'Metasequoia'.",
    "warning" : "",
    "wiki_url" : "",
    "tracker_url" : "",
    "category" : "3D View"
}

# properties used by this script
class MCMProperties(bpy.types.PropertyGroup):
    running = BoolProperty(
        name = "Is Running",
        description = "Is merge tool running now?",
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

# Merge by Mouse Click.
class MCMOperator(bpy.types.Operator):
    """Merge by Mouse Click."""
    
    bl_idname = "view3d.mouse_click_merge"
    bl_label = "Merge by Mouse Click"
    bl_description = "Merge by Mouse Click"
    bl_options = {'REGISTER', 'UNDO'}
    
    def __init__(self):
        pass
    
    def __del__(self):
        pass
    
    def modal(self, context, event):
        mcm_props = bpy.context.scene.mcm_props
        
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
                bpy.ops.mesh.merge(type='CENTER', uvs=False)
                mcm_props.merged_count = mcm_props.merged_count + 1
            mcm_props.merged = True
        
        # restrain merge operation is down more than twice
        if mcm_props.right_mouse_down is False or mcm_props.left_mouse_down is False:
            mcm_props.merged = False
        
        return {'PASS_THROUGH'}
    
    def invoke(self, context, event):
        mcm_props = bpy.context.scene.mcm_props
        if context.area.type == 'VIEW_3D':
            # start merge
            if mcm_props.running is False:
                mcm_props.running = True
                mcm_props.merged = False
                mcm_props.left_mouse_down = False
                mcm_props.right_mouse_down = False
                mcm_props.merged_count = 0
                context.window_manager.modal_handler_add(self)
                return {'RUNNING_MODAL'}
            # stop merge
            else:
                mcm_props.running = False
                self.report({'INFO'}, "Merged: %d vertices." % (mcm_props.merged_count))
                return {'FINISHED'}
        else:
            return {'CANCELLED'}
        
# UI view
class OBJECT_PT_MCM(bpy.types.Panel):
    bl_label = "Mouse Click Merge"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    
    def draw(self, context):
        layout = self.layout
        mcm_props = bpy.context.scene.mcm_props
        if mcm_props.running is False:
            layout.operator(MCMOperator.bl_idname, text="Start Merge Tool", icon="PLAY")
        else:
            layout.operator(MCMOperator.bl_idname, text="Stop Merge Tool", icon="PAUSE")


def register():
    bpy.utils.register_module(__name__)
    bpy.types.Scene.mcm_props = PointerProperty(
        name = "MCM internal data",
        description = "MCM internal data",
        type = MCMProperties)


def unregister():
    bpy.utils.unregister_module(__name__)
    del bpy.types.Scene.mcm_props


if __name__ == "__main__":
    register()
    
