console.log("✅ map.js Loaded");

// Open WebSocket connection for real-time earthquake updates
const socket = new WebSocket("wss://" + window.location.host + "/ws/earthquakes/");

socket.onmessage = function (event) {
    const earthquake = JSON.parse(event.data);
    console.log("🔴 Real-time earthquake update received:", earthquake);

    // Add the new earthquake to the map
    addEarthquakeMarker(earthquake);

    // Update the table dynamically
    updateEarthquakeTable(earthquake);
};

socket.onopen = function () {
    console.log("✅ WebSocket connection established!");
};

socket.onerror = function (error) {
    console.error("❌ WebSocket error:", error);
};

socket.onclose = function () {
    console.warn("⚠️ WebSocket connection closed.");
};

let map;
let markers = [];

document.addEventListener("DOMContentLoaded", function () {
    console.log("✅ DOM Loaded! Initializing map...");
    initializeMap();
    updateDashboard();
});

// Initialize the map with default view
function initializeMap() {
    console.log("🌍 Initializing Map...");

    if (!document.getElementById("map")) {
        console.error("❌ ERROR: Map container not found! Check if #map exists in the HTML.");
        return;
    }

    map = L.map("map").setView([0, 0], 2);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "&copy; OpenStreetMap contributors"
    }).addTo(map);

    displayEarthquakes("24h");
}

// Get marker size based on earthquake magnitude
function getMarkerSize(magnitude) {
    return Math.max(magnitude * 5, 8);
}

// Get marker color based on earthquake status
function getMarkerColor(status) {
    switch (status) {
        case "alert": return "#FF0000"; // Red
        case "warning": return "#FFA500"; // Orange
        case "safe": return "#90EE90"; // Light Green
        default: return "#90EE90";
    }
}

// Format date for better readability
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
}

// Create popup content for each earthquake
function createPopupContent(earthquake) {
    return `
        <div class="earthquake-popup">
            <h3 class="font-bold">${earthquake.place}</h3>
            <p>Magnitude: <strong>${earthquake.magnitude}</strong></p>
            <p>Depth: <strong>${earthquake.depth} km</strong></p>
            <p>Time: ${formatDate(earthquake.time)}</p>
            <p>Status: <span style="color:${getMarkerColor(earthquake.status)};">
                ${earthquake.status.charAt(0).toUpperCase() + earthquake.status.slice(1)}
            </span></p>
        </div>
    `;
}

// Display earthquakes on the map
function displayEarthquakes(timeFrame) {
    console.log("📍 Updating map with earthquakes:", earthquakeData.length, "entries");

    // Remove existing markers
    markers.forEach(marker => marker.remove());
    markers = [];

    const filteredData = filterEarthquakesByTime(earthquakeData, timeFrame);

    filteredData.forEach(addEarthquakeMarker);
}

// Function to add a single earthquake marker to the map
function addEarthquakeMarker(earthquake) {
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

    // Adjust map view dynamically
    if (markers.length > 0) {
        const group = L.featureGroup(markers);
        map.fitBounds(group.getBounds().pad(0.1));
    }
}

// Filter earthquakes based on selected time frame
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

// Function to filter the map by time frame
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

// Function to update the earthquake table dynamically
function updateEarthquakeTable(earthquake) {
    const tableBody = document.getElementById("earthquakeTableBody");

    if (!tableBody) {
        console.error("❌ ERROR: Earthquake table body not found.");
        return;
    }

    const newRow = `
        <tr class="hover:bg-gray-50">
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">${earthquake.place}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${earthquake.magnitude}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${earthquake.depth} km</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${formatDate(earthquake.time)}</td>
            <td class="px-6 py-4 whitespace-nowrap">
                <span class="px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full"
                      style="background-color: ${getMarkerColor(earthquake.status)};">
                    ${earthquake.status.charAt(0).toUpperCase() + earthquake.status.slice(1)}
                </span>
            </td>
        </tr>
    `;
    
    tableBody.insertAdjacentHTML("afterbegin", newRow);
}

// Function to update the dashboard with the latest earthquake data
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

// Search functionality for earthquake table
document.addEventListener('DOMContentLoaded', function () {
    const searchInput = document.getElementById('searchInput');
    const tableBody = document.getElementById('earthquakeTableBody');
    const rows = tableBody.getElementsByTagName('tr');

    if (searchInput) {
        searchInput.addEventListener('input', function () {
            const searchValue = this.value.toLowerCase();

            for (let i = 0; i < rows.length; i++) {
                const locationCell = rows[i].getElementsByTagName('td')[0];  // First column: Location
                if (locationCell) {
                    const locationText = locationCell.textContent.toLowerCase();
                    rows[i].style.display = locationText.includes(searchValue) ? '' : 'none';
                }
            }
        });
    }
});

// Refresh dashboard data every minute
setInterval(updateDashboard, 60000);
