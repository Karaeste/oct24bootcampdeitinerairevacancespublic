import shutil
import dotenv
import os
import requests
import zipfile
import kagglehub
import logging


def check_file_exists(directory: str, filename: str) -> bool:
    file_path = os.path.join(directory, filename)
    return os.path.isfile(file_path)


def download_datatourisme_archive(url, download_path) -> bool:
    """
    Télécharge l'archive ZIP depuis DataTourisme si elle n'existe pas déjà.

    :return: bool - True si le fichier a été téléchargé avec succès, False sinon.
    """
    os.makedirs(download_path, exist_ok=True)
    file_path = os.path.join(download_path, "archive.zip")


    # Vérification si le fichier existe déjà
    if os.path.exists(file_path):
        logging.info(f"Le fichier existe déjà : {file_path}. Téléchargement ignoré.")
        return True

    try:
        logging.info(f"Téléchargement de l'archive depuis {url}...")
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()  # Vérifie les erreurs HTTP (404, 500, etc.)

        # Vérification du type de contenu
        content_type = response.headers.get('Content-Type')
        if 'application/zip' not in content_type:
            logging.error(f"Type de contenu inattendu : {content_type}")
            return False

        # Sauvegarde du fichier ZIP
        with open(file_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

        logging.info(f"Archive téléchargée avec succès et enregistrée sous : {file_path}.")
        return True

    except requests.exceptions.Timeout:
        logging.error("Le téléchargement a expiré après 60 secondes.")
        return False
    except requests.exceptions.RequestException as e:
        logging.error(f"Erreur lors du téléchargement : {e}")
        return False
    except Exception as e:
        logging.exception(f"Erreur inattendue lors du téléchargement : {e}")
        return False


def extract_data() -> bool:
    try:
        with zipfile.ZipFile("./raw_archive/archive.zip", "r") as zip_ref:
            zip_ref.extractall("./data")
            # Destruction de l'archive téléchargée
            shutil.rmtree("./raw_archive")
        return True
    except zipfile.BadZipFile:
        return False

def download_datatourisme_categories() -> bool:
    """
    Permet de télécharger le fichier ontology.TTL de datatourisme
    """
    # Répertoire de stockage temporaire du fichier ontology.TTL
    download_path = "./temporary_categories"
    os.makedirs(download_path, exist_ok=True)
    file_path = os.path.join(download_path, "ontology.TTL")

    # Téléchargement du fichier ontology.TTL depuis datatourisme
    url = "https://www.datatourisme.fr/ontology/core/ontology.ttl"

    if not check_file_exists("../temporary_categories", "ontology.TTL"):

        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()  # Renvoi une exception si le code de statut de la réponse HTTP n'est pas 200

            # Sauvegarde du fichier ontology.TTL
            with open(file_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)

            return True
        except requests.exceptions.RequestException as e:
            return False
    else:
        pass

def download_and_get_shapefile() -> str:
    """
    Télécharge les données géographiques (Shapefile) via KaggleHub.

    :return
        str : Chemin vers le fichier Shapefile.
    """
    print("Téléchargement des données géographiques...")
    path = kagglehub.dataset_download("abdulkerimnee/ne-110m-admin-0-countries")
    path_to_delete = path
    shp_path = os.path.join(path, "ne_110m_admin_0_countries", "ne_110m_admin_0_countries.shp")

    if not os.path.exists(shp_path):
        raise FileNotFoundError(f"Fichier Shapefile non trouvé : {shp_path}")
    return shp_path, path_to_delete

def cleanup_downloaded_data(path: str) -> None:
    """
    Supprime les fichiers temporaires.

    :param
        path (str): Chemin du répertoire à supprimer.
    """
    print("Nettoyage des fichiers temporaires...")
    if os.path.exists(path):
        shutil.rmtree(path)
        print(f"Supprimé : {path}")