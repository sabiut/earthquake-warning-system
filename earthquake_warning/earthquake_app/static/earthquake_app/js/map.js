console.log("✅ map.js Loaded");

// Ensure `earthquakeData` exists and is defined globally
if (typeof earthquakeData === "undefined") {
    console.error("❌ ERROR: `earthquakeData` is not defined! Check if it's injected correctly in base.html.");
} else {
    console.log("✅ Earthquake Data Available:", earthquakeData);
}

let map;
let markers = [];

function initializeMap() {
    console.log("🌍 Initializing Map...");
    
    // Ensure the map div exists before initializing
    if (!document.getElementById("map")) {
        console.error("❌ ERROR: Map container not found! Check if #map exists in the HTML.");
        return;
    }

    // Initialize the map centered at a default position
    map = L.map("map").setView([0, 0], 2);

    // Add OpenStreetMap tiles
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "&copy; OpenStreetMap contributors"
    }).addTo(map);

    // Display earthquakes initially for the last 24 hours
    displayEarthquakes("24h");
}

function getMarkerSize(magnitude) {
    return Math.max(magnitude * 5, 8);
}

function getMarkerColor(status) {
    switch (status) {
        case "alert": return "#FF0000"; // Red
        case "warning": return "#FFA500"; // Orange
        case "safe": return "#90EE90"; // Light Green
        default: return "#90EE90";
    }
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
}

function createPopupContent(earthquake) {
    return `
        <div class="earthquake-popup">
            <h3 class="font-bold">${earthquake.place}</h3>
            <p>Magnitude: <strong>${earthquake.magnitude}</strong></p>
            <p>Depth: <strong>${earthquake.depth} km</strong></p>
            <p>Time: ${formatDate(earthquake.time)}</p>
            <p>Status: <span style="color:${getMarkerColor(earthquake.status)};">${earthquake.status.charAt(0).toUpperCase() + earthquake.status.slice(1)}</span></p>
        </div>
    `;
}

function displayEarthquakes(timeFrame) {
    console.log("📍 Updating map with earthquakes:", earthquakeData.length, "entries");

    // Remove existing markers
    markers.forEach(marker => marker.remove());
    markers = [];

    // Filter earthquakes based on timeFrame
    const filteredData = filterEarthquakesByTime(earthquakeData, timeFrame);

    // Add new markers
    filteredData.forEach(earthquake => {
        console.log("📍 Adding Marker:", earthquake.place, earthquake.latitude, earthquake.longitude);

        const marker = L.circleMarker(
            [earthquake.latitude, earthquake.longitude],
            {
                radius: getMarkerSize(earthquake.magnitude),
                fillColor: getMarkerColor(earthquake.status),
                color: '#000',
                weight: 1,
                opacity: 1,
                fillOpacity: 0.8
            }
        );

        marker.bindPopup(createPopupContent(earthquake));
        marker.addTo(map);
        markers.push(marker);
    });

    // Adjust map view
    if (markers.length > 0) {
        const group = L.featureGroup(markers);
        map.fitBounds(group.getBounds().pad(0.1));
    }
}

function filterEarthquakesByTime(data, timeFrame) {
    const now = new Date();
    const cutoff = new Date();

    switch (timeFrame) {
        case "24h":
            cutoff.setDate(now.getDate() - 1);
            break;
        case "week":
            cutoff.setDate(now.getDate() - 7);
            break;
        case "month":
            cutoff.setMonth(now.getMonth() - 1);
            break;
    }

    return data.filter(quake => new Date(quake.time) >= cutoff);
}

function filterMap(timeFrame) {
    console.log(`🗺️ Filtering map: ${timeFrame}`);
    
    document.querySelectorAll(".flex.space-x-2 button").forEach(btn => {
        btn.classList.remove("bg-gray-200");
        btn.classList.add("bg-gray-100");
    });
    event.target.classList.remove("bg-gray-100");
    event.target.classList.add("bg-gray-200");

    displayEarthquakes(timeFrame);
}

function updateDashboard() {
    console.log("🔄 Fetching latest earthquake data...");
    
    fetch("/api/dashboard-data")
        .then(response => response.json())
        .then(data => {
            console.log("✅ Data fetched successfully:", data);
            earthquakeData = data.earthquakes;
            displayEarthquakes("24h");
        })
        .catch(error => console.error("❌ Error updating dashboard:", error));
}

// Ensure everything runs after DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
    console.log("✅ DOM Loaded! Initializing map...");
    initializeMap();
});

// Refresh data every minute
setInterval(updateDashboard, 60000);
