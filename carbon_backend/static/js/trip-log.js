// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM Content Loaded");
    
    // Setup transport mode selection
    setupTransportOptions();
    
    // Additional direct event handling for transport options - using event delegation
    const optionsContainer = document.getElementById('transport-options-container');
    if (optionsContainer) {
        optionsContainer.addEventListener('click', function(e) {
            // Find the closest transport option
            const option = e.target.closest('.transport-option');
            if (option) {
                const transportMode = option.getAttribute('data-mode');
                console.log("Direct click handler triggered for:", transportMode);
                
                // Clear all selections
                document.querySelectorAll('.transport-option').forEach(opt => {
                    opt.classList.remove('selected');
                });
                
                // Set this option as selected
                option.classList.add('selected');
                
                // Update form value
                const transportInput = document.getElementById('transport-mode');
                if (transportInput) {
                    transportInput.value = transportMode;
                    console.log("Set transport mode to:", transportMode);
                    
                    // Special handling for work from home
                    if (transportMode === 'work_from_home') {
                        const mapSection = document.getElementById('map-section');
                        if (mapSection) mapSection.style.display = 'none';
                        
                        const distanceInput = document.getElementById('distance-km');
                        if (distanceInput) distanceInput.value = '0';
                        
                        updateTripPreview(0, 0);
                    } else {
                        const mapSection = document.getElementById('map-section');
                        if (mapSection) mapSection.style.display = 'block';
                        
                        calculateRouteIfPossible();
                    }
                }
            }
        });
    }
    
    // We don't initialize the map here anymore - it will be called by the callback
});

// Set up transport option clicks
function setupTransportOptions() {
    console.log("Setting up transport options");
    const transportOptions = document.querySelectorAll('.transport-option');
    
    if (transportOptions.length === 0) {
        console.warn("No transport options found");
        return;
    }
    
    console.log(`Found ${transportOptions.length} transport options`);
    
    transportOptions.forEach(option => {
        option.addEventListener('click', function(e) {
            e.preventDefault();
            console.log("Transport option clicked:", this.getAttribute('data-mode'));
            
            // Remove selected class from all options
            transportOptions.forEach(opt => {
                opt.classList.remove('selected');
            });
            
            // Add selected class to clicked option
            this.classList.add('selected');
            
            // Update hidden input with selected transport mode
            const transportMode = this.getAttribute('data-mode');
            const transportModeInput = document.getElementById('transport-mode');
            
            if (!transportModeInput) {
                console.error("Transport mode input not found");
                return;
            }
            
            transportModeInput.value = transportMode;
            console.log("Selected transport mode:", transportMode);
            
            // Special handling for work from home
            const mapSection = document.getElementById('map-section');
            const distanceInput = document.getElementById('distance-km');
            
            if (transportMode === 'work_from_home') {
                if (mapSection) mapSection.style.display = 'none';
                if (distanceInput) distanceInput.value = '0';
                updateTripPreview(0, 0);
            } else {
                if (mapSection) mapSection.style.display = 'block';
                calculateRouteIfPossible();
            }
        });
    });
}

// Add a temporary notification
function addNotification(message, type = 'info') {
    const container = document.createElement('div');
    container.className = `p-4 rounded-lg mb-4 ${
        type === 'success' ? 'bg-green-100 text-green-800' : 
        type === 'error' ? 'bg-red-100 text-red-800' : 
        'bg-blue-100 text-blue-800'
    }`;
    container.textContent = message;
    
    // Find the messages section or create one
    let messagesSection = document.querySelector('.messages-section');
    if (!messagesSection) {
        messagesSection = document.createElement('div');
        messagesSection.className = 'messages-section mb-6';
        
        // Insert after the header section
        const header = document.querySelector('.relative.mb-8');
        header.parentNode.insertBefore(messagesSection, header.nextSibling);
    }
    
    // Add the notification
    messagesSection.appendChild(container);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        container.style.opacity = '0';
        container.style.transition = 'opacity 0.5s ease';
        
        setTimeout(() => {
            if (container.parentNode) {
                container.parentNode.removeChild(container);
            }
        }, 500);
    }, 5000);
}

// Global variables for map components
let map, startMarker, endMarker, directionsService, directionsRenderer;

