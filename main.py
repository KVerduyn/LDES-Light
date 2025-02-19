from fastapi import FastAPI, Request, HTTPException
from rdflib import Graph, URIRef, Literal, BNode, Namespace
import os
from datetime import datetime

app = FastAPI()

PAGE_SIZE = 250
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
rdf_store = []
pages = []

TREE = Namespace("https://w3id.org/tree#")
LDES = Namespace("https://w3id.org/ldes#")
DCTERMS = Namespace("http://purl.org/dc/terms/")
BASE = URIRef("http://localhost:8000/ldes/")
VIEW_NAME = "view_1"  # Vaste naam voor de view

@app.post("/ingest")
async def ingest_rdf(request: Request):
    content_type = request.headers.get('content-type')
    data = await request.body()

    g = Graph()
    try:
        rdf_format = content_type.split('/')[-1]
        if rdf_format == "ld+json":
            rdf_format = "json-ld"

        g.parse(data=data, format=rdf_format)
        print(f"Received {len(g)} triples")  # ✅ Debug print

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse RDF data: {str(e)}")

    objects = extract_objects(g)
    print(f"Extracted {len(objects)} objects")  # ✅ Debug print

    rdf_store.extend(objects)

    print(f"Current buffer size: {len(rdf_store)}")  # ✅ Debug print

    if len(rdf_store) >= PAGE_SIZE:
        print("Calling write_ldes_page()...")  # ✅ Debug print
        await write_ldes_page()

    return {"message": "RDF data ingested successfully."}


def extract_objects(graph):
    objects = []
    for subj in set(graph.subjects()):
        print(f"Processing subject: {subj}")  # ✅ Debug output
        
        if isinstance(subj, URIRef):
            subgraph = Graph()
            for triple in graph.triples((subj, None, None)):
                subgraph.add(triple)
                for obj in graph.objects(subj, None):
                    if isinstance(obj, BNode):
                        for t in graph.triples((obj, None, None)):
                            subgraph.add(t)
            objects.append(subgraph)
    return objects

@app.post("/finalize")
async def finalize_ldes():
    if rdf_store:
        await write_ldes_page(force=True)
        return {"message": "Final page written successfully."}
    return {"message": "No data to finalize."}

async def write_ldes_page(force=False):
    global rdf_store, pages
    if not force and len(rdf_store) < PAGE_SIZE:
        print(f"Buffer size {len(rdf_store)} is too small, waiting for more data...")  # Debug print
        return

    print(f"Writing LDES page with {len(rdf_store[:PAGE_SIZE] if not force else rdf_store)} objects")  # Debug print
    
    page_file = os.path.join(DATA_DIR, "view_1.ttl")
    g = Graph()

    for obj in rdf_store[:PAGE_SIZE] if not force else rdf_store:
        for triple in obj:
            g.add(triple)

    page_uri = BASE + "view_1"
    g.add((page_uri, DCTERMS.created, Literal(datetime.utcnow().isoformat())))
    g.add((page_uri, LDES.EventStream, Literal("LDES Stream Page")))

    if pages:
        prev_page = pages[-1]
        g.add((URIRef(prev_page), TREE.relation, g.resource(None).add(TREE.node, page_uri).add(TREE.type, TREE.NextPageRelation)))

    pages.append(str(page_uri))
    g.serialize(destination=page_file, format="turtle")

    print(f"Page successfully written to {page_file}")  # Debug print
    rdf_store = [] if force else rdf_store[PAGE_SIZE:]


@app.get("/ldes")
async def get_ldes_start():
    g = Graph()
    collection_uri = BASE
    g.add((collection_uri, DCTERMS.created, Literal(datetime.utcnow().isoformat())))
    g.add((collection_uri, LDES.EventStream, Literal("LDES Collection")))
    for page in pages:
        g.add((collection_uri, TREE.view, URIRef(page)))
    return g.serialize(format="turtle")

@app.get("/ldes/{page_id}")
async def get_ldes_page(page_id: str):
    page_file = os.path.join(DATA_DIR, f"{page_id}.ttl")
    if not os.path.exists(page_file):
        raise HTTPException(status_code=404, detail="Page not found")
    with open(page_file, 'r') as f:
        return f.read()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
