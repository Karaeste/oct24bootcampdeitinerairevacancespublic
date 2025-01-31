import fireducks.pandas as pd
import json
import utils.json_helper_functions as helper
import dotenv
import os
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Engine
from typing import List
import psycopg2
from .point_of_interest_helper import Poi

# Chargement des variables d'environnement
dotenv.load_dotenv()


def connect_to_db() -> Engine:
    """
    Connexion à la BDD
    :return: engine : moteur de connexion à la BDD
    """
    engine = create_engine(f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}")
    return engine


def show_tables(engine: create_engine) -> list:
    """
    Permet d'interroger la BDD pour obtenir la liste des tables à fin de tests
    :param engine:
    :return: tables : liste des tables présentes dans la BDD
    """
    db_inspection = inspect(engine)
    tables = db_inspection.get_table_names()
    return tables

def save_dataframe_to_postgres(df: pd.DataFrame, table_name: str, engine: create_engine, if_exists: str='replace'):
    """
    Sauvegarde un DataFrame pandas dans une table PostgreSQL.

    ATTENTION : Le Dataframe doit être formaté avec le même nombre et noms de colonnes

    :param df: pd.DataFrame - Le DataFrame à sauvegarder
    :param table_name: str - Le nom de la table dans laquelle sauvegarder le DataFrame
    :param engine:
    :param if_exists: str - L'action si la table existe {"fail", "replace", "append"}(default: "replace")
    """
    df.to_sql(table_name, engine, if_exists=if_exists, index=False)

def parse_index_datatourisme(index_path:str = "./data/index.json") -> list:
    """
    Parse le fichier index.json pour récupérer les URL des fichiers JSON.

    :param index_path:str - Le chemin du fichier d'index (default: "../data/index.json")
    :return: list - La liste des URL des fichiers JSON
    """
    with open(index_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    urls = []
    for item in data:
        urls.append("data/objects/"+item["file"])
    return urls

def collect_region_information_from_files(urls: list) -> pd.DataFrame:
    """
    Collecte les informations des points d'intérêt à partir des fichiers JSON.

    :param urls: list - La liste des URL des fichiers JSON
    :return: pd.DataFrame - Le DataFrame contenant les informations des points d'intérêt
    """
    data = []
    for url in urls:
        poi_region_id, poi_region_name = helper.get_poi_region(url)
        data.append([poi_region_id, poi_region_name])
    # On crée un dataframe pour stocker les résultats
    region_df = pd.DataFrame(data, columns=["dt_region_id", "name"])
    return region_df

def collect_department_information_from_files(urls: list) -> pd.DataFrame:
    """
    Collecte les informations concernant les département des points d'intérêt à partir des fichiers JSON.

    :param urls: list - La liste des URL des fichiers JSON
    :return: pd.DataFrame - Le DataFrame contenant les informations des points d'intérêt
    """
    data = []
    for url in urls:
        poi_departement_id, poi_departement_name = helper.get_poi_department(url)
        poi_region_id, poi_region_name = helper.get_poi_region(url)
        data.append([poi_departement_id, poi_region_id, poi_departement_name])
    # On crée un dataframe pour stocker les résultats
    department_df = pd.DataFrame(data, columns=["dt_departement_id", "dt_region_id", "name"])

    return department_df

def collect_city_information_from_files(urls: list) -> pd.DataFrame:
    """
    Collecte les informations des points d'intérêt à partir des fichiers JSON.

    :param urls: list - La liste des URL des fichiers JSON
    :return: pd.DataFrame - Le DataFrame contenant les informations des points d'intérêt
    """
    data = []
    for url in urls:
        # Récuperation de l'ID de la ville et de son nom
        poi_city_id, poi_city_name = helper.get_poi_city(url)
        # Récupération du département de la ville
        poi_departement_id, poi_department_name = helper.get_poi_department(url)
        data.append([poi_city_id, poi_departement_id, poi_city_name])
    # On crée un dataframe pour stocker les résultats
    city_df = pd.DataFrame(data, columns=["dt_city_id","dt_departement_id","name"])
    # Et on supprime les doublons
    city_df = city_df.drop_duplicates()
    return city_df

def collect_all_categories(urls: list) -> pd.DataFrame:
    """
    Remplissage de la table Category à partir du fichier ontology.TTL
    :param urls: list - La liste des URL des fichiers JSON
    :return: pd.DataFrame - Le DataFrame contenant la liste des catégories à insérer dans la table Category
    """
    # On récupère les catégories de POI et on les ajoute à un set
    # pour s'assurer de leur unicité
    # Si on récupère une liste, on l'eclate et on ajoute chaque élément un à un dans le set

    categories = set()
    for url in urls:
        poi_category = helper.get_poi_category(url)
        if isinstance(poi_category, list):
            for category in poi_category:
                categories.add(category)
        else:
            categories.add(poi_category)

    # Transformation du set en DataFrame
    category_df = pd.DataFrame(categories, columns=["name"])
    return category_df

def connect_to_db_V2(dbname, user, password, host, port):
    """
    Crée une connexion à la base de données PostgreSQL.
    """
    return psycopg2.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port)

