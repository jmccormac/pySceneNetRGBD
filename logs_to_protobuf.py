from collections import namedtuple
import numpy as np
import pathlib
import re
import scenenet_pb2 as sn
import sys

PoseData = namedtuple('PoseData', ['time', 'camera_position', 'camera_lookat'])

def get_info_log_lines(info_log):
    with open(str(info_log),'r') as f:
        readlines = f.readlines()
    return readlines

def get_text_layout_lines(text_layout_file):
    with open(text_layout_file,'r') as f:
        readlines = f.readlines()
    return readlines

def get_layout_type(line):
    layouts = {'office':sn.SceneLayout.OFFICE,
               'kitchen':sn.SceneLayout.KITCHEN,
               'livingroom':sn.SceneLayout.LIVING_ROOM,
               'bedroom':sn.SceneLayout.BEDROOM,
               'bathroom':sn.SceneLayout.BATHROOM,
              }
    for key,layout_enum in layouts.items():
        if key in line:
            return layout_enum
    return None

def process_objects_into_instances(layout_lines):
    objects = []
    current_object = None
    next_line_type = None
    for line in layout_lines:
        if line.startswith('#first'):
            break
        if line.strip() == 'object':
            next_line_type = 'object'
            continue
        if line.strip() == 'wnid':
            next_line_type = 'wnid'
            continue
        if line.strip() == 'scale':
            next_line_type = 'scale'
            continue
        if line.strip() == 'transformation':
            next_line_type = 'trans'
            continue
        if next_line_type == 'object':
            if current_object is not None:
                objects.append(current_object)
            current_object = {}
            num_transformations = 0
            current_object['hash'] = line.rstrip()
            continue
        if next_line_type == 'wnid':
            current_object['wnid'] = line.rstrip()
            continue
        if next_line_type == 'scale':
            current_object['scale'] = float(line.rstrip())
            continue
        if next_line_type == 'trans':
            if num_transformations == 0:
                current_object['transformation'] = []
            if num_transformations < 3:
                current_object['transformation'].append([float(x) for x in line.rstrip().split()])
            num_transformations += 1
            continue
    if current_object is not None:
        objects.append(current_object)
    return objects

def parse_log_to_frame_pose_pairs(log_lines,skip_frames = 25):
    def chunks(l, n):
        for i in range(0, len(l), n):
            yield l[i:i + n]
    regex = re.compile("time:([e\.\-\d]+) pose:([e\.\-\d]+),([e\.\-\d]+),([e\.\-\d]+) lookat:([e\.\-\d]+),([e\.\-\d]+),([e\.\-\d]+)")
    time_center_lookats = []
    # Get the list of poses
    for line in log_lines:
        m = regex.search(line)
        if m is not None:
            time_center_lookat = PoseData(time=float(m.group(1)),
                                            camera_position=np.array([float(m.group(i)) for i in range(2, 5)]),
                                            camera_lookat=np.array([float(m.group(i)) for i in range(5, 8)]))
            time_center_lookats.append(time_center_lookat)
    # Take them in pairs (i.e. time and pose of shutter open, time and pose of shutter close),
    # and filter out poses without a frame - using the pose_frame_skip info
    frame_pose_pair_list = []
    for idx,(shutter_open, shutter_close) in enumerate(chunks(time_center_lookats,2)):
        if idx % skip_frames == 0:
            frame_pose_pair_list.append((shutter_open,shutter_close))
    return frame_pose_pair_list

