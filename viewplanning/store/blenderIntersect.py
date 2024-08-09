'''
uses blender to intersect two visiblity regions
'''
# To run
# blender --python modifyViewRegion.py -- --out ../../data/viewRegions/generated ../../data/viewRegions/full/
import sys
import bpy
import argparse

MAX_SIZE = 4000
CONE_OFFSET = 5
OFFSET_MIN = 4e-5
OFFSET_MAX = 1e-3


def clear():
    # clear workspace
    for item in bpy.data.objects:
        bpy.data.objects.remove(item)


def intersect(a, b, out):
    clear()

    # import view volume
    bpy.ops.import_mesh.ply(filepath=a)
    aMesh = bpy.context.selected_objects[0]
    bpy.ops.import_mesh.ply(filepath=b)
    bMesh = bpy.context.selected_objects[0]
    

    bool = aMesh.modifiers.new(name='cone_intersect', type='BOOLEAN')
    bool.object = bMesh
    bool.operation = 'INTERSECT'
    aMesh.select_set(True)
    with bpy.context.temp_override(object=aMesh):
        bpy.ops.object.modifier_apply(modifier=bool.name)

    bpy.data.objects.remove(bMesh)
    aMesh.select_set(True)
    if len(aMesh.data.polygons) == 0:
        return
    # save
    bpy.ops.export_mesh.ply(filepath=out)


def main():
    print(sys.argv)
    parser = argparse.ArgumentParser(
        description='Clip and Decimate View Regions')
    parser.add_argument('--a', dest='a')
    parser.add_argument('--b', dest='b')
    parser.add_argument('--out', dest='outpath')
    i = sys.argv.index('--')
    args = parser.parse_args(sys.argv[i + 1:])

    out = args.outpath
    intersect(args.a, args.b, out)
    # exit blender
    bpy.ops.wm.quit_blender()


if __name__ == '__main__':
    main()
