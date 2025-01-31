from typing import List
from utils import *
from datetime import datetime
import multiprocessing


def process_batch_neo4j(pois: List[Poi]):
    driver = connect_to_neo4j()
    import_pois(driver, pois)
    driver.close()


if __name__ == "__main__":

    start_etl = datetime.now()

    print("Téléchargement de l'archive")
    zip_path = "./raw_archive/archive.zip"
    download_datatourisme_archive()

    print("Récupération des medata dans le fichier index.json")
    poi_metadata_list = get_all_poi_metadata(zip_path)


    batch_size = len(poi_metadata_list) // multiprocessing.cpu_count()
    engine = connect_to_db_V2()
    db_pois = get_all_pois_from_db(engine)

    print("Parcours des fichiers json pour faire une liste de POI")

    # Lancer le parsing en parallèle
    start_parsing = datetime.now()
    poi_list = get_all_poi_parallel(zip_path, poi_metadata_list, batch_size=batch_size)

    print(f"Parsing terminé en {datetime.now() - start_parsing}")
    print(f"Nombre total de POIs extraits: {len(poi_list)}")

    # Check si le POI est en France
    path_shape_file, path_to_delete = download_and_get_shapefile()
    shape_geometry = get_france_geometry(path_shape_file)
    poi_list = filter_poi_in_france(poi_list, shape_geometry)

    # Check si le POI doit être créé, modifié ou rien
    pois_to_create, pois_to_update = compare_pois(db_pois, poi_list)
    print("nombre de poi a créé", len(pois_to_create))
    print("nombre de poi a modifié", len(pois_to_update))
    print('intégration à la DB ...')

    # Diviser en batches
    create_batches = [pois_to_create[i:i+batch_size] for i in range(0, len(pois_to_create), batch_size)]
    update_batches = [pois_to_update[i:i+batch_size] for i in range(0, len(pois_to_update), batch_size)]

    # Parallélisation pour les créations
    print("Insertion des POI dans la base de données")
    start_create = datetime.now()
    with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
        pool.starmap(process_batch, [(batch, "insert") for batch in create_batches])

    print(f"Création terminée en {datetime.now() - start_create}")

    # Parallélisation pour les mises à jour
    print("Mise à jour des POI dans la base de données")
    start_update = datetime.now()
    with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
        pool.starmap(process_batch, [(batch, "update") for batch in update_batches])
    start_get_poid_db_after = datetime.now()

    print(f"Mise à jour terminée en {datetime.now() - start_update}")

    # Parallélisation pour neo4j
    print("Création ou mise à jour des POI dans le graphe")
    neo4j_batches = [poi_list[i:i+batch_size] for i in range(0, len(poi_list), batch_size)]
    start_neo4j = datetime.now()
    with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
        pool.starmap(process_batch_neo4j, [(batch,) for batch in neo4j_batches])
    print(f"Mise à jour du graphe terminée en {datetime.now() - start_neo4j}")

    #clean des fichiers / conn
    cleanup_downloaded_data(path_to_delete)
    cleanup_downloaded_data("./raw_archive")
    engine.close()

    print("Tout est pret en", datetime.now() - start_etl)