def get_instances(info_lines):
    instances = []
    for line in info_lines:
        if line.startswith('time:'):
            break
        if line.startswith('instance:'):
            instance_dict = {}
            try:
                instance_num,wnid,english,shapenethash = line.strip().split(';')
            except:
                try:
                    instance_num,wnid,english,position,radius,power = line.strip().split(';')
                    position = position.replace('position[','').replace(']','').split(',')
                    instance_dict['light_position'] = [float(x) for x in position]
                    radius = radius.replace('radius[','').replace(']','')
                    instance_dict['light_radius'] = float(radius)
                    power = power.replace('power[','').replace(']','').split(',')
                    instance_dict['light_power'] = [float(x) for x in power]
                except:
                    instance_num,wnid,english,position,v1,v2,power = line.strip().split(';')
                    position = position.replace('position[','').replace(']','').split(',')
                    instance_dict['light_position'] = [float(x) for x in position]
                    v1 = v1.replace('v1[','').replace(']','').split(',')
                    instance_dict['light_v1'] = [float(x) for x in v1]
                    v2 = v2.replace('v2[','').replace(']','').split(',')
                    instance_dict['light_v2'] = [float(x) for x in v2]
                    power = power.replace('power[','').replace(']','').split(',')
                    instance_dict['light_power'] = [float(x) for x in power]
                shapenethash = None
            instance_num = instance_num.split(':')[1]
            wnid = wnid.split(',')[0]
            english = english.split(',')[0]
            if shapenethash == '':
                shapenethash = None
            instance_dict['instance_num'] = int(instance_num)
            instance_dict['wnid'] = wnid
            instance_dict['english'] = english
            instance_dict['hash'] = shapenethash
            instances.append(instance_dict)
    return instances

def get_all_instances_dict(layout_lines,info_lines):
    objects_and_transforms = process_objects_into_instances(layout_lines)
    instances_in_log = get_instances(info_lines)
    for idx,instance in enumerate(instances_in_log):
        if instance['hash'] is not None:
            shapenet_idx = idx
            break
    for objects_and_transform in objects_and_transforms:
        shapenethash = objects_and_transform['hash']
        assert instances_in_log[shapenet_idx]['hash'] == shapenethash
        instances_in_log[shapenet_idx]['scale'] = objects_and_transform['scale']
        instances_in_log[shapenet_idx]['transformation'] = objects_and_transform['transformation']
        shapenet_idx += 1
    return instances_in_log

