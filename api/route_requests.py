from fastapi import FastAPI, HTTPException
from utils import connect_to_db_from_env, connect_to_neo4j


async def get_route(start_poi_id: str, end_poi_id: str, category: str):
  query = """
    MATCH (startCluster:Cluster {category: $category})-[v1:VICINITY]->(startPoi:POI {id: $start_poi_id}),
          (endCluster:Cluster {category: $category})-[v2:VICINITY]->(endPoi:POI {id: $end_poi_id})

    MATCH path = shortestPath((startCluster)-[:ROUTE*]-(endCluster))

    WITH nodes(path) AS clustersInPath
    UNWIND clustersInPath AS cluster
    MATCH (cluster)-[:VICINITY]->(poi:POI)
    WITH cluster, collect(poi.id) AS poiIds
    WITH collect(poiIds) AS poiIdsAlongPath
    RETURN poiIdsAlongPath
    ORDER BY size(poiIdsAlongPath) ASC
    LIMIT 1;
    """
  with connect_to_neo4j() as driver:
    if not driver:
      raise HTTPException(status_code=500, detail="Failed to connect to Neo4j")
    try:
      with driver.session() as session:
        result = session.run(
          query,
          start_poi_id=start_poi_id,
          end_poi_id=end_poi_id,
          category=category,
        )
        record = result.single()
        if not record:
          raise HTTPException(status_code=404, detail="No path found")
        return record["poiIdsAlongPath"]
    except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))
