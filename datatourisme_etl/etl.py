from dt_utils import download_datatourisme_archive, extract_data
from dt_utils.database_helper import connect_to_db, parse_index_datatourisme, collect_region_information_from_files, save_dataframe_to_postgres, collect_department_information_from_files, collect_city_information_from_files, collect_all_categories,show_tables
from dt_utils.json_helper_functions import get_poi_identifier, get_poi_category, category_cleanup, get_poi_name, get_poi_creation_date, get_poi_update_date, get_poi_coordinates, get_poi_postal_code, get_poi_city
import dotenv
import fireducks.pandas as pd
from sqlalchemy import text


if __name__ == "__main__":

    dotenv.load_dotenv()

    #################################################################################
    # ATTENTION : Les tables doivent être créées avant l'exécution du script        #
    # Je coderai le check /create de la DB au moment de l'intégration dans Airflow  #
    #################################################################################


    # Etablissement de la connexion à la base de données
    engine = connect_to_db()

    # Phase 1 : Download de l'archive
    if download_datatourisme_archive():
        print("Archive Datatourisme téléchargée")
        extract_data()
        print("Données extraites")

    # Récuperation des URL dans le fichier index.json
    urls = parse_index_datatourisme()

    # Phase 2 : Remplissage des tables Region, Department, City

    # Remplissage de la table Region
    region_df = collect_region_information_from_files(urls)
    # Suppression des doublons
    region_df.drop_duplicates(subset=["dt_region_id"], inplace=True)
    save_dataframe_to_postgres(region_df, "region", engine, "append")
    print("Table Region remplie")

    # Remplissage de la table Departement
    departement_df = collect_department_information_from_files(urls)
    departement_df.drop_duplicates(subset=["dt_departement_id"], inplace=True)
    save_dataframe_to_postgres(departement_df, "departement", engine, "append")
    print("Table Departement remplie")

    # Remplissage de la table City
    city_df = collect_city_information_from_files(urls) 
    city_df.drop_duplicates(subset=["dt_city_id"], inplace=True)
    save_dataframe_to_postgres(city_df, "city", engine, "append")
    print("Table City remplie")

     # Phase 3 : Remplissage de la table Category
    
    poi_categories = collect_all_categories(urls)
    # Nettoyage des catégories
    poi_categories_cleaned = category_cleanup(poi_categories)
    save_dataframe_to_postgres(poi_categories, "category", engine, 'append')
    print("Table Category remplie")

    # Phase 4 : Remplissage de la table Point_Of_Interest

    # Création d'une liste pour stocker les informations des points d'intérêt
    # poi_id / osm_node_id = 0 / name / rating = 0 / 
    # dt_created_at / dt_updated_at / latitude / longitude / postal_code / dt_city_id / 
    poi_list = []
    for url in urls:
        poi_id = get_poi_identifier(url)
        osm_mode_id = 0
        poi_name = get_poi_name(url)
        rating = 0
        poi_created_at = get_poi_creation_date(url)
        poi_updated_at = get_poi_update_date(url)
        poi_latitude, poi_longitude = get_poi_coordinates(url)
        poi_postal_code = get_poi_postal_code(url)
        poi_city_id , poi_city_name = get_poi_city(url)

        poi_list.append([poi_id, osm_mode_id, poi_name, rating, poi_created_at, poi_updated_at, poi_latitude, poi_longitude, poi_postal_code, poi_city_id])
    
    # Conversion de la liste en DataFrame
    poi_df = pd.DataFrame(poi_list, columns=["dt_poi_id", "osm_node_id", "name", "rating", "dt_created_at", "dt_updated_at", "latitude", "longitude", "postal_code", "dt_city_id"])
    # Suppression des doublons par sécurité
    poi_df.drop_duplicates(subset=["dt_poi_id"], inplace=True)
    save_dataframe_to_postgres(poi_df, "point_of_interest", engine, "append")


    # Phase 5 : Remplissage de la table Category_Point_Of_Interest
    
    # Création d'une liste pour stocker les couples poi_id, category_id
    poi_category_list =[] 
    for url in urls:
        poi_id = get_poi_identifier(url)
        poi_category = category_cleanup(get_poi_category(url))
        for category in poi_category:
            # Recupération de la category_id en fonction de la category
            with engine.connect() as connection:
                result = connection.execute(text("SELECT dt_category_id FROM category WHERE name = :category"), {"category": category})
                category_id = result.fetchone()
                if category_id is not None:
                    poi_category_list.append((poi_id, category_id[0]))
                else:
                    print(f"La catégorie {category} n'existe pas dans la table Category")
 
    # Conversion de la liste en DataFrame
    poi_category_df = pd.DataFrame(poi_category_list, columns=["dt_poi_id", "dt_category_id"])
    # Suppression des doublons
    poi_category_df.drop_duplicates(subset=["dt_poi_id", "dt_category_id"], inplace=True)
    save_dataframe_to_postgres(poi_category_df, "category_point_of_interest", engine, "append")
    print("Table Category_Point_Of_Interest remplie")

    

    

