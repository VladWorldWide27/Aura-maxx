mapboxgl.accessToken =
  "pk.eyJ1IjoiZGVpYW5vdnZ2IiwiYSI6ImNtZmhhc2xvbDA5aWcyaXEzNmd0YTN5ZXoifQ.D_zOKU7AeIB6iLBhd3umAw"
// this is vlad's key. since it is connected to my credit card, please, do not abuse it and create your own keys
navigator.geolocation.getCurrentPosition(successLocation, errorLocation, {
  enableHighAccuracy: true
});

let map;
let currentPosition = null;
let routeVisible = false;
let availableBuildings = [];

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

async function loadAvailableBuildings() {
  try {
    const response = await fetch('http://127.0.0.1:8000/buildings');
    const data = await response.json();
    availableBuildings = data.buildings;
    
    // Set up autocomplete for building inputs
    setupBuildingAutocomplete();
    
    console.log(`✅ Loaded ${availableBuildings.length} buildings:`, availableBuildings);
  } catch (error) {
    console.error('Error loading buildings:', error);
  }
}

function setupBuildingAutocomplete() {
  const fromInput = document.getElementById('from-input');
  const toInput = document.getElementById('to-input');
  
  // Update placeholders with example building names
  if (availableBuildings.length > 0) {
    fromInput.placeholder = `e.g., ${availableBuildings[0]}`;
    toInput.placeholder = `e.g., ${availableBuildings[1] || availableBuildings[0]}`;
  }
  
  // Add datalist for autocomplete
  const datalist = document.createElement('datalist');
  datalist.id = 'buildings-list';
  
  availableBuildings.forEach(building => {
    const option = document.createElement('option');
    option.value = building;
    datalist.appendChild(option);
  });
  
  document.body.appendChild(datalist);
  
  // Connect datalist to inputs
  fromInput.setAttribute('list', 'buildings-list');
  toInput.setAttribute('list', 'buildings-list');
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
  
  map.on("load", () => {
    // Load available buildings
    loadAvailableBuildings();
    
    // Add route source (initially empty)
    map.addSource("dynamic-route", {
      type: "geojson",
      data: {
        type: "Feature",
        geometry: {
          type: "LineString",
          coordinates: []
        }
      }
    });

    // Load and display accessibility markers
    loadAccessibilityMarkers();
  });
}

function loadAccessibilityMarkers() {
  // accessible entrances to display (mapbox order: [lng, lat])
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

// Function to get dynamic directions
async function getDirections() {
  const fromBuilding = document.getElementById('from-input').value.trim();
  const toBuilding = document.getElementById('to-input').value.trim();
  
  if (!fromBuilding || !toBuilding) {
    alert('Please enter both starting and destination buildings.');
    return;
  }
  
  if (fromBuilding === toBuilding) {
    alert('Starting and destination buildings cannot be the same.');
    return;
  }
  
  // Update button state
  const button = document.querySelector('.get-directions-btn');
  const originalText = button.textContent;
  button.textContent = 'Finding Route...';
  button.disabled = true;
  
  try {
    const response = await fetch(`http://127.0.0.1:8000/directions?start=${encodeURIComponent(fromBuilding)}&end=${encodeURIComponent(toBuilding)}`);
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || `HTTP ${response.status}`);
    }
    
    const routeData = await response.json();
    
    if (routeData.path_found && routeData.route_coordinates.length > 0) {
      // Clear any existing route
      clearRoute();
      
      // Update the route source with new coordinates
      map.getSource("dynamic-route").setData({
        type: "Feature",
        geometry: {
          type: "LineString",
          coordinates: routeData.route_coordinates
        }
      });
      
      // Add the route layer if it doesn't exist
      if (!map.getLayer("dynamic-route")) {
        map.addLayer({
          id: "dynamic-route",
          type: "line",
          source: "dynamic-route",
          paint: {
            "line-color": "#0074D9",
            "line-width": 4,
            "line-opacity": 0.8
          }
        });
      }
      
      // Add start and end markers
      const coordinates = routeData.route_coordinates;
      const startCoord = coordinates[0];
      const endCoord = coordinates[coordinates.length - 1];
      
      new mapboxgl.Marker({ color: "green" })
        .setLngLat(startCoord)
        .setPopup(new mapboxgl.Popup().setHTML(`<strong>Start:</strong> ${fromBuilding}`))
        .addTo(map);
        
      new mapboxgl.Marker({ color: "red" })
        .setLngLat(endCoord)
        .setPopup(new mapboxgl.Popup().setHTML(`<strong>Destination:</strong> ${toBuilding}`))
        .addTo(map);
      
      // Fit map to route bounds
      const bounds = new mapboxgl.LngLatBounds();
      coordinates.forEach(coord => bounds.extend(coord));
      map.fitBounds(bounds, { padding: 50 });
      
      routeVisible = true;
      
      // Show info about blocked nodes if any
      if (routeData.blocked_nodes && routeData.blocked_nodes.length > 0) {
        console.log(`⚠️ Route avoids ${routeData.blocked_nodes.length} blocked nodes due to obstacles`);
      }
      
      alert(`Route found from ${fromBuilding} to ${toBuilding}!`);
      
    } else {
      alert('No route found between these buildings.');
    }
    
  } catch (error) {
    console.error('Error getting directions:', error);
    alert(`Error: ${error.message}`);
  } finally {
    button.textContent = originalText;
    button.disabled = false;
  }
}

function clearRoute() {
  // Clear existing route
  if (map.getSource("dynamic-route")) {
    map.getSource("dynamic-route").setData({
      type: "Feature", 
      geometry: {
        type: "LineString",
        coordinates: []
      }
    });
  }
  
  // Remove existing markers (except accessibility markers)
  const markers = document.querySelectorAll('.mapboxgl-marker:not(.ada-marker)');
  markers.forEach(marker => {
    if (!marker.parentElement.classList.contains('ada-marker')) {
      marker.remove();
    }
  });
  
  routeVisible = false;
}
