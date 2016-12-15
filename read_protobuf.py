import scenenet_pb2 as sn
from nltk.corpus import wordnet as wn

trajectories = sn.Trajectories()
file_path = 'data/scenenet_rgbd_val.pb'
try:
    with open(file_path,'rb') as f:
        trajectories.ParseFromString(f.read())
except IOError:
    print('Scenenet protobuf data not found at location:{0}'.format(file_path))
    print('Please ensure you have copied the pb file to the data directory')

print('Number of trajectories:{0}'.format(len(trajectories.trajectories)))
for traj in trajectories.trajectories:
    layout_type = sn.SceneLayout.LayoutType.Name(traj.layout.layout_type)
    layout_path = traj.layout.model
    print('='*20)
    print('Render path:{0}'.format(traj.render_path))
    print('Layout type:{0} path:{1}'.format(layout_type,layout_path))
    print('='*20)
    print('')
    print('Number of instances: {0}'.format(len(traj.instances)))
    for instance in traj.instances:
        instance_type = sn.Instance.InstanceType.Name(instance.instance_type)
        print('='*20)
        print('Instance id:{0}'.format(instance.instance_id))
        print('Instance type:{0}'.format(instance_type))
        if instance.instance_type != sn.Instance.BACKGROUND:
            print('Wordnet id:{0}'.format(instance.semantic_wordnet_id))
            print('Plain english name:{0}'.format(instance.semantic_english))
        if instance.instance_type == sn.Instance.LIGHT_OBJECT:
            light_type = sn.LightInfo.LightType.Name(instance.light_info.light_type)
            print('Light type:{0}'.format(light_type))
        if instance.instance_type == sn.Instance.RANDOM_OBJECT:
            print('Object info:{0}'.format(instance.object_info))
        print('-'*20)
        print('')
    print('Render path:{0}'.format(traj.render_path))
    for view in traj.views:
        print(view)
    break
