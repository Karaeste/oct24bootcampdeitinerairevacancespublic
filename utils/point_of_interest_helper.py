from shapely.geometry import Point
from typing import List, Tuple
from datetime import datetime
import json
import logging


class Region:
    def __init__(self, name: str, id: str):
        """
        Représente une région.

        param:
            name (str): Nom de la région.
            id (str): Identifiant unique de la région (ex. "kb:France44").
        """
        self.name = name
        self.id = id

    def to_dict(self):
        return {
            "name": self.name,
            "id": self.id
        }

    @staticmethod
    def from_dict(data):
        return Region(
            name=data["name"],
            id=data["id"]
        )

    def __repr__(self):
        return f"<Region name={self.name}, id={self.id}>"


class Departement:
    def __init__(self, name: str, id: str, region: Region):
        """
        Représente un département.

        :param
            name (str): Nom du département.
            id (str): Identifiant unique du département (ex. "kb:France4410").
            region (Region): Instance de la classe Region associée.
        """
        self.name = name
        self.id = id
        self.region = region

    def to_dict(self):
        return {
            "name": self.name,
            "id": self.id,
            "region": self.region.to_dict() if self.region else None
        }

    @staticmethod
    def from_dict(data):
        if isinstance(data.get("region"), str):
            try:
                data["region"] = json.loads(data["region"])  # Si c'est une chaîne JSON
            except json.JSONDecodeError:
                logging.warning(f"Le champ 'region' est une chaîne invalide : {data['region']}")
        
        # Désérialisation de la région, seulement si c'est un dictionnaire
        region = Region.from_dict(data["region"]) if isinstance(data.get("region"), dict) else None
        
        return Departement(
            name=data["name"],
            id=data["id"],
            region=region
        )

    def __repr__(self):
        return f"<Departement name={self.name}, id={self.id}, region={self.region.name}>"


class City:
    def __init__(self, name: str, id: str, departement: Departement):
        """
        Représente une ville.

        :param
            name (str): Nom de la ville.
            id (str): Identifiant unique de la ville (ex. "kb:10387").
            departement (Departement): Instance de la classe Departement associée.
        """
        self.name = name
        self.id = id
        self.departement = departement

    def to_dict(self):
        return {
            "name": self.name,
            "id": self.id,
            "departement": self.departement.to_dict() if self.departement else None
        }

    @staticmethod
    def from_dict(data):
        if isinstance(data.get("departement"), str):
            try:
                data["departement"] = json.loads(data["departement"])
            except json.JSONDecodeError:
                logging.warning(f"Le champ 'departement' est une chaîne invalide : {data['departement']}")

        departement = Departement.from_dict(data["departement"]) if isinstance(data.get("departement"), dict) else None
        return City(
            name=data["name"],
            id=data["id"],
            departement=departement
        )

    def __repr__(self):
        return f"<City name={self.name}, id={self.id}, departement={self.departement.name}>"



class Category:
    def __init__(self, name: str, id: str):
        """
        Représente une catégorie.

        :param
            name (str): Nom de la catégorie.
            id (str): Identifiant unique de la catégorie.
        """
        self.name = name
        self.id = id
    
    def to_dict(self):
        return {
            "name": self.name,
            "id": self.id
        }

    @staticmethod
    def from_dict(data):
        return Category(
            name=data["name"],
            id=data["id"]
        )

    def __repr__(self):
        return f"<Category name={self.name}, id={self.id}>"


