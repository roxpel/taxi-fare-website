import datetime
import requests
import streamlit as st
from streamlit_folium import st_folium  # Updated from folium_static
import folium
import urllib.parse

# 🌍 Set page config
st.set_page_config(page_title="NY Taxi Fare Predictor", page_icon="🚖", layout="wide")

# 🎽 App Title
st.markdown("# Taxi Fare Prediction App")
st.markdown("## Predict the fare of your taxi ride in New York City with an interactive map.")

# 🔑 Mapbox API Key (Move this to the top before calling API functions)
mapbox_access_token = 'pk.eyJ1Ijoia3Jva3JvYiIsImEiOiJja2YzcmcyNDkwNXVpMnRtZGwxb2MzNWtvIn0.69leM_6Roh26Ju7Lqb2pwQ'

# 🚖 Initialize Session State Variables
if "pickup_location" not in st.session_state:
    st.session_state["pickup_location"] = "Times Square, NY"
if "dropoff_location" not in st.session_state:
    st.session_state["dropoff_location"] = "JFK Airport, NY"
if "pickup_datetime" not in st.session_state:
    st.session_state["pickup_datetime"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
if "pickup_latitude" not in st.session_state or "pickup_longitude" not in st.session_state:
    st.session_state["pickup_latitude"], st.session_state["pickup_longitude"] = None, None
if "dropoff_latitude" not in st.session_state or "dropoff_longitude" not in st.session_state:
    st.session_state["dropoff_latitude"], st.session_state["dropoff_longitude"] = None, None

# 🏩 Convert locations to coordinates (Mapbox API)
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

# 🌇 Update locations dynamically when user types
def update_location():
    """Update the coordinates when user enters a new location"""
    if st.session_state["pickup_location"]:
        st.session_state["pickup_latitude"], st.session_state["pickup_longitude"] = get_coordinates(st.session_state["pickup_location"])
    if st.session_state["dropoff_location"]:
        st.session_state["dropoff_latitude"], st.session_state["dropoff_longitude"] = get_coordinates(st.session_state["dropoff_location"])

# Initialize default coordinates
update_location()

# 🚖 User Inputs
st.subheader("Select Your Locations")
pickup_location = st.text_input("Pickup Location", st.session_state["pickup_location"], key="pickup_location", on_change=update_location)
dropoff_location = st.text_input("Dropoff Location", st.session_state["dropoff_location"], key="dropoff_location", on_change=update_location)

# 🏩 Ensure valid coordinates exist
pickup_lat, pickup_lon = st.session_state.get("pickup_latitude"), st.session_state.get("pickup_longitude")
dropoff_lat, dropoff_lon = st.session_state.get("dropoff_latitude"), st.session_state.get("dropoff_longitude")

if (pickup_lat is None or pickup_lon is None) or (dropoff_lat is None or dropoff_lon is None):
    st.warning("Invalid location coordinates. Please enter a valid address.")
else:
    # 🏩 **Render Interactive Map**
    st.subheader("Interactive Route Map")
    m = folium.Map(location=[pickup_lat, pickup_lon], zoom_start=12)
    folium.Marker([pickup_lat, pickup_lon], popup="Pickup", icon=folium.Icon(color="green")).add_to(m)
    folium.Marker([dropoff_lat, dropoff_lon], popup="Dropoff", icon=folium.Icon(color="red")).add_to(m)
    folium.PolyLine([[pickup_lat, pickup_lon], [dropoff_lat, dropoff_lon]], color="blue", weight=5).add_to(m)
    st_folium(m, height=400)

# 🚖 **Fare Prediction**
st.subheader("Fare Prediction")
if st.button("Predict Fare"):
    if None in [pickup_lat, pickup_lon, dropoff_lat, dropoff_lon]:
        st.warning("Invalid location coordinates. Please enter a valid address.")
    else:
        ride_data = {
            "pickup_datetime": st.session_state["pickup_datetime"],
            "pickup_longitude": float(pickup_lon) if pickup_lon else 0.0,
            "pickup_latitude": float(pickup_lat) if pickup_lat else 0.0,
            "dropoff_longitude": float(dropoff_lon) if dropoff_lon else 0.0,
            "dropoff_latitude": float(dropoff_lat) if dropoff_lat else 0.0,
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

# 🗽 Footer
st.markdown("---")
st.markdown("© 2025 NY Taxi Fare Predictor | Built with Streamlit & Folium")
