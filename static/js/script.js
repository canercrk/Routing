// =====================
// GLOBAL DEĞİŞKENLER
// =====================
// Uygulamanın farklı bölümlerinde kullanılacak ana değişkenler burada tanımlanır.
let selectionMode = 'start'; // Kullanıcı haritada hangi noktayı seçecek: 'start' (başlangıç), 'end' (bitiş), 'waypoint' (ara durak)
let leafletMap; // Leaflet harita nesnesi (harita işlemleri için kullanılır)
let customMarkers = {
    start: null, // Başlangıç noktası işaretçisi
    end: null,   // Bitiş noktası işaretçisi
    waypoints: [] // Ara durak işaretçileri (birden fazla olabilir)
};
let intersectionMarkers = []; // Haritadaki tüm kavşak işaretçileri (kullanıcıya seçim kolaylığı sağlar)

// =====================
// SAYFA YÜKLENİNCE BAŞLATILANLAR
// =====================
document.addEventListener('DOMContentLoaded', function() {
    // Haritayı başlat
    initMap();
    // Butonlar ve formlar için olay dinleyicileri ekle
    setupEventListeners();
    // Kullanıcı ayarlarını yükle (daha önce kaydedildiyse)
    loadSavedSettings();
});

// =====================
// KULLANICI AYARLARINI KAYDETME VE YÜKLEME
// =====================
// Kullanıcı yakıt tüketimi, fiyatı ve "gidiş-dönüş" seçimini kaydedebilir.
function saveSettings() {
    const settings = {
        fuelCons: document.getElementById('fuel-consumption-input').value,
        fuelPrice: document.getElementById('fuel-price-input').value,
        returnTrip: document.getElementById('return-trip').checked
    };
    // Ayarları tarayıcıda sakla
    localStorage.setItem('routeSettings', JSON.stringify(settings));
}

function loadSavedSettings() {
    const savedSettings = localStorage.getItem('routeSettings');
    if (savedSettings) {
        const settings = JSON.parse(savedSettings);
        document.getElementById('fuel-consumption-input').value = settings.fuelCons || 7.5;
        document.getElementById('fuel-price-input').value = settings.fuelPrice || 40;
        document.getElementById('return-trip').checked = settings.returnTrip || false;
    }
}

