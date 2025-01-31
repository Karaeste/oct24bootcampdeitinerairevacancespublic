import json
from .point_of_interest_helper import Poi, PoiMetadata, Category, City, Departement, Region
import zipfile
from typing import List
from datetime import datetime
import os
import geopandas as gpd
import multiprocessing
from dateutil.parser import isoparse

def get_poi_identifier(filename: str) -> str | None:
    """
    Récupère l'identifiant du point d'intérêt dans le fichier JSON
    :param filename: str
    :return: str | None si l'identifiant n'est pas trouvé
    """
    with open(filename, "r", encoding="utf-8") as file:
        content = json.load(file)
    try:
        _poi_id = content["dc:identifier"]
        return _poi_id
    except KeyError as e:
        print(f"Erreur de clé: {e}. Vérifier la structure et recommencer.")
        return None


def get_poi_name(filename: str) -> str | None:
    """
    Récupère le nom du point d'intérêt dans le fichier JSON
    :param filename: str
    :return: str | None si le nom n'est pas trouvé
    """
    with open(filename, "r", encoding="utf-8") as file:
        content = json.load(file)
    try:
        _poi_name = content["rdfs:label"]["fr"][0]
        return _poi_name
    except KeyError as e:
        print(f"Erreur de clé: {e}. Vérifier la structure et recommencer.")
        return None


def get_poi_creation_date(filename: str) -> str | None:
    """
    Récupère la date de création du point d'intérêt dans le fichier JSON
    :param filename: str
    :return: str | None si la date de création n'est pas trouvée
    """
    with open(filename, "r", encoding="utf-8") as file:
        content = json.load(file)
    try:
        _poi_created_date = content["creationDate"]
        return _poi_created_date
    except KeyError as e:
        print(f"Erreur de clé: {e}. Clé introuvable.")
        print("Renvoi d'une valeur par défaut")
        default_timestamp = "1970-01-01T00:00:00Z"
        return default_timestamp


def get_poi_update_date(filename: str) -> str | None:
    """
    Récupère la date de mise à jour du point d'intérêt dans le fichier JSON
    :param filename: str
    :return: str | None si la date de mise à jour n'est pas trouvée
    """
    with open(filename, "r", encoding="utf-8") as file:
        content = json.load(file)
    try:
        _poi_updated_date = content["lastUpdateDatatourisme"]
        return _poi_updated_date
    except KeyError as e:
        print(f"Erreur de clé: {e}. Vérifier la structure et recommencer.")
        return None


def find_last_update_by_label(label: str) -> str | None:
    """
    Trouve la valeur de `lastUpdateDatatourisme` pour un label donné dans le fichier index.json
    :param label: str
    :return: str | None si le label n'est pas trouvé
    """
    with open("../data/index.json", "r", encoding="utf-8") as file:
        data = json.load(file)

    for item in data:
        if item.get("label") == label:
            return item.get("lastUpdateDatatourisme")
    return None


def get_poi_category(filename: str) -> list | None:
    """
    Récupère la catégorie du point d'intérêt dans le fichier JSON
    :param filename: str
    :return: str | None si la catégorie n'est pas trouvée
    """
    with open(filename, "r", encoding="utf-8") as file:
        content = json.load(file)
    try:
        _poi_category = content["@type"]
        return _poi_category
    except KeyError as e:
        print(f"Erreur de clé: {e}. Vérifier la structure et recommencer.")
        return None


def category_cleanup(category_list: list) -> list:
    """
    Nettoie la liste des catégories en supprimant celles qui sont uniquement utiles au schéma
    Les catégories suivantes sont supprimées:
    - schema:*

    :param category_list: list
    :return: list
    """

    return [
        category for category in category_list if not category.startswith("schema:")
    ]


def get_poi_region(filename: str) -> tuple[str, str] | tuple[None, None]:
    """
    Récupère la région du point d'intérêt dans le fichier JSON
    :param filename: str
    :return: str | None si la région n'est pas trouvée
    """
    with open(filename, "r", encoding="utf-8") as file:
        content = json.load(file)
    try:
        _poi_region_id = content["isLocatedAt"][0]["schema:address"][0][
            "hasAddressCity"
        ]["isPartOfDepartment"]["isPartOfRegion"]["@id"]
        _poi_region_name = content["isLocatedAt"][0]["schema:address"][0][
            "hasAddressCity"
        ]["isPartOfDepartment"]["isPartOfRegion"]["rdfs:label"]["fr"][0]
        return _poi_region_id, _poi_region_name
    except KeyError as e:
        print(f"Erreur de clé: {e}. Vérifier la structure et recommencer.")
        return None, None


