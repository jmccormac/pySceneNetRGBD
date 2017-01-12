from PIL import Image
import numpy as np
import os
import pathlib
import random
import scenenet_pb2 as sn

NYU_13_CLASSES = [(0,'Unknown'),
                  (1,'Bed'),
                  (2,'Books'),
                  (3,'Ceiling'),
                  (4,'Chair'),
                  (5,'Floor'),
                  (6,'Furniture'),
                  (7,'Objects'),
                  (8,'Picture'),
                  (9,'Sofa'),
                  (10,'Table'),
                  (11,'TV'),
                  (12,'Wall'),
                  (13,'Window')
]

colour_code = np.array([[0, 0, 0],
                       [0, 0, 1],
                       [0.9137,0.3490,0.1882], #BOOKS
                       [0, 0.8549, 0], #CEILING
                       [0.5843,0,0.9412], #CHAIR
                       [0.8706,0.9451,0.0941], #FLOOR
                       [1.0000,0.8078,0.8078], #FURNITURE
                       [0,0.8784,0.8980], #OBJECTS
                       [0.4157,0.5333,0.8000], #PAINTING
                       [0.4588,0.1137,0.1608], #SOFA
                       [0.9412,0.1373,0.9216], #TABLE
                       [0,0.6549,0.6118], #TV
                       [0.9765,0.5451,0], #WALL
                       [0.8824,0.8980,0.7608]])

NYU_WNID_TO_CLASS = {
    '04593077':4, '03262932':4, '02933112':6, '03207941':7, '03063968':10, '04398044':7, '04515003':7,
    '00017222':7, '02964075':10, '03246933':10, '03904060':10, '03018349':6, '03786621':4, '04225987':7,
    '04284002':7, '03211117':11, '02920259':1, '03782190':11, '03761084':7, '03710193':7, '03367059':7,
    '02747177':7, '03063599':7, '04599124':7, '20000036':10, '03085219':7, '04255586':7, '03165096':1,
    '03938244':1, '14845743':7, '03609235':7, '03238586':10, '03797390':7, '04152829':11, '04553920':7,
    '04608329':10, '20000016':4, '02883344':7, '04590933':4, '04466871':7, '03168217':4, '03490884':7,
    '04569063':7, '03071021':7, '03221720':12, '03309808':7, '04380533':7, '02839910':7, '03179701':10,
    '02823510':7, '03376595':4, '03891251':4, '03438257':7, '02686379':7, '03488438':7, '04118021':5,
    '03513137':7, '04315948':7, '03092883':10, '15101854':6, '03982430':10, '02920083':1, '02990373':3,
    '03346455':12, '03452594':7, '03612814':7, '06415419':7, '03025755':7, '02777927':12, '04546855':12,
    '20000040':10, '20000041':10, '04533802':7, '04459362':7, '04177755':9, '03206908':7, '20000021':4,
    '03624134':7, '04186051':7, '04152593':11, '03643737':7, '02676566':7, '02789487':6, '03237340':6,
    '04502670':7, '04208936':7, '20000024':4, '04401088':7, '04372370':12, '20000025':4, '03956922':7,
    '04379243':10, '04447028':7, '03147509':7, '03640988':7, '03916031':7, '03906997':7, '04190052':6,
    '02828884':4, '03962852':1, '03665366':7, '02881193':7, '03920867':4, '03773035':12, '03046257':12,
    '04516116':7, '00266645':7, '03665924':7, '03261776':7, '03991062':7, '03908831':7, '03759954':7,
    '04164868':7, '04004475':7, '03642806':7, '04589593':13, '04522168':7, '04446276':7, '08647616':4,
    '02808440':7, '08266235':10, '03467517':7, '04256520':9, '04337974':7, '03990474':7, '03116530':6,
    '03649674':4, '04349401':7, '01091234':7, '15075141':7, '20000028':9, '02960903':7, '04254009':7,
    '20000018':4, '20000020':4, '03676759':11, '20000022':4, '20000023':4, '02946921':7, '03957315':7,
    '20000026':4, '20000027':4, '04381587':10, '04101232':7, '03691459':7, '03273913':7, '02843684':7,
    '04183516':7, '04587648':13, '02815950':3, '03653583':6, '03525454':7, '03405725':6, '03636248':7,
    '03211616':11, '04177820':4, '04099969':4, '03928116':7, '04586225':7, '02738535':4, '20000039':10,
    '20000038':10, '04476259':7, '04009801':11, '03909406':12, '03002711':7, '03085602':11, '03233905':6,
    '20000037':10, '02801938':7, '03899768':7, '04343346':7, '03603722':7, '03593526':7, '02954340':7,
    '02694662':7, '04209613':7, '02951358':7, '03115762':9, '04038727':6, '03005285':7, '04559451':7,
    '03775636':7, '03620967':10, '02773838':7, '20000008':6, '04526964':7, '06508816':7, '20000009':6,
    '03379051':7, '04062428':7, '04074963':7, '04047401':7, '03881893':13, '03959485':7, '03391301':7,
    '03151077':12, '04590263':13, '20000006':1, '03148324':6, '20000004':1, '04453156':7, '02840245':2,
    '04591713':7, '03050864':7, '03727837':5, '06277280':11, '03365592':5, '03876519':8, '03179910':7,
    '06709442':7, '03482252':7, '04223580':7, '02880940':7, '04554684':7, '20000030':9, '03085013':7,
    '03169390':7, '04192858':7, '20000029':9, '04331277':4, '03452741':7, '03485997':7, '20000007':1,
    '02942699':7, '03231368':10, '03337140':7, '03001627':4, '20000011':6, '20000010':6, '20000013':6,
    '04603729':10, '20000015':4, '04548280':12, '06410904':2, '04398951':10, '03693474':9, '04330267':7,
    '03015149':9, '04460038':7, '03128519':7, '04306847':7, '03677231':7, '02871439':6, '04550184':6,
    '14974264':7, '04344873':9, '03636649':7, '20000012':6, '02876657':7, '03325088':7, '04253437':7,
    '02992529':7, '03222722':12, '04373704':4, '02851099':13, '04061681':10, '04529681':7,
}