def fill_trajectory(info_lines,layout_lines,trajectory,frame_skip=25):
    layout = trajectory.layout
    layout.layout_type = get_layout_type(layout_lines[0])
    layout.model = layout_lines[0].split(': ./')[1].strip()
    all_instance_data = get_all_instances_dict(layout_lines,info_lines)

    instance = trajectory.instances.add()
    instance.instance_id = 0
    instance.instance_type = sn.Instance.BACKGROUND
    for instance_dict in all_instance_data:
        # This is the background object
        instance = trajectory.instances.add()
        instance.instance_id = instance_dict['instance_num']
        instance.semantic_wordnet_id = instance_dict['wnid']
        instance.semantic_english = instance_dict['english'].split('.')[0].lower()
        if 'light_power' in instance_dict:
            instance.instance_type = sn.Instance.LIGHT_OBJECT
            instance.light_info.light_output.r = instance_dict['light_power'][0]
            instance.light_info.light_output.g = instance_dict['light_power'][1]
            instance.light_info.light_output.b = instance_dict['light_power'][2]
            instance.light_info.position.x = instance_dict['light_position'][0]
            instance.light_info.position.y = instance_dict['light_position'][1]
            instance.light_info.position.z = instance_dict['light_position'][2]
            if 'light_radius' in instance_dict:
                instance.light_info.light_type = sn.LightInfo.SPHERE
                instance.light_info.radius = instance_dict['light_radius']
            elif 'light_v1' in instance_dict:
                instance.light_info.light_type = sn.LightInfo.PARALLELOGRAM
                instance.light_info.v1.x = instance_dict['light_v1'][0]
                instance.light_info.v1.y = instance_dict['light_v1'][1]
                instance.light_info.v1.z = instance_dict['light_v1'][2]
                instance.light_info.v2.x = instance_dict['light_v2'][0]
                instance.light_info.v2.y = instance_dict['light_v2'][1]
                instance.light_info.v2.z = instance_dict['light_v2'][2]
            else:
                assert False
        elif instance_dict['hash'] is None:
            instance.instance_type = sn.Instance.LAYOUT_OBJECT
        else:
            instance.instance_type = sn.Instance.RANDOM_OBJECT
            instance.object_info.height_meters = instance_dict['scale']
            instance.object_info.shapenet_hash = instance_dict['hash']
            instance.object_info.object_pose.translation_x = instance_dict['transformation'][0][3]
            instance.object_info.object_pose.translation_y = instance_dict['transformation'][1][3]
            instance.object_info.object_pose.translation_z = instance_dict['transformation'][2][3]
            instance.object_info.object_pose.rotation_mat11 = instance_dict['transformation'][0][0]
            instance.object_info.object_pose.rotation_mat12 = instance_dict['transformation'][0][1]
            instance.object_info.object_pose.rotation_mat13 = instance_dict['transformation'][0][2]
            instance.object_info.object_pose.rotation_mat21 = instance_dict['transformation'][1][0]
            instance.object_info.object_pose.rotation_mat22 = instance_dict['transformation'][1][1]
            instance.object_info.object_pose.rotation_mat23 = instance_dict['transformation'][1][2]
            instance.object_info.object_pose.rotation_mat31 = instance_dict['transformation'][2][0]
            instance.object_info.object_pose.rotation_mat32 = instance_dict['transformation'][2][1]
            instance.object_info.object_pose.rotation_mat33 = instance_dict['transformation'][2][2]
    pose_data = parse_log_to_frame_pose_pairs(info_lines,skip_frames=frame_skip)
    for idx,(shutter_open,shutter_close) in enumerate(pose_data):
        view = trajectory.views.add()
        view.frame_num = idx * frame_skip
        shutter_open_pose = view.shutter_open
        shutter_open_pose.camera.x = shutter_open.camera_position[0]
        shutter_open_pose.camera.y = shutter_open.camera_position[1]
        shutter_open_pose.camera.z = shutter_open.camera_position[2]
        shutter_open_pose.lookat.x = shutter_open.camera_lookat[0]
        shutter_open_pose.lookat.y = shutter_open.camera_lookat[1]
        shutter_open_pose.lookat.z = shutter_open.camera_lookat[2]
        shutter_open_pose.timestamp = shutter_open.time
        shutter_close_pose = view.shutter_close
        shutter_close_pose.camera.x = shutter_close.camera_position[0]
        shutter_close_pose.camera.y = shutter_close.camera_position[1]
        shutter_close_pose.camera.z = shutter_close.camera_position[2]
        shutter_close_pose.lookat.x = shutter_close.camera_lookat[0]
        shutter_close_pose.lookat.y = shutter_close.camera_lookat[1]
        shutter_close_pose.lookat.z = shutter_close.camera_lookat[2]
        shutter_close_pose.timestamp = shutter_close.time

if __name__ == '__main__':
    trajectories = sn.Trajectories()
    if len(sys.argv) < 3:
        print('Please run as python logs_to_protobuf.py /path/to/scenenetrgbd/renderer/build/render_info.log /path/to/scenenetrgbd/camera_trajectory_generator/build/scene_and_trajectory_description.txt')
        sys.exit(1)
    # Here we add only one trajectory, but it can be a full list
    render_log_path = sys.argv[1]
    scene_and_trajectory_description_path = sys.argv[2]
    info_lines = get_info_log_lines(render_log_path)
    layout_lines = get_text_layout_lines(scene_and_trajectory_description_path)
    trajectory = trajectories.trajectories.add()
    trajectory.render_path = str(pathlib.Path(render_log_path).parent)
    fill_trajectory(info_lines,layout_lines,trajectory)
    output_path = './scenenet_metadata.pb'
    print('Finished processing - writing to:{0}'.format(output_path))
    with open(output_path,'wb') as f:
        f.write(trajectories.SerializeToString())
