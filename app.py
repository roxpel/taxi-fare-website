import datetime
import requests
import streamlit as st
from streamlit_folium import folium_static
import folium
import urllib.parse

# 🌍 Set page config
st.set_page_config(page_title="NY Taxi Fare Predictor", page_icon="🚕", layout="wide")

# 🏷️ App Title
st.title("NY Taxi Fare Predictor")
st.markdown("Predict the fare of your taxi ride in New York City with an interactive map.")

# 🎯 Sidebar Inputs
with st.sidebar:
    st.header("Ride Details")
    pickup_date = st.date_input("Pickup Date", datetime.date.today())
    pickup_time = st.time_input("Pickup Time", datetime.time(12, 0))
    passenger_count = st.slider("Number of Passengers", 1, 8, 1)

# 🚖 Default Locations
default_locations = {
    "pickup_location": "Times Square, New York",
    "dropoff_location": "JFK Airport, New York",
}

# 🌍 Store in session state
for key, value in default_locations.items():
    if key not in st.session_state:
        st.session_state[key] = value

# 🌍 Default Coordinates
default_coords = {
    "pickup_latitude": 40.7614,
    "pickup_longitude": -73.9776,
    "dropoff_latitude": 40.6413,
    "dropoff_longitude": -73.7781
}

for key, value in default_coords.items():
    if key not in st.session_state:
        st.session_state[key] = value

# 🗺 Convert locations to coordinates (Mapbox API)
mapbox_access_token = "pk.eyJ1Ijoia3Jva3JvYiIsImEiOiJja2YzcmcyNDkwNXVpMnRtZGwxb2MzNWtvIn0.69leM_6Roh26Ju7Lqb2pwQ"

def get_coordinates(location):
    """Fetch latitude & longitude from Mapbox API"""
    location_encoded = urllib.parse.quote(location)
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{location_encoded}.json?access_token={mapbox_access_token}&limit=10"

    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if "features" in data and len(data["features"]) > 0:
            lon, lat = data["features"][0]["center"]
            return lat, lon
    return None, None

def get_suggestions(query):
    """Fetch address suggestions from Mapbox with increased results"""
    if not query:
        return []

    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{urllib.parse.quote(query)}.json?access_token={mapbox_access_token}&limit=25&country=us&types=address"

    response = requests.get(url)

    # Debugging: Print API response in the terminal
    print(f"API Request: {url}")
    print(f"Response Status Code: {response.status_code}")
    print(f"Response JSON: {response.json()}")  # Check if data is correctly fetched

    if response.status_code == 200:
        data = response.json()
        return [feature["place_name"] for feature in data.get("features", [])]

    return []

# 🏙️ User selects pickup/dropoff locations (ONLY ONE INPUT EACH)
st.subheader("Select Your Locations")

# Fetch pickup location suggestions and use selectbox
pickup_suggestions = get_suggestions(st.session_state["pickup_location"])
pickup_location = st.selectbox(
    "Pickup Location",
    options=pickup_suggestions if pickup_suggestions else [st.session_state["pickup_location"]],
    key="pickup"
)

# Fetch dropoff location suggestions and use selectbox
dropoff_suggestions = get_suggestions(st.session_state["dropoff_location"])
dropoff_location = st.selectbox(
    "Dropoff Location",
    options=dropoff_suggestions if dropoff_suggestions else [st.session_state["dropoff_location"]],
    key="dropoff"
)

# 🔄 Update locations dynamically
if st.button("Update Locations"):
    pickup_lat, pickup_lon = get_coordinates(pickup_location)
    dropoff_lat, dropoff_lon = get_coordinates(dropoff_location)

    if pickup_lat and dropoff_lat:
        st.session_state["pickup_location"] = pickup_location
        st.session_state["dropoff_location"] = dropoff_location
        st.session_state["pickup_latitude"] = pickup_lat
        st.session_state["pickup_longitude"] = pickup_lon
        st.session_state["dropoff_latitude"] = dropoff_lat
        st.session_state["dropoff_longitude"] = dropoff_lon

        st.rerun()  # 🚀 Refresh UI
    else:
        st.error("Could not find coordinates for one or both locations. Try another address.")

# 🗺 Ensure valid coordinates exist
pickup_lat = st.session_state.get("pickup_latitude")
pickup_lon = st.session_state.get("pickup_longitude")
dropoff_lat = st.session_state.get("dropoff_latitude")
dropoff_lon = st.session_state.get("dropoff_longitude")

if None in [pickup_lat, pickup_lon, dropoff_lat, dropoff_lon]:
    st.warning("Invalid location coordinates. Please update the locations.")
else:
    # 🗺 **Render Interactive Map**
    st.subheader("Interactive Route Map")

    m = folium.Map(location=[pickup_lat, pickup_lon], zoom_start=12)

    # Add Pickup & Dropoff Markers
    folium.Marker([pickup_lat, pickup_lon], popup="Pickup", icon=folium.Icon(color="green")).add_to(m)
    folium.Marker([dropoff_lat, dropoff_lon], popup="Dropoff", icon=folium.Icon(color="red")).add_to(m)

    # Add Trip Route Line
    folium.PolyLine([[pickup_lat, pickup_lon], [dropoff_lat, dropoff_lon]], color="blue", weight=5).add_to(m)

    # Display the interactive map
    folium_static(m)

# 🚖 **Fare Prediction**
st.subheader("Fare Prediction")

if st.button("Predict Fare"):
    pickup_datetime = datetime.datetime.combine(pickup_date, pickup_time).strftime("%Y-%m-%d %H:%M:%S")

    ride_data = {
        "pickup_datetime": pickup_datetime,
        "pickup_longitude": float(st.session_state["pickup_longitude"]),
        "pickup_latitude": float(st.session_state["pickup_latitude"]),
        "dropoff_longitude": float(st.session_state["dropoff_longitude"]),
        "dropoff_latitude": float(st.session_state["dropoff_latitude"]),
        "passenger_count": int(passenger_count)
    }

    try:
        api_url = "https://taxifare.lewagon.ai/predict"
        response = requests.get(f"{api_url}?{'&'.join([f'{k}={v}' for k,v in ride_data.items()])}")

        if response.status_code == 200:
            result = response.json()
            if "fare" in result:
                predicted_fare = round(result["fare"], 2)
                st.success(f"Predicted Fare: **${predicted_fare}**")
            else:
                st.error("Error: API response did not contain a fare value.")
        else:
            st.error(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        st.error(f"Error: {str(e)}")

# 🔽 Footer
st.markdown("---")
st.markdown("© 2025 NY Taxi Fare Predictor | Built with Streamlit & Folium")