// =====================
// HARİTA BAŞLATMA VE KAVŞAKLARI GÖSTERME
// =====================
// Harita ekrana çizilir ve kavşaklar işaretlenir.
function initMap() {
    // Kayseri'nin merkez koordinatları
    const kayeriCenter = [38.7333, 35.4833];
    leafletMap = L.map('map').setView(kayeriCenter, 13);
    // Harita görselini OpenStreetMap'ten al
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(leafletMap);
    // Sürükleme ve tıklama işlemlerini yönetmek için değişkenler
    let isDragging = false;
    let wasDragged = false;
    let dragStartTime = 0;
    // Harita sürüklenmeye başlandığında
    leafletMap.on('dragstart', function() {
        isDragging = true;
        wasDragged = true;
        dragStartTime = Date.now();
    });
    // Sürükleme bittiğinde
    leafletMap.on('dragend', function() {
        isDragging = false;
        // Sürükleme sonrası kısa bir süre tıklamaları engelle
        setTimeout(function() {
            wasDragged = false;
        }, 300); // 300ms bekle
    });
    // Haritaya tıklanınca (ama sürükleme değilse!)
    leafletMap.on('click', function(e) {
        // Eğer sürükleme yapılıyorsa veya son sürükleme üzerinden yeterli süre geçmediyse işlem yapma
        if (isDragging || wasDragged || (Date.now() - dragStartTime < 200)) {
            return;
        }
        // Gerçek bir tıklama olduğundan emin olduk, nokta seçimini yap
        handleMapClick(e.latlng.lat, e.latlng.lng);
    });
    // Sunucudan kavşakları al ve haritaya ekle
    fetch('/get_intersections')
        .then(response => response.json())
        .then(intersections => {
            intersections.forEach(intersection => {
                // Alanı 5 olanlar mavi, diğerleri yeşil renkte gösterilir
                const iconColor = intersection.area === 5 ? 'blue' : 'green';
                // Kavşak işaretçisi için özel bir simge oluştur
                const markerIcon = L.divIcon({
                    className: 'marker-intersection',
                    html: `<div style="background-color: ${iconColor}; width: 18px; height: 18px; border-radius: 50%; border: 2px solid white;"></div>`,
                    iconSize: [22, 22],
                    iconAnchor: [11, 11]
                });
                // Kavşağı haritaya ekle
                const marker = L.marker(
                    [intersection.latitude, intersection.longitude], 
                    {
                        title: intersection.intersection_name,
                        icon: markerIcon
                    }
                ).addTo(leafletMap);
                marker.intersection = intersection; // Kavşak verisini işaretçiye ekle
                // Kavşak işaretçisine tıklanınca açılacak pencereyi hazırla
                const popupContent = document.createElement('div');
                popupContent.innerHTML = `
                    <strong>${intersection.intersection_name}</strong><br>
                    ID: ${intersection.intersection_id}<br>
                    <button class="btn btn-sm btn-success select-start w-100 mb-1">Başlangıç Olarak Seç</button>
                    <button class="btn btn-sm btn-danger select-end w-100 mb-1">Bitiş Olarak Seç</button>
                    <button class="btn btn-sm btn-warning select-waypoint w-100">Ara Durak Olarak Ekle</button>
                `;
                // Penceredeki butonlara tıklanınca ilgili noktayı seç
                popupContent.querySelector('.select-start').addEventListener('click', function() {
                    handleMapClick(intersection.latitude, intersection.longitude, 'start');
                    leafletMap.closePopup();
                });
                popupContent.querySelector('.select-end').addEventListener('click', function() {
                    handleMapClick(intersection.latitude, intersection.longitude, 'end');
                    leafletMap.closePopup();
                });
                popupContent.querySelector('.select-waypoint').addEventListener('click', function() {
                    handleMapClick(intersection.latitude, intersection.longitude, 'waypoint');
                    leafletMap.closePopup();
                });
                marker.bindPopup(popupContent); // Pencereyi işaretçiye bağla
                marker.on('click', function() {
                    marker.openPopup();
                });
                intersectionMarkers.push(marker); // Listeye ekle
            });
        });
}

// =====================
// BUTONLAR VE FORM OLAYLARI
// =====================
// Kullanıcı arayüzündeki butonlar ve formlar için olay dinleyicileri ekler.
function setupEventListeners() {
    document.getElementById('route-form').addEventListener('submit', calculateRoute);
    const addWaypointBtn = document.getElementById('add-waypoint');
    addWaypointBtn.addEventListener('click', function() {
        openAddStopModal();
    });
    document.getElementById('add-area-waypoints').addEventListener('click', function() {
        const area = document.getElementById('area-select').value;
        if (!area) return;
        fetch('/get_intersections')
            .then(response => response.json())
            .then(data => {
                const selected = data.filter(item => item.area == area);
                selected.forEach(item => {
                    const coordStr = `${item.latitude},${item.longitude}`;
                    if (!isWaypointAlreadyAdded(coordStr)) {
                        addWaypoint(coordStr, item);
                    }
                });
                updateWaypointMarkers();
            });
    });
    document.getElementById('select-start-btn').addEventListener('click', function() {
        setSelectionMode('start');
    });
    document.getElementById('select-end-btn').addEventListener('click', function() {
        setSelectionMode('end');
    });
    document.getElementById('select-waypoint-btn').addEventListener('click', function() {
        setSelectionMode('waypoint');
    });
    // Başlangıç veya bitiş noktası değişirse haritadaki işaretçiyi güncelle
    document.getElementById('start-point').addEventListener('change', function() {
        if (this.value) {
            const [lat, lng] = this.value.split(',').map(parseFloat);
            updateMarker('start', lat, lng);
        }
    });
    document.getElementById('end-point').addEventListener('change', function() {
        if (this.value) {
            const [lat, lng] = this.value.split(',').map(parseFloat);
            updateMarker('end', lat, lng);
        }
    });
}

