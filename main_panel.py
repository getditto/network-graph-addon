import bpy
import math
import pdb
from mathutils import Vector
from bpy.types import (Panel, Operator)
from itertools import combinations


# ------------------------------------------------------------------------
#    Operators
# ------------------------------------------------------------------------


class SimpleMeshOperator(Operator):
    """Creates poly lines between all selected objects and hooks them"""
    bl_idname = "object.with_empty_objects"
    bl_label = "Simple Mesh Operator"

    @staticmethod
    def deselect_everything():
        bpy.ops.object.mode_set(mode = 'OBJECT')
        for obj in bpy.data.objects:
            obj.select_set(False)

    def execute(self, context):
        if len(context.selected_objects) < 2:
            self.report({'ERROR'}, "Please select at least two objects")
    
        collection = bpy.data.collections.new("Mesh Lines")
        bpy.context.scene.collection.children.link(collection)

        # Get a combination of all the paths to draw
        object_combo = list(combinations(context.selected_objects, 2))
        for o in object_combo:
            a = o[0]
            b = o[1]

            coords = [a.location, b.location]
            curveData = bpy.data.curves.new(f'{a.name}.{b.name}', type='CURVE')
            curveData.dimensions = '3D'
            curveData.resolution_u = 2
            # map coords to spline
            polyline = curveData.splines.new('POLY')
            polyline.points.add(len(coords)-1)

            for i, coord in enumerate(coords):
                x,y,z = coord
                polyline.points[i].co = (x, y, z, 1)

            # create Object
            curveOB = bpy.data.objects.new(f'{a.name}.{b.name}', curveData)
            curveOB['network_graph_path'] = True
            curveData.bevel_depth = 0.01
            # attach to scene and validate context
            collection.objects.link(curveOB)

            hook_a_mod_name = f'{a.name}-hook'
            hook_b_mod_name = f'{b.name}-hook'
            modifier_a = curveOB.modifiers.new(name=hook_a_mod_name, type='HOOK')
            modifier_a.object = a
            modifier_b = curveOB.modifiers.new(name=hook_b_mod_name, type='HOOK')
            modifier_b.object = b

            self.deselect_everything()

            curveOB.select_set(state=True)
            bpy.context.view_layer.objects.active = curveOB

            bpy.ops.object.mode_set(mode = 'EDIT')
            # I have no idea why I need to call points.update()
            points = curveOB.data.splines[0].points
            points[0].select = True
            bpy.ops.object.hook_assign(modifier=hook_a_mod_name)
            # I have no idea why I need to call points.update()
            # but it is crucial for this to work without creating errors
            points.update()
            points[0].select = False
            points.update()
            points[1].select = True
            bpy.ops.object.hook_assign(modifier=hook_b_mod_name) 
            

        self.deselect_everything()
        bpy.ops.object.mode_set(mode = 'OBJECT')
        return {'FINISHED'}

class NETWORK_GRAPH_PT_main_panel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "Network Graph Curve Maker"
    bl_idname = "NETWORK_GRAPH_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Network Graph"
    bl_context = '.objectmode'

    def draw(self, context):
        layout = self.layout

        layout.label(text="Operators:")

        col = layout.column(align=True)
        col.operator(SimpleMeshOperator.bl_idname, text="Create Network Graph", icon="CONSOLE")

        layout.separator()