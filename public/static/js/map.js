/* ============================================================
   ATW — Map Viewer dengan Choropleth + Detail Panel
============================================================ */

// Init map
const map = L.map('map', {
    center: [-2.5, 118.0],
    zoom: 5,
    minZoom: 3,
    maxZoom: 15,
    zoomControl: true,
    preferCanvas: true,
});

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap',
    maxZoom: 19,
}).addTo(map);

// Guard heavy layer
const HEAVY_LAYERS = {
    kelurahan: 'Layer 82.983 kelurahan terlalu berat untuk browser. Butuh vector tiles — coming soon.',
};

function guardHeavyLayer(level) {
    if (HEAVY_LAYERS[level]) {
        alert(HEAVY_LAYERS[level]);
        return true;
    }
    return false;
}

// ============================================================
// COLOR SCALE
// ============================================================
function getColor(kategori) {
    switch (kategori) {
        case 'baik':   return '#16a34a';
        case 'sedang': return '#f59e0b';
        case 'rendah': return '#dc2626';
        default:       return '#94a3b8';
    }
}

function getStyle(feature) {
    const kat = feature.properties.kategori;
    const fill = getColor(kat);
    return {
        color: '#1e293b',
        weight: 0.5,
        fillColor: fill,
        fillOpacity: kat === 'belum_ada_data' ? 0.15 : 0.7,
    };
}

// ============================================================
// FORMAT
// ============================================================
function formatRp(value) {
    if (!value || value === 0) return 'Rp 0';
    const miliar = value / 1e9;
    if (miliar >= 1000) return `Rp ${(miliar/1000).toFixed(2)} T`;
    return `Rp ${miliar.toFixed(1)} M`;
}

function formatRpFull(value) {
    if (!value || value === 0) return 'Rp 0';
    return 'Rp ' + Math.round(value).toLocaleString('id-ID');
}

function formatPct(value) {
    return `${value.toFixed(1)}%`;
}

// ============================================================
// LOAD LAYER
// ============================================================
let currentLayer = null;
let currentLevel = null;

async function loadLevel(level) {
    if (currentLevel === level) return;
    if (guardHeavyLayer(level)) return;

    setLoading(true);

    if (currentLayer) {
        map.removeLayer(currentLayer);
        currentLayer = null;
    }

    try {
        const url = `/api/regions/${level}/fiscal-geojson?year=2024`;
        console.log(`Loading ${level}:`, url);

        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();

        console.log(`Loaded ${data.features.length} features for ${level}`);

        currentLayer = L.geoJSON(data, {
            style: getStyle,
            onEachFeature: (feature, layer) => {
                const props = feature.properties;

                // Tooltip on hover
                layer.bindTooltip(
                    `<strong>${props.nama}</strong><br>Realisasi: ${formatPct(props.realisasi_pct)}`,
                    { sticky: true, direction: 'top' }
                );

                // Hover effect
                layer.on('mouseover', function () {
                    this.setStyle({
                        weight: 2.5,
                        color: '#0f172a',
                        fillOpacity: 0.85,
                    });
                    this.bringToFront();
                });

                layer.on('mouseout', function () {
                    if (currentLayer) currentLayer.resetStyle(this);
                });

                // Click → tampil di detail panel kanan
                layer.on('click', function () {
                    showDetailPanel(props.id);
                });
            },
        }).addTo(map);

        currentLevel = level;
        console.log(`✓ ${level} layer added`);

    } catch (err) {
        console.error('Failed to load:', err);
        alert(`Gagal load ${level}: ${err.message}`);
    } finally {
        setLoading(false);
    }
}

