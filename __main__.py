import os

import numpy as np
from tifffile import tiffcomment, imwrite

from bioformats.omexml import OMEXML
from omero.gateway import BlitzGateway

def getRemoteMetadata(img):
    exporter = img._conn.createExporter()

    exporter.addImage(img.getId())
    xml = OMEXML(exporter.read(0, exporter.generateXml()).decode())

    exporter.close()
    return xml

def generateRGBTiles(img, tileSize=None):
    # generate tile list (z,c,t,(x,y,w,h))
    pix = img.getPrimaryPixels()
    size_x = img.getSizeX() 
    size_y = img.getSizeY()
    size_z = img.getSizeZ()
    size_t = img.getSizeT()
    size_c = img.getSizeC()

    if tileSize == None: tileSize = img._re.getTileSize()
    width, height = tileSize

    tileList=[]
    # generate tile list (not compatible with omero tileutils)
    for z in range(size_z):
        for t in range(size_t):
            for y in range(0, size_y, height):
                width, height = tileSize # reset tilesize
                # if tileheight is greater than remaining pixels, get remaining pixels
                if size_y-y < height: height = size_y-y
                for x in range(0, size_x, width):
                # if tilewidth is greater than remaining pixels, get remaining pixels
                    if size_x-x < width: width = size_x-x
                    for c in range(size_c): tileList.append((z,c,t,(x,y,width,height)))

    # gather tiles
    c=0
    tile = np.zeros((height, width, size_c))
    for tileChannel in pix.getTiles(tileList):
    # for i, tileChannel in enumerate(pix.getTiles(tileList)):
        if tileChannel.shape != tile.shape[:-1]:
            tile = np.zeros((tileChannel.shape[0], tileChannel.shape[1], size_c))
        tile[..., c] = tileChannel
        c+=1
        if c == size_c:  
            c=0  
            yield tile.astype(np.uint8)

# downloads a full res, single layer omero image from an id
def downloadFull(conn, img, out):
    rps = conn.createRawPixelsStore()
    pix = img.getPrimaryPixels()
    rps.setPixelsId(pix.getId(), False)
    tileSize = rps.getTileSize()
    
    # archived images require reconversion for webuse anyway, so worth using larger tiles for speed
    tileSize = (tileSize[0]*4,tileSize[1]*4)

    # write image
    imwrite(out, generateRGBTiles(img, tileSize), dtype='uint8', ome=True,
                    shape=(img.getSizeY(),img.getSizeX(),img.getSizeC()), tile=tileSize, 
                    compression='JPEG',compressionargs={"level":100}
                    )
    # write metadata
    tiffcomment(out, getRemoteMetadata(img))
    return out


def updateMetadata(localPath: str, img):
    """
    Updates ome.xml metadata (including ROIs) for given local omero copy. 
    localPath: String path to local copy of img
    img: omero.model.ImageI representing omero copy of localPath
    """
    localPath=os.path.abspath(localPath)
    # get xml objects
    localXml=tiffcomment(localPath)
    remoteXml=getRemoteMetadata(img).decode()
    # if not equivilent update the local xml
    if localXml != remoteXml:
        tiffcomment(localXml, remoteXml)

def main(conn, outdir):
    try:
        print(conn.connect())
        for group in conn.getGroupsMemberOf():
            group_name=group.getName()
            group_dir=os.path.join(outdir, group_name)
            os.makedirs(group_dir, exist_ok=True)
            conn.setGroupForSession(group.getId())
                
            for project in conn.getObjects('project'):
                project_name=project.getName()
                project_dir=os.path.join(group_dir, project_name)
                os.makedirs(project_dir, exist_ok=True)
                for dataset in conn.getObjects('dataset',opts={'project':project.getId()}):
                    dataset_name=dataset.getName()
                    dataset_dir=os.path.join(project_dir, dataset_name)
                    os.makedirs(dataset_dir, exist_ok=True)
                    for image in conn.getObjects('image',opts={'dataset':dataset.getId()}):
                        image_id=image.getId()
                        image_name=image.getName()
                        # has ome.xml metadata, so it's an ome.tiff
                        if not image_name.endswith('.ome.tiff'): 
                            image_name = os.path.splitext(image_name)[0]+".ome.tiff"
                        image_path = os.path.abspath(
                            os.path.join(dataset_dir, f"{image_id}_{image_name}"))
                        print(image_path)
                        if os.path.exists(image_path):
                            updateMetadata(image_path, image)
                        else:
                            downloadFull(conn,image,image_path)

    finally:
        conn.close()
    

#TODO get variables from environment
# server details
user='mjbarrett'
password='gzyxby01'
host='wss://wsi.lavlab.mcw.edu/api-wss/'
port=443
secure=True
# archive details
outdir=os.path.abspath('./archive')

conn = BlitzGateway(user, password, host=host, port=port, secure=secure)
main(conn, outdir)