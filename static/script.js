document.addEventListener('DOMContentLoaded', function() {
    
    // --- 1. Location Functionality ---
    const locationBtn = document.getElementById('get-location');
    const latInput = document.getElementById('latitude');
    const longInput = document.getElementById('longitude');
    const locationStatus = document.getElementById('location-status');

    if (locationBtn) {
        locationBtn.addEventListener('click', function() {
            if (!navigator.geolocation) {
                alert("Aapke browser mein Location support nahi hai.");
                return;
            }

            locationStatus.textContent = "Location fetch ho rahi hai...";
            locationStatus.style.color = "orange";

            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const lat = position.coords.latitude;
                    const long = position.coords.longitude;

                    // Hidden inputs mein value set karna
                    latInput.value = lat;
                    longInput.value = long;

                    locationStatus.textContent = `Location Set: ${lat.toFixed(4)}, ${long.toFixed(4)}`;
                    locationStatus.style.color = "green";
                    locationBtn.disabled = true;
                    locationBtn.textContent = "Location Set Ho Gaya";
                },
                (error) => {
                    locationStatus.textContent = "Location access nahi mila. Please allow permissions.";
                    locationStatus.style.color = "red";
                    console.error(error);
                }
            );
        });
    }

    // --- 2. Image Preview Functionality ---
    const photoInput = document.getElementById('photo');
    const previewContainer = document.getElementById('image-preview');

    if (photoInput && previewContainer) {
        photoInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                
                reader.onload = function(e) {
                    previewContainer.innerHTML = `<img src="${e.target.result}" alt="Preview" style="max-width: 100%; height: auto; border-radius: 5px; margin-top: 10px;">`;
                }
                
                reader.readAsDataURL(file);
            } else {
                previewContainer.innerHTML = '';
            }
        });
    }
});