# ncbi_mesh_parser

This is a simple project to parse the [NCBI MeSH xml file descDDDD.gz](https://nlmpubs.nlm.nih.gov/projects/mesh/MESH_FILES/xmlmesh/).

## Usage

```python
from ncbi_mesh_parser.desc_parser import parse_mesh

async def mesh_xml_to_ndjson(xmlfile: str) -> str:
    generator = parse_mesh(xmlfile)
    numlines = 0
    with open("mesh.ndjson", "w") as f:
        for record in generator:
            numlines += 1
            f.write(record.json() + "\n")

if __name__=="__main__":
    asyncio.run(mesh_xml_to_ndjson(XMLFILENAME))
```

Note that `parse_mesh` is implemented as a low-memory-requiring generator. 

# Thanks

The code in this repo is adapted from 
[this gist](https://gist.github.com/spock/67cc995b765573a8a8dac3a815806d01) to a poetry project
and utilizes pydantic classes rather than regular python
classes. 