def get_poi_department(filename: str) -> tuple[str, str] | tuple[None, None]:
    """
    Récupère le département du point d'intérêt dans le fichier JSON
    :param filename: str
    :return: str | None si le département n'est pas trouvé
    """
    with open(filename, "r", encoding="utf-8") as file:
        content = json.load(file)
    try:
        _poi_department_id = content["isLocatedAt"][0]["schema:address"][0][
            "hasAddressCity"
        ]["isPartOfDepartment"]["@id"]
        _poi_department_name = content["isLocatedAt"][0]["schema:address"][0][
            "hasAddressCity"
        ]["isPartOfDepartment"]["rdfs:label"]["fr"][0]
        return _poi_department_id, _poi_department_name
    except KeyError as e:
        print(f"Erreur de clé: {e}. Vérifier la structure et recommencer.")
        return None, None


def get_poi_city(filename: str) -> tuple[str, str] | tuple[None, None]:
    """
    Récupère la ville du point d'intérêt dans le fichier JSON
    :param filename: str
    :return: str | None si la ville n'est pas trouvée
    """
    with open(filename, "r", encoding="utf-8") as file:
        content = json.load(file)
    try:
        _poi_city_id = content["isLocatedAt"][0]["schema:address"][0]["hasAddressCity"][
            "@id"
        ]
        _poi_city = content["isLocatedAt"][0]["schema:address"][0]["hasAddressCity"][
            "rdfs:label"
        ]["fr"][0]
        # _poi_postcode = content["isLocatedAt"][0]["schema:address"][0]["schema:postalCode"]
        return _poi_city_id, _poi_city
    except KeyError as e:
        print(f"Erreur de clé: {e}. Vérifier la structure et recommencer.")
        return None, None


def get_poi_postal_code(filename: str) -> str | None:
    """
    Récupère le code postal du point d'intérêt dans le fichier JSON
    :param filename: str
    :return: str | None si le code postal n'est pas trouvé
    """
    with open(filename, "r", encoding="utf-8") as file:
        content = json.load(file)
    try:
        _poi_postcode = content["isLocatedAt"][0]["schema:address"][0][
            "schema:postalCode"
        ]
        return _poi_postcode
    except KeyError as e:
        print(f"Erreur de clé: {e}. Vérifier la structure et recommencer.")
        return None


def get_poi_coordinates(filename: str) -> tuple[float, float] | tuple[None, None]:
    """
    Récupère les coordonnées du point d'intérêt dans le fichier JSON
    :param filename: str
    :return: Tuple[float, float] | None si les coordonnées ne sont pas trouvées
    """
    with open(filename, "r", encoding="utf-8") as file:
        content = json.load(file)
    try:
        _poi_lat = float(content["isLocatedAt"][0]["schema:geo"]["schema:latitude"])
        _poi_long = float(content["isLocatedAt"][0]["schema:geo"]["schema:longitude"])
        return _poi_lat, _poi_long
    except KeyError as e:
        print(f"Erreur de clé: {e}. Vérifier la structure et recommencer.")
        return None, None