// Initialize Google Maps when API is loaded
function initMap() {
    console.log("Google Maps API loaded");
    
    // Hide all map loading indicators
    document.querySelectorAll('.map-loading').forEach(loading => {
        loading.style.display = 'none';
    });
    
    // Create map
    const mapElement = document.getElementById('trip-map');
    if (!mapElement) {
        console.error("Map element not found");
        return;
    }
    
    map = new google.maps.Map(mapElement, {
        zoom: 12,
        center: { lat: 27.6648, lng: -81.5158 }, // Default center (Florida)
        mapTypeControl: true,
        streetViewControl: false,
        fullscreenControl: true
    });
    
    // Create markers for start and end locations
    startMarker = new google.maps.Marker({
        map: map,
        icon: {
            url: 'https://maps.google.com/mapfiles/ms/icons/blue-dot.png',
            scaledSize: new google.maps.Size(40, 40)
        },
        animation: google.maps.Animation.DROP,
        title: 'Start Location'
    });
    
    endMarker = new google.maps.Marker({
        map: map,
        icon: {
            url: 'https://maps.google.com/mapfiles/ms/icons/red-dot.png',
            scaledSize: new google.maps.Size(40, 40)
        },
        animation: google.maps.Animation.DROP,
        title: 'End Location'
    });
    
    // Hide markers initially
    startMarker.setMap(null);
    endMarker.setMap(null);
    
    // Create directions service and renderer
    directionsService = new google.maps.DirectionsService();
    directionsRenderer = new google.maps.DirectionsRenderer({
        map: map,
        suppressMarkers: true,
        polylineOptions: {
            strokeColor: '#10B981',
            strokeWeight: 5,
            strokeOpacity: 0.7
        }
    });
    
    // Set up search box
    const searchInput = document.getElementById('map-search-input');
    if (searchInput) {
        const searchBox = new google.maps.places.SearchBox(searchInput);
        
        // Bias search results to current map view
        map.addListener('bounds_changed', function() {
            searchBox.setBounds(map.getBounds());
        });
        
        // Handle search results
        searchBox.addListener('places_changed', function() {
            const places = searchBox.getPlaces();
            if (places.length === 0) return;
            
            const place = places[0];
            if (!place.geometry || !place.geometry.location) return;
            
            // Get location coordinates
            const location = {
                lat: place.geometry.location.lat(),
                lng: place.geometry.location.lng(),
                address: place.formatted_address || place.name
            };
            
            // Determine if we're setting start or end location
            const activeSelect = document.activeElement;
            if (activeSelect && activeSelect.id === 'start-location') {
                // Set start location
                startMarker.setPosition(location);
                startMarker.setMap(map);
                activeSelect.value = 'other';
                
                // Update hidden fields
                document.getElementById('custom-lat').value = location.lat;
                document.getElementById('custom-lng').value = location.lng;
                document.getElementById('custom-address').value = location.address;
            } else if (activeSelect && activeSelect.id === 'end-location') {
                // Set end location
                endMarker.setPosition(location);
                endMarker.setMap(map);
                activeSelect.value = 'other';
                
                // Update hidden fields
                document.getElementById('custom-lat').value = location.lat;
                document.getElementById('custom-lng').value = location.lng;
                document.getElementById('custom-address').value = location.address;
            } else {
                // Default to setting center of map
                map.setCenter(location);
            }
            
            // Try to calculate route
            if (startMarker.getMap() && endMarker.getMap()) {
                calculateRoute();
            }
        });
    }
    
    // Set up location selectors
    const startSelect = document.getElementById('start-location');
    const endSelect = document.getElementById('end-location');
    
    if (startSelect) {
        startSelect.addEventListener('change', function() {
            handleLocationSelection(this.value, 'start');
        });
    }
    
    if (endSelect) {
        endSelect.addEventListener('change', function() {
            handleLocationSelection(this.value, 'end');
        });
    }
}

// Handle location selection from dropdowns
function handleLocationSelection(locationValue, locationType) {
    if (!locationValue) return;
    
    // Skip for "other" option (handled by map click)
    if (locationValue === 'other') return;
    
    // Get selected option
    const select = document.getElementById(locationType + '-location');
    const option = select.options[select.selectedIndex];
    
    if (!option) return;
    
    // Get coordinates from data attributes
    const lat = option.getAttribute('data-lat');
    const lng = option.getAttribute('data-lng');
    
    if (!lat || !lng) {
        console.warn('Selected location missing coordinates');
        return;
    }
    
    const location = {
        lat: parseFloat(lat),
        lng: parseFloat(lng)
    };
    
    // Set appropriate marker
    if (locationType === 'start') {
        startMarker.setPosition(location);
        startMarker.setMap(map);
    } else {
        endMarker.setPosition(location);
        endMarker.setMap(map);
    }
    
    // Center map on this location
    map.setCenter(location);
    
    // Try to calculate route
    if (startMarker.getMap() && endMarker.getMap()) {
        calculateRoute();
    }
}