// ============================================================
// DETAIL PANEL (RIGHT SIDEBAR)
// ============================================================
async function showDetailPanel(regionId) {
    const panel = document.getElementById('detail-panel');
    const content = document.getElementById('detail-content');

    // Show panel
    panel.classList.remove('collapsed');

    // Loading state
    content.innerHTML = `<div class="detail-loading">Memuat detail wilayah...</div>`;

    try {
        const response = await fetch(`/api/regions/${regionId}/fiscal?year=2024`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();

        const f = data.fiscal;
        const color = getColor(
            f.realisasi_pct >= 80 ? 'baik' :
            f.realisasi_pct >= 60 ? 'sedang' :
            f.pagu > 0 ? 'rendah' : 'belum_ada_data'
        );

        // TKD breakdown
        let tkdRows = '';
        if (data.tkd && data.tkd.length > 0) {
            tkdRows = data.tkd.map(t => {
                const cls = t.pct >= 80 ? 'pct-baik' : t.pct >= 60 ? 'pct-sedang' : 'pct-rendah';
                return `
                    <tr>
                        <td>${t.type.replace(/_/g, ' ')}</td>
                        <td class="num">${formatRp(t.pagu)}</td>
                        <td class="num ${cls}">${t.pct}%</td>
                    </tr>
                `;
            }).join('');
        } else {
            tkdRows = '<tr><td colspan="3" class="empty">Belum ada data TKD</td></tr>';
        }

        // Quarterly bars
        const quarters = [
            { label: 'Q1', value: f.q1 },
            { label: 'Q2', value: f.q2 },
            { label: 'Q3', value: f.q3 },
            { label: 'Q4', value: f.q4 },
        ];
        const maxQ = Math.max(f.q1, f.q2, f.q3, f.q4, 1);
        const qBars = quarters.map(q => `
            <div class="q-item">
                <span class="q-label">${q.label}</span>
                <div class="q-bar-bg">
                    <div class="q-bar" style="width: ${(q.value/maxQ*100).toFixed(1)}%; background: ${color}"></div>
                </div>
                <span class="q-value">${formatRp(q.value)}</span>
            </div>
        `).join('');

        content.innerHTML = `
            <div class="detail-header">
                <span class="detail-level-badge" style="background: ${color}">${data.level}</span>
                <h2 class="detail-title">${data.nama}</h2>
                <div class="detail-kode">Kode BPS: ${data.kode_bps}</div>
            </div>

            <div class="detail-section">
                <h3>💰 Anggaran Tahun ${data.year}</h3>
                <div class="fiscal-big">
                    <div class="fiscal-row">
                        <span class="fiscal-row label">Pagu</span>
                        <span class="fiscal-row value">${formatRpFull(f.pagu)}</span>
                    </div>
                    <div class="fiscal-row">
                        <span class="fiscal-row label">Realisasi</span>
                        <span class="fiscal-row value">${formatRpFull(f.realisasi)}</span>
                    </div>
                    <div class="fiscal-highlight">
                        <div class="fiscal-row label" style="margin-bottom: 4px;">Realisasi Anggaran</div>
                        <div class="fiscal-pct-big" style="color: ${color}">${formatPct(f.realisasi_pct)}</div>
                    </div>
                </div>
            </div>

            <div class="detail-section">
                <h3>📅 Realisasi per Kuartal</h3>
                <div class="q-list">${qBars}</div>
            </div>

            <div class="detail-section">
                <h3>🏛️ Transfer ke Daerah (TKD)</h3>
                <table class="tkd-table">
                    <thead>
                        <tr>
                            <th>Komponen</th>
                            <th class="num">Pagu</th>
                            <th class="num">%</th>
                        </tr>
                    </thead>
                    <tbody>${tkdRows}</tbody>
                </table>
            </div>

            <div class="detail-actions">
                <button onclick="addDocumentation(${data.id}, '${data.nama.replace(/'/g, "\\'")}')">
                    📷 Tambah Dokumentasi
                </button>
            </div>
        `;

    } catch (err) {
        console.error('Failed to load detail:', err);
        content.innerHTML = `
            <div class="detail-loading" style="color: #dc2626">
                ❌ Gagal memuat: ${err.message}
            </div>
        `;
    }
}

// ============================================================
// PLACEHOLDER: Documentation
// ============================================================
function addDocumentation(regionId, regionName) {
    openPhotoModal(regionId, regionName);
}

// ============================================================
// LOADING STATE (fix)
// ============================================================
function setLoading(isLoading) {
    document.querySelectorAll('.layer-btn').forEach(btn => {
        btn.disabled = isLoading;
    });
}

// ============================================================
// SEARCH & QUICK ZOOM
// ============================================================
let searchTimeout = null;
let allRegionsCache = null;

async function getAllRegions() {
    if (allRegionsCache) return allRegionsCache;
    try {
        const r = await fetch('/api/regions/kabupaten/fiscal-geojson?year=2024');
        const data = await r.json();
        allRegionsCache = data.features.map(f => ({
            id: f.properties.id,
            nama: f.properties.nama,
            kode: f.properties.kode_bps,
            pagu: f.properties.pagu,
            pct: f.properties.realisasi_pct,
            geom: f.geometry,
        }));
        return allRegionsCache;
    } catch (e) {
        console.error('Failed to load regions:', e);
        return [];
    }
}

function initSearch() {
    const input = document.getElementById('search-input');
    const resultsBox = document.getElementById('search-results');
    if (!input || !resultsBox) return;

    input.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        const query = e.target.value.trim().toLowerCase();

        if (query.length < 2) {
            resultsBox.innerHTML = '';
            resultsBox.style.display = 'none';
            return;
        }

        searchTimeout = setTimeout(async () => {
            const regions = await getAllRegions();
            const matches = regions.filter(r =>
                r.nama.toLowerCase().includes(query) ||
                r.kode.includes(query)
            ).slice(0, 8);

            if (matches.length === 0) {
                resultsBox.innerHTML = '<div class="search-empty">Tidak ditemukan</div>';
            } else {
                resultsBox.innerHTML = matches.map(r => `
                    <div class="search-item" data-id="${r.id}">
                        <strong>${r.nama}</strong>
                        <span class="search-meta">${r.kode} · ${r.pct.toFixed(1)}%</span>
                    </div>
                `).join('');
            }
            resultsBox.style.display = 'block';

            // Click handler
            resultsBox.querySelectorAll('.search-item').forEach(item => {
                item.addEventListener('click', () => {
                    const id = parseInt(item.dataset.id);
                    const match = matches.find(r => r.id === id);
                    if (match && match.geom) {
                        zoomToGeometry(match.geom);
                        showDetailPanel(id);
                    }
                    resultsBox.style.display = 'none';
                    input.value = '';
                });
            });
        }, 250);
    });

    // Close on blur
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.search-box')) {
            resultsBox.style.display = 'none';
        }
    });
}