def parse_poi_from_json(json_data: dict) -> Poi:
    """
    Parse un fichier JSON pour créer un objet Poi avec toutes ses relations.

    :param
        json_data (dict): Contenu JSON du POI.

    :return
        Poi: Objet Poi créé avec ses relations.
    """
    try:
        # Extraire les informations de base
        poi_id = json_data.get("dc:identifier", "UnknownID")
        name = None
        label_fr = json_data.get("rdfs:label", {}).get("fr")
        if isinstance(label_fr, list):
            name = label_fr[0]
        elif isinstance(label_fr, str):
            name = label_fr
        else:
            name = "UnknownName"

        creation_date_str = json_data.get("creationDate", "1970-01-01")
        created_at = datetime.strptime(creation_date_str, "%Y-%m-%d")

        updated_date_str = json_data.get("lastUpdateDatatourisme", "1970-01-01")
        try:
            # Convertir la date ISO 8601 en objet datetime
            updated_at = isoparse(updated_date_str)
        except ValueError:
            # En cas de format incorrect, utiliser une valeur par défaut
            print(f"Format de date invalide pour {updated_date_str}. Utilisation de la date par défaut.")
            updated_at = datetime(1970, 1, 1)

        # Initialisation des variables d'adresse et géolocalisation
        latitude, longitude, postal_code = None, None, None
        city_name, city_id = "UnknownCity", "UnknownCityID"
        departement_name, departement_id = "UnknownDepartement", "UnknownDepartementID"
        region_name, region_id = "UnknownRegion", "UnknownRegionID"

        isLocatedAt = json_data.get("isLocatedAt", [])
        if isinstance(isLocatedAt, list) and len(isLocatedAt) > 0:
            location_info = isLocatedAt[0]  # Supposons qu'on utilise la première adresse
            geo_info = location_info.get("schema:geo", {})
            latitude = float(geo_info.get("schema:latitude", 0.0))
            longitude = float(geo_info.get("schema:longitude", 0.0))

            address_info = location_info.get("schema:address", [])
            if isinstance(address_info, list) and len(address_info) > 0:
                address = address_info[0]  # Première adresse
                postal_code = address.get("schema:postalCode", "00000")

                # Informations sur la ville
                city_info = address.get("hasAddressCity", {})
                if isinstance(city_info, dict):
                    city_name = city_info.get("rdfs:label", {}).get("fr", ["UnknownCity"])[0]
                    city_id = city_info.get("@id", "UnknownCityID")

                    # Informations sur le département
                    departement_info = city_info.get("isPartOfDepartment", {})
                    if isinstance(departement_info, dict):
                        departement_name = departement_info.get("rdfs:label", {}).get("fr", ["UnknownDepartement"])[0]
                        departement_id = departement_info.get("@id", "UnknownDepartementID")

                        # Informations sur la région
                        region_info = departement_info.get("isPartOfRegion", {})
                        if isinstance(region_info, dict):
                            region_name = region_info.get("rdfs:label", {}).get("fr", ["UnknownRegion"])[0]
                            region_id = region_info.get("@id", "UnknownRegionID")

        # Construire les objets hiérarchiques
        region = Region(name=region_name, id=region_id)
        departement = Departement(name=departement_name, id=departement_id, region=region)
        city = City(name=city_name, id=city_id, departement=departement)

        # Extraire les catégories
        categories = []
        if "@type" in json_data and isinstance(json_data["@type"], list):
            for category_type in json_data["@type"]:
                if not (category_type.startswith("schema:") or category_type.startswith("olo:")):
                    categories.append(Category(name=category_type, id=None)) 
        # Construire l'objet Poi
        poi = Poi(
            id=poi_id,
            name=name,
            rating=None,  # Rating peut être calculé ou extrait si disponible
            created_at=created_at,
            updated_at=updated_at,
            latitude=latitude,
            longitude=longitude,
            postal_code=postal_code,
            city=city,
            categories=categories,
            osm_node_id=None
        )

        return poi
    except KeyError as e:
        print(f"Clé manquante dans le JSON : {e}")
        raise
    except TypeError as e:
        print(f"Problème de type dans le JSON : {e}")
        raise
    except Exception as e:
        print(f"Erreur inattendue lors du parsing du POI : {e}")
        raise


# Fonction pour lire tous les POIs depuis les fichiers référencés dans les métadonnées
def get_all_poi(zip_path: str, poi_metadata_list: List[PoiMetadata]) -> List[Poi]:
    """
    Lit tous les POIs (Points of Interest) à partir des fichiers référencés dans les métadonnées.

    :param
        - zip_path (str) : Chemin vers l'archive ZIP contenant les fichiers.
        - poi_metadata_list (List[PoiMetadata]) : Liste des métadonnées des POIs.

    :return
        - List[Poi] : Liste des objets Poi extraits et parsés.
    """
    pois = []
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            i = 0
            start_run = datetime.now()
            for metadata in poi_metadata_list:
                file_path = os.path.join("objects", metadata.file_path)
                # Vérifier si le fichier existe (correspondance exacte ou approximative)
                i += 1
                if i % 10000 == 0:
                    print(i, "/", len(poi_metadata_list), datetime.now() - start_run)
                try:
                    # Lire le fichier JSON
                    with zip_ref.open(file_path) as poi_file:
                        json_data = json.load(poi_file)
                        poi = parse_poi_from_json(json_data)  # Transformer en objet Poi
                        pois.append(poi)
                except KeyError:
                    print(f"Fichier {file_path} introuvable dans l'archive.")
                except json.JSONDecodeError:
                    print(f"Erreur : le fichier {file_path} n'est pas un JSON valide.")
                except Exception as e:
                    print(f"Erreur inattendue pour {file_path} : {str(e)}")
    except Exception as e:
        print(f"Erreur lors de l'ouverture de l'archive : {str(e)}")
    return pois

