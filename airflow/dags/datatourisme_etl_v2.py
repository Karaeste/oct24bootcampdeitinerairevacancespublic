import os
import uuid
import json
import redis
import logging
import datetime
from datetime import timedelta
import psycopg2
from typing import List
from airflow import DAG
from airflow.decorators import task
from airflow.models import Variable
from airflow.utils.trigger_rule import TriggerRule
from airflow.utils.dates import days_ago
from utils import *
import neo4j as neo4j
from parts.clusters import create_cluster_tasks

# Variables Airflow
CUR_DIR = os.path.abspath(os.path.dirname(__file__))
POSTGRES_HOST = Variable.get("POSTGRES_HOST")
POSTGRES_PORT = Variable.get("POSTGRES_PORT")
POSTGRES_USER = Variable.get("POSTGRES_USER")
POSTGRES_PASSWORD = Variable.get("POSTGRES_PASSWORD")
POSTGRES_DB = Variable.get("POSTGRES_DB")
POSTGRES_DATATOURISME_DB = Variable.get("POSTGRES_DATATOURISME_DB")
REDIS_HOST = Variable.get("REDIS_HOST")
REDIS_PORT = Variable.get("REDIS_PORT")
URL_ARCHIVE = Variable.get("URL_ARCHIVE")
NEO4J_USER = Variable.get("NEO4J_USER")
NEO4J_PASSWORD = Variable.get("NEO4J_PASSWORD")
NEO4J_URL = Variable.get("NEO4J_URL")
DOWNLOAD_PATH = "./raw_archive"
ZIP_PATH = "./raw_archive/archive.zip"

def get_redis_client():
    """
    Retourne un client Redis.
    """
    return redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=0)


