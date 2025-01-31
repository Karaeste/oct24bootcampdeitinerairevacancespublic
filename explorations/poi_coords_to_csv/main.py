import json
import os
import math
import pandas as pd
from pyproj import Transformer


data_folder = '../../../datatourisme/metropole'
data = []
n = 0
# EPSG:2154 is the EPSG code for the RGF93 / Lambert-93 projection used in France
transformer = Transformer.from_crs("EPSG:4326", "EPSG:2154", always_xy=True)


with open(os.path.join(data_folder, 'index.json'), 'r') as file:
  index_data = json.load(file)
  for entry in index_data:
    label = entry['label']
    file_path = entry['file']
    full_file_path = os.path.join(data_folder, 'objects', file_path)
    with open(full_file_path, 'r') as ref_file:
      ref_data = json.load(ref_file)
      if 'isLocatedAt' in ref_data and isinstance(ref_data['isLocatedAt'], list):
        for location in ref_data['isLocatedAt']:
          if 'schema:geo' in location:
            geo = location['schema:geo']
            latitude = float(geo.get('schema:latitude'))
            longitude = float(geo.get('schema:longitude'))
            x, y = transformer.transform(longitude, latitude)
            if math.isfinite(x) and math.isfinite(y):
              data.append({
                'label': label,
                'lat': latitude,
                'lon': longitude,
                'x': int(x),
                'y': int(y)
              })
              n += 1
              if n % 1000 == 0:
                print(n)

print("nombre de POI:", n)
df = pd.DataFrame(data)
df.to_csv('poi.csv', index=False)
