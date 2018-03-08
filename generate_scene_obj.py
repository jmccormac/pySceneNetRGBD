# Script developed by Jingdao Chen
# Modified by John McCormac

import scenenet_pb2 as sn
import sys
import os
import numpy
import random

def get_bounding_box(path):
	shapenet_file = open(path,'r')
	vertices = []
	for l in shapenet_file:
		if l.startswith('v '):
			s = l[2:].split()
			x = float(s[0])
			y = float(s[1])
			z = float(s[2])
			vertices.append([x,y,z])
	shapenet_file.close()
	minX = min([v[0] for v in vertices])
	maxX = max([v[0] for v in vertices])
	minY = min([v[1] for v in vertices])
	maxY = max([v[1] for v in vertices])
	minZ = min([v[2] for v in vertices])
	maxZ = max([v[2] for v in vertices])
	return minX,maxX,minY,maxY,minZ,maxZ

# The usual ScenenetRGBD paths
data_root_path = 'data/val'
protobuf_path = 'data/scenenet_rgbd_val.pb'
# Sign up and download the ShapeNetCore.v1 dataset (https://www.shapenet.org/) extract to the path below
shapenet_dir = 'data/ShapeNetCore.v1'
# Clone the layouts for our dataset (https://github.com/jmccormac/SceneNetRGBD_Layouts.git) to the path below
layout_dir = 'data/SceneNetRGBD_Layouts'

if __name__ == '__main__':
    trajectories = sn.Trajectories()
    try:
        with open(protobuf_path,'rb') as f:
            trajectories.ParseFromString(f.read())
    except IOError:
        print('Scenenet protobuf data not found at location:{0}'.format(data_root_path))
        print('Please ensure you have copied the pb file to the data directory')
        raise

    traj = random.choice(trajectories.trajectories)

    layout_path = traj.layout.model
    layout_file = open(os.path.join(layout_dir,layout_path),'r')
    output_path = 'data/complete_scene.obj'
    output_file = open(output_path,'w')
    offset_vertex = 0
    offset_texture = 0
    print('Producing scene layout obj for render path:{0} outputting to:{1}'.format(traj.render_path,output_path))
    # Write out the layout obj file
    for l in layout_file:
        if l.startswith('v '):
            offset_vertex += 1
        elif l.startswith('vt '):
            offset_texture += 1
        output_file.write(l)
    layout_file.close()
    for instance in traj.instances:
        # Add the instance object obj mesh to the combined scene
        if instance.instance_type == sn.Instance.RANDOM_OBJECT:
            shapenet_id = instance.object_info.shapenet_hash
            height = instance.object_info.height_meters
            i = instance.object_info.object_pose
            T = numpy.array([i.translation_x,i.translation_y,i.translation_z])
            R = numpy.array([
                [i.rotation_mat11,i.rotation_mat12,i.rotation_mat13],
                [i.rotation_mat21,i.rotation_mat22,i.rotation_mat23],
                [i.rotation_mat31,i.rotation_mat32,i.rotation_mat33],
            ])
            shapenet_model_path = os.path.join(shapenet_dir,shapenet_id,'model.obj')
            if not os.path.isfile(shapenet_model_path):
                print('ShapeNet object model not found at path:{0} trying secondary location...'.format(shapenet_model_path))
                shapenet_model_path = os.path.join(shapenet_dir,shapenet_id,'models','model_normalized.obj')
                if not os.path.isfile(shapenet_model_path):
                    print('ShapeNet object model not found at path:{0}'.format(shapenet_model_path))
                    sys.exit(1)
            bb = get_bounding_box(shapenet_model_path)
            centroid = numpy.array([bb[0]+((bb[1]-bb[0])/2.0),bb[2]+((bb[3]-bb[2])/2.0),bb[4]+((bb[5]-bb[4])/2.0)])
            centroid[1] -= 0.6 * (bb[3] - bb[2])
            shapenet_file = open(shapenet_model_path,'r')
            num_vertices = 0
            num_texture = 0
            for l in shapenet_file:
                if l.startswith('v '):
                    num_vertices += 1
                    s = l[2:].split()
                    x = float(s[0])
                    y = float(s[1])
                    z = float(s[2])
                    p = numpy.array([x,y,z])

                    tmp = p[0]
                    p[0] = p[2]
                    p[2] = -tmp

                    p = (p - centroid) * (height / (bb[3] - bb[2]))
                    p = R.dot(p) + T
                    output_file.write('v %f %f %f\n' % (p[0],p[1],p[2]))
                elif l.startswith('vt '):
                    num_texture += 1
                    output_file.write(l)
                elif l.startswith('f '):
                    s = 'f'
                    for p in l[2:].split():
                        if '/' in p:
                            vid = int(p.split('/')[0])
                            try:
                                vtid = int(p.split('/')[1])
                                s += ' '+str(vid+offset_vertex)+'/'+str(vtid+offset_texture)
                            except:
                                vtid = int(p.split('/')[2])
                                s += ' '+str(vid+offset_vertex)+'//'+str(vtid+offset_texture)
                        else:
                            s +=' ' + str(int(p)+offset_vertex)
                    output_file.write(s+'\n')
                elif l.startswith('mtllib '):
                    pass
                else:
                    output_file.write(l)
            offset_vertex += num_vertices
            offset_texture += num_texture
            shapenet_file.close()
    output_file.close()
