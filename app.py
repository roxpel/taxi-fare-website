import streamlit as st
import requests
import pandas as pd
import numpy as np
import datetime
import folium
from streamlit_folium import folium_static

# Helper function to calculate distance
def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance between two points on the earth (specified in decimal degrees)"""
# Convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])

# Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    r = 6371  # Radius of earth in kilometers
    return c * r

# Set page configuration
st.set_page_config(
	page_title="NY Taxi Fare Predictor",
	page_icon="🚕",
	layout="wide"
)

# App title and description
st.title("NY Taxi Fare Predictor")
st.markdown("Predict the fare of your taxi ride in New York City")

# Sidebar for inputs
with st.sidebar:
	st.header("Ride Details")

	# Date and time
	pickup_date = st.date_input("Pickup Date", datetime.date.today())
	pickup_time = st.time_input("Pickup Time", datetime.time(12, 0))

	# Passenger count
	passenger_count = st.slider("Number of Passengers", 1, 8, 1)

	# API URL (hidden from UI)
	api_url = "https://taxifare.lewagon.ai/predict"

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
	st.subheader("Select Pickup and Dropoff Locations")

	# Initialize default map centered on NYC
	m = folium.Map(location=[40.7128, -74.0060], zoom_start=11)

	# Create a container for the map
	map_container = st.container()

	# Coordinates input
	st.subheader("Coordinates")
	pickup_col, dropoff_col = st.columns(2)

	with pickup_col:
		st.markdown("**Pickup Location**")
		pickup_lat = st.number_input("Pickup Latitude", value=40.7614, format="%.6f")
		pickup_lon = st.number_input("Pickup Longitude", value=-73.9776, format="%.6f")

		# Add marker for pickup
		folium.Marker(
			[pickup_lat, pickup_lon],
			popup="Pickup",
			icon=folium.Icon(color="green", icon="play", prefix="fa")
		).add_to(m)

	with dropoff_col:
		st.markdown("**Dropoff Location**")
		dropoff_lat = st.number_input("Dropoff Latitude", value=40.6413, format="%.6f")
		dropoff_lon = st.number_input("Dropoff Longitude", value=-73.7781, format="%.6f")

		# Add marker for dropoff
		folium.Marker(
			[dropoff_lat, dropoff_lon],
			popup="Dropoff",
			icon=folium.Icon(color="red", icon="stop", prefix="fa")
		).add_to(m)

	# Add line between pickup and dropoff
	folium.PolyLine(
		locations=[[pickup_lat, pickup_lon], [dropoff_lat, dropoff_lon]],
		color="blue",
		weight=5,
		opacity=0.7
	).add_to(m)

	# Display the map
	with map_container:
		folium_static(m)

with col2:
	st.subheader("Fare Prediction")

	# Create prediction button
	if st.button("Predict Fare", type="primary"):
		# Combine date and time
		pickup_datetime = datetime.datetime.combine(
			pickup_date,
			pickup_time
		).strftime("%Y-%m-%d %H:%M:%S")

		# Prepare data for prediction
		ride_data = {
			"pickup_datetime": pickup_datetime,
			"pickup_longitude": float(pickup_lon),
			"pickup_latitude": float(pickup_lat),
			"dropoff_longitude": float(dropoff_lon),
			"dropoff_latitude": float(dropoff_lat),
			"passenger_count": int(passenger_count)
		}

		# Show the data being sent
		st.json(ride_data)

		try:
			# Call prediction API
			with st.spinner("Calculating fare..."):
				# Build query string manually to match the original format
				query_params = '&'.join([f"{key}={value}" for key, value in ride_data.items()])
				url = f"{api_url}?{query_params}"

				response = requests.get(url)

				if response.status_code == 200:
					# Extract prediction
					result = response.json()
					predicted_fare = result.get('fare', 0)

					# Display prediction
					st.success(f"Predicted Fare: ${predicted_fare:.2f}")

					# Display additional information
					st.info(f"Distance: Approximately {haversine_distance(pickup_lat, pickup_lon, dropoff_lat, dropoff_lon):.2f} km")
				else:
					st.error(f"Error: {response.status_code} - {response.text}")
		except Exception as e:
			st.error(f"Error: {str(e)}")

	# Display some statistics or information
	st.subheader("Fare Estimation Details")
	st.markdown("""
	The fare prediction is based on:
	- Distance between pickup and dropoff
	- Time of day and day of week
	- Number of passengers
	- Historical fare data
	""")

	# Add a simple fare breakdown
	st.subheader("Typical Fare Components")
	components = {
		"Base fare": "$2.50",
		"Per mile": "$2.50",
		"Per minute (in traffic)": "$0.50",
		"Airport fee (if applicable)": "$5.00",
		"Tolls": "Varies"
	}

	for component, value in components.items():
		st.text(f"{component}: {value}")



# Footer
st.markdown("---")
st.markdown("© 2025 NY Taxi Fare Predictor | Built with Streamlit")