// =====================
// SEÇİM MODUNU DEĞİŞTİRME
// =====================
// Kullanıcı hangi noktayı seçecekse (başlangıç, bitiş, ara durak) onu ayarlar.
function setSelectionMode(mode) {
    selectionMode = mode;
    document.getElementById('select-start-btn').classList.remove('active');
    document.getElementById('select-end-btn').classList.remove('active');
    document.getElementById('select-waypoint-btn').classList.remove('active');
    if (mode === 'start') {
        document.getElementById('select-start-btn').classList.add('active');
    } else if (mode === 'end') {
        document.getElementById('select-end-btn').classList.add('active');
    } else if (mode === 'waypoint') {
        document.getElementById('select-waypoint-btn').classList.add('active');
    }
}

// =====================
// HARİTADA NOKTA SEÇME
// =====================
// Kullanıcı haritaya tıkladığında veya bir kavşak seçtiğinde çalışır.
// Seçilen noktayı ilgili kutuya yazar ve haritada işaretçi ekler.
function handleMapClick(lat, lng, forceMode = null) {
    const mode = forceMode || selectionMode;
    // En yakın kavşağı bulmak için yardımcı fonksiyon
    function findNearestIntersection(lat, lng) {
        const MAX_DISTANCE = 0.0001; // Yaklaşık 10 metre
        let nearest = null;
        let minDistance = MAX_DISTANCE;
        for (let marker of intersectionMarkers) {
            const intersection = marker.intersection;
            const distance = haversineDistance(lat, lng, intersection.latitude, intersection.longitude);
            if (distance < minDistance) {
                minDistance = distance;
                nearest = intersection;
            }
        }
        return nearest;
    }
    // En yakın kavşağı bul
    const nearestIntersection = findNearestIntersection(lat, lng);
    // Seçim moduna göre işlemler
    if (mode === 'start') {
        document.getElementById('start-point').value = `${lat},${lng}`;
        const select = document.getElementById('start-point');
        const nearestOption = findNearestOption(select, lat, lng);
        if (nearestOption) {
            select.value = nearestOption.value;
        } else {
            if (!hasOption(select, `${lat},${lng}`)) {
                const newOption = document.createElement('option');
                newOption.value = `${lat},${lng}`;
                newOption.textContent = nearestIntersection ? 
                    nearestIntersection.intersection_name : 
                    `Özel Nokta (${lat.toFixed(5)}, ${lng.toFixed(5)})`;
                select.appendChild(newOption);
                select.value = `${lat},${lng}`;
            }
        }
        updateMarker('start', lat, lng);
        // Eğer bitiş noktası seçilmemişse otomatik olarak ona geç
        if (!document.getElementById('end-point').value) {
            setSelectionMode('end');
        }
    } else if (mode === 'end') {
        document.getElementById('end-point').value = `${lat},${lng}`;
        const select = document.getElementById('end-point');
        const nearestOption = findNearestOption(select, lat, lng);
        if (nearestOption) {
            select.value = nearestOption.value;
        } else {
            if (!hasOption(select, `${lat},${lng}`)) {
                const newOption = document.createElement('option');
                newOption.value = `${lat},${lng}`;
                newOption.textContent = nearestIntersection ? 
                    nearestIntersection.intersection_name : 
                    `Özel Nokta (${lat.toFixed(5)}, ${lng.toFixed(5)})`;
                select.appendChild(newOption);
                select.value = `${lat},${lng}`;
            }
        }
        updateMarker('end', lat, lng);
        setSelectionMode('waypoint');
    } else if (mode === 'waypoint') {
        if (!isWaypointAlreadyAdded(`${lat},${lng}`)) {
            addWaypoint(`${lat},${lng}`, nearestIntersection);
            updateWaypointMarkers();
        }
    }
}

