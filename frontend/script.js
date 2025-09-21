mapboxgl.accessToken =
  "pk.eyJ1IjoiZGVpYW5vdnZ2IiwiYSI6ImNtZmhhc2xvbDA5aWcyaXEzNmd0YTN5ZXoifQ.D_zOKU7AeIB6iLBhd3umAw"
// this is vlad's key. since it is connected to my credit card, please, do not abuse it and create your own keys

mapboxgl.accessToken =
  "pk.eyJ1IjoiZGVpYW5vdnZ2IiwiYSI6ImNtZmhhc2xvbDA5aWcyaXEzNmd0YTN5ZXoifQ.D_zOKU7AeIB6iLBhd3umAw"

// Store nodes for autocomplete
let nodeList = [];
let map;
let currentPosition = null;
let routeLayerId = "custom-route";
let routeSourceId = "custom-route";

// Fetch nodes from backend for autocomplete
async function fetchNodes() {
  const res = await fetch("/nodes");
  const nodes = await res.json();
  nodeList = nodes;
  setupAutocomplete(nodes);
}
fetchNodes();

// Setup autocomplete for input fields
function setupAutocomplete(nodes) {
  const fromInput = document.getElementById("from-input");
  const toInput = document.getElementById("to-input");

  function createDatalist(id, nodes) {
    let dl = document.getElementById(id);
    if (dl) dl.remove();
    dl = document.createElement("datalist");
    dl.id = id;
    nodes.forEach(n => {
      const opt = document.createElement("option");
      opt.value = n.name;
      dl.appendChild(opt);
    });
    document.body.appendChild(dl);
  }
  fromInput.setAttribute("list", "from-list");
  toInput.setAttribute("list", "to-list");
  createDatalist("from-list", nodes);
  createDatalist("to-list", nodes);
}

// Find nodeId by name (case-insensitive)
function findNodeIdByName(name) {
  name = name.trim().toLowerCase();
  for (const n of nodeList) {
    if (n.name.trim().toLowerCase() === name) return n.nodeId;
  }
  return null;
}

// Setup the map and user's location
navigator.geolocation.getCurrentPosition(successLocation, errorLocation, {
  enableHighAccuracy: true,
});

function successLocation(position) {
  currentPosition = {
    lng: position.coords.longitude,
    lat: position.coords.latitude
  };
  setupMap([position.coords.longitude, position.coords.latitude]);
}

function errorLocation() {
  setupMap([-79.9532, 40.4443]);
}

function setupMap(center) {
  map = new mapboxgl.Map({
    container: "map",
    style: "mapbox://styles/mapbox/streets-v11",
    center: center,
    zoom: 15
  });

  const nav = new mapboxgl.NavigationControl();
  map.addControl(nav);

  // ADA entrances as markers (keep this, but could later be moved to DB)
  const adaEntrances = [
    {
      name: "Thackeray Hall",
      entrance: "University Place ground level doors",
      coords: [-79.95725, 40.44432]
    },
    {
      name: "Old Engineering Hall",
      entrance: "O'Hara St entrance",
      coords: [-79.958045, 40.444959]
    },
    {
      name: "Allen Hall",
      entrance: "O'Hara St entrance",
      coords: [-79.95837, 40.44458]
    },
    {
      name: "Thaw Hall",
      entrance: "SRCC/Thaw shared lobby on O'Hara St",
      coords: [-79.95763, 40.44516]
    },
    {
      name: "Public Health Building",
      entrance: "Fifth Ave main doors",
      coords: [-79.95850, 40.44279]
    },
    {
      name: "Public Health Building",
      entrance: "De Soto St doors",
      coords: [-79.95795, 40.44273]
    }
  ];

  const wheelchairSVG = `
    <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      <path d="M10 4a2 2 0 1 1 0 4 2 2 0 0 1 0-4zm7.3 12.6-2.2-4.3H12V9h1.7l3.3 6.3 2 .1a1 1 0 1 1 0 2h-2a1 1 0 0 1-.7-.4zM9.5 12a5 5 0 1 0 0 10 5 5 0 0 0 0-10zm0 2a3 3 0 1 1 0 6 3 3 0 0 1 0-6z"/>
    </svg>
  `;

  adaEntrances.forEach(({ name, entrance, coords }) => {
    const el = document.createElement("div");
    el.className = "ada-marker";
    el.innerHTML = wheelchairSVG;
    el.setAttribute("role", "img");
    el.setAttribute("aria-label", `${name} accessible entrance: ${entrance}`);

    const popupHtml = `
      <strong>${name}</strong><br>${entrance}
      <div class="coord">[${coords[0].toFixed(5)}, ${coords[1].toFixed(5)}]</div>
    `;

    new mapboxgl.Marker({ element: el })
      .setLngLat(coords)
      .setPopup(new mapboxgl.Popup({ offset: 12 }).setHTML(popupHtml))
      .addTo(map);
  });
}