function zoomToGeometry(geojson) {
    try {
        const tempLayer = L.geoJSON(geojson);
        const bounds = tempLayer.getBounds();
        map.fitBounds(bounds, { padding: [50, 50], maxZoom: 10 });
    } catch (e) {
        console.error('Zoom failed:', e);
    }
}

function initQuickZoom() {
    document.querySelectorAll('.qz-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const lat = parseFloat(btn.dataset.lat);
            const lng = parseFloat(btn.dataset.lng);
            const zoom = parseInt(btn.dataset.zoom);
            map.setView([lat, lng], zoom);
        });
    });
}

// ============================================================
// PHOTO DOCUMENTATION
// ============================================================
let photoLayer = null;
let photoVisible = false;
let currentPhotoRegion = null;

// Init toggle
function initPhotoToggle() {
    const toggle = document.getElementById('toggle-photos');
    if (!toggle) return;

    // Restore state dari localStorage
    const savedState = localStorage.getItem('atw_photo_markers') === 'true';
    if (savedState) {
        toggle.checked = true;
        photoVisible = true;
        // Load setelah halaman siap
        setTimeout(() => loadPhotoMarkers(), 500);
    }

    toggle.addEventListener('change', async (e) => {
        photoVisible = e.target.checked;
        localStorage.setItem('atw_photo_markers', photoVisible);

        if (photoVisible) {
            await loadPhotoMarkers();
        } else if (photoLayer) {
            map.removeLayer(photoLayer);
            photoLayer = null;
        }
    });

    updatePhotoCount();
}

