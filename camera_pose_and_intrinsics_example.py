from PIL import Image
import math
import numpy as np
import os
import pathlib
import random
import scenenet_pb2 as sn
import sys

def normalize(v):
    return v/np.linalg.norm(v)

def world_to_camera_with_pose(view_pose):
    lookat_pose = position_to_np_array(view_pose.lookat)
    camera_pose = position_to_np_array(view_pose.camera)
    up = np.array([0,1,0])
    R = np.diag(np.ones(4))
    R[2,:3] = normalize(lookat_pose - camera_pose)
    R[0,:3] = normalize(np.cross(R[2,:3],up))
    R[1,:3] = -normalize(np.cross(R[0,:3],R[2,:3]))
    T = np.diag(np.ones(4))
    T[:3,3] = -camera_pose
    return R.dot(T)

def camera_to_world_with_pose(view_pose):
    return np.linalg.inv(world_to_camera_with_pose(view_pose))

def camera_intrinsic_transform(vfov=45,hfov=60,pixel_width=320,pixel_height=240):
    camera_intrinsics = np.zeros((3,4))
    camera_intrinsics[2,2] = 1
    camera_intrinsics[0,0] = (pixel_width/2.0)/math.tan(math.radians(hfov/2.0))
    camera_intrinsics[0,2] = pixel_width/2.0
    camera_intrinsics[1,1] = (pixel_height/2.0)/math.tan(math.radians(vfov/2.0))
    camera_intrinsics[1,2] = pixel_height/2.0
    return camera_intrinsics

def position_to_np_array(position):
    return np.array([position.x,position.y,position.z])

def interpolate_poses(start_pose,end_pose,alpha):
    assert alpha >= 0.0
    assert alpha <= 1.0
    camera_pose = alpha * position_to_np_array(end_pose.camera)
    camera_pose += (1.0 - alpha) * position_to_np_array(start_pose.camera)
    lookat_pose = alpha * position_to_np_array(end_pose.lookat)
    lookat_pose += (1.0 - alpha) * position_to_np_array(start_pose.lookat)
    timestamp = alpha * end_pose.timestamp + (1.0 - alpha) * start_pose.timestamp
    pose = sn.Pose()
    pose.camera.x = camera_pose[0]
    pose.camera.y = camera_pose[1]
    pose.camera.z = camera_pose[2]
    pose.lookat.x = lookat_pose[0]
    pose.lookat.y = lookat_pose[1]
    pose.lookat.z = lookat_pose[2]
    pose.timestamp = timestamp
    return pose

data_root_path = 'data/val'
protobuf_path = 'data/scenenet_rgbd_val.pb'

def photo_path_from_view(render_path,view):
    photo_path = os.path.join(render_path,'photo')
    image_path = os.path.join(photo_path,'{0}.jpg'.format(view.frame_num))
    return os.path.join(data_root_path,image_path)

if __name__ == '__main__':
    trajectories = sn.Trajectories()
    try:
        with open(protobuf_path,'rb') as f:
            trajectories.ParseFromString(f.read())
    except IOError:
        print('Scenenet protobuf data not found at location:{0}'.format(data_root_path))
        print('Please ensure you have copied the pb file to the data directory')


    for idx,a_traj in enumerate(trajectories.trajectories):
        if a_traj.render_path == '0/68':
            traj = a_traj
            break
    # This is the 3D position of the center of the spherical light in 
    # the validation trajectory '0/68' in world coordinates
    light_position = np.array([-2.02838,1.57111,-0.388005,1.0])
    intrinsic_matrix = camera_intrinsic_transform()
    print('Instrinsic Camera Matrix')
    print(intrinsic_matrix)
    for idx,view in enumerate(traj.views):
        # Get camera pose
        ground_truth_pose = interpolate_poses(view.shutter_open,view.shutter_close,0.5)
        world_to_camera_matrix = world_to_camera_with_pose(ground_truth_pose)
         # Get light center in camera coordinates
        light_position_in_camera_coordinates = world_to_camera_matrix.dot(light_position)
         # Use camera intrinsics to project light center to pixel position
        uv_projection = intrinsic_matrix.dot(light_position_in_camera_coordinates)
        uv_projection /= uv_projection[2]
        # Augment the photo image with a black cross over the light in all frames 
        # in which it's visible
        pixel_x_position = int(uv_projection[0])
        pixel_y_position = int(uv_projection[1])
        photo_path = photo_path_from_view(traj.render_path,view)
        img = Image.open(photo_path)
        if pixel_x_position > 0 and pixel_x_position < 319:
            if pixel_y_position > 0 and pixel_y_position < 239:
                array = np.array(img)
                array[pixel_y_position,pixel_x_position,:] = 0.0
                array[pixel_y_position-1,pixel_x_position,:] = 0.0
                array[pixel_y_position+1,pixel_x_position,:] = 0.0
                array[pixel_y_position,pixel_x_position-1,:] = 0.0
                array[pixel_y_position,pixel_x_position+1,:] = 0.0
                img = Image.fromarray(np.uint8(array))
        img.save('{0}_marking_light.jpg'.format(idx))