// Fetch directions and draw route
window.getDirections = async function() {
  const fromName = document.getElementById("from-input").value;
  const toName = document.getElementById("to-input").value;
  const startId = findNodeIdByName(fromName);
  const endId = findNodeIdByName(toName);

  if (!startId || !endId) {
    alert("Start or End location not found. Please select from the autocomplete list.");
    return;
  }
  const startNode = nodeList.find(n => n.nodeId === startId);
  const endNode = nodeList.find(n => n.nodeId === endId);

  // Fetch directions from backend
  const res = await fetch(`/directions?start=${encodeURIComponent(startId)}&end=${encodeURIComponent(endId)}`);
  const data = await res.json();

  // Remove previous route layer/source if any
  if (map.getLayer(routeLayerId)) map.removeLayer(routeLayerId);
  if (map.getSource(routeSourceId)) map.removeSource(routeSourceId);

  // If your backend returns route coordinates, draw them
  if (data.route && data.route.length > 0) {
    map.addSource(routeSourceId, {
      type: "geojson",
      data: {
        type: "Feature",
        geometry: {
          type: "LineString",
          coordinates: data.route
        }
      }
    });
    map.addLayer({
      id: routeLayerId,
      type: "line",
      source: routeSourceId,
      paint: {
        "line-color": "#ff0000",
        "line-width": 5
      }
    });
    // Add start/end markers
    new mapboxgl.Marker({ color: "green" }).setLngLat(data.route[0]).addTo(map);
    new mapboxgl.Marker({ color: "blue" }).setLngLat(data.route[data.route.length - 1]).addTo(map);
    map.fitBounds([data.route[0], data.route[data.route.length - 1]], { padding: 80 });
  } else {
    // If route not found, just show start/end markers
    new mapboxgl.Marker({ color: "green" }).setLngLat([startNode.coordinates.lng, startNode.coordinates.lat]).addTo(map);
    new mapboxgl.Marker({ color: "blue" }).setLngLat([endNode.coordinates.lng, endNode.coordinates.lat]).addTo(map);
    map.flyTo({ center: [startNode.coordinates.lng, startNode.coordinates.lat], zoom: 16 });
    alert("No route found.");
  }

  // Show directions text (if any)
  if (data.directions) {
    alert("Directions:\n" + data.directions.join("\n"));
  }
  // Show obstacles (if any)
  if (data.obstacles && data.obstacles.length) {
    data.obstacles.forEach(obs => {
      new mapboxgl.Marker({ color: "#ff6b35" })
        .setLngLat([obs.coords.lng, obs.coords.lat])
        .setPopup(new mapboxgl.Popup().setHTML(`<b>Obstacle:</b><br>${obs.description}`))
        .addTo(map);
    });
  }
};

// ========== Obstacle Popup Logic ==========
window.openObstaclePopup = function() {
  document.getElementById("obstaclePopup").classList.add("show");
  getCurrentGPS();
};

window.closeObstaclePopup = function() {
  document.getElementById("obstaclePopup").classList.remove("show");
  document.getElementById("obstacleDescription").value = "";
  document.getElementById("photoPreview").style.display = "none";
  document.getElementById("cameraInput").value = "";
};

window.triggerCamera = function() {
  document.getElementById("cameraInput").click();
};

window.previewPhoto = function(event) {
  const file = event.target.files[0];
  if (file) {
    const reader = new FileReader();
    reader.onload = function(e) {
      const preview = document.getElementById("photoPreview");
      preview.src = e.target.result;
      preview.style.display = "block";
    };
    reader.readAsDataURL(file);
  }
};

