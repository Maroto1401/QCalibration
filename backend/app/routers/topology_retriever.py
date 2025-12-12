from fastapi import APIRouter
from ..retrievers.ibm_retriever import fetch_ibm_topologies


async def fetch_all_topologies() -> dict[str, dict]:
    topologies = {}
    
    # fetch IBM
    ibm_topos = fetch_ibm_topologies()
    print(f"Fetched {len(ibm_topos)} IBM topologies")
    for t in ibm_topos:
        topologies[t["id"]] = t
    ''' 
    # fetch Rigetti
    rigetti_topos = await fetch_rigetti_topologies()
    for t in rigetti_topos:
        topologies[t["id"]] = t

    # fetch Google
    google_topos = await fetch_google_topologies()
    for t in google_topos:
        topologies[t["id"]] = t
'''
    return topologies

router = APIRouter(prefix="", tags=["retriever"])

@router.get("/retrieve-topologies")
async def retrieve_topologies():
    """
    Retrieves available quantum hardware topologies from all vendors.
    """
    print("Retrieving all topologies")
    topologies = await fetch_all_topologies()
    print(f"Total topologies retrieved: {len(topologies)}")
    return topologies

@router.get("/topology/{topology_id}")
async def get_topology(topology_id: str):
    topologies = await fetch_all_topologies()
    for topo in topologies:
        if topo["id"] == topology_id:
            return topo
    return {"error": "Topology not found"}
