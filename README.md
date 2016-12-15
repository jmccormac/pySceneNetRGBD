# pySceneNetRGBD

A set of python3 scripts showing examples of how to navigate and access the data within the SceneNetRGBD dataset.

# Requirements

python3
numpy
PIL
protobuf

# Dataset structure

The dataset consists of two components.  The first component is a set of files organised into trajectory folders.  Each of these folders contains three directorys:

* photo - which contains the photorealistic renders, each of which is named after its frame_num (e.g. 0.jpg is the first pose, 25.jpg the next)
* depth - which contains the accompanying depth information stored as unsigned 16-bit integers.  The units are millimeters.  So a value of 1000 is a meter, and the depth is the euclidean ray length from the camera position to the first point of intersection.
* instance - which contains instances labels for a trajectory also in unsigned 16-bit integers.  Instance 1 is the first object and will be the same through all of the frames within this folder

The second component is a protobuf file.  The definition of this protobuf is given in scenenet.proto.  It stores a list of trajectories, with the 

# How to get started with the validation set

* Download the validation set (15GB) and the validation set protobuf file from the [SceneNet RGB-D project page](http://robotvault.bitbucket.org/scenenet-rgbd.html).

* Extract the validation set, to a location on you local machine. To avoid editing more code, you can place it directly within the data directory of this repo data/val, or optionally place it somewhere else, and edit line 4 of the read_protobuf.py file to point towards the folder location.

* This validation folder should contain a single folder 0, with 1,000 folders in it for each of the validation trajectories.

* Copy the protobuf file to data folder of this repo.

* Run make in the root folder of the repo to generate the protobuf description

* Run the read_protobuf.py to print out information about a single trajectory (remove the final break to print our information about them all)

    python3 read_protobuf.py

# License
GPL. We would like to thank Dyson Technologies Limited for supporting this work.