def connect_to_db_from_env():
    """
    Crée une connexion à la base de données PostgreSQL.
    """
    return psycopg2.connect(
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        host=os.environ["POSTGRES_HOST"],
        port=os.environ["POSTGRES_PORT"])

def get_all_pois_from_db(conn) -> List[Poi]:
    """
    Récupère tous les POIs de la base de données.

    :param
        conn: Connexion à la base de données PostgreSQL.

    :return
        List[Poi]: Liste des objets Poi.
    """
    query = """
    SELECT * FROM Point_Of_Interest AS poi
    """
    with conn.cursor() as cursor:
      cursor.execute(query)
      return _pois_query(cursor)


def select_pois_from_db(conn, category: str) -> List[Poi]:
  """
  Récupère tous les POIs de la base de données pour une catégorie.

  :param
      conn: Connexion à la base de données PostgreSQL.
      category: Catégorie des POIs à sélectionner.

  :return
      List[Poi]: Liste des objets Poi.
  """
  query = """
    SELECT poi.* FROM Point_Of_Interest AS poi
    LEFT JOIN category_point_of_interest cpoi on poi.dt_poi_id = cpoi.dt_poi_id
    LEFT JOIN category on cpoi.dt_category_id = category.dt_category_id
    WHERE category.name = %s
    """
  with conn.cursor() as cursor:
    cursor.execute(query, (category,))
    return _pois_query(cursor)


def _pois_query(cursor) -> List[Poi]:
  pois = []
  results = cursor.fetchall()
  for row in results:
    # Extraire les informations
    poi_id, osm_node_id, name, rating, created_at, updated_at, latitude, longitude, postal_code, city = row

    if isinstance(city, str):
            try:
                city = json.loads(city)  # Si c'est une chaîne JSON, la désérialiser
            except json.JSONDecodeError:
                city = None
    # Créer une instance de la classe Poi
    poi = Poi(
      id=poi_id,
      name=name,
      rating=rating,
      created_at=created_at,
      updated_at=updated_at,
      latitude=latitude,
      longitude=longitude,
      postal_code=postal_code,
      city=city,
      categories=[],
      osm_node_id=osm_node_id
    )
    pois.append(poi)
  return pois


