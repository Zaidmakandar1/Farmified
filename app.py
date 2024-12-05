import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
from flask import Flask, request, jsonify
import requests
import sqlite3

app = Flask(__name__)

# Load the model from the CSV dataset when the server starts
def load_model_from_csv():
    """Load the model from the CSV dataset."""
    # Read the dataset from CSV
    df = pd.read_csv("crop_data.csv")  # Adjust the path to your CSV file

    # Define features and target
    X = df[["rainfall", "temperature", "soil_ph", "fertilizer_use"]]
    y = df["crop_yield"]

    # Split the data into training and test sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Train the model
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Evaluate the model (optional)
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    print(f"Model trained with Mean Squared Error: {mse}")

    # Save the trained model as a global variable
    global trained_model
    trained_model = model

@app.route("/")
def home():
    return (
        "Welcome to the Crop Yield Prediction and Suitability API!<br>"
        "Endpoints:<br>"
        "<code>/predict</code> - Predict crop yield<br>"
        "<code>/weather</code> - Get weather data<br>"
        "<code>/suitability</code> - Check crop suitability<br>"
        "<code>/regions</code> - Find regions for optimal crop growth<br>"
    )

# Your OpenWeatherMap API Key (replace with your actual API key)
OPENWEATHER_API_KEY = 'YOUR_OPENWEATHER_API_KEY'

@app.route("/weather", methods=["GET"])
def get_weather():
    """Fetch weather data for a location (city or coordinates)."""
    city = request.args.get("city")
    lat = request.args.get("lat")
    lon = request.args.get("lon")

    # Ensure that at least one of the parameters (city or coordinates) is provided
    if not (city or (lat and lon)):
        return jsonify({"error": "City name or coordinates (lat, lon) are required"}), 400

    try:
        # Construct the OpenWeatherMap API URL based on the provided parameters
        if city:
            WEATHER_URL = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
        elif lat and lon:
            WEATHER_URL = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"

        # Fetch the weather data from OpenWeatherMap
        response = requests.get(WEATHER_URL)
        response.raise_for_status()  # Raise an exception for HTTP errors
        weather_data = response.json()

        # Extract relevant weather information
        weather_info = {
            "temperature": weather_data["main"]["temp"],
            "humidity": weather_data["main"]["humidity"],
            "description": weather_data["weather"][0]["description"],
            "city": weather_data.get("name", "Your Location")
        }
        return jsonify(weather_info)

    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

@app.route("/predict", methods=["POST"])
def predict():
    """Predict the crop yield based on input data."""
    try:
        data = request.get_json()
        features = [
            data["rainfall"],
            data["temperature"],
            data["soil_ph"],
            data["fertilizer_use"]
        ]

        prediction = trained_model.predict([features])[0]  # Use the global model
        return jsonify({"predicted_yield": round(prediction, 2)})

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/suitability", methods=["POST"])
def get_suitability():
    """Check crop suitability based on environmental conditions."""
    CROP_SUITABILITY = {
        "wheat": {"temperature": (15, 25), "soil_ph": (6.0, 7.0), "rainfall": (300, 500)},
        "rice": {"temperature": (20, 30), "soil_ph": (5.5, 6.5), "rainfall": (500, 2000)},
        "corn": {"temperature": (18, 27), "soil_ph": (5.8, 7.0), "rainfall": (400, 800)}
    }

    try:
        data = request.get_json()
        crop = data["crop"].lower()
        rainfall = data["rainfall"]
        temperature = data["temperature"]
        soil_ph = data["soil_ph"]

        if crop not in CROP_SUITABILITY:
            return jsonify({"error": f"No data available for crop: {crop}"}), 400

        suitability = CROP_SUITABILITY[crop]
        is_suitable = (
            suitability["rainfall"][0] <= rainfall <= suitability["rainfall"][1] and
            suitability["temperature"][0] <= temperature <= suitability["temperature"][1] and
            suitability["soil_ph"][0] <= soil_ph <= suitability["soil_ph"][1]
        )

        message = f"The conditions are {'suitable' if is_suitable else 'not suitable'} for growing {crop}."
        return jsonify({"message": message})

    except Exception as e:
        return jsonify({"error": str(e)}), 400

def suggest_crops_by_region(temperature, soil_ph, rainfall):
    """Query the database to find suitable regions and crops."""
    conn = sqlite3.connect("crop_data.db")
    cursor = conn.cursor()

    query = """
        SELECT region_name, suggested_crops
        FROM regions
        WHERE ? BETWEEN temperature_min AND temperature_max
        AND ? BETWEEN soil_ph_min AND soil_ph_max
        AND ? BETWEEN rainfall_min AND rainfall_max
    """
    cursor.execute(query, (temperature, soil_ph, rainfall))
    results = cursor.fetchall()
    conn.close()

    if results:
        return [{"region": row[0], "crops": row[1]} for row in results]
    else:
        return [{"message": "No suitable regions found"}]

@app.route("/regions", methods=["POST"])
def regions():
    """Find suitable regions for a given environmental condition."""
    data = request.get_json()
    temperature = data["temperature"]
    soil_ph = data["soil_ph"]
    rainfall = data["rainfall"]

    results = suggest_crops_by_region(temperature, soil_ph, rainfall)
    return jsonify(results)

if __name__ == "__main__":
    # Load the model before starting the server
    load_model_from_csv()
    
    # Run the app
    app.run(debug=True)
