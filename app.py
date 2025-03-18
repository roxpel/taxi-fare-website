import datetime
import requests
import streamlit as st
from streamlit_folium import folium_static
import folium
import urllib.parse

# 🌍 Set page config
st.set_page_config(page_title="NY Taxi Fare Predictor", page_icon="🚕", layout="wide")

# 🏷️ App Title
st.markdown("# Taxi Fare Prediction App")
st.markdown("## Predict the fare of your taxi ride in New York City with an interactive map.")

# 🔑 Mapbox API Key (Move this to the top before calling API functions)
mapbox_access_token = 'pk.eyJ1Ijoia3Jva3JvYiIsImEiOiJja2YzcmcyNDkwNXVpMnRtZGwxb2MzNWtvIn0.69leM_6Roh26Ju7Lqb2pwQ';

# 🚖 Initialize Session State Variables
if "pickup_location" not in st.session_state:
    st.session_state["pickup_location"] = ""
if "dropoff_location" not in st.session_state:
    st.session_state["dropoff_location"] = ""

if "pickup_latitude" not in st.session_state:
    st.session_state["pickup_latitude"] = None
if "pickup_longitude" not in st.session_state:
    st.session_state["pickup_longitude"] = None
if "dropoff_latitude" not in st.session_state:
    st.session_state["dropoff_latitude"] = None
if "dropoff_longitude" not in st.session_state:
    st.session_state["dropoff_longitude"] = None

# 🗺 Convert locations to coordinates (Mapbox API)
def get_coordinates(location):
    """Fetch latitude & longitude from Mapbox API"""
    location_encoded = urllib.parse.quote(location)
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{location_encoded}.json?access_token={mapbox_access_token}&limit=10"

    response = requests.get(url)
    print(f"API Request: {url}")
    print(f"Response Status Code: {response.status_code}")
    print(f"Response JSON: {response.json()}")  # Logs API response

    if response.status_code == 200:
        data = response.json()
        if "features" in data and len(data["features"]) > 0:
            lon, lat = data["features"][0]["center"]
            return lat, lon
    return None, None


# 🏙️ Update locations dynamically when user types
def update_location():
    """Update the coordinates when user enters a new location"""
    if st.session_state["pickup_location"]:
        lat, lon = get_coordinates(st.session_state["pickup_location"])
        if lat and lon:
            st.session_state["pickup_latitude"], st.session_state["pickup_longitude"] = lat, lon
        else:
            st.warning(f"Could not find coordinates for {st.session_state['pickup_location']}")

    if st.session_state["dropoff_location"]:
        lat, lon = get_coordinates(st.session_state["dropoff_location"])
        if lat and lon:
            st.session_state["dropoff_latitude"], st.session_state["dropoff_longitude"] = lat, lon
        else:
            st.warning(f"Could not find coordinates for {st.session_state['dropoff_location']}")

# 🚖 User Inputs: Free text fields instead of selectbox
st.subheader("Select Your Locations")

pickup_location = st.text_input(
    "Pickup Location",
    st.session_state["pickup_location"],
    key="pickup_location",
    on_change=update_location
)

dropoff_location = st.text_input(
    "Dropoff Location",
    st.session_state["dropoff_location"],
    key="dropoff_location",
    on_change=update_location
)

# 🗺 Ensure valid coordinates exist
pickup_lat = st.session_state.get("pickup_latitude")
pickup_lon = st.session_state.get("pickup_longitude")
dropoff_lat = st.session_state.get("dropoff_latitude")
dropoff_lon = st.session_state.get("dropoff_longitude")

if None in [pickup_lat, pickup_lon, dropoff_lat, dropoff_lon]:
    st.warning("Invalid location coordinates. Please enter a valid address.")
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

if (st.session_state["pickup_location"] and (pickup_lat is None or pickup_lon is None)) or \
   (st.session_state["dropoff_location"] and (dropoff_lat is None or dropoff_lon is None)):
    st.warning("Invalid location coordinates. Please enter a valid address.")

else:
    # Proceed with prediction
    pickup_datetime = datetime.datetime.combine(datetime.date.today(), datetime.datetime.now().time()).strftime("%Y-%m-%d %H:%M:%S")

    ride_data = {
        "pickup_longitude": float(st.session_state["pickup_longitude"]) if st.session_state["pickup_longitude"] else 0.0,
        "pickup_latitude": float(st.session_state["pickup_latitude"]) if st.session_state["pickup_latitude"] else 0.0,
        "dropoff_longitude": float(st.session_state["dropoff_longitude"]) if st.session_state["dropoff_longitude"] else 0.0,
        "dropoff_latitude": float(st.session_state["dropoff_latitude"]) if st.session_state["dropoff_latitude"] else 0.0,
        "passenger_count": 1
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
