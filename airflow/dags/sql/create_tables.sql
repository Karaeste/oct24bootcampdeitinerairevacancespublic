-- Create the Region table
CREATE TABLE Region
(
    dt_region_id VARCHAR(255) PRIMARY KEY,
    name         VARCHAR(255) NOT NULL
);

-- Create the Departement table
CREATE TABLE Departement
(
    dt_departement_id VARCHAR(255) PRIMARY KEY,
    dt_region_id      VARCHAR(255),
    name              VARCHAR(255) NOT NULL,
    FOREIGN KEY (dt_region_id) REFERENCES Region (dt_region_id)
);

-- Create the City table
CREATE TABLE City
(
    dt_city_id        VARCHAR(255) PRIMARY KEY,
    dt_departement_id VARCHAR(255),
    name              VARCHAR(255) NOT NULL,
    FOREIGN KEY (dt_departement_id) REFERENCES Departement (dt_departement_id)
);

-- Create the Point_Of_Interest table
CREATE TABLE Point_Of_Interest
(
    dt_poi_id     VARCHAR(255) PRIMARY KEY,
    osm_node_id   VARCHAR(255),
    name          VARCHAR(255) NOT NULL,
    rating        FLOAT,
    dt_created_at TIMESTAMP,
    dt_updated_at TIMESTAMP,
    latitude      FLOAT,
    longitude     FLOAT,
    postal_code   VARCHAR(20),
    dt_city_id    VARCHAR(255),
    FOREIGN KEY (dt_city_id) REFERENCES City (dt_city_id)
);

-- Create the Category table
CREATE TABLE Category
(
    dt_category_id SERIAL PRIMARY KEY,
    name           VARCHAR(255) NOT NULL UNIQUE
);

-- Create the Category_Point_Of_Interest table
CREATE TABLE Category_Point_Of_Interest
(
    id             SERIAL PRIMARY KEY,
    dt_poi_id      VARCHAR(255),
    dt_category_id INT,
    FOREIGN KEY (dt_poi_id) REFERENCES Point_Of_Interest (dt_poi_id),
    FOREIGN KEY (dt_category_id) REFERENCES Category (dt_category_id)
);