def add_poi_to_db(conn, poi: Poi):
    """
    Ajoute un POI dans la base de données.

    :param
        conn: Connexion à la base de données PostgreSQL.
        poi (Poi): POI à ajouter.
    """
    with conn.cursor() as cursor:
        # Vérifier ou insérer la région
        cursor.execute(
            "INSERT INTO region (dt_region_id, name) VALUES (%s, %s) ON CONFLICT (dt_region_id) DO NOTHING",
            (poi.city.departement.region.id, poi.city.departement.region.name)
        )
        # Vérifier ou insérer le département
        cursor.execute(
            "INSERT INTO departement (dt_departement_id, name, dt_region_id) VALUES (%s, %s, %s) ON CONFLICT (dt_departement_id) DO NOTHING",
            (poi.city.departement.id, poi.city.departement.name, poi.city.departement.region.id)
        )
        # Vérifier ou insérer la ville
        cursor.execute(
            "INSERT INTO city (dt_city_id, name, dt_departement_id) VALUES (%s, %s, %s) ON CONFLICT (dt_city_id) DO NOTHING",
            (poi.city.id, poi.city.name, poi.city.departement.id)
        )
        # Insérer le POI
        cursor.execute(
            """
            INSERT INTO point_of_interest (
                dt_poi_id, name, rating, dt_created_at, dt_updated_at,
                latitude, longitude, postal_code, dt_city_id, osm_node_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (dt_poi_id) DO NOTHING
            """,
            (
                poi.id, poi.name, poi.rating, poi.created_at, poi.updated_at,
                poi.latitude, poi.longitude, poi.postal_code, poi.city.id, poi.osm_node_id
            )
        )
        # Insérer les catégories
        for category in poi.categories:
            cursor.execute(
                """
                INSERT INTO category (name)
                VALUES (%s)
                ON CONFLICT (name) DO NOTHING
                RETURNING dt_category_id
                """,
                (category.name,)
            )
            result = cursor.fetchone()

            if result:
                category_id = result[0]  # ID retourné si l'insertion réussit
            else:
                # Rechercher l'ID existant si la catégorie était déjà présente
                cursor.execute(
                    "SELECT dt_category_id FROM category WHERE name = %s",
                    (category.name,)
                )
                category_id = cursor.fetchone()[0]  # Récupérer l'ID inséré

            # Lier le POI à la catégorie
            cursor.execute(
                """
                INSERT INTO category_point_of_interest (dt_poi_id, dt_category_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
                """,
                (poi.id, category_id)
            )
        conn.commit()


def update_poi_in_db(conn, poi: Poi):
    """
    Met à jour un POI dans la base de données.

    :param
        conn: Connexion à la base de données PostgreSQL.
        poi (Poi): POI à mettre à jour.
    """
    with conn.cursor() as cursor:
        # Mettre à jour le POI
        cursor.execute(
            """
            UPDATE point_of_interest
            SET name = %s, rating = %s, dt_created_at = %s, dt_updated_at = %s,
                latitude = %s, longitude = %s, postal_code = %s, dt_city_id = %s, osm_node_id = %s
            WHERE dt_poi_id = %s
            """,
            (
                poi.name, poi.rating, poi.created_at, poi.updated_at,
                poi.latitude, poi.longitude, poi.postal_code, poi.city.id, poi.osm_node_id, poi.id
            )
        )
        # Mettre à jour les catégories
        cursor.execute(
            "DELETE FROM category_point_of_interest WHERE dt_poi_id = %s",
            (poi.id,)
        )
        for category in poi.categories:
            cursor.execute(
                "SELECT dt_category_id FROM category WHERE name = %s",
                (category.name,)
            )
            result = cursor.fetchone()

            if result:
                category_id = result[0]  # Récupérer l'ID si la catégorie existe déjà
            else:
                # Insérer la catégorie si elle n'existe pas et récupérer l'ID
                cursor.execute(
                    "INSERT INTO category (name) VALUES (%s) RETURNING dt_category_id",
                    (category.name,)
                )
                category_id = cursor.fetchone()[0]  # Récupérer l'ID inséré
            cursor.execute(
                """
                INSERT INTO category_point_of_interest (dt_poi_id, dt_category_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
                """,
                (poi.id, category_id)
            )
        conn.commit()

def process_batch(pois: List[Poi], type: str, dbname, user, password, host, port):
    """
    Fonction pour mettre à jour/insérer créer un batch de POIs dans la base de données.

    Args:
        pois (List[Poi]): Liste des POIs à mettre à jour/insérer.
        type (str): type d'action sur la base de donné "update" pour modifier et "insert" pour insérer
    """
    engine = connect_to_db_V2(dbname, user, password, host, port)
    if type == "update":
        for poi in pois:
            update_poi_in_db(engine, poi)
    if type == "insert":
        for poi in pois:
            add_poi_to_db(engine, poi)
    engine.close()