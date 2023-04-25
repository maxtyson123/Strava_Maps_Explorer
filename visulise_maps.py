import os

import eel
import folium
import json

# Load GeoJSON data
# Step 5: Combine the map data from all activities into a single GeoJSON file

geojson_list = []
USE_MARKERS = False


map_directory = "maps"
for filename in os.listdir(map_directory):
    if filename.endswith(".txt") and "latlng" in filename:
        filepath = os.path.join(map_directory, filename)
        try:
            with open(filepath, "r") as f:
                geojson = {
                    "type": "FeatureCollection",
                    "features": []
                }
                map_data = f.readlines()
                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [[float(c) for c in row.strip().split(",")] for row in map_data]
                    },
                    "properties": {
                        "name": filename[:-4]
                    }
                }
                geojson["features"].append(feature)
                geojson_list.append(geojson)
        except Exception as e:
            print(f"Error reading file {filename}: {e}")
    else:
        print(f"Skipping file {filename}")


# Create map centered on first coordinate
m = folium.Map(zoom_start=13, max_zoom = 40)

for geojson_data in geojson_list:

    # Extract coordinates from GeoJSON data
    coordinates = []
    for feature in geojson_data['features']:
        if feature['geometry']['type'] == 'LineString':
            coordinates.extend(feature['geometry']['coordinates'])

    # Get the filename
    filename = geojson_data['features'][0]['properties']['name']

    # Add polyline connecting all coordinates
    try:
        folium.PolyLine(locations=coordinates, color='blue').add_to(m)

        # Add markers for start and end points
        if USE_MARKERS:
            folium.Marker(coordinates[0], popup='Start').add_to(m)
            folium.Marker(coordinates[-1], popup='End').add_to(m)

    except Exception as e:
        print(f"Error adding polyline to map ({filename}): {e}")

# Convert to HTML and display
m.save('web/map.html')
eel.init('web')
eel.start('map.html', size=(1000, 600))
