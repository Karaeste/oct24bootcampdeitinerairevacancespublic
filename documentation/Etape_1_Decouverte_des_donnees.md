# Datascientest / Projet itinéraire de vacances

## Étape 1 / Découverte des sources de données disponibles  

## A - Contexte et périmètre du projet

- Objectifs :  

Développer un outil de recommandation d'itinéraires de vacances, basé sur les préférences des utilisateurs permettant de découvrir des lieux touristiques et des activités à proximité

- Contraintes :
  - Les données doivent être collectées de manière automatisée
  - Les données doivent être actualisées régulièrement
  - Les données doivent être exploitables via une API

## B - Sources de données identifiées

- Datatourisme : 
  - Base de données de l'offre touristique française 
  - Segmentée par région et par type d'activité (hébergement, restauration, loisirs, culture, etc.)
  - Neutre et sans avis de consommateurs

- Tripadvisor.fr : 
  - Avis de voyageurs sur les lieux touristiques
- Google Places API : 
  - Informations sur les lieux touristiques

## C - Fonctionnement et extrait des différentes sources de données
- ### DataTourisme : 
  - Il faut créer un flux sur le portail datatourisme.gouv.fr contenant les éléments souhaités.
  - Le flux se génère automatiquement tous les jours à un horaire *indéterminé* sous
  - Il faut ensuite créer une "application" pour recevoir une clé afin de consommer l'API via une URL donnée
    - Par exemple : https://diffuseur.datatourisme.fr/webservice/a92d9021ef870f512dd7c4146b94f0a2/{app_key}  

  - le fichier ZIP contient 3 fichiers:
    - Un fichier d'index, listant les points d'intérêt contenus dans l'archive, avec leur dernière date de modication et le fichier json correspondant.
    - Un dossier objects contenant, au sein d'une hiérarchie itérative de dossiers, **un fichier pour chaque point d'intérêt**
    - Un fichier de contexte, permettant de transformer chaque fichier en JSON-LD (si besoin)

Exemple de fichier d'index :
```
index.json
[
  {
    "label": "JARDIN BOTANIQUE JEAN MARIE PELT",
    "lastUpdateDatatourisme": "2020-04-01T04:14:11.23Z",
    "file": "0/00/10-0037c361-4662-3bde-b1b3-6ac17d4e404d.json"
  },
  {
    "label": "MUSÉE DES ILLUSIONS",
    "lastUpdateDatatourisme": "2020-05-06T04:06:26.155Z",
    "file": "0/00/10-00f8d302-76a9-3691-a870-6b3a29e1bc6a.json"
  },
  {
    "label": "LA VIEILLE PORTE",
    "lastUpdateDatatourisme": "2020-05-06T04:06:26.154Z",
    "file": "0/02/10-0260d366-c31b-393b-aa0c-cfde4f067d30.json"
  }
]
```
Exemple de fichier pour un POI (tronqué pour lisibilité) :
```
objects/0/00/10-0037c361-4662-3bde-b1b3-6ac17d4e404d.json
{
  "@id": "https://data.datatourisme.fr/10/0037c361-4662-3bde-b1b3-6ac17d4e404d",
  "dc:identifier": "737000233",
  "@type": [
    "schema:Park",
    "CulturalSite",
    "ParkAndGarden",
    "PlaceOfInterest",
    "PointOfInterest"
  ],

 [...]

   "schema:geo": {
        "@id": "https://data.datatourisme.fr/caf751a5-191a-32bc-936f-4223eeb9986c",
        "schema:latitude": "48.66289762",
        "schema:longitude": "6.1553688",
        "@type": [
          "schema:GeoCoordinates"
        ]
      },
[...]
 ```

Nous allons détaillé ce que l'on retrouve dans un fichier du dossier objects en se penchant uniquement sur les données que nous considérons comme importante dans notre cas pour plus d'informations il y a une doc sur l'ontologie de DATAtourisme:

    "@id": L'unique id exemple https://data.datatourisme.fr/3/00da4750-e592-3538-aa49-876f0b0f4f18
    "@type": Les catégories exemple ["schema:LocalBusiness", "PlaceOfInterest", "PointOfInterest", "Store"]
    "rdfs:comment": Une description avec toutes ses traductions
    "rdfs:label": Le nom il peut être écrit avec plusieurs traductions exemple {"fr": ["Nemesis Pâtisserie"]}
    "hasContact": Avec les emails "schema:email", les téléphones "schema:telephone" et les sites "foaf:homepage"
    "isLocatedAt": La localisation avec "schema:address" où l'on retrouve la commune, le code postal, le département, la région et l'adresse, mais aussi avec "schema:geo" nous avons la latitude et la longitude et pour finir avec "openingHoursSpecification" nous obtenons les horaires d'ouverture.
    "lastUpdate" et "lastUpdateDatatourisme": Nous donne la date de dernière mise à jour ce qui nous permettra de savoir si nous sommes à jour.
    "offers": Les tarifs si il y en a.

