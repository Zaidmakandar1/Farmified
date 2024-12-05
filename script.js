// Handle Crop Yield Prediction
document.getElementById("predictForm").addEventListener("submit", async function (event) {
    event.preventDefault();

    const rainfall = parseFloat(document.getElementById("rainfall").value);
    const temperature = parseFloat(document.getElementById("temperature").value);
    const soil_ph = parseFloat(document.getElementById("soil_ph").value);
    const fertilizer = parseFloat(document.getElementById("fertilizer").value);

    const payload = { rainfall, temperature, soil_ph, fertilizer };

    try {
        const response = await fetch("http://127.0.0.1:5000/predict", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);

        const data = await response.json();
        document.getElementById("yieldResult").innerHTML = `
            <strong>Predicted Crop Yield:</strong> ${data.predicted_yield} kg/ha
        `;
    } catch (error) {
        console.error("Error:", error);
        document.getElementById("yieldResult").innerHTML = `
            <span style="color: red;">Error predicting yield. Please try again.</span>
        `;
    }
});

// Handle Crop Suitability Check
document.getElementById("suitabilityForm").addEventListener("submit", async function (event) {
    event.preventDefault();

    const crop = document.getElementById("crop").value.toLowerCase();
    const rainfall = parseFloat(document.getElementById("rainfall_suitability").value);
    const temperature = parseFloat(document.getElementById("temperature_suitability").value);
    const soil_ph = parseFloat(document.getElementById("soil_ph_suitability").value);

    const payload = { crop, rainfall, temperature, soil_ph };

    try {
        const response = await fetch("http://127.0.0.1:5000/suitability", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);

        const data = await response.json();
        document.getElementById("suitabilityResult").innerHTML = `
            <strong>${data.message}</strong>
        `;
    } catch (error) {
        console.error("Error:", error);
        document.getElementById("suitabilityResult").innerHTML = `
            <span style="color: red;">Error checking suitability. Please try again.</span>
        `;
    }
});

// Handle Regional Crop Recommendations
document.getElementById("regionsForm").addEventListener("submit", async function (event) {
    event.preventDefault();

    const temperature = parseFloat(document.getElementById("temperature_region").value);
    const soil_ph = parseFloat(document.getElementById("soil_ph_region").value);
    const rainfall = parseFloat(document.getElementById("rainfall_region").value);

    const payload = { temperature, soil_ph, rainfall };

    try {
        const response = await fetch("http://127.0.0.1:5000/regions", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);

        const results = await response.json();
        let output = "<strong>Suggested Regions:</strong><br>";
        results.forEach((region) => {
            if (region.message) {
                output += `${region.message}<br>`;
            } else {
                output += `Region: ${region.region}, Crops: ${region.crops}<br>`;
            }
        });
        document.getElementById("regionsResult").innerHTML = output;
    } catch (error) {
        console.error("Error:", error);
        document.getElementById("regionsResult").innerHTML = `
            <span style="color: red;">Error finding regions. Please try again.</span>
        `;
    }
});

// Handle Geolocation and Weather Data
document.getElementById("getLocation").addEventListener("click", async function () {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(async (position) => {
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;

            try {
                const response = await fetch(`http://127.0.0.1:5000/weather?lat=${lat}&lon=${lon}`);
                if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);

                const weatherData = await response.json();
                document.getElementById("geoWeatherResult").innerHTML = `
                    <strong>Your Location Weather:</strong><br>
                    Temperature: ${weatherData.temperature} °C<br>
                    Humidity: ${weatherData.humidity}%<br>
                    Weather: ${weatherData.description}<br>
                `;

                suggestCrop(weatherData.temperature, weatherData.humidity);

            } catch (error) {
                console.error("Error:", error);
                document.getElementById("geoWeatherResult").innerHTML = `
                    <span style="color: red;">Error fetching location-based weather. Please try again.</span>
                `;
            }
        });
    } else {
        alert("Geolocation is not supported by your browser.");
    }
});

// Suggest Crop Based on Weather
function suggestCrop(temperature, humidity) {
    let cropSuggestion = "unknown";
    if (temperature >= 15 && temperature <= 25 && humidity >= 40 && humidity <= 70) {
        cropSuggestion = "wheat";
    } else if (temperature >= 20 && temperature <= 30 && humidity >= 60 && humidity <= 80) {
        cropSuggestion = "rice";
    } else if (temperature >= 18 && temperature <= 27 && humidity >= 50 && humidity <= 70) {
        cropSuggestion = "corn";
    }

    document.getElementById("geoWeatherResult").innerHTML += `
        <strong>Suggested Crop for Your Region:</strong> ${cropSuggestion}
    `;
}

