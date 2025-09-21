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
  
 
  const routeCoords = [[-79.956718, 40.443175], [-79.95667804, 40.44321601], [-79.95663504, 40.4432468], [-79.956584, 40.443264], [-79.95654905, 40.44330839], [-79.95650605, 40.44333918], [-79.95646305, 40.44336997], [-79.95642005, 40.44340077], [-79.95637705, 40.44343156], [-79.95633405, 40.44346235], [-79.95629105, 40.44349314], [-79.95624805, 40.44352394], [-79.95620505, 40.44355473], [-79.95616205, 40.44358552], [-79.95611905, 40.44361632], [-79.95607605, 40.44364711], [-79.95603305, 40.4436779], [-79.95599005, 40.44370869], [-79.95594705, 40.44373949], [-79.95590405, 40.44377028], [-79.95586105, 40.44380107], [-79.955862, 40.443851], [-79.9559245, 40.44389937], [-79.9559659, 40.44393142], [-79.9560073, 40.44396346], [-79.9560487, 40.44399551], [-79.95609011, 40.44402755], [-79.95613151, 40.4440596], [-79.95617291, 40.44409165], [-79.95621431, 40.44412369], [-79.95625572, 40.44415574], [-79.95629712, 40.44418778], [-79.95633852, 40.44421983], [-79.95637992, 40.44425187], [-79.95642133, 40.44428392], [-79.95646273, 40.44431596], [-79.95650413, 40.44434801], [-79.95654553, 40.44438005], [-79.95658694, 40.4444121], [-79.95662834, 40.44444414], [-79.95666974, 40.44447619], [-79.95671115, 40.44450823], [-79.95675255, 40.44454028], [-79.95679395, 40.44457232], [-79.95683535, 40.44460437], [-79.95687676, 40.44463641], [-79.95691816, 40.44466846], [-79.95695956, 40.4447005], [-79.95700097, 40.44473255], [-79.95704237, 40.4447646], [-79.95708377, 40.44479664], [-79.95712518, 40.44482869], [-79.95716658, 40.44486073], [-79.95720798, 40.44489278], [-79.95724939, 40.44492482], [-79.95729079, 40.44495687], [-79.95733219, 40.44498891], [-79.9573736, 40.44502096], [-79.957415, 40.445053]];
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

    // accessible entrances to display (mapbox order: [lng, lat])
const adaEntrances = [
  //thackeray
  {
    name: "Thackeray Hall",
    entrance: "University Place ground level doors",
    coords: [-79.95725, 40.44432]
  },

  //old engineering
  {
    name: "Old Engineering Hall",
    entrance: "O'Hara St entrance",
    coords: [-79.958045, 40.444959]
  },

  //allen hall
  {
    name: "Allen Hall",
    entrance: "O'Hara St entrance",
    coords: [-79.95837, 40.44458]
  },

  //thaw hall
  {
    name: "Thaw Hall",
    entrance: "SRCC/Thaw shared lobby on O'Hara St",
    coords: [-79.95763, 40.44516]
  },

  //pitt public health
  {
    name: "Public Health Building",
    entrance: "Fifth Ave main doors",
    coords: [-79.95850, 40.44279]
  },
  {
    name: "Public Health Building",
    entrance: "De Soto St doors",
    // slight east-side offset toward De Soto; tweak on site if needed
    coords: [-79.95795, 40.44273]
  }
];

// Simple wheelchair SVG you can reuse
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
  
  if (!navigator.geolocation) {
    gpsDisplay.textContent = 'GPS not supported by this browser.';
    return;
  }
  
  gpsDisplay.textContent = 'Getting current location...';
  
  navigator.geolocation.getCurrentPosition(
    function(position) {
      const lat = position.coords.latitude.toFixed(6);
      const lng = position.coords.longitude.toFixed(6);
      gpsDisplay.innerHTML = `Latitude: ${lat}<br>Longitude: ${lng}`;
      currentPosition = { lat: parseFloat(lat), lng: parseFloat(lng) };
    },
    function(error) {
      let errorMsg;
      switch(error.code) {
        case error.PERMISSION_DENIED:
          errorMsg = 'Location access denied by user.';
          break;
        case error.POSITION_UNAVAILABLE:
          errorMsg = 'Location information unavailable.';
          break;
        case error.TIMEOUT:
          errorMsg = 'Location request timed out.';
          break;
        default:
          errorMsg = 'Unknown error getting location.';
          break;
      }
      gpsDisplay.textContent = errorMsg;
      console.error('Geolocation error:', error);
    },
    {
      enableHighAccuracy: true,
      timeout: 10000,
      maximumAge: 60000
    }
  );
}

async function submitObstacle() {
  const description = document.getElementById('obstacleDescription').value;
  const photoFile = document.getElementById('cameraInput').files[0];

  if (!description.trim()) {
    alert('Please describe the obstacle before submitting.');
    return;
  }
  if (!photoFile) {
    alert('Please take a photo of the obstacle before submitting.');
    return;
  }
  if (!currentPosition) {
    alert('GPS location is required. Please wait for location to be detected.');
    return;
  }

  const submitBtn = document.querySelector('.submit-btn');
  const originalText = submitBtn.textContent;
  submitBtn.textContent = 'Compressing...';
  submitBtn.disabled = true;

  try {
    // Compress before upload
    const compressedFile = await compressImage(photoFile, 800, 0.7);

    const formData = new FormData();
    formData.append('image', compressedFile);
    formData.append('gps_coordinates', JSON.stringify({
      lat: currentPosition.lat,
      lng: currentPosition.lng
    }));
    formData.append('description', description);

    const response = await fetch('http://127.0.0.1:8000/report-obstacle', {
      method: 'POST',
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

    if (result.analysis.is_obstacle) {
      alert(`Obstacle detected!\nType: ${result.analysis.obstacle_type}\nConfidence: ${result.analysis.confidence}`);
    } else {
      alert(`No obstacle detected.\nThe way looks clear.`);
    }

    console.log("AI Result:", result);
    closeObstaclePopup();

  } catch (error) {
    console.error('Error submitting obstacle report:', error);
    alert(`Error: ${error.message}`);
  } finally {
    submitBtn.textContent = originalText;
    submitBtn.disabled = false;
  }
}


// Add function to check Gemini service status
async function checkGeminiStatus() {
  try {
    const response = await fetch('http://127.0.0.1:8000/gemini-status');  // ✅ absolute URL
    const status = await response.json();
    
    if (!status.gemini_available) {
      console.warn('Gemini obstacle detection service is not available');
    }
    
    return status.gemini_available;
  } catch (error) {
    console.error('Error checking Gemini status:', error);
    return false;
  }
}

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
          quality // compression quality (0–1)
        );
      };

      img.onerror = reject;
    };
    reader.onerror = reject;
  });
}


// Check service status when page loads
document.addEventListener('DOMContentLoaded', function() {
  checkGeminiStatus();
});