def get_all_poi_metadata(zip_path) -> List[PoiMetadata]:
    """
    Récupère les métadonnées de tous les POIs à partir d'un fichier `index.json` dans une archive ZIP.

    :param
        - zip_path (str) : Chemin vers l'archive ZIP contenant `index.json`.

    :return
        - List[PoiMetadata] : Liste des objets PoiMetadata contenant les informations sur les POIs.
    """
    try:
        # Ouvrir l'archive ZIP
        print(f"Ouverture de l'archive ZIP : {zip_path}")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Vérifier la présence de `index.json`
            if 'index.json' not in zip_ref.namelist():
                raise KeyError("`index.json` introuvable dans l'archive ZIP.")

            # Lire `index.json`
            print("Lecture de `index.json`")
            with zip_ref.open('index.json') as index_file:
                content = index_file.read().decode('utf-8')

                # Charger et traiter les données JSON
                index_data = json.loads(content)
                poi_metadata_list = []
                for item in index_data:
                    # Vérifier les clés dans chaque objet
                    if not all(key in item for key in ['label', 'lastUpdateDatatourisme', 'file']):
                        print(f"Erreur : Clés manquantes dans l'objet JSON : {item}")          
                    # Ajouter à la liste des POIs
                    else:
                        poi_metadata_list.append(
                            PoiMetadata(
                                label=item['label'],
                                last_update=item['lastUpdateDatatourisme'],
                                file_path=item['file']
                            )
                        )

                return poi_metadata_list

    except KeyError as e:
        print(f"Erreur : {str(e)}")
    except json.JSONDecodeError as e:
        print(f"Erreur : Problème de parsing JSON - {str(e)}")
    except Exception as e:
        print(f"Erreur inattendue : {str(e)}")
        return []
    
def get_france_geometry(shp_path: str) -> gpd.GeoDataFrame:
    """
    Charge les données géographiques et extrait la géométrie de la France.

    :param
        shp_path (str): Chemin vers le fichier Shapefile.

    :return
        gpd.GeoDataFrame : Géométrie de la France.
    """
    world = gpd.read_file(shp_path, engine="pyogrio")
    return world[world['name'] == 'France']

def filter_poi_in_france(pois: list[Poi], france_geometry: gpd.GeoDataFrame) -> list[str]:
    """
    Filtre les POI pour ne garder que ceux situés en France.

    :param
        pois (list[POI]): Liste des objets POI.
        france_geometry (gpd.GeoDataFrame): Géométrie de la France.

    :return
        list[str] : Liste des chemins des fichiers JSON des POI en France.
    """
    poi_in_france_files = []

    for poi in pois:
        try:
            point = poi.to_point()
            if france_geometry.geometry.contains(point).any():
                poi_in_france_files.append(poi)
        except Exception as e:
            print(f"Erreur lors du traitement de {poi} : {e}")
    return poi_in_france_files

def parse_poi_batch(zip_path: str, batch_metadata: List[PoiMetadata]) -> List[Poi]:
    """
    Parse un batch de fichiers JSON pour extraire les POIs.

    Args:
        zip_path (str): Chemin vers l'archive ZIP contenant les fichiers JSON.
        batch_metadata (List[PoiMetadata]): Liste des métadonnées des fichiers JSON à traiter.

    Returns:
        List[Poi]: Liste des objets POI extraits.
    """
    pois = []
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for metadata in batch_metadata:
                file_path = os.path.join("objects", metadata.file_path)
                try:
                    with zip_ref.open(file_path) as poi_file:
                        json_data = json.load(poi_file)
                        poi = parse_poi_from_json(json_data)
                        pois.append(poi)
                except KeyError:
                    print(f"Fichier {file_path} introuvable dans l'archive.")
                except json.JSONDecodeError:
                    print(f"Erreur : le fichier {file_path} n'est pas un JSON valide.")
                except Exception as e:
                    print(f"Erreur inattendue pour {file_path} : {str(e)}")
    except Exception as e:
        print(f"Erreur lors de l'ouverture de l'archive : {str(e)}")
    return pois

def get_all_poi_parallel(zip_path: str, poi_metadata_list: List[PoiMetadata], batch_size: int = 1000) -> List[Poi]:
    """
    Lire et parser tous les POIs depuis une archive ZIP en parallèle.

    Args:
        zip_path (str): Chemin vers l'archive ZIP contenant les fichiers JSON.
        poi_metadata_list (List[PoiMetadata]): Liste des métadonnées des POIs.
        batch_size (int): Taille des batches pour le traitement parallèle.

    Returns:
        List[Poi]: Liste complète des POIs extraits.
    """
    # Diviser les métadonnées en batches
    batches = [poi_metadata_list[i:i + batch_size] for i in range(0, len(poi_metadata_list), batch_size)]
    # Initialiser un pool de processus
    with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
        # Appliquer parse_poi_batch à chaque batch en parallèle
        results = pool.starmap(parse_poi_batch, [(zip_path, batch) for batch in batches])
    
    # Fusionner les résultats de tous les batches
    all_pois = [poi for batch in results for poi in batch]
    return all_pois