class Poi:
    def __init__(
        self,
        id: str,  # Identifiant principal (extrait du JSON)
        name: str,
        rating: float,
        created_at: datetime,
        updated_at: datetime,
        latitude: float,
        longitude: float,
        postal_code: str,
        city: City,
        categories: List[Category],
        osm_node_id: str = None  # Champ optionnel, utilisé uniquement si nécessaire
    ):
        """
        Représente un Point of Interest (POI).

        :param
            id (str): Identifiant unique du POI.
            name (str): Nom du POI.
            rating (float): Évaluation (si disponible).
            created_at (datetime): Date de création.
            updated_at (datetime): Date de mise à jour.
            latitude (float): Latitude géographique.
            longitude (float): Longitude géographique.
            postal_code (str): Code postal associé au POI.
            city (City): Instance de la classe City associée.
            categories (List[Category]): Liste des catégories associées.
            osm_node_id (str): Identifiant OSM du POI (optionnel).
        """
        self.id = id
        self.name = name
        self.rating = rating
        self.created_at = created_at
        self.updated_at = updated_at
        self.latitude = latitude
        self.longitude = longitude
        self.postal_code = postal_code
        self.city = city
        self.categories = categories
        self.osm_node_id = osm_node_id

    def to_point(self) -> Point:
        """
        Convertit les coordonnées en un objet Point Shapely.

        return:
            Point : Objet Shapely Point.
        """
        return Point(self.longitude, self.latitude)
    
    def to_dict(self):
        """
        Convertit l'objet Poi en dictionnaire sérialisable en JSON.
        """
        return {
            "id": self.id,
            "name": self.name,
            "rating": self.rating if self.rating else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "postal_code": self.postal_code,
            "city": self.city.to_dict() if isinstance(self.city, City) else self.city,  # Sérialisation conditionnelle de l'objet City
            "categories": [cat.to_dict() for cat in self.categories] if self.categories else [],
            "osm_node_id": self.osm_node_id if self.osm_node_id else None
        }

    @staticmethod
    def from_dict(data):
        """
        Crée un objet Poi à partir d'un dictionnaire.
        """
        # Désérialisation des catégories
        categories = [Category.from_dict(cat_data) for cat_data in data.get("categories", [])]
        
        # Désérialisation de la ville
        city = City.from_dict(data["city"]) if data.get("city") else None
        
        # Création de l'objet Poi
        return Poi(
            id=data["id"],
            name=data["name"],
            rating=data["rating"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            latitude=data["latitude"],
            longitude=data["longitude"],
            postal_code=data["postal_code"],
            city=city,
            categories=categories,
            osm_node_id=data.get("osm_node_id")
        )

    def __repr__(self):
        city_name = self.city.name if isinstance(self.city, City) else "UnknownCity"
        categories = [cat.name for cat in self.categories] if self.categories else []
        return f"<Poi name={self.name}, postal_code={self.postal_code}, city={city_name}, categories={categories}>"


    

    
class PoiMetadata:
    def __init__(self, label, last_update, file_path):
        self.label = label
        self.last_update = last_update
        self.file_path = file_path

    def __repr__(self):
        return f"PoiMetadata(label={self.label}, last_update={self.last_update}, file_path={self.file_path})"
    
    def to_dict(self):
        """
        Convertit l'objet PoiMetadata en un dictionnaire sérialisable en JSON.
        """
        return {
            "label": self.label,
            "last_update": self.last_update,
            "file_path": self.file_path
        }

    @staticmethod
    def from_dict(data):
        """
        Crée un objet PoiMetadata à partir d'un dictionnaire.
        """
        return PoiMetadata(
            label=data["label"],
            last_update=data["last_update"],
            file_path=data["file_path"]
        )

def compare_pois(db_pois: List[Poi], poi_list: List[Poi]) -> Tuple[List[Poi], List[Poi]]:
    """
    Compare les POIs de la base de données avec les POIs de la liste extraits.
    - Ajoute dans `pois_to_create` les POIs de `poi_list` qui ne sont pas dans `db_pois`.
    - Ajoute dans `pois_to_update` les POIs dont la date d'update est plus récente dans `poi_list`.

    :param
        db_pois (List[Poi]): Liste des POIs dans la base de données.
        poi_list (List[Poi]): Liste des POIs extraits des fichiers JSON.

    :return
        tuple: (pois_to_create, pois_to_update)
    """
    # Indexer les POIs de la DB par leur ID pour un accès rapide
    db_pois_dict = {poi.id: poi for poi in db_pois}

    pois_to_create = []
    pois_to_update = []

    for poi in poi_list:
        if poi.id not in db_pois_dict:
            # POI n'existe pas dans la DB, il faut le créer
            pois_to_create.append(poi)
        else:
            # POI existe, vérifier si une mise à jour est nécessaire
            db_poi = db_pois_dict[poi.id]
            if poi.updated_at.tzinfo is not None:
                poi.updated_at = poi.updated_at.replace(tzinfo=None)
            if db_poi.updated_at.tzinfo is not None:
                db_poi.updated_at = db_poi.updated_at.replace(tzinfo=None)
            if poi.updated_at > db_poi.updated_at:  # Comparer les dates d'update
                pois_to_update.append(poi)

    return pois_to_create, pois_to_update