// =====================
// YARDIMCI FONKSİYONLAR
// =====================
// Seçenekler arasında bir değer var mı kontrol eder
function hasOption(select, value) {
    for (let i = 0; i < select.options.length; i++) {
        if (select.options[i].value === value) {
            return true;
        }
    }
    return false;
}
// Aynı ara durak tekrar eklenmesin diye kontrol eder
function isWaypointAlreadyAdded(coordStr) {
    let isAlreadyAdded = false;
    document.querySelectorAll('.waypoint-select').forEach(select => {
        if (select.value === coordStr) {
            isAlreadyAdded = true;
        }
    });
    return isAlreadyAdded;
}
// Seçenekler arasında en yakın olanı bulur (kullanıcı haritadan tıklayınca otomatik eşleşme için)
function findNearestOption(select, lat, lng) {
    const MAX_DISTANCE = 0.001;
    let nearestOption = null;
    let minDistance = MAX_DISTANCE;
    for (let i = 1; i < select.options.length; i++) {
        const value = select.options[i].value;
        if (!value) continue;
        const [optLat, optLng] = value.split(',').map(parseFloat);
        const distance = haversineDistance(lat, lng, optLat, optLng);
        if (distance < minDistance) {
            minDistance = distance;
            nearestOption = select.options[i];
        }
    }
    return nearestOption;
}
// İki nokta arasındaki mesafeyi (km cinsinden) hesaplar
function haversineDistance(lat1, lon1, lat2, lon2) {
    const R = 6371;
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = 
        Math.sin(dLat/2) * Math.sin(dLat/2) +
        Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * 
        Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
}

// =====================
// HARİTADA İŞARETÇİLERİ GÜNCELLEME
// =====================
// Başlangıç, bitiş ve ara durak işaretçilerini haritada gösterir.
function updateMarker(type, lat, lng) {
    // Önce eski işaretçiyi kaldır
    if (customMarkers[type]) {
        leafletMap.removeLayer(customMarkers[type]);
    }
    // İşaretçi stilini belirle
    let markerStyle;
    if (type === 'start') {
        markerStyle = {
            className: 'marker-start',
            html: '<div style="background-color: #28a745; width: 20px; height: 20px; border-radius: 50%; border: 2px solid white;"></div>',
            iconSize: [24, 24],
            iconAnchor: [12, 12]
        };
    } else if (type === 'end') {
        markerStyle = {
            className: 'marker-end',
            html: '<div style="background-color: #dc3545; width: 20px; height: 20px; border-radius: 50%; border: 2px solid white;"></div>',
            iconSize: [24, 24],
            iconAnchor: [12, 12]
        };
    } else {
        markerStyle = {
            className: 'marker-waypoint',
            html: '<div style="background-color: #ffc107; width: 20px; height: 20px; border-radius: 50%; border: 2px solid white;"></div>',
            iconSize: [24, 24],
            iconAnchor: [12, 12]
        };
    }
    // İşaretçiyi oluştur ve haritaya ekle
    const icon = L.divIcon(markerStyle);
    customMarkers[type] = L.marker([lat, lng], { icon }).addTo(leafletMap);
    // İşaretçiye açıklama ekle
    const popupContent = type === 'start' ? 'Başlangıç Noktası' : 
                        type === 'end' ? 'Bitiş Noktası' : 'Ara Durak';
    customMarkers[type].bindPopup(popupContent);
}
// Ara durak işaretçilerini günceller
function updateWaypointMarkers() {
    // Önce eski işaretçileri kaldır
    customMarkers.waypoints.forEach(marker => {
        leafletMap.removeLayer(marker);
    });
    customMarkers.waypoints = [];
    // Her ara durak için işaretçi ekle
    document.querySelectorAll('.waypoint-select').forEach(select => {
        if (select.value) {
            const [lat, lng] = select.value.split(',').map(parseFloat);
            const icon = L.divIcon({
                className: 'marker-waypoint',
                html: '<div style="background-color: #ffc107;"></div>',
                iconSize: [16, 16],
                iconAnchor: [8, 8]
            });
            const marker = L.marker([lat, lng], { icon }).addTo(leafletMap);
            marker.bindPopup(`Ara Durak #${customMarkers.waypoints.length + 1}`);
            customMarkers.waypoints.push(marker);
        }
    });
}