async function updatePhotoCount() {
    try {
        const r = await fetch('/api/photos?limit=1');
        const data = await r.json();
        const countEl = document.getElementById('photo-count');
        if (countEl) {
            countEl.textContent = data.length === 0 ? 'Belum ada foto' : `Total: ${data.length}+ foto`;
        }
    } catch (e) {
        console.error(e);
    }
}

async function loadPhotoMarkers() {
    try {
        const r = await fetch('/api/photos/geojson');
        const data = await r.json();

        if (photoLayer) {
            map.removeLayer(photoLayer);
        }

        photoLayer = L.geoJSON(data, {
            pointToLayer: (feature, latlng) => {
                const cat = feature.properties.category;
                const icon = getCategoryEmoji(cat);
                return L.marker(latlng, {
                    icon: L.divIcon({
                        html: `<div class="photo-marker">${icon}</div>`,
                        className: 'photo-marker-wrapper',
                        iconSize: [36, 36],
                        iconAnchor: [18, 18],
                    }),
                });
            },
            onEachFeature: (feature, layer) => {
                const p = feature.properties;
                layer.on('click', () => {
                    const dateStr = p.created_at
                        ? new Date(p.created_at).toLocaleDateString('id-ID', {
                            day: 'numeric', month: 'short', year: 'numeric'
                          })
                        : '';

                    layer.bindPopup(`
                        <div class="photo-popup">
                            <img src="${p.file_path}"
                                 alt="${p.title}"
                                 class="photo-popup-img"
                                 onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                            <div class="photo-popup-img-error" style="display:none">
                                📷 Foto tidak dapat dimuat
                            </div>
                            <h4>${p.title}</h4>
                            <div class="photo-popup-meta">
                                <span class="photo-cat">${getCategoryEmoji(p.category)} ${p.category}</span>
                                <span class="photo-region">📍 ${p.region_nama}</span>
                            </div>
                            ${p.description ? `<p class="photo-popup-desc">${p.description}</p>` : ''}
                            <div class="photo-popup-footer">
                                <span>Oleh: ${p.uploaded_by || 'Anonim'}</span>
                                ${dateStr ? `<span class="photo-date">${dateStr}</span>` : ''}
                            </div>
                        </div>
                    `, {
                        maxWidth: 400,
                        minWidth: 340,
                        className: 'photo-popup-container',
                    }).openPopup();
                });
            },
        }).addTo(map);

        const countEl = document.getElementById('photo-count');
        if (countEl) {
            countEl.textContent = `Total: ${data.features.length} foto`;
        }
    } catch (e) {
        console.error('Photo markers failed:', e);
    }
}

function getCategoryEmoji(cat) {
    const map = {
        sekolah: '🏫', jalan: '🛣️', jembatan: '🌉',
        kesehatan: '🩺', irigasi: '💧', gambut: '🌾', lainnya: '📝',
    };
    return map[cat] || '📷';
}

// ============================================================
// AUTH STATE CACHE
// ============================================================
let currentUser = null;

async function checkAuth() {
    if (currentUser !== null) return currentUser;
    try {
        const r = await fetch('/api/auth/me');
        const data = await r.json();
        currentUser = data.authenticated ? data.user : false;
        return currentUser;
    } catch (e) {
        currentUser = false;
        return false;
    }
}