function getCurrentGPS() {
  const gpsDisplay = document.getElementById("gpsCoords");
  if (!navigator.geolocation) {
    gpsDisplay.textContent = "GPS not supported by this browser.";
    return;
  }
  gpsDisplay.textContent = "Getting current location...";
  navigator.geolocation.getCurrentPosition(
    function(position) {
      const lat = position.coords.latitude.toFixed(6);
      const lng = position.coords.longitude.toFixed(6);
      gpsDisplay.innerHTML = `Latitude: ${lat}<br>Longitude: ${lng}`;
      currentPosition = { lat: parseFloat(lat), lng: parseFloat(lng) };
    },
    function(error) {
      let errorMsg;
      switch (error.code) {
        case error.PERMISSION_DENIED:
          errorMsg = "Location access denied by user.";
          break;
        case error.POSITION_UNAVAILABLE:
          errorMsg = "Location information unavailable.";
          break;
        case error.TIMEOUT:
          errorMsg = "Location request timed out.";
          break;
        default:
          errorMsg = "Unknown error getting location.";
          break;
      }
      gpsDisplay.textContent = errorMsg;
      console.error("Geolocation error:", error);
    },
    {
      enableHighAccuracy: true,
      timeout: 10000,
      maximumAge: 60000
    }
  );
}

// Obstacle report submit
async function compressImage(file, maxWidth = 800, quality = 0.7) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);

    reader.onload = event => {
      const img = new Image();
      img.src = event.target.result;

      img.onload = () => {
        const canvas = document.createElement("canvas");
        const scaleSize = maxWidth / img.width;
        canvas.width = maxWidth;
        canvas.height = img.height * scaleSize;
        const ctx = canvas.getContext("2d");
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        canvas.toBlob(
          blob => {
            resolve(new File([blob], file.name, { type: "image/jpeg" }));
          },
          "image/jpeg",
          quality
        );
      };
      img.onerror = reject;
    };
    reader.onerror = reject;
  });
}

window.submitObstacle = async function() {
  const description = document.getElementById("obstacleDescription").value;
  const photoFile = document.getElementById("cameraInput").files[0];

  if (!description.trim()) {
    alert("Please describe the obstacle before submitting.");
    return;
  }
  if (!photoFile) {
    alert("Please take a photo of the obstacle before submitting.");
    return;
  }
  if (!currentPosition) {
    alert("GPS location is required. Please wait for location to be detected.");
    return;
  }

  const submitBtn = document.querySelector(".submit-btn");
  const originalText = submitBtn.textContent;
  submitBtn.textContent = "Compressing...";
  submitBtn.disabled = true;

  try {
    // Compress before upload
    const compressedFile = await compressImage(photoFile, 800, 0.7);

    const formData = new FormData();
    formData.append("image", compressedFile);
    formData.append("gps_coordinates", JSON.stringify({
      lat: currentPosition.lat,
      lng: currentPosition.lng
    }));
    formData.append("description", description);

    const response = await fetch("/report-obstacle", {
      method: "POST",
      body: formData
    });

    if (!response.ok) {
      let errorMsg;
      try {
        const errorData = await response.json();
        errorMsg = errorData.detail || `HTTP error! status: ${response.status}`;
      } catch {
        errorMsg = `Non-JSON error response (status ${response.status})`;
      }
      throw new Error(errorMsg);
    }

    const result = await response.json();

    if (result.analysis && result.analysis.is_obstacle) {
      alert(`Obstacle detected!\nType: ${result.analysis.obstacle_type}\nConfidence: ${result.analysis.confidence}`);
    } else {
      alert("No obstacle detected.\nThe way looks clear.");
    }

    console.log("AI Result:", result);
    closeObstaclePopup();

  } catch (error) {
    console.error("Error submitting obstacle report:", error);
    alert(`Error: ${error.message}`);
  } finally {
    submitBtn.textContent = originalText;
    submitBtn.disabled = false;
  }
};

// Gemini Service status check
async function checkGeminiStatus() {
  try {
    const response = await fetch("/gemini-status");
    const status = await response.json();
    if (!status.gemini_available) {
      console.warn("Gemini obstacle detection service is not available");
    }
    return status.gemini_available;
  } catch (error) {
    console.error("Error checking Gemini status:", error);
    return false;
  }
}

document.addEventListener('DOMContentLoaded', function() {
  checkGeminiStatus();
});

// Check service status when page loads
document.addEventListener('DOMContentLoaded', function() {
  checkGeminiStatus();
});
