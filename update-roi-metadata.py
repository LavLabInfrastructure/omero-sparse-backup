import os
import tempfile

import bioformats
import javabridge

from omero.gateway import BlitzGateway
from tifffile import tiffcomment
from bioformats.omexml import OMEXML, qn

def getRemoteMetadata(img):
    exporter = img._conn.createExporter()

    exporter.addImage(img.getId())
    xml = OMEXML(exporter.read(0, exporter.generateXml()).decode())

    exporter.close()
    return xml


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

    return localPath
    
if __name__ == "__main__":
    conn = BlitzGateway("mjbarrett","gzyxby01",host="wss://wsi.lavlab.mcw.edu/api-wss/",port=443,secure=True)
    conn.connect()
    print(updateMetadata("CMU-orig.tiff", conn.getObject('image',1)))
    conn.close()
    exit(0)
