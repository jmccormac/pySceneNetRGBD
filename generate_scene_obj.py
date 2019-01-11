# Script developed by Jingdao Chen
# Modified by John McCormac

import scenenet_pb2 as sn
import sys
import os
import numpy
import random

import argparse

datasets = ["val", "train"]

parser = argparse.ArgumentParser(description='Reads in scene from protobuf and output a complete .obj and .mtl file')
parser.add_argument('--materials', action='store_true')
parser.add_argument('--v1', action='store_true', help="Models are using ShapeNet v1 repo rather than v2")
parser.add_argument('--shapenet-dir')
parser.add_argument('--layout-dir')
parser.add_argument('--ids', help="The indices of the trajectories to choose, comma separated,"
                                  "if empty, then all trajectories are processed")
parser.add_argument('protobuf')


def get_bounding_box(shapenet_path):
    shapenet_obj_file = open(shapenet_path, "r")
    vertices = []
    for l in shapenet_obj_file:
        if l.startswith('v '):
            s = l[2:].split()
            x = float(s[0])
            y = float(s[1])
            z = float(s[2])
            vertices.append([x, y, z])
    min_x = min([v[0] for v in vertices])
    max_x = max([v[0] for v in vertices])
    min_y = min([v[1] for v in vertices])
    max_y = max([v[1] for v in vertices])
    min_z = min([v[2] for v in vertices])
    max_z = max([v[2] for v in vertices])
    return min_x, max_x, min_y, max_y, min_z, max_z


def load_obj(shapenet_dir, instance, suffix):
    shapenet_id = instance.object_info.shapenet_hash
    # As of v2 preference is given to the model_normalized naming convention
    shapenet_obj_path = os.path.join(shapenet_dir, shapenet_id, 'models', 'model_normalized.' + suffix)
    if not os.path.isfile(shapenet_obj_path):
        if not args.v1:
            print('Cannot find normalized model. Most likely using ShapeNet.v1 - try running script with --v1 flag. Missing object at path:{0} trying secondary location...'.format(shapenet_obj_path))
        shapenet_obj_path = os.path.join(shapenet_dir, shapenet_id, 'model.' + suffix)
        if not os.path.isfile(shapenet_obj_path):
            print('ShapeNet object not found at path:{0}'.format(shapenet_obj_path))
            sys.exit(1)
    elif args.v1:
        print('This looks like a ShapeNet.v2 model with the name "model_normalized.obj", consider running without the v1 flag')
    return shapenet_obj_path


# Given offsets for (v, vn, vv)
# Merges scenenet object into the combined `merge_into_file` obj file
def merge_scenenet_obj(output_obj_file, shapenet_dir, instance, k, offsets):
    num_v = 0
    num_vt = 0
    num_vn = 0
    offset_v, offset_vt, offset_vn = offsets

    input_path = load_obj(shapenet_dir, instance, suffix="obj")

    height = instance.object_info.height_meters
    i = instance.object_info.object_pose
    T = numpy.array([i.translation_x, i.translation_y, i.translation_z])
    R = numpy.array([
        [i.rotation_mat11, i.rotation_mat12, i.rotation_mat13],
        [i.rotation_mat21, i.rotation_mat22, i.rotation_mat23],
        [i.rotation_mat31, i.rotation_mat32, i.rotation_mat33],
    ])
    bb = get_bounding_box(input_path)
    centroid = numpy.array(
        [bb[0] + ((bb[1] - bb[0]) / 2.0), bb[2] + ((bb[3] - bb[2]) / 2.0), bb[4] + ((bb[5] - bb[4]) / 2.0)])
    centroid[1] -= 0.6 * (bb[3] - bb[2])

    input_file = open(input_path, 'r')
    output_obj_file.write('o rand_obj.%d\n' % k)
    for l in input_file:
        if l.startswith('v '):
            num_v += 1
            s = l[2:].split()
            x = float(s[0])
            y = float(s[1])
            z = float(s[2])
            p = numpy.array([x, y, z])

            if args.v1:
                tmp = p[0]
                p[0] = p[2]
                p[2] = -tmp

            p = (p - centroid) * (height / (bb[3] - bb[2]))
            p = R.dot(p) + T
            output_obj_file.write('v %f %f %f\n' % (p[0], p[1], p[2]))
        elif l.startswith('vt '):
            num_vt += 1
            output_obj_file.write(l)
        elif l.startswith('vn '):
            num_vn += 1
            s = l[2:].split()
            x = float(s[0])
            y = float(s[1])
            z = float(s[2])
            n = numpy.array([x, y, z])
            n = R.dot(n)
            output_obj_file.write('vn %f %f %f\n' % (n[0],n[1],n[2]))
        elif l.startswith('f '):
            s = 'f'
            for p in l[2:].split():
                s += ' '
                if '/' in p:
                    # face statement is 'f v/vt/vn v/vt/vn v/vt/vn'
                    try:
                        vid_s, vtid_s, vnid_s = p.split('/')
                    except ValueError:
                        # This is for compatibility with some v1 object models
                        vid_s, vtid_s = p.split('/')
                        vnid_s = None
                    s += str(int(vid_s) + offset_v)
                    s += '/'
                    if vtid_s:  # If there is a vertex texture
                        s += str(int(vtid_s) + offset_vt)
                    s += '/'
                    if vnid_s:  # If there is a vertex normal
                        s += str(int(vnid_s) + offset_vn)
                else:
                    s += str(int(p) + offset_v)
            output_obj_file.write(s + '\n')
        elif l.startswith('mtllib '):
            # pass, as we combine all materials
            pass
        else:
            output_obj_file.write(l)

    input_file.close()
    return [offset_v + num_v, offset_vt + num_vt, offset_vn + num_vn]


