#
import os

import tifffile
import numpy as np
from bioformats.omexml import OMEXML, qn



from omero.gateway import BlitzGateway
def getRemoteMetadata(img) -> bytes:
    exporter = img._conn.createExporter()
    exporter.addImage(img.getId())
    
    fsize = exporter.generateXml()
    
    xml = exporter.read(0, fsize)
    exporter.close()
    return xml
    # omexml = OMEXML(xml)
    # qname=qn(omexml.ns['ome'],'ROI')
    # print(omexml)
    # return omexml.root_node.findall(qname)

# gen
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
def downloadFull(conn, img, outdir="./"):
    rps = conn.createRawPixelsStore()
    pix = img.getPrimaryPixels()
    rps.setPixelsId(pix.getId(), False)
    tileSize = rps.getTileSize()
    
    # archived images require reconversion for webuse anyway, so worth using larger tiles for speed
    tileSize = (tileSize[0]*4,tileSize[1]*4)

    name=img.getName()
    if name.endswith('.ome.tiff'): name = os.path.splitext(name)[0]
    out = os.path.abspath(os.path.join(outdir, os.path.splitext(name)[0]+".ome.tiff"))
    # write image
    tifffile.imwrite(out, generateRGBTiles(img, tileSize), dtype='uint8', ome=True,
                    shape=(img.getSizeY(),img.getSizeX(),img.getSizeC()), tile=tileSize, 
                    compression='JPEG',compressionargs={"level":100}
                    )
    # write metadata
    tifffile.tiffcomment(out, getRemoteMetadata(img))

    return out

if __name__ == "__main__":
    conn = BlitzGateway("mjbarrett","gzyxby01",host="wss://wsi.lavlab.mcw.edu/api-wss/",port=443,secure=True)
    conn.connect()
    print(downloadFull(conn,conn.getObject('image',1)))
    conn.close()