with DAG(
    "datatourisme_etl_v2",
    description="ETL DataTourisme avec Redis, PostgreSQL, et traitement par lots dynamiques",
    schedule_interval=timedelta(days=1),
    start_date=days_ago(2),
    #start_date=datetime.datetime(2024, 12, 8),
    catchup=False,
    max_active_runs=1,
) as dag:

    @task(task_id="check_postgres_service")
    def check_postgres_service() -> bool:
        """
        Vérification si il est possible de se connecter au service postgres
        
        :return: 
            bool
        """
        try:
            connection = psycopg2.connect(
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
                dbname=POSTGRES_DB,
            )
            connection.close()
            return True
        except Exception as e:
            logging.error(f"Erreur de connexion à PostgreSQL : {e}")
            return False

    @task(task_id="check_database")
    def check_database() -> bool:
        """
        Vérification si la base de donnée datatourisme est présente sur postgres

        :return: 
            bool
        """
        try:
            connection = psycopg2.connect(
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
                dbname=POSTGRES_DB,
            )
            connection.autocommit = True
            cursor = connection.cursor()
            cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{POSTGRES_DATATOURISME_DB}'")
            exists = cursor.fetchone() is not None
            cursor.close()
            connection.close()
            return exists
        except Exception as e:
            logging.error(f"Erreur lors de la vérification de la base de données : {e}")
            return False

    @task.branch(task_id="decide_database_creation")
    def decide_database_creation(database_exists: bool) -> str:
        """
        Décide de la prochaine étape:
            - Si la base de donnée datatourisme est présente sur postgres on passe à l'étape de vérification de la présence des tables dans la base de donnée
            - Si la base de donnée datatourisme n'est pas présente sur postgres on passe à l'étape de création de la base de donnée datatourisme avant l'étape de vérification de la présence des tables dans la base de donnée
        
        :param: 
            database_exists: bool - La base de donnée est présente ou non
        
        :return: 
            str - "check_tables" si la base de donnée datatourisme est présente ou "create_database" Si la base de donnée datatourisme n'est pas présente
        """
        if database_exists:
            return "check_tables"
        else:
            return "create_database"

    @task(task_id="create_database")
    def create_database() -> None:
        """
        Création de la base de donnée datatourisme
        """
        try:
            connection = psycopg2.connect(
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
                dbname=POSTGRES_DB,
            )
            connection.autocommit = True
            cursor = connection.cursor()
            cursor.execute(f"CREATE DATABASE {POSTGRES_DATATOURISME_DB}")
            cursor.close()
            connection.close()
            logging.info("Base de données créée avec succès !")
        except Exception as e:
            logging.error(f"Erreur lors de la création de la base de données : {e}")

    @task(task_id="check_tables", trigger_rule=TriggerRule.ONE_SUCCESS)
    def check_tables() -> bool:
        """
        Vérification de la présence des tables dans la base de donnée

        :return: 
            bool
        """
        try:
            connection = psycopg2.connect(
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
                dbname=POSTGRES_DATATOURISME_DB,
            )
            connection.autocommit = True
            cursor = connection.cursor()

            tables = ["point_of_interest", "category_point_of_interest", "category", "city", "departement", "region"]
            existing_tables = []
            for table in tables:
                cursor.execute(f"SELECT 1 FROM information_schema.tables WHERE table_name = '{table}'")
                if cursor.fetchone():
                    existing_tables.append(table)

            cursor.close()
            connection.close()
            return len(existing_tables) == len(tables)
        except Exception as e:
            logging.error(f"Erreur lors de la vérification des tables : {e}")
            return False

    @task.branch(task_id="decide_table_creation")
    def decide_table_creation(tables_exist: bool) -> str:
        """
        Décide de la prochaine étape:
            - Si les tables sont présentes dans la base de donnée on passe à l'étape de récupération des Pois dans la base de donnée
            - Si les tables ne sont pas présentes dans la base de donnée on passe à l'étape de création des tables dans la base de donnée

        :param: 
            tables_exist: bool - La tables sont présentes ou non

        :return: 
            str - "check_all_tables_available" si les tables sont présentes dans la base de donnée, "create_tables" si les tables ne sont pas présentes dans la base de donnée
        """
        if tables_exist:
            return "check_all_tables_available"
        else:
            return "create_tables"

    @task(task_id="create_tables")
    def create_tables() -> None:
        """
        Création des tables dans la base de donnée
        """
        try:
            connection = psycopg2.connect(
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
                dbname=POSTGRES_DATATOURISME_DB,
            )
            connection.autocommit = True
            cursor = connection.cursor()
            with open(f"{CUR_DIR}/sql/create_tables.sql", "r") as sql_file:
                cursor.execute(sql_file.read())
            cursor.close()
            connection.close()
            logging.info("Tables créées avec succès !")
        except Exception as e:
            logging.error(f"Erreur lors de la création des tables : {e}")

    @task(task_id="download_archive")
    def download_archive() -> None:
        """
        Téléchargement de l'archive depuis datatourisme
        """
        archive = download_datatourisme_archive(url = URL_ARCHIVE, download_path=DOWNLOAD_PATH)
        if not archive:
            raise

    @task(task_id="get_all_poi_metadata_from_archive")
    def get_all_poi_metadata_from_archive() -> str:
        """
        Récupération des métadata des Pois depuis l'archive datatourisme

        :return: 
            str - clé redis
        """
        redis_client = get_redis_client()
        poi_metadata_list = get_all_poi_metadata(ZIP_PATH)
        redis_key = f"metadata_{uuid.uuid4()}"
        redis_client.set(redis_key, json.dumps([PoiMetadata.to_dict(metadata) for metadata in poi_metadata_list]))
        return redis_key


    @task(task_id="get_all_poi_from_archive")
    def get_all_poi_from_archive(metadata_redis_key: str) -> str:
        """
        Récupération des Pois depuis l'archive datatourisme grace au metadata des Pois

        :param: 
            metadata_redis_key: str - clé redis des metadata

        :return: 
            str - clé redis
        """
        redis_client = get_redis_client()
        metadata_data = json.loads(redis_client.get(metadata_redis_key))
        poi_metadata_objects = [PoiMetadata.from_dict(item) for item in metadata_data]
        pois = parse_poi_batch(ZIP_PATH, poi_metadata_objects)
        redis_key = f"pois_{uuid.uuid4()}"
        redis_client.set(redis_key, json.dumps([Poi.to_dict(poi) for poi in pois]))
        return redis_key
        

    @task(task_id="download_shape")
    def download_shape(**kwargs) -> None:
        """
        Téléchargment de la forme de la France
        """
        task_instance = kwargs['ti']
        path_shape_file, path_to_delete = download_and_get_shapefile()
        task_instance.xcom_push(key="path_shape_file", value=path_shape_file)
        task_instance.xcom_push(key="path_to_delete", value=path_to_delete)


    @task(task_id="get_france_poi")
    def get_france_poi(pois_redis_key: str, **kwargs) -> str:
        """
        Récupération des Pois présent en France uniquement

        :param: 
            urls: pois_redis_key: str - clé redis des pois

        :return: 
            str - clé redis des Pois en France
        """
        task_instance = kwargs['ti']
        path_shape_file = task_instance.xcom_pull(task_ids="download_shape", key="path_shape_file")
        shape_geometry = get_france_geometry(path_shape_file)
        redis_client = get_redis_client()
        pois = json.loads(redis_client.get(pois_redis_key))
        pois = [Poi.from_dict(poi) for poi in pois]
        pois = filter_poi_in_france(pois, shape_geometry)
        redis_key = f"pois_{uuid.uuid4()}"
        redis_client.set(redis_key, json.dumps([Poi.to_dict(poi) for poi in pois]))
        return redis_key

    @task(task_id="check_all_tables_available", trigger_rule=TriggerRule.ONE_SUCCESS, retries=3, retry_delay=datetime.timedelta(seconds=10))
    def check_all_tables_available():
        """
        Vérifications si toutes les tables sont présentes dans la base de donnée datatourisme
        """
        try:
            connection = psycopg2.connect(
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
                dbname=POSTGRES_DATATOURISME_DB,
            )
            cursor = connection.cursor()

            # Liste des tables attendues
            tables = ["point_of_interest", "category_point_of_interest", "category", "city", "departement", "region"]
            missing_tables = []

            # Vérification de la présence de chaque table
            for table in tables:
                cursor.execute(f"SELECT 1 FROM information_schema.tables WHERE table_name = '{table}'")
                if not cursor.fetchone():
                    missing_tables.append(table)

            cursor.close()
            connection.close()

            if missing_tables:
                logging.error(f"Les tables suivantes sont manquantes : {', '.join(missing_tables)}")
                raise ValueError(f"Les tables suivantes sont manquantes : {', '.join(missing_tables)}")

            logging.info("Toutes les tables sont disponibles.")
            return True

        except Exception as e:
            logging.error(f"Erreur lors de la vérification des tables : {e}")
            raise

    @task(task_id="get_all_poi_from_db")
    def get_all_poi_from_db() -> str:
        """
        Récupération de tous les Pois depuis la base de donnée datatourisme

        :return: 
            str - clé redis des Pois dans la base de donnée
        """
        engine = connect_to_db_V2(host=POSTGRES_HOST,
                port=POSTGRES_PORT,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
                dbname=POSTGRES_DATATOURISME_DB,)
        db_pois = get_all_pois_from_db(engine)
        redis_client = get_redis_client()
        redis_key = f"pois_{uuid.uuid4()}"
        redis_client.set(redis_key, json.dumps([Poi.to_dict(poi) for poi in db_pois]))
        return redis_key

    @task(task_id="compare_archive_pois_with_db")
    def compare_archive_pois_with_db(pois_redis_key: str, db_pois_redis_key: str, **kwargs):
        """
        Compare les Pois présent dans la base de donnée datatourisme et ce de l'archive afin de ne garder que les Pois a créé et a modifié

        :param: 
            pois_redis_key: str - clé redis des Pois de l'archive
            db_pois_redis_key: str - clé redis des Pois dans la base de donnée
        """
        task_instance = kwargs['ti']
        redis_client = get_redis_client()
        
        # Récupérer les POIs depuis Redis
        pois_data = redis_client.get(pois_redis_key)
        if not pois_data:
            logging.error(f"Erreur : Les données pour {pois_redis_key} sont vides ou inexistantes.")
            return

        try:
            pois = json.loads(pois_data)
            pois = [Poi.from_dict(poi) for poi in pois]
        except json.JSONDecodeError as e:
            logging.error(f"Erreur lors de la désérialisation des POIs depuis Redis pour {pois_redis_key}: {str(e)}")
            return

        # Récupérer les POIs de la base de données depuis Redis
        db_pois_data = redis_client.get(db_pois_redis_key)
        if not db_pois_data:
            logging.error(f"Erreur : Les données pour {db_pois_redis_key} sont vides ou inexistantes.")
            return

        try:
            db_pois = json.loads(db_pois_data)
            
            # Vérifier si les données sont sous forme de liste, sinon loguer l'erreur
            if not isinstance(db_pois, list):
                logging.error(f"Erreur : Les données pour {db_pois_redis_key} ne sont pas une liste valide.")
                return
            
            db_pois = [Poi.from_dict(poi) for poi in db_pois]
        except json.JSONDecodeError as e:
            logging.error(f"Erreur lors de la désérialisation des POIs de la base de données : {str(e)}")
            return

        # Comparer les POIs de la base de données avec les POIs de l'archive
        pois_to_create, pois_to_update = compare_pois(db_pois, pois)
        # Enregistrer les POIs à créer et à mettre à jour dans Redis
        redis_key_pois_to_create = f"pois_{uuid.uuid4()}"
        redis_client.set(redis_key_pois_to_create, json.dumps([Poi.to_dict(poi) for poi in pois_to_create]))

        redis_key_pois_to_update = f"pois_{uuid.uuid4()}"
        redis_client.set(redis_key_pois_to_update, json.dumps([Poi.to_dict(poi) for poi in pois_to_update]))

        # Sauvegarder les clés dans XCom pour le traitement suivant
        task_instance.xcom_push(key="pois_to_create_key", value=redis_key_pois_to_create)
        task_instance.xcom_push(key="pois_to_update_key", value=redis_key_pois_to_update)


    @task(task_id="create_batches")
    def create_batches(action: str, batch_size: int=10000, **kwargs) -> List[str] :
        """
        Création des batch de Pois

        :param:
            action: str - L'action liée au batch
            batch_size: int - Taille des batch par défaut 10000
        
        :return: 
            List[str] - Liste de clé redis des batch
        """
        task_instance = kwargs['ti']
        if action == "insert":
            redis_key = task_instance.xcom_pull(task_ids="compare_archive_pois_with_db", key="pois_to_create_key")
        else:
            redis_key = task_instance.xcom_pull(task_ids="compare_archive_pois_with_db", key="pois_to_update_key")
        batch_keys = []
        redis_client = get_redis_client()
        redis_data = redis_client.get(redis_key)
        if not redis_data:
            logging.info(f"Aucun POI à {action} pour la clé Redis {redis_key}.")
            return batch_keys
        pois = json.loads(redis_client.get(redis_key))
        pois = [Poi.from_dict(poi) for poi in pois]
        batches = [pois[i:i + batch_size] for i in range(0, len(pois), batch_size)]
        
        

        for batch in batches:
            batch_key = f"batch_{uuid.uuid4()}"
            redis_client.set(batch_key, json.dumps([Poi.to_dict(poi) for poi in batch]))
            batch_keys.append(batch_key)

        return batch_keys
    
    @task(task_id="process_neo4j")
    def process_neo4j(redis_key_pois: str) -> None:
        """
        Enregistrement des Pois dans neo4j

        :param: 
            redis_key_pois: str - clé redis de Pois
        """
        redis_client = get_redis_client()
        pois = json.loads(redis_client.get(redis_key_pois))
        pois = [Poi.from_dict(poi) for poi in pois]
        driver = neo4j.GraphDatabase.driver(
            NEO4J_URL,
            auth=(NEO4J_USER, NEO4J_PASSWORD)
        )
        import_pois(driver, pois)
        driver.close()


    @task(task_id="process_batch_task", trigger_rule=TriggerRule.ALL_DONE)
    def process_batch_task(action_dict: dict) -> None:
        """
        Traite un batch en fonction de la clé Redis et de l'action spécifiée.
        
        :param 
            action_dict: dict - Dictionnaire contenant la clé du batch dans Redis et l'action à effectuer.
                Exemple : {"batch_key": "batch_123", "action": "insert"}
        """
        batch_key = action_dict["batch_key"]
        action = action_dict["action"]

        redis_client = get_redis_client()
        try:
            # Récupérer les données du batch depuis Redis
            pois = json.loads(redis_client.get(batch_key))
            pois = [Poi.from_dict(poi) for poi in pois]

            # Appeler la fonction process_batch avec les POIs et l'action
            process_batch(
                pois,
                type=action,
                dbname=POSTGRES_DATATOURISME_DB,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
            )
            logging.info(f"Batch {batch_key} traité avec succès (action : {action}).")

        except Exception as e:
            logging.error(f"Erreur lors du traitement du batch {batch_key} : {e}")
            raise

    @task(task_id="cleanup_data", trigger_rule=TriggerRule.ALL_DONE)
    def cleanup_data(metadata_redis_key: str, pois_redis_key: str, pois_in_france_redis_key: str, pois_db_redis_key: str, create_keys: List[str], update_keys: List[str], **kwargs) -> None:
        """
        Néttoyage des données

        :param: 
            metadata_redis_key: str - La clé redis des metadata
            pois_redis_key: str - La clé redis des Pois
            pois_db_redis_key: str - La clé redis des Pois de la base de donnée
            create_keys: List[str] - La liste des clés redis des batch de création
            update_keys: List[str] - La liste des clés redis des batch de modification
        """
        task_instance = kwargs['ti']
        path_to_delete = task_instance.xcom_pull(task_ids="download_shape", key="path_to_delete")
        pois_to_create_key = task_instance.xcom_pull(task_ids="compare_archive_pois_with_db", key="pois_to_create_key")
        pois_to_update_key = task_instance.xcom_pull(task_ids="compare_archive_pois_with_db", key="pois_to_update_key")
        redis_client = get_redis_client()
        if pois_to_create_key:
            redis_client.delete(pois_to_create_key)
        if pois_to_update_key:
            redis_client.delete(pois_to_update_key)
        if metadata_redis_key:
            redis_client.delete(metadata_redis_key)
        if pois_redis_key:
            redis_client.delete(pois_redis_key)
            pois_in_france_redis_key
        if pois_in_france_redis_key:
            redis_client.delete(pois_in_france_redis_key)
        if pois_db_redis_key:
            redis_client.delete(pois_db_redis_key)
        if create_keys:
            for key in create_keys:
                redis_client.delete(key)
        if update_keys:
            for key in update_keys:
                redis_client.delete(key)
        if path_to_delete:
            cleanup_downloaded_data(path_to_delete)
        cleanup_downloaded_data(DOWNLOAD_PATH)

    @task(task_id="prepare_action_list")
    def prepare_action_list(batch_keys: List[str], action: str) -> List[dict]:
        """
        Prépare une liste de dictionnaires contenant les informations nécessaires pour chaque tâche batch.
        
        :param: 
            batch_keys: List[str] - La liste des URL des fichiers JSON
            action: str - Action liée au batch

        :return: 
            List[dict]: Liste de dictionnaires contenant la clé du batch et l'action à effectuer.
        """
        return [{"batch_key": key, "action": action} for key in batch_keys]

    # Orchestration dans le DAG
    postgres_ready = check_postgres_service()
    database_exists = check_database()
    decide_database_creation_task = decide_database_creation(database_exists)
    create_db = create_database()
    tables_checked = check_tables()
    table_decision = decide_table_creation(tables_checked)
    create_tables_task = create_tables()
    download_archive_task = download_archive()
    get_all_poi_metadata_from_archive_task = get_all_poi_metadata_from_archive()
    get_all_poi_from_db_task = get_all_poi_from_db()
    get_all_poi_from_archive_task = get_all_poi_from_archive(get_all_poi_metadata_from_archive_task)
    download_shape_task = download_shape()
    get_france_poi_task = get_france_poi(get_all_poi_from_archive_task)
    compare_archive_pois_with_db_task = compare_archive_pois_with_db(get_france_poi_task, get_all_poi_from_db_task)
    create_batches_task = create_batches("insert")
    update_batches_task = create_batches("update")
    create_action_list = prepare_action_list(create_batches_task, "insert")
    update_action_list = prepare_action_list(update_batches_task, "update")
    check_all_tables_available_task = check_all_tables_available()
    process_neo4j_task = process_neo4j(get_france_poi_task)
    # Utilisation de la tâche `expand`
    create_process_batches = process_batch_task.expand(action_dict=create_action_list)
    update_process_batches = process_batch_task.expand(action_dict=update_action_list)

    cleanup_data_task = cleanup_data(get_all_poi_metadata_from_archive_task, get_all_poi_from_archive_task, get_france_poi_task, get_all_poi_from_db_task, create_batches_task, update_batches_task)

    # Dépendances
    postgres_ready >> database_exists >> decide_database_creation_task
    decide_database_creation_task >> create_db >> tables_checked
    decide_database_creation_task >> tables_checked

    tables_checked >> table_decision
    table_decision >> create_tables_task >> check_all_tables_available_task
    table_decision >> check_all_tables_available_task
    check_all_tables_available_task >> get_all_poi_from_db_task

    download_archive_task >> get_all_poi_metadata_from_archive_task
    get_all_poi_metadata_from_archive_task >> get_all_poi_from_archive_task
    get_all_poi_from_archive_task >> download_shape_task
    download_shape_task >> get_france_poi_task
    
    get_france_poi_task >> [compare_archive_pois_with_db_task, process_neo4j_task]
    get_all_poi_from_db_task >> compare_archive_pois_with_db_task

    [get_france_poi_task, get_all_poi_from_db_task] >> compare_archive_pois_with_db_task

    compare_archive_pois_with_db_task >> create_batches_task >> create_process_batches >> cleanup_data_task
    compare_archive_pois_with_db_task >> update_batches_task >> update_process_batches >> cleanup_data_task
    process_neo4j_task >> cleanup_data_task
    [create_process_batches, update_process_batches, process_neo4j_task] >> cleanup_data_task

    cleanup_data_task >> create_cluster_tasks()
