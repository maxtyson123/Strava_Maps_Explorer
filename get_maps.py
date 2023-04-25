import requests
import os
from urllib.parse import urlparse, parse_qs

# Read file
with open('access.token', 'r') as f:
    for line in f:
        if line.startswith('id='):
            id = line.strip().split('=')[1]
        elif line.startswith('secret='):
            secret = line.strip().split('=')[1]

# Step 1: Register your application and obtain a client ID and secret from Strava
CLIENT_ID = id
CLIENT_SECRET = secret
AUTHORIZE_URL = "https://www.strava.com/oauth/authorize"
TOKEN_URL = "https://www.strava.com/oauth/token"
REDIRECT_URI = "http://localhost/exchange_token"

# Step 2: Redirect the user to the authorization page
authorize_params = {
    "client_id": CLIENT_ID,
    "response_type": "code",
    "redirect_uri": REDIRECT_URI,
    "scope": "activity:read_all",
}
authorize_url = AUTHORIZE_URL + "?" + "&".join([f"{k}={v}" for k, v in authorize_params.items()])

print(f"Please visit this URL to authorize the application: {authorize_url}")
authorization_code = input("Enter the authorization code (COPY URL): ")
parsed_url = urlparse(authorization_code)
authorization_code = parse_qs(parsed_url.query)['code'][0]

# Step 3: Exchange the authorization code for an access token
token_params = {
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "code": authorization_code,
    "grant_type": "authorization_code",
    "redirect_uri": REDIRECT_URI,
}
response = requests.post(TOKEN_URL, data=token_params)
if response.status_code == 200:
    access_token = response.json()["access_token"]
    print(f"Access token: {access_token}")
else:
    print(f"Error (access token): {response.status_code} - {response.json()}")

# Step 4: Retrieve activity data
BASE_URL = "https://www.strava.com/api/v3"
activities_url = BASE_URL + "/athlete/activities"
params = {'per_page': 200, 'page': 1}
activities = []


# Get the athlete information for the authenticated user
def get_athlete():
    url = BASE_URL + "/athlete"
    headers = {'Authorization': 'Bearer ' + access_token}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return None


# Check the scopes for the access token
athlete = get_athlete()
if athlete is None:
    print("Failed to get athlete")
else:
    print(f"Access token has the following scopes: {athlete['resource_state']}")

# Retrieve activity data
while True:
    headers = {'Authorization': 'Bearer ' + access_token}
    response = requests.get(url=activities_url, headers=headers, params=params)
    if response.status_code == 200:
        activities.extend(response.json())
        if len(response.json()) < params['per_page']:
            break
        else:
            params['page'] += 1
    else:
        print(f"Error (activities):  {response.json()}")
        break

failed = []
# Step 3: Loop through the activities and retrieve the map data
for activity in activities:
    activity_id = activity['id']
    activity_name = activity['name'].replace(" ", "_")
    map_url = f"https://www.strava.com/api/v3/activities/{activity_id}/streams?keys=latlng"
    response = requests.get(url=map_url, headers=headers)

    # Step 4: Store the map data in a file
    if response.status_code == 200:
        print(f"")
        map_data = response.json()

        try:
            latlng_data = map_data[0]['data']
            latlng_file = os.path.join("maps", f"{activity_name}_{activity_id}_latlng.txt")
            with open(latlng_file, "w") as f:
                f.write("\n".join([f"{float(lat)},{float(lng)}" for lat, lng in latlng_data]))
                print(f"Map data saved to {latlng_file} - Activity: {activity_id} | {activity_name}")
        except Exception as e:
            print(f"Error (map data): {e} - Activity: {activity_id} | {activity_name}")
            failed.append(activity_id)

    else:
        print(f"Error (map data): {response.status_code} - Activity: {activity_id} | {activity_name}")

print("STATS: ")
print(f"Total activities: {len(activities)}")
print(f"Total activities with map data: {len([a for a in activities if a['map']['summary_polyline'] is not None])}")
print(f"Total activities without map data: {len([a for a in activities if a['map']['summary_polyline'] is None])}")
print(f"Total failed: {len(failed)}")
print(f"Total succeeded: {len(activities) - len(failed)}")