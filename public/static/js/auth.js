/* ATW — Auth Handler */
document.addEventListener('DOMContentLoaded', () => {
    const alertBox = document.getElementById('auth-alert');

    function showAlert(msg, type) {
        alertBox.innerHTML = msg;
        alertBox.className = `feedback-alert feedback-alert-${type}`;
        alertBox.style.display = 'block';
    }

    // Login form
    document.getElementById('login-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('login-username').value;
        const password = document.getElementById('login-password').value;

        try {
            const r = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username, password}),
            });
            const data = await r.json();
            if (!r.ok) throw new Error(data.detail || 'Login gagal');
            showAlert('✅ Login berhasil, redirect...', 'success');
            setTimeout(() => window.location.href = '/', 800);
        } catch (err) {
            showAlert(`❌ ${err.message}`, 'error');
        }
    });

    // Register form
    document.getElementById('register-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('reg-username').value;
        const email = document.getElementById('reg-email').value;
        const full_name = document.getElementById('reg-fullname').value;
        const password = document.getElementById('reg-password').value;

        try {
            const r = await fetch('/api/auth/register', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username, email, full_name, password}),
            });
            const data = await r.json();
            if (!r.ok) throw new Error(data.detail || 'Registrasi gagal');
            showAlert('✅ Registrasi berhasil, redirect...', 'success');
            setTimeout(() => window.location.href = '/', 800);
        } catch (err) {
            showAlert(`❌ ${err.message}`, 'error');
        }
    });
});