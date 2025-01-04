document.addEventListener("DOMContentLoaded", function () {
    console.log("✅ JavaScript Loaded");

    function fetchDashboardData() {
        fetch('/api/dashboard-data/')
            .then(response => response.json())
            .then(data => {
                console.log("✅ Data fetched successfully:", data);
                updateDashboard(data);
                updateMap(data.earthquakes);
            })
            .catch(error => console.error("❌ Error fetching dashboard data:", error));
    }

    function updateDashboard() {
        fetch('/api/dashboard-data')
            .then(response => response.json())
            .then(data => {
                console.log("✅ Data fetched successfully:", data);
    
                // Only update if element exists
                if (document.getElementById("total-events")) {
                    document.getElementById("total-events").innerText = data.stats.total_24h;
                }
                if (document.getElementById("avg-magnitude")) {
                    document.getElementById("avg-magnitude").innerText = data.stats.avg_magnitude;
                }
                if (document.getElementById("active-alerts")) {
                    document.getElementById("active-alerts").innerText = data.stats.active_alerts;
                }
    
            })
            .catch(error => console.error("❌ Error fetching dashboard data:", error));
    }
    

    function updateMap(earthquakes) {
        var map = L.map("map").setView([0, 0], 2);
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            attribution: "&copy; OpenStreetMap contributors",
            maxZoom: 18,
        }).addTo(map);

        earthquakes.forEach(eq => {
            var marker = L.marker([eq.latitude, eq.longitude]).addTo(map);
            marker.bindPopup(`<b>${eq.place}</b><br>Magnitude: ${eq.magnitude}<br>Depth: ${eq.depth} km`);
        });
    }

    fetchDashboardData();
    setInterval(fetchDashboardData, 60000);  // Auto refresh every 60 seconds
});