def merge_scenenet_mtl(output_mtl_file, shapenet_dir, instance, k):
    input_path = load_obj(shapenet_dir, instance, suffix="mtl")
    input_file = open(input_path, 'r')
    output_mtl_file.write('# Material copied for shape %d from %s\n' % (k, input_path))
    for l in input_file:
        if l.startswith('map_Kd '):
            texture_path = l[len('map_Kd '):]
            # fix to relative path
            output_mtl_file.write('map_Kd %s\n' % os.path.join(os.path.dirname(input_path), texture_path))
        else:
            output_mtl_file.write(l)


def convert_trajectory(i, traj, shapenet_dir, layout_dir):
    out_name = "trajectory_%d" % i

    layout_path = traj.layout.model
    layout_file = open(os.path.join(layout_dir, layout_path), 'r')

    output_obj_filename = out_name + '.obj'
    output_mtl_filename = out_name + '.mtl'
    output_obj_file = open(output_obj_filename, 'w')

    output_mtl_file = None
    if args.materials:
        output_mtl_file = open(output_mtl_filename, 'w')

    offset_v = 0
    offset_vt = 0
    offset_vn = 0

    print('Producing complete obj for render path:{0} outputting to:{1}'.format(traj.render_path, output_obj_filename))

    # Write out the layout obj file
    for l in layout_file:
        if l.startswith('v '):
            offset_v += 1
        elif l.startswith('vt '):
            offset_vt += 1
        elif l.startswith('vn '):
            offset_vn += 1
        output_obj_file.write(l)

    layout_file.close()

    if args.materials:
        output_obj_file.write('mtllib %s\n' % output_mtl_filename)

    offsets = [offset_v, offset_vt, offset_vn]

    # TODO: Read in the layout mtl file, and assign random texture
    # While the mtl files from the layout obj are re-used,
    # We combine all other mtl files form the meshes into one.
    for k, instance in enumerate(traj.instances):
        # Add the instance object obj mesh to the combined scene
        if instance.instance_type == sn.Instance.RANDOM_OBJECT:
            offsets = merge_scenenet_obj(output_obj_file, shapenet_dir, instance, k, offsets)
            if args.materials:
                merge_scenenet_mtl(output_mtl_file, shapenet_dir, instance, k)

    output_obj_file.close()
    if args.materials:
        output_mtl_file.close()


def main(protobuf_path, shapenet_dir, layout_dir, indices):
    trajectories_pb = sn.Trajectories()
    try:
        with open(protobuf_path, 'rb') as f:
            trajectories_pb.ParseFromString(f.read())
    except IOError:
        print('Scenenet protobuf data not found at location:{0}'.format(protobuf_path))
        raise

    trajectories = trajectories_pb.trajectories

    if indices:
        trajectories = [(i,trajectories[i]) for i in indices]
    else:
        trajectories = [(i,trajectory) for i,trajectory in enumerate(trajectories)]

    for index,traj in trajectories:
        convert_trajectory(index, traj, shapenet_dir, layout_dir)
    print('Scene Generation Complete')


if __name__ == '__main__':
    args = parser.parse_args()

    ids = [int(i) for i in args.ids.split(",")] if args.ids else None
    data_dir = os.path.dirname(args.protobuf)

    # The usual ScenenetRGBD paths
    main(
        protobuf_path=args.protobuf,
        # Sign up and download the ShapeNetCore.v1 dataset (https://www.shapenet.org/) extract to the path below
        shapenet_dir=args.shapenet_dir or os.path.join(data_dir, 'ShapeNetCore.v2'),
        # Clone the layouts for our dataset (https://github.com/jmccormac/SceneNetRGBD_Layouts.git) to the path below
        layout_dir=args.layout_dir or os.path.join(data_dir, 'SceneNetRGBD_Layouts'),
        indices=ids)
