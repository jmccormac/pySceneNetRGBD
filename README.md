# pySceneNetRGBD

A set of python3 scripts showing examples of how to navigate and access the core elements of the data within the SceneNetRGBD dataset.

# Requirements

python3
numpy
PIL
protobuf

# Dataset structure

The dataset consists of two components.  The first component is a set of files organised into trajectory folders.  Each of these folders contains three directorys:

* photo - which contains the photorealistic renders, each of which is named after its frame_num (e.g. 0.jpg is the first pose, 25.jpg the next)
* depth - which contains the accompanying depth information stored as unsigned 16-bit integers within a PNG. The numbering scheme is the same as for photo (0.png is the first frame).  The units are millimeters, a value of 1000 is a meter. Depth is defined as the euclidean ray length from the camera position to the first point of intersection.
* instance - which contains instances labels for a trajectory also in unsigned 16-bit integers.  Instance 1 is the first object and will be the same through all of the frames within this folder

The second component is a protobuf file.  The definition of this protobuf is given in scenenet.proto.  It stores a list of trajectories, with the attribute 'render_path' which points towards the appropriate folder for the renders of that trajectory.  The protobuf also stores a set of views, each with a 'frame_number' telling you which number within photo/depth/instance is applicable to that view.  The view contains both a timestamp and the camera position and lookat positions.

The protobuf also stores instances for each trajectory, with each instance having an 'instance_id'.  This instance_id provides a mapping from the instance information stored in the protobuf and the instances rendered in the instance folder.  If a pixel within the instance/0.png is 1 then at that pixel, the instance within this trajectory with the 'instance_id' of 1 stores all of the relevant information for this object.  That information depends on the 'instance_type', but for everthing except background includes a wordnet id semantic label.

# How to get started with the validation set

* Download the validation set (15GB) and the validation set protobuf file from the [SceneNet RGB-D project page](http://robotvault.bitbucket.org/scenenet-rgbd.html).

* Extract the validation set, to a location on you local machine. To avoid editing more code, you can place it directly within the data directory of this repo data/val, or optionally place it somewhere else, and edit line 4 of the read_protobuf.py file to point towards the folder location.

* This validation folder should contain a single folder 0, with 1,000 folders in it for each of the validation trajectories.

* Copy the protobuf file to data folder of this repo.

* Run make in the root folder of the repo to generate the protobuf description

* Run the read_protobuf.py to print out information about a single trajectory (remove the final break to print our information about them all)

    python3 read_protobuf.py
    
* You should see a print out of the information available for one of the trajectories within the dataset.

# License
GPL. We would like to thank Dyson Technologies Limited for supporting this work.
