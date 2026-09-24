/* ============================================================
   ATW — Feedback Form Handler
   ============================================================ */
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('feedback-form');
    const submitBtn = document.getElementById('fb-submit');
    const alertBox = document.getElementById('feedback-alert');
    const messageInput = document.getElementById('fb-message');
    const charCount = document.getElementById('fb-count');

    // Char counter
    messageInput?.addEventListener('input', () => {
        charCount.textContent = messageInput.value.length;
    });

    // Submit
    form?.addEventListener('submit', async (e) => {
        e.preventDefault();

        // Honeypot check
        const honeypot = document.getElementById('fb-website').value;
        if (honeypot) {
            showAlert('Spam terdeteksi.', 'error');
            return;
        }

        // Collect data
        const payload = {
            name: form.name.value.trim() || null,
            email: form.email.value.trim() || null,
            category: form.category.value,
            subject: form.subject.value.trim(),
            message: form.message.value.trim(),
            region_id: form.region_id.value ? parseInt(form.region_id.value) : null,
            page_url: window.location.href,
        };

        // Validate
        if (!payload.category || !payload.subject || !payload.message) {
            showAlert('Mohon lengkapi semua field yang wajib diisi (*).', 'error');
            return;
        }

        // Disable button
        submitBtn.disabled = true;
        submitBtn.textContent = '⏳ Mengirim...';

        try {
            const response = await fetch('/api/feedback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });

            const data = await response.json();

            if (response.ok && data.success) {
                showAlert(
                    `✅ Terima kasih! Feedback Anda telah kami terima. ` +
                    `ID tiket: <strong>#${data.feedback_id}</strong>`,
                    'success'
                );
                form.reset();
                charCount.textContent = '0';
                window.scrollTo({ top: 0, behavior: 'smooth' });
            } else {
                showAlert(`❌ Gagal: ${data.detail || data.message || 'Unknown error'}`, 'error');
            }
        } catch (err) {
            showAlert(`❌ Error: ${err.message}`, 'error');
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = '📨 Kirim Feedback';
        }
    });

    function showAlert(html, type) {
        alertBox.innerHTML = html;
        alertBox.className = `feedback-alert feedback-alert-${type}`;
        alertBox.style.display = 'block';
    }
});