// =====================
// ARA DURAK EKLEME
// =====================
// Kullanıcı yeni bir ara durak eklemek isterse çalışır.
function addWaypoint(coords = '', nearestIntersection = null) {
    // Yeni bir ara durak kutusu oluştur
    const waypointDiv = document.createElement('div');
    waypointDiv.className = 'input-group mb-2 waypoint-item';
    // Önce select elementi oluştur
    const select = document.createElement('select');
    select.className = 'form-select waypoint-select';
    select.innerHTML = '<option value="">Ara durak seçiniz veya haritadan seçin</option>';
    // Kavşak listesini al ve options'ları doldur
    fetch('/get_intersections')
        .then(response => response.json())
        .then(intersections => {
            intersections.forEach(i => {
                const option = document.createElement('option');
                option.value = `${i.latitude},${i.longitude}`;
                option.textContent = i.intersection_name;
                select.appendChild(option);
            });
            // Eğer coordinates verilmişse, uygun seçeneği seç
            if (coords) {
                const [lat, lng] = coords.split(',').map(parseFloat);
                const nearestOption = findNearestOption(select, lat, lng);
                if (nearestOption) {
                    select.value = nearestOption.value;
                }
            }
        });
    // Silme butonu oluştur
    const removeButton = document.createElement('button');
    removeButton.className = 'btn btn-outline-danger remove-waypoint';
    removeButton.type = 'button';
    removeButton.textContent = 'X';
    // Elementleri div'e ekle
    waypointDiv.appendChild(select);
    waypointDiv.appendChild(removeButton);
    document.getElementById('waypoint-list').appendChild(waypointDiv);
    // Eğer haritadan tıklanarak eklendiyse, en yakın kavşağı seçili yap
    if (coords) {
        const nearestOption = findNearestOption(select, ...coords.split(',').map(parseFloat));
        if (nearestOption) {
            select.value = nearestOption.value;
        } else {
            const [lat, lng] = coords.split(',').map(parseFloat);
            if (!hasOption(select, coords)) {
                const newOption = document.createElement('option');
                newOption.value = coords;
                newOption.textContent = nearestIntersection ? 
                    nearestIntersection.intersection_name : 
                    `Özel Nokta (${lat.toFixed(5)}, ${lng.toFixed(5)})`;
                select.appendChild(newOption);
            }
            select.value = coords;
        }
    }
    // Ara durak silme butonu
    removeButton.addEventListener('click', function() {
        waypointDiv.remove();
        updateWaypointMarkers();
    });
    // Ara durak değişirse işaretçileri güncelle
    select.addEventListener('change', function() {
        updateWaypointMarkers();
    });
    if (coords) {
        updateWaypointMarkers();
    }
}

// Modalı açıp kavşak isimlerini doldurur
function openAddStopModal() {
    fetch('/get_intersections')
        .then(response => response.json())
        .then(data => {
            const select = document.getElementById('intersectionSelect');
            select.innerHTML = '';
            data.forEach(item => {
                const option = document.createElement('option');
                option.value = `${item.latitude},${item.longitude}`;
                option.text = `${item.intersection_name} (Bölge: ${item.area})`;
                select.appendChild(option);
            });
            const modal = new bootstrap.Modal(document.getElementById('addStopModal'));
            modal.show();
        });
}
// Modalda seçilen durağı ekler
function addSelectedStop() {
    const select = document.getElementById('intersectionSelect');
    const coords = select.value;
    if (!isWaypointAlreadyAdded(coords)) {
        const [lat, lng] = coords.split(',').map(parseFloat);
        addWaypoint(coords, {latitude: lat, longitude: lng, intersection_name: select.options[select.selectedIndex].text});
        updateWaypointMarkers();
    }
    const modalEl = document.getElementById('addStopModal');
    const modal = bootstrap.Modal.getInstance(modalEl);
    modal.hide();
}

