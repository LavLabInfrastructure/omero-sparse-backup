from omero.gateway import BlitzGateway
user='mjbarrett'
password='gzyxby01'
host='wss://wsi.lavlab.mcw.edu/api-wss/'
port=443
secure=True

conn = BlitzGateway(user, password, host=host, port=port, secure=secure)
conn.connect()
i=0
for g in conn.getGroupsMemberOf():
    conn.setGroupForSession(g.getId())
    for x in conn.getObjects('image'):
        i+=1
print(i)
conn.close()