- Les données de DataTourisme sont grosses mais la totalité de la base peut être récupérée sans problème.
- Un feed qui prend tous les POI de France métropolitaine avec la totalité de leurs données fait 2.2GB zippé et ~12GB dezippé
- Le format est très verbeux. Par exemple le json complet pour ce [POI](https://data.datatourisme.fr/23/ff534eae-b544-3018-8ea0-9dfbc0c0ba63) fait 206kb dont 150kb ne servent qu'à donner les urls d'une soixantaine d'images jpeg

Pour la phase d'ingestion des données et compte tenu du fait que le rafraichissement du flux intervient toutes les 24H à un horaire inconnu, 
il semblerait utile de créer un flux sur un critère précis (région, type de POI...) et créer autant de flux que nécéssaire 
pour récupérer toutes les Informations "lissées" dans le temps.

Sur ce sujet, il semble q'une extraction des données par région soit effectuée et publiée sur [data.gouv.fr](https://data.datatourisme.fr/23/ff534eae-b544-3018-8ea0-9dfbc0c0ba63)
sous forme d'un fichier CSV.  


Ces fichiers possèdent la structure suivante :
```
Nom_du_POI,Categories_de_POI,Latitude,Longitude,Adresse_postale,Code_postal_et_commune,Periodes_regroupees,Covid19_mesures_specifiques,Createur_de_la_donnee,SIT_diffuseur,Date_de_mise_a_jour,Contacts_du_POI,Classements_du_POI,Description,URI_ID_du_POI
```
Les séparateurs sont des ","
Les noms des colonnes sont:

    "Nom_du_POI": Le nom du point d'intéret
    "Categories_de_POI": Les catégories, chaque catégorie est séparé par des "|" exemple : https://www.datatourisme.fr/ontology/core#PlaceOfInterest|https://www.datatourisme.fr/ontology/core#PointOfInterest|https://www.datatourisme.fr/ontology/core#Accommodation|https://www.datatourisme.fr/ontology/core#RentalAccommodation|https://www.datatourisme.fr/ontology/core#SelfCateringAccommodation|http://schema.org/Accommodation|http://schema.org/LodgingBusiness)
    
    "Latitude": La latitude.
    
    "Longitude": La longitude.
    
    "Adresse_postale": L'adresse postale.
    
    "Code_postal_et_commune": Le code postal et la commune, le code postal et la commune sont séparé par un "#" exemple: 84580#Oppède
    
    "Periodes_regroupees": Les dates de débuts et de fin d'évènement, elles sont composé d'une date de début (YYYY_MM-DD), la date de début est de fin est séparé par "<->", suivi de la date de fin et séparé par "|" exemple 2024-11-02<->2024-11-02|2024-12-07<->2024-12-07|2024-10-27<->2024-10-27|2024-11-17<->2024-11-17|2024-12-22<->2024-12-22
    
    "Covid19_mesures_specifiques": La listes des mesures Covid19, c'est un texte détaillant les différentes mesures.
    
    "Createur_de_la_donnee": Le créateur de la donnée.
    
    "SIT_diffuseur": Le Système d'Information Touristique diffuseur.
    
    "Date_de_mise_a_jour": La date de la dernière mise à jour.
    
    "Contacts_du_POI": Les contacts, ils sont séparés par des "#" si il n'y a que "#" dans le champ c'est une valuer null, exemple #https://www.aixenprovencetourism.com/|Office de Tourisme d'Aix-en-Provence#https://reservation.aixenprovencetourism.com/musee-regards-de-provence-visite-libre.html
    
    "Classements_du_POI": Classements suivant différente catégories.   
    On retrouve des classements avec une valeur et une catégorie séparé par "#" qui sont séparés par "|"  
    Exemple : Tourisme & Handicap auditif#Marque Tourisme et Handicap|Tourisme & Handicap visuel#Marque Tourisme et Handicap|Tourisme & Handicap mental#Marque Tourisme et Handicap|Tourisme & Handicap moteur#Marque Tourisme et Handicap
    
    "Description": La description.
    
    "URI_ID_du_POI": L'ID unique

Les champs (Periodes_regroupees, Covid19_mesures_specifiques, Contacts_du_POI, Classements_du_POI, Description) sont facultatifs.  
En information importante nous avons l'id unique "URI_ID_du_POI"

- ### Tripadvisor  

[Cette discussion](https://www.growthhacking.fr/t/scraping-tripadvisor-code-sans-code/12971?page=2) donne une approche systématique pour parcourir TripAdvisor :
- récupérer le [robots.txt](https://www.tripadvisor.fr/robots.txt)
- on y trouve l'adresse de plusieurs sitemaps. 6 me semblent intéressants a priori :
  - le [sitemap global](https://www.tripadvisor.fr/sitemap/2/fr/sitemap_fr_index.xml)
  - le [sitemap "user reviews"](https://www.tripadvisor.fr/sitemap/2/fr/sitemap_fr_show_user_reviews_index.xml)
  - les sitemaps "attractions" :
    - [les attractions](https://www.tripadvisor.fr/sitemap/att/fr/sitemap_fr_attractions_index.xml)
    - [leurs reviews](https://www.tripadvisor.fr/sitemap/att/fr/sitemap_fr_attraction_review_index.xml)
    - [une autre sorte de reviews ?](https://www.tripadvisor.fr/sitemap/att/fr/sitemap_fr_attraction_product_review_index.xml)
    - [les voisinages des attractions](https://www.tripadvisor.fr/sitemap/att/fr/sitemap_fr_attractions_near_index.xml)

- **Le sitemap general** :  
  - C'est un xml qui contient lui même des liste d'urls d'xml.  
  - Ce sont en grande majorité des sitemaps "hotels" et "restaurants".  
  - En récupérant la totalité de ces fichiers, on obtient les urls de tous les hotels et restaurants sur TripAdvisor.  
  - Par exemple chaque fichier hotel_review-xxxxxx.xml.gz contient 50000 urls d'hotels.  
  - Les fichiers "tourism" peuvent également être intéressants.  
  - Ils donnent les listes de lieux avec l'url "Vacations" pour chacun d'entre eux. [Exemple](https://www.tripadvisor.fr/Tourism-g13320446-Carcassonne_Aude_Occitanie-Vacations.html).

  Ces pages vacations pourraient peut être permettre d'identifier les POI les plus intéressants en ne récupérant qu'une seule page par ville/village ?

- **Le sitemap user reviews**

  - C'est une liste d'environ 900 fichiers xml "user reviews".  
  - Chacun d'entre eux contient 50000 urls, soit au total plus de 45 millions d'urls (!!!)  
  - Ce sont les pages "reviews" de tous les hotels/restaurants/activités/etc. [Exemple](https://www.tripadvisor.fr/ShowUserReviews-g187175-d241435-r610823357-Theatre_Du_Capitole_Toulouse-Toulouse_Haute_Garonne_Occitanie.html)

- **Les sitemaps attractions**

  - Dans le [map principal des attractions](https://www.tripadvisor.fr/sitemap/att/fr/sitemap_fr_attractions_index.xml), on trouve la liste des fichiers attractions-xxxxxxx.xml.gz dans lesquels on va retrouver les urls des activités pour chaque lieu.  
  - Les "meilleures activités" pour un lieu donné [Exemple](https://www.tripadvisor.fr/Attractions-g13320446-Activities-Carcassonne_Aude_Occitanie.html) y sont aussi mais il faut les filtrer par rapport à la structure de l'url.

  - Dans [le map des attractions reviews](https://www.tripadvisor.fr/sitemap/att/fr/sitemap_fr_attraction_review_index.xml), on a des fichiers attraction_review-xxxxxxxx.xml qui listent les pages des reviews avec 1 page par activité. [Exemple](https://www.tripadvisor.fr/Attraction_Review-g187151-d5502593-Reviews-Eglise_Saint_Gimer-Carcassonne_Center_Carcassonne_Aude_Occitanie.html)

  - Dans [l'autre map des attractions reviews](https://www.tripadvisor.fr/sitemap/att/fr/sitemap_fr_attraction_product_review_index.xml), qui s'appelle "attractions _product_ review", on trouve plutôt des visites ou des trajets. [Exemple](https://www.tripadvisor.fr/AttractionProductReview-g187151-d13830944-Carcassonne_walking_tour-Carcassonne_Center_Carcassonne_Aude_Occitanie.html)

  - Mais on trouve aussi des visites dans le "attractions reviews" [Exemple](https://www.tripadvisor.fr/Attraction_Review-g13320446-d20295971-Reviews-Carcassonne_During_World_War_2-Carcassonne_Aude_Occitanie.html) alors je ne sais pas trop...

  - Dans le [map des voisinages des attractions](https://www.tripadvisor.fr/sitemap/att/fr/sitemap_fr_attractions_near_index.xml), on trouve les activités près d'une autre activité.

- ### Google Places
---
  - L'API Google Places accessible via Google Cloud permet de récupérer des informations sur les lieux grâce à une recherche full text.
  - L'API renvoie un JSON contenant les informations du lieu sous la forme suivante :
  - ``` {
    "business_status": "OPERATIONAL",
    "formatted_address": "1 Rue Viollet le Duc, 11000 Carcassonne, France",
    "geometry": {
        "location": {
            "lat": 43.2060816,
            "lng": 2.3641961
        },
        "viewport": {
            "northeast": {
                "lat": 43.20763622989273,
                "lng": 2.366772349999999
            },
            "southwest": {
                "lat": 43.20493657010728,
                "lng": 2.363337350000001
            }
        }
    },
    "icon": "https://maps.gstatic.com/mapfiles/place_api/icons/v1/png_71/generic_business-71.png",
    "icon_background_color": "#7B9EB0",
    "icon_mask_base_uri": "https://maps.gstatic.com/mapfiles/place_api/icons/v2/generic_pinlet",
    "name": "Cit\u00e9 de Carcassonne",
    "opening_hours": {
        "open_now": true
    },
    "photos": [
        {
            "height": 4000,
            "html_attributions": [
                "<a href=\"https://maps.google.com/maps/contrib/103693207243911837951\">A Google User</a>"
            ],
            "photo_reference": "AdDdOWol5kMeaYziE-UZYB9AAqiHoNbqANXnxNg0F3xM-0PisZEC7BS_bB6Dh3W9w69OaJjRaeQAUFyFh-imYWeDYQos8tDMwxs531tJAhp9VrWEFPkmLdepcFqp490moYv7XyVtlkJa1oD8JaNwrrlGHXE-w91dCya6p9a6cxLSPZkdFfUn",
            "width": 6000
        }
    ],
    "place_id": "ChIJtzSv52osrhIRdMhoy9K25VI",
    "plus_code": {
        "compound_code": "6947+CM Carcassonne",
        "global_code": "8FM46947+CM"
    },
    "rating": 4.7,
    "reference": "ChIJtzSv52osrhIRdMhoy9K25VI",
    "types": [
        "tourist_attraction",
        "point_of_interest",
        "establishment"
    ],
    "user_ratings_total": 85126}

- ### Openstreetmaps

Les données dans Open Street Map peuvent être :

- Un noeud (node) = un point avec une paire de coordonnées latitude/longitude
- Une voie (way) = une succession de noeuds
- Une relation = ensemble de noeuds et voies auquel on associe une sémantique

Chacun de ces éléments, noeud, voie ou relation possède un dictionnaire d'attributs (tags).  
Chaque attribut est composé d'une clef et d'une valeur.  
Pour tout ce qui est relatif au toursime, on peut s'intéresser aux clefs d'attribut :  
- 'historic' : qui présente un aspect historique. Exemples: historic=castle, historic=tomb, historic=monument, etc.
- 'attraction' : qui est une attraction. Exemple: attraction=carousel, attration=animal, attraction=water_slide, etc.
- 'tourism' : qui présente un aspect touristique.
  - Exemple : tourism=museum, tourism=picnic_site, etc.

Idéalement, tous les éléments avec un attribut 'attraction=xxxx' ont aussi un 'tourism=attraction': C'est parfois le cas.
Les éléments avec un attribut 'historic=xxxx' ont parfois un 'tourism=historic' ou un 'tourism=attraction'.
Les règles ont pu évoluer il ne semble pas y avoir de consistence.

Ces attributs relatifs au tourisme portent le plus souvent sur des noeuds mais parfois aussi sur des voies. Exemple : contour d'un site, rue touristique, oeuvre d'art...
et plus rarement sur des relations pour les grands ensembles architecturaux

Il existe 2 façons de récupérer les données :

Via une API nommée Overpass : Elle peut être testée sur https://overpass-turbo.eu/  
En téléchargeant l'ensemble des données pour une zone extraites dans un format binaire '.pbf' :
- La totalité des données pour la France dans ce format fait ~5Gb
- Il existe aussi des extractions par région et par département

Pour les gros volumes de données, le format binaire sur une grande zone est préférable: Il existe des bibliothèques Python pour lire ces fichiers.

## D - Remarques et Evolutions  

Evolutions possibles de l'application :
- Possibilités de filtrage selon plusieurs critères, par exemple :
  - Filtrage par type de POI
  - Filtrage par rating
  - Distance maximum à parcourir
  - Temps maximum du circuit de visite
  - ...

Dans le cadre de ce projet, il y a quelques contraintes que nous pouvons rencontrer :
- En terme d'acquisition et d'extraction de données :
  - Risque de bannissement d'IP suite à un scrapping trop intensif (Exemple : scrapping du frontend de Tripadvisor)
  - Limitation de la fréquence du refresh des données sur Datatourisme
  - Cout d'utilisation de certaines API:  
    - Google Places 32$ pour 1000 requètes (sachant qu'une recherche peut utiliser **plusieurs** appels avec la pagination.)