// Calculate route between start and end
function calculateRoute() {
    if (!startMarker.getMap() || !endMarker.getMap()) {
        console.warn('Cannot calculate route: missing markers');
        return;
    }
    
    // Get transport mode from selected option
    const transportMode = document.getElementById('transport-mode').value;
    if (!transportMode) {
        console.warn('No transport mode selected');
        return;
    }
    
    // Map transport modes to Google Maps travel modes
    let travelMode;
    switch (transportMode) {
        case 'walking':
            travelMode = google.maps.TravelMode.WALKING;
            break;
        case 'bicycle':
            travelMode = google.maps.TravelMode.BICYCLING;
            break;
        case 'public_transport':
            travelMode = google.maps.TravelMode.TRANSIT;
            break;
        default:
            travelMode = google.maps.TravelMode.DRIVING;
    }
    
    // Create route request
    const request = {
        origin: startMarker.getPosition(),
        destination: endMarker.getPosition(),
        travelMode: travelMode
    };
    
    // Calculate route
    directionsService.route(request, function(result, status) {
        if (status === google.maps.DirectionsStatus.OK) {
            // Display route
            directionsRenderer.setDirections(result);
            
            // Calculate distance and duration
            const route = result.routes[0];
            let distance = 0;
            let duration = 0;
            
            route.legs.forEach(leg => {
                distance += leg.distance.value;
                duration += leg.duration.value;
            });
            
            // Convert to km and minutes
            const distanceKm = Math.round(distance / 100) / 10;
            const durationMin = Math.round(duration / 60);
            
            // Update hidden field
            document.getElementById('distance-km').value = distanceKm;
            
            // Update preview
            updateTripPreview(distanceKm, durationMin);
        } else {
            console.error('Directions request failed:', status);
        }
    });
}

// Calculate route if possible (called from transport mode selection)
function calculateRouteIfPossible() {
    if (startMarker && endMarker && startMarker.getMap() && endMarker.getMap()) {
        calculateRoute();
    }
}

// Update trip preview with calculated values
function updateTripPreview(distance, duration) {
    const previewSection = document.getElementById('trip-preview');
    if (!previewSection) return;
    
    // Show preview section
    previewSection.classList.remove('hidden');
    
    // Get selected transport mode
    const transportMode = document.getElementById('transport-mode').value;
    
    // Set mode name and credit rate
    let modeName = 'Unknown';
    let creditsPerKm = 0.5;
    
    switch (transportMode) {
        case 'walking':
            modeName = 'Walking';
            creditsPerKm = 6;
            break;
        case 'bicycle':
            modeName = 'Bicycle';
            creditsPerKm = 5;
            break;
        case 'public_transport':
            modeName = 'Public Transport';
            creditsPerKm = 3;
            break;
        case 'carpool':
            modeName = 'Carpool';
            creditsPerKm = 2;
            break;
        case 'car':
            modeName = 'Car (Single)';
            creditsPerKm = 0.5;
            break;
        case 'work_from_home':
            modeName = 'Work from Home';
            creditsPerKm = 0;
            break;
    }
    
    // Calculate credits
    let totalCredits = 0;
    if (transportMode === 'work_from_home') {
        totalCredits = 10; // Fixed amount for WFH
    } else {
        totalCredits = Math.round(distance * creditsPerKm * 10) / 10;
    }
    
    // Update preview elements
    document.getElementById('preview-transport').textContent = modeName;
    document.getElementById('preview-distance').textContent = distance + ' km';
    document.getElementById('preview-duration').textContent = duration + ' min';
    document.getElementById('preview-credits').textContent = totalCredits + ' credits';
}

// Make sure initMap is available globally for Google Maps API callback
window.initMap = initMap;
console.log("initMap function exported to window:", typeof window.initMap === 'function' ? 'YES' : 'NO'); 