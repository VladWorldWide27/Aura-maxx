mapboxgl.accessToken =
  "pk.eyJ1IjoiZGVpYW5vdnZ2IiwiYSI6ImNtZmhhc2xvbDA5aWcyaXEzNmd0YTN5ZXoifQ.D_zOKU7AeIB6iLBhd3umAw"
// this is vlad's key. since it is connected to my credit card, please, do not abuse it and create your own keys
navigator.geolocation.getCurrentPosition(successLocation, errorLocation, {
  enableHighAccuracy: true
});

let map;
let currentPosition = null;


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
  
 
  const routeCoords = [
    [-79.9611011,40.4373888], // 304 Coltart
    [-79.9605289, 40.4389107], // enter 5th
    [-79.9602472, 40.4393695], // along 5th
    [-79.9601826, 40.439956],
    [-79.9551722, 40.4434976],
    [-79.9551722, 40.4434976],    
  ];
  
  map.on("load", () => {
    map.addSource("custom-route", {
      type: "geojson",
      data: {
        type: "Feature",
        geometry: {
          type: "LineString",
          coordinates: routeCoords
        }
      }
    });
    
    map.addLayer({
      id: "custom-route",
      type: "line",
      source: "custom-route",
      paint: {
        "line-color": "#ff0000",
        "line-width": 5
      }
    });
    
    // Mark start & end
    new mapboxgl.Marker({ color: "green" }).setLngLat(routeCoords[0]).addTo(map);
    new mapboxgl.Marker({ color: "blue" }).setLngLat(routeCoords[routeCoords.length - 1]).addTo(map);
  });
}


function openObstaclePopup() {
  document.getElementById('obstaclePopup').classList.add('show');
  getCurrentGPS();
}

function closeObstaclePopup() {
  document.getElementById('obstaclePopup').classList.remove('show');
  document.getElementById('obstacleDescription').value = '';
  document.getElementById('photoPreview').style.display = 'none';
  document.getElementById('cameraInput').value = '';
}

function triggerCamera() {
  document.getElementById('cameraInput').click();
}

function previewPhoto(event) {
  const file = event.target.files[0];
  if (file) {
    const reader = new FileReader();
    reader.onload = function(e) {
      const preview = document.getElementById('photoPreview');
      preview.src = e.target.result;
      preview.style.display = 'block';
    };
    reader.readAsDataURL(file);
  }
}

function getCurrentGPS() {
  const gpsDisplay = document.getElementById('gpsCoords');
  
  if (navigator.geolocation) {
    gpsDisplay.textContent = 'Getting current location...';
    
    navigator.geolocation.getCurrentPosition(
      function(position) {
        const lat = position.coords.latitude.toFixed(6);
        const lng = position.coords.longitude.toFixed(6);
        gpsDisplay.innerHTML = `Latitude: ${lat}<br>Longitude: ${lng}`;
        currentPosition = { lat: parseFloat(lat), lng: parseFloat(lng) };
      },
      function(error) {
        gpsDisplay.textContent = 'Unable to get location. Please enable GPS.';
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 60000
      }
    );
  } else {
    gpsDisplay.textContent = 'GPS not supported by this browser.';
  }
}

function submitObstacle() {
  const description = document.getElementById('obstacleDescription').value;
  const photoFile = document.getElementById('cameraInput').files[0];
  
  if (!description.trim()) {
    alert('Please describe the obstacle before submitting.');
    return;
  }
  
  
  console.log('Obstacle Report:', {
    description: description,
    photo: photoFile,
    coordinates: currentPosition,
    timestamp: new Date().toISOString()
  });
  
  alert('Obstacle report submitted successfully!');
  closeObstaclePopup();
}