// ============================================================
// UPLOAD MODAL — dengan cek login
// ============================================================
async function openPhotoModal(regionId, regionName) {
    const user = await checkAuth();

    if (!user) {
        if (confirm('🔐 Anda perlu login untuk mengupload foto dokumentasi.\n\nLogin sekarang?')) {
            sessionStorage.setItem('atw_redirect', window.location.href);
            window.location.href = '/login';
        }
        return;
    }

    if (!['kontributor', 'verifikator', 'admin'].includes(user.role)) {
        alert(`Role Anda (${user.role}) tidak bisa mengupload foto.\n\nHubungi admin untuk upgrade role.`);
        return;
    }

    currentPhotoRegion = regionId;
    document.getElementById('photo-region-id').value = regionId;
    document.getElementById('photo-modal-region').textContent =
        `Region: ${regionName} (ID: ${regionId}) — Login sebagai: ${user.full_name || user.username}`;
    document.getElementById('photo-modal').classList.add('active');
    document.getElementById('photo-form').reset();
    document.getElementById('photo-region-id').value = regionId;
    document.getElementById('photo-lat').value = '';
    document.getElementById('photo-lng').value = '';
}

// ============================================================
// CLOSE PHOTO MODAL
// ============================================================
function closePhotoModal() {
    const modal = document.getElementById('photo-modal');
    if (modal) modal.classList.remove('active');
    currentPhotoRegion = null;
}

// ============================================================
// INIT PHOTO MODAL — submit handler + buttons + GPS
// ============================================================
function initPhotoModal() {
    const modal = document.getElementById('photo-modal');
    if (!modal) {
        console.warn('photo-modal not found');
        return;
    }

    // Close handlers
    document.getElementById('photo-modal-close')?.addEventListener('click', closePhotoModal);
    document.getElementById('photo-cancel')?.addEventListener('click', closePhotoModal);

    // Click backdrop
    modal.addEventListener('click', (e) => {
        if (e.target.id === 'photo-modal') closePhotoModal();
    });

    // ESC key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.classList.contains('active')) {
            closePhotoModal();
        }
    });

    // GPS detection
    document.getElementById('photo-get-gps')?.addEventListener('click', () => {
        if (!navigator.geolocation) {
            alert('Browser tidak mendukung deteksi GPS');
            return;
        }
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                document.getElementById('photo-lat').value = pos.coords.latitude.toFixed(6);
                document.getElementById('photo-lng').value = pos.coords.longitude.toFixed(6);
            },
            (err) => alert(`Gagal deteksi lokasi: ${err.message}`),
            { enableHighAccuracy: true, timeout: 10000 }
        );
    });

    // Submit form
    document.getElementById('photo-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = document.getElementById('photo-submit');
        btn.disabled = true;
        btn.textContent = '⏳ Uploading...';

        try {
            const formData = new FormData(e.target);
            if (!formData.get('latitude')) formData.delete('latitude');
            if (!formData.get('longitude')) formData.delete('longitude');

            const r = await fetch('/api/photos/upload', {
                method: 'POST',
                body: formData,
            });

            const data = await r.json();
            if (!r.ok) throw new Error(data.detail || 'Upload gagal');

            alert(`✅ Foto berhasil diupload! ID: #${data.photo_id}\n\nStatus: PENDING — menunggu verifikasi.`);

            closePhotoModal();

            // Reload marker jika sedang aktif
            if (photoVisible) await loadPhotoMarkers();
            await updatePhotoCount();
        } catch (err) {
            alert(`❌ ${err.message}`);
        } finally {
            btn.disabled = false;
            btn.textContent = '📤 Upload Foto';
        }
    });
}

// ============================================================
// MAIN INIT
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
    // 1. Detail panel close
    document.getElementById('detail-close')?.addEventListener('click', () => {
        document.getElementById('detail-panel').classList.add('collapsed');
    });

    // 2. Layer buttons
    document.querySelectorAll('.layer-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const level = btn.dataset.level;
            if (guardHeavyLayer(level)) return;

            document.querySelectorAll('.layer-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            loadLevel(level);
        });
    });

    // 3. Init semua modul
    initPhotoToggle();
    initPhotoModal();
    initSearch();
    initQuickZoom();

    // 4. Default layer — kabupaten
    loadLevel('kabupaten');

    console.log('🌾 ATW Map ready');
});