data_root_path = 'data/val'
protobuf_path = 'data/scenenet_rgbd_val.pb'

def instance_path_from_view(render_path,view):
    photo_path = os.path.join(render_path,'instance')
    image_path = os.path.join(photo_path,'{0}.png'.format(view.frame_num))
    return os.path.join(data_root_path,image_path)

def save_class_from_instance(instance_path,class_path, class_NYUv2_colourcode_path, mapping):
    instance_img = np.asarray(Image.open(instance_path))
    class_img = np.zeros(instance_img.shape)
    h,w  = instance_img.shape

    class_img_rgb = np.zeros((h,w,3),dtype=np.uint8)
    r = class_img_rgb[:,:,0]
    g = class_img_rgb[:,:,1]
    b = class_img_rgb[:,:,2]

    for instance, semantic_class in mapping.items():
        class_img[instance_img == instance] = semantic_class
        r[instance_img==instance] = np.uint8(colour_code[semantic_class][0]*255)
        g[instance_img==instance] = np.uint8(colour_code[semantic_class][1]*255)
        b[instance_img==instance] = np.uint8(colour_code[semantic_class][2]*255)

    class_img_rgb[:,:,0] = r
    class_img_rgb[:,:,1] = g
    class_img_rgb[:,:,2] = b

    class_img = Image.fromarray(np.uint8(class_img))
    class_img_rgb = Image.fromarray(class_img_rgb)
    class_img.save(class_path)
    class_img_rgb.save(class_NYUv2_colourcode_path)

if __name__ == '__main__':
    trajectories = sn.Trajectories()
    try:
        with open(protobuf_path,'rb') as f:
            trajectories.ParseFromString(f.read())
    except IOError:
        print('Scenenet protobuf data not found at location:{0}'.format(data_root_path))
        print('Please ensure you have copied the pb file to the data directory')

    traj = random.choice(trajectories.trajectories)
    instance_class_map = {}
    for instance in traj.instances:
        instance_type = sn.Instance.InstanceType.Name(instance.instance_type)
        if instance.instance_type != sn.Instance.BACKGROUND:
            instance_class_map[instance.instance_id] = NYU_WNID_TO_CLASS[instance.semantic_wordnet_id]
    for view in traj.views:
        instance_path = instance_path_from_view(traj.render_path,view)
        print('Converting instance image:{0} to class image'.format(instance_path))
        save_class_from_instance(instance_path,'semantic_class.png','NYUv2.png',instance_class_map)
        print('Breaking early and writing class to semantic_class.png')
        break