// =====================
// ROTA HESAPLAMA
// =====================
// Kullanıcı "Rotayı Hesapla" butonuna bastığında çalışır.
// Seçilen noktaları ve ayarları sunucuya gönderir, sonucu ekrana yazar.
function calculateRoute(e) {
    e.preventDefault(); // Formun sayfayı yenilemesini engelle
    const startPoint = document.getElementById('start-point').value;
    const endPoint = document.getElementById('end-point').value;
    if (!startPoint || !endPoint) {
        alert('Lütfen başlangıç ve bitiş noktalarını seçin.');
        return;
    }
    const calculateButton = document.getElementById('calculate-button');
    const resetButton = document.getElementById('reset-button');
    const buttonContainer = document.getElementById('button-container');

    calculateButton.disabled = true;
    calculateButton.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Rota hesaplanıyor...';

    // Nokta ve ayarları hazırla
    const startCoords = startPoint.split(',');
    const endCoords = endPoint.split(',');
    const fuelCons = document.getElementById('fuel-consumption-input').value;
    const fuelPrice = document.getElementById('fuel-price-input').value;
    const returnTrip = document.getElementById('return-trip').checked;
    const intermediateCoords = [];
    document.querySelectorAll('.waypoint-select').forEach(select => {
        if (select.value) {
            intermediateCoords.push(select.value.split(',').map(parseFloat));
        }
    });
    // Ayarları kaydet
    saveSettings();
    // Sunucuya rota isteği gönder
    fetch('/calculate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            start_lat: parseFloat(startCoords[0]),
            start_lon: parseFloat(startCoords[1]),
            end_lat: parseFloat(endCoords[0]),
            end_lon: parseFloat(endCoords[1]),
            intermediate_coords: intermediateCoords,
            fuel_cons: parseFloat(fuelCons),
            fuel_price: parseFloat(fuelPrice),
            return_trip: returnTrip,
            route_type: "shortest"  // Her zaman en kısa yol kullan
        }),
    })
    .then(response => response.json())
    .then(data => {
        calculateButton.disabled = false;
        calculateButton.innerHTML = '<i class="fas fa-route me-1"></i> Rotayı Hesapla';
        if (data.error) {
            alert('Hata: ' + data.error);
            return;
        }

        // Rota hesaplama başarılı, sonuçları göster
        document.getElementById('map').innerHTML = data.map_html;
        document.getElementById('results').classList.remove('d-none');

        // "Yeni Rota Hesapla" butonunu görünür yap ve "Rotayı Hesapla" butonunun genişliğini ayarla
        resetButton.classList.remove('d-none');
        calculateButton.classList.remove('w-100');
        calculateButton.classList.add('w-50');

        // Sonuç değerlerini animasyonla güncelle
        animateValue('total-distance', 0, data.total_km, 1000);
        animateValue('fuel-consumption', 0, data.fuel_consumption, 1000);
        animateValue('fuel-cost', 0, data.fuel_cost, 1000);
        document.getElementById('travel-time').textContent = data.formatted_time || "00:00";
    })
    .catch(error => {
        calculateButton.disabled = false;
        calculateButton.innerHTML = '<i class="fas fa-route me-1"></i> Rotayı Hesapla';
        alert('Bir hata oluştu: ' + error);
    });
}

// "Yeni Rota Hesapla" butonuna tıklanınca sayfayı yenile
document.getElementById('reset-button').addEventListener('click', function() {
    location.reload(); // Sayfayı yeniler
});

// =====================
// DEĞERLERİ ANİMASYONLU GÜNCELLEME
// =====================
function animateValue(elementId, start, end, duration) {
    const element = document.getElementById(elementId);
    let startTime = null;
    // Sonucun ondalık olup olmadığını kontrol et
    const decimals = end.toString().includes('.') ? 1 : 0;
    function animation(currentTime) {
        if (startTime === null) startTime = currentTime;
        const timeElapsed = currentTime - startTime;
        const progress = Math.min(timeElapsed / duration, 1);
        const value = progress * (end - start) + start;
        element.textContent = value.toFixed(decimals);
        if (progress < 1) {
            requestAnimationFrame(animation);
        } else {
            element.textContent = end.toFixed(decimals);
        }
    }
    requestAnimationFrame(animation);
}