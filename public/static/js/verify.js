/* ATW — Verification Handler */
async function loadPending() {
    const list = document.getElementById('pending-list');
    try {
        const r = await fetch('/api/photos/pending');
        const data = await r.json();

        if (data.length === 0) {
            list.innerHTML = '<p class="verify-empty">✨ Tidak ada foto pending</p>';
            return;
        }

        list.innerHTML = data.map(p => `
            <div class="verify-card">
                <img src="${p.file_path}" alt="${p.title}" class="verify-img">
                <div class="verify-info">
                    <h3>${p.title}</h3>
                    <div class="verify-meta">
                        <span class="photo-cat">${p.category}</span>
                        <span>📍 ${p.region_nama}</span>
                        <span>Oleh: ${p.uploaded_by}</span>
                    </div>
                    <p class="verify-desc">${p.description || '(tanpa deskripsi)'}</p>
                </div>
                <div class="verify-actions">
                    <button onclick="approvePhoto(${p.id})" class="btn-approve">✅ Approve</button>
                    <button onclick="rejectPhoto(${p.id})" class="btn-reject">❌ Reject</button>
                </div>
            </div>
        `).join('');
    } catch (err) {
        list.innerHTML = `<p style="color:red">Error: ${err.message}</p>`;
    }
}

async function approvePhoto(id) {
    const r = await fetch(`/api/photos/${id}/approve`, { method: 'POST' });
    if (r.ok) { loadPending(); }
    else { alert('Gagal approve'); }
}

async function rejectPhoto(id) {
    const reason = prompt('Alasan reject:');
    if (!reason) return;
    const fd = new FormData();
    fd.append('reason', reason);
    const r = await fetch(`/api/photos/${id}/reject`, { method: 'POST', body: fd });
    if (r.ok) { loadPending(); }
    else { alert('Gagal reject'); }
}

document.addEventListener('DOMContentLoaded', loadPending);