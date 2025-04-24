// Initialize Google Maps
let map;
let marker;
let geocoder;

function initMap() {
    // Default center (San Francisco)
    const defaultLocation = { lat: 37.7749, lng: -122.4194 };
    
    // Create map
    map = new google.maps.Map(document.getElementById('home-map'), {
        zoom: 13,
        center: defaultLocation,
        mapTypeControl: true,
        streetViewControl: false,
        fullscreenControl: true
    });
    
    // Create marker for home location
    marker = new google.maps.Marker({
        position: defaultLocation,
        map: map,
        draggable: true,
        animation: google.maps.Animation.DROP,
        title: 'Your Home Location'
    });
    
    // Update latitude and longitude fields when marker is moved
    google.maps.event.addListener(marker, 'dragend', function() {
        reverseGeocode(marker.getPosition());
    });
    
    // Set up the search box
    const searchInput = document.getElementById('map-search-input');
    const searchBox = new google.maps.places.SearchBox(searchInput);
    
    // Bias search results to current map view
    map.addListener('bounds_changed', () => {
        searchBox.setBounds(map.getBounds());
    });
    
    // Listen for search box selections
    searchBox.addListener('places_changed', () => {
        const places = searchBox.getPlaces();
        if (places.length === 0) return;
        
        const place = places[0];
        if (!place.geometry || !place.geometry.location) return;
        
        // Set marker position to selected place
        marker.setPosition(place.geometry.location);
        map.setCenter(place.geometry.location);
        map.setZoom(15);
        
        // Update address field
        document.getElementById('id_home_address').value = place.formatted_address;
    });
    
    // Listen for click on map
    map.addListener('click', (event) => {
        marker.setPosition(event.latLng);
        reverseGeocode(event.latLng);
    });
}

function reverseGeocode(position) {
    if (!geocoder) {
        geocoder = new google.maps.Geocoder();
    }
    
    geocoder.geocode({'location': position}, function(results, status) {
        if (status === 'OK' && results[0]) {
            document.getElementById('id_home_address').value = results[0].formatted_address;
        }
    });
}

function setupFormValidation() {
    const form = document.getElementById('employeeRegistrationForm');
    
    form.addEventListener('submit', function(e) {
        if (!validateForm()) {
            e.preventDefault();
        }
    });
}

function validateForm() {
    let isValid = true;
    const requiredFields = [
        'id_email',
        'id_username',
        'id_password',
        'id_first_name',
        'id_last_name',
        'id_employer',
        'id_home_address',
        'id_terms'
    ];
    
    requiredFields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (!field || !field.value.trim()) {
            if (field) field.classList.add('is-invalid');
            isValid = false;
        } else {
            field.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

// Initialize map when the page loads
document.addEventListener('DOMContentLoaded', function() {
    // Initialize the map
    initMap();
    
    // Set up form validation
    setupFormValidation();
}); 