// dashboard.js
console.log("✅ Dashboard.js Loaded");

let map;
let markers = [];
let socket;

document.addEventListener("DOMContentLoaded", function () {
    console.log("✅ DOM Loaded");
    initializeWebSocket();
    initializeMap();
    initializeSearch();
    fetchDashboardData();
});

function initializeWebSocket() {
    socket = new WebSocket(`${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/earthquakes/`);

    socket.onmessage = function(event) {
        const earthquake = JSON.parse(event.data);
        console.log("🔴 Real-time earthquake update received:", earthquake);
        
        // Update all components
        addEarthquakeMarker(earthquake);
        updateEarthquakeTable(earthquake);
        updateStatistics();
    };

    socket.onopen = () => console.log("✅ WebSocket connected");
    socket.onerror = (error) => console.error("❌ WebSocket error:", error);
    socket.onclose = () => {
        console.warn("⚠️ WebSocket closed, attempting to reconnect...");
        setTimeout(initializeWebSocket, 1000);
    };
}

function initializeMap() {
    if (!document.getElementById("map")) {
        console.error("❌ Map container not found!");
        return;
    }

    map = L.map("map").setView([0, 0], 2);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "&copy; OpenStreetMap contributors"
    }).addTo(map);
}

function fetchDashboardData() {
    fetch('/api/dashboard-data/')
        .then(response => response.json())
        .then(data => {
            console.log("✅ Initial data loaded:", data);
            updateDashboard(data);
            displayEarthquakes(data.earthquakes);
        })
        .catch(error => console.error("❌ Error:", error));
}

function updateDashboard(data) {
    // Update statistics
    document.getElementById("total-events")?.innerText = data.stats.total_24h;
    document.getElementById("avg-magnitude")?.innerText = data.stats.avg_magnitude;
    document.getElementById("active-alerts")?.innerText = data.stats.active_alerts;
    
    // Update last update time
    document.getElementById("last-update")?.innerText = new Date().toLocaleString();
}

// Your existing map.js functions (addEarthquakeMarker, getMarkerSize, etc.)
// ... (keep all the marker and map-related functions)

function initializeSearch() {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchValue = this.value.toLowerCase();
            const rows = document.querySelectorAll('#earthquakeTableBody tr');
            
            rows.forEach(row => {
                const locationCell = row.querySelector('td');
                if (locationCell) {
                    const locationText = locationCell.textContent.toLowerCase();
                    row.style.display = locationText.includes(searchValue) ? '' : 'none';
                }
            });
        });
    }
}

// Auto refresh
setInterval(fetchDashboardData, 60000); // Every minute