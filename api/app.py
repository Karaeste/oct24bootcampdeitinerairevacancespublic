from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from utils import connect_to_db_from_env, connect_to_neo4j
import route_requests as rr
import psycopg2

app = FastAPI(
  title="API Itinéraire de vacances",
  description="API pour le calcul d'un itinéraire entre POI selon une catégorie et une localisation donnée",
  version="1.0.0"
)

@app.get("/")
def read_root():
  return {"message": "API Itineraire de Vacances", "code": "200"}

app.mount("/demo", StaticFiles(directory="/app/demo"), name="demo")

@app.get("/db_health")
def db_service_health():
  try:
    conn = connect_to_db_from_env()
    return {"message": "PostgreSQL is UP", "code": 200}
  except(Exception, psycopg2.Error) as error:
    return {"status": error, "code": 500}


@app.get("/count_poi")
def count_point_of_interest():
  conn = connect_to_db_from_env()
  cursor = conn.cursor()
  cursor.execute("SELECT COUNT(*) FROM point_of_interest")
  record = cursor.fetchone()
  conn.close()
  return {"count": record[0], "code": 200}


@app.get(
  "/clustered_categories",
  summary="List Categories with Associated Clusters",
  description="This endpoint returns a list of categories with their associated clusters and route counts."
)
def list_categories_with_associated_clusters():
  """
  Returns a list of categories with their associated clusters and route counts.
  - **category**: The category name.
  - **clusterCount**: The number of clusters associated with the category.
  - **routeCount**: The number of routes associated with the category.
  """
  with connect_to_neo4j() as driver:
    with driver.session() as session:
      result = session.run('''
        MATCH (c:Cluster)
        WITH c.category AS category, COUNT(c) AS clusterCount
        MATCH (c)-[r:ROUTE]->(c2)
        WHERE c.category = c2.category AND c.category = category
        RETURN category, clusterCount, COUNT(r) AS routeCount
        ''')
      return [dict(r) for r in result]


class RouteRequest(BaseModel):
  start_poi_id: str
  end_poi_id: str
  category: str


@app.post(
  "/route",
  response_model=List[List[str]],
  summary="Get Route Between Points of Interest",
  description="This endpoint calculates and returns a route between two points of interest based on a given category.")
async def get_route(request: RouteRequest):
  """
  Calculates and returns a route between two points of interest (POI) based on a given category.
  - **start_poi_id**: The ID of the starting POI.
  - **end_poi_id**: The ID of the destination POI.
  - **category**: The category of the POIs.
  - **response**: A list of routes, where each route is a list of POI IDs.
  """
  return await rr.get_route(request.start_poi_id, request.end_poi_id, request.category)


class FindCityRequest(BaseModel):
  category: str
  query: str


@app.post("/find_cities")
async def find_poi(request: FindCityRequest):
  with connect_to_db_from_env() as conn:
    cursor = conn.cursor()
    cursor.execute("""
    SELECT DISTINCT city.name FROM Point_Of_Interest AS poi
    LEFT JOIN category_point_of_interest cpoi on poi.dt_poi_id = cpoi.dt_poi_id
    LEFT JOIN category on cpoi.dt_category_id = category.dt_category_id
    LEFT JOIN city on poi.dt_city_id = city.dt_city_id
    WHERE city.name LIKE %s and category.name=%s
""", (f'{request.query}%', request.category))
    return [city for row in cursor.fetchall() for city in row]


class FindPoiRequest(BaseModel):
  city: str
  category: str


@app.post("/find_poi")
async def find_poi(request: FindPoiRequest):
  with connect_to_db_from_env() as conn:
    cursor = conn.cursor()
    cursor.execute("""
    SELECT poi.* FROM Point_Of_Interest AS poi
    LEFT JOIN category_point_of_interest cpoi on poi.dt_poi_id = cpoi.dt_poi_id
    LEFT JOIN category on cpoi.dt_category_id = category.dt_category_id
    LEFT JOIN city on poi.dt_city_id = city.dt_city_id
    WHERE city.name=%s and category.name=%s
""", (request.city, request.category))
    record = cursor.fetchone()
    return record[0]


@app.get("/poi")
async def get_poi(id: str):
  with connect_to_db_from_env() as conn:
    cursor = conn.cursor()
    cursor.execute("""
    SELECT poi.dt_poi_id, poi.name, poi.postal_code, city.name, poi.latitude, poi.longitude FROM Point_Of_Interest AS poi
    LEFT JOIN city on poi.dt_city_id = city.dt_city_id
    WHERE poi.dt_poi_id = %s
""", (id,))
    record = cursor.fetchone()
    if not record:
      raise HTTPException(status_code=404, detail="POI not found")
    return {
      "id": record[0],
      "name": record[1],
      "postal_code": record[2],
      "city": record[3],
      "latitude": record[4],
      "longitude": record[5]
    }

