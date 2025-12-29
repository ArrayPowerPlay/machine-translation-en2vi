// --- CONFIGURATION ---
const API_BASE_URL = "http://localhost:8000";

// --- THEME LOGIC (Keep existing logic) ---
window.forceToggleTheme = (e) => {
    if (e) e.preventDefault();
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeIcon(newTheme);
};

function updateThemeIcon(theme) {
    const themeToggle = document.getElementById('themeToggle');
    if (!themeToggle) return;
    const icon = themeToggle.querySelector('i');
    if (theme === 'dark') {
        icon.classList.remove('fa-sun');
        icon.classList.add('fa-moon');
    } else {
        icon.classList.remove('fa-moon');
        icon.classList.add('fa-sun');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // --- INIT ---
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);

    // --- ELEMENTS ---
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const inputText = document.getElementById('inputText');
    const outputText = document.getElementById('outputText');
    const translateBtn = document.getElementById('translateBtn');
    const historyList = document.getElementById('historyList');
    const logoutBtn = document.getElementById('logoutBtn');

    // --- STATE ---
    let token = localStorage.getItem('accessToken');

    checkAuth();

    // --- AUTH FUNCTIONS ---
    function checkAuth() {
        const path = window.location.pathname;
        const isAuthPage = path.includes('login.html');
        // Simple check: if token exists, assume logged in (backend will verify validity on requests)
        if (token) {
            if (logoutBtn) logoutBtn.style.display = 'inline-block';
            if (isAuthPage) window.location.href = 'translate.html'; // Redirect if already logged in
        } else {
            if (logoutBtn) logoutBtn.style.display = 'none';
        }
    }

    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            localStorage.removeItem('accessToken');
            window.location.href = 'index.html';
        });
    }

    // Exported for login.html
    window.handleLogin = async (type) => {
        if (type === 'guest') {
            localStorage.removeItem('accessToken');
            window.location.href = 'translate.html';
            return;
        }

        const username = document.getElementById('loginUser').value;
        const password = document.getElementById('loginPass').value;

        try {
            const response = await fetch(`${API_BASE_URL}/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });

            if (!response.ok) {
                const err = await response.json();
                alert(err.detail);
                return;
            }

            const data = await response.json();
            localStorage.setItem('accessToken', data.access_token);
            window.location.href = 'translate.html';
        } catch (e) {
            alert("Connection error: " + e.message);
        }
    };

    window.handleRegister = async () => {
        const username = document.getElementById('regUser').value;
        const password = document.getElementById('regPass').value;
        const confirm_password = document.getElementById('regConfirmPass').value;

        try {
            const response = await fetch(`${API_BASE_URL}/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password, confirm_password })
            });

            if (!response.ok) {
                const err = await response.json();
                alert(err.detail);
                return;
            }

            const data = await response.json();
            localStorage.setItem('accessToken', data.access_token); // Auto login
            alert("Registration successful!");
            window.location.href = 'translate.html';
        } catch (e) {
            alert("Connection error: " + e.message);
        }
    };

    window.switchTab = (tab) => {
        document.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.auth-form').forEach(f => f.style.display = 'none');
        document.querySelector(`.auth-tab[onclick="switchTab('${tab}')"]`).classList.add('active');
        document.getElementById(`${tab}Form`).style.display = 'block';
    };

    // --- TRANSLATION LOGIC ---
    if (translateBtn) {
        translateBtn.addEventListener('click', async () => {
            const text = inputText.value.trim();
            const sourceLang = document.getElementById('sourceLang').value;
            const targetLang = document.getElementById('targetLang').value;

            if (!text) return;

            translateBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Translating...';
            translateBtn.disabled = true;

            try {
                const headers = { 'Content-Type': 'application/json' };
                if (token) headers['Authorization'] = `Bearer ${token}`;

                const response = await fetch(`${API_BASE_URL}/translate`, {
                    method: 'POST',
                    headers: headers,
                    body: JSON.stringify({ text, source_lang: sourceLang, target_lang: targetLang })
                });

                if (!response.ok) {
                    const err = await response.json();
                    outputText.value = "Error: " + (err.detail || "Unknown error");
                } else {
                    const data = await response.json();
                    outputText.value = data.translated;
                    if (headers['Authorization']) loadHistory(); // Reload history if logged in
                }
            } catch (e) {
                outputText.value = "Network Error: " + e.message;
            } finally {
                translateBtn.innerHTML = 'Translate';
                translateBtn.disabled = false;
            }
        });
    }

    // --- HISTORY LOGIC ---
    async function loadHistory() {
        if (!historyList || !token) return; // Only load if logged in and on translate page

        try {
            const response = await fetch(`${API_BASE_URL}/history`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                const history = await response.json();
                renderHistoryList(history);
            }
        } catch (e) {
            console.error("Failed to load history", e);
        }
    }

    function renderHistoryList(history) {
        historyList.innerHTML = '';
        if (history.length === 0) {
            historyList.innerHTML = '<div style="text-align:center; padding:1rem; color: var(--text-muted)">No history</div>';
            return;
        }

        history.forEach(item => {
            const el = document.createElement('div');
            el.className = 'history-item';
            el.innerHTML = `
                <div class="history-content" onclick="fillTranslation('${escapeHtml(item.original_text)}', '${escapeHtml(item.translated_text)}')">
                    <div class="history-source">${escapeHtml(item.original_text)}</div>
                    <div class="history-target">${escapeHtml(item.translated_text)}</div>
                </div>
                <div class="history-actions">
                    <button class="action-btn delete-btn" onclick="deleteHistoryItem(${item.id})">
                        <i class="fa-solid fa-trash"></i>
                    </button>
                </div>
            `;
            historyList.appendChild(el);
        });
    }

    window.deleteHistoryItem = async (id) => {
        if (!confirm("Delete this item?")) return;
        try {
            await fetch(`${API_BASE_URL}/history/${id}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            loadHistory();
        } catch (e) {
            alert("Error deleting item");
        }
    }

    window.fillTranslation = (src, tgt) => {
        if (inputText) inputText.value = src;
        if (outputText) outputText.value = tgt;
    }

    const clearHistoryBtn = document.getElementById('clearHistoryBtn');
    if (clearHistoryBtn) {
        clearHistoryBtn.addEventListener('click', async () => {
            if (!confirm("Clear ALL history?")) return;
            try {
                await fetch(`${API_BASE_URL}/history`, {
                    method: 'DELETE',
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                loadHistory();
            } catch (e) {
                alert("Error clearing history");
            }
        });
    }

    function escapeHtml(text) {
        if (!text) return "";
        return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
    }

    // Initial Load
    if (historyList) loadHistory();

    // --- OTHER UI UTILS ---
    if (inputText) {
        inputText.addEventListener('input', () => {
            const charCount = document.getElementById('charCount');
            if (charCount) charCount.textContent = `${inputText.value.length} / 5000`;
        });
    }



    // --- FULL HISTORY & SAVED LOGIC ---
    const fullHistoryList = document.getElementById('fullHistoryList');
    const savedList = document.getElementById('savedList');

    if (fullHistoryList) {
        loadFullHistory();


    }

    if (savedList) {
        loadSavedTranslations();
    }

    async function loadFullHistory() {
        if (!token) {
            fullHistoryList.innerHTML = `
                <div style="text-align:center; padding:2rem; color: var(--text-muted)">
                    <p style="margin-bottom:1rem;">Please login to view and save your translation history.</p>
                    <a href="login.html" class="btn-primary">Login Now</a>
                </div>`;
            return;
        }

        try {
            // Fetch History and Saved items to check status
            const [histRes, savedRes] = await Promise.all([
                fetch(`${API_BASE_URL}/history`, { headers: { 'Authorization': `Bearer ${token}` } }),
                fetch(`${API_BASE_URL}/saved-translations`, { headers: { 'Authorization': `Bearer ${token}` } })
            ]);

            if (histRes.ok) {
                const history = await histRes.json();
                const savedItems = savedRes.ok ? await savedRes.json() : [];

                // Create a Set of saved original texts for fast lookup
                const savedTexts = new Set(savedItems.map(i => i.original_text));

                renderFullHistory(history, savedTexts);
            }
        } catch (e) {
            fullHistoryList.innerHTML = '<div style="text-align:center; padding:1rem;">Error loading history</div>';
        }
    }

    function renderFullHistory(history, savedTexts) {
        fullHistoryList.innerHTML = '';
        if (history.length === 0) {
            fullHistoryList.innerHTML = '<div style="text-align:center; padding:1rem; color: var(--text-muted)">No history records.</div>';
            return;
        }

        history.forEach(item => {
            const isSaved = savedTexts.has(item.original_text);
            const el = document.createElement('div');
            el.className = 'history-card';

            // Icons logic (mocking liked/disliked/edited as they are not returned by backend yet)
            // ideally backend returns item.is_liked, item.is_edited etc.
            // For now only Saved is real.
            let iconsHtml = '';
            if (isSaved) iconsHtml += '<i class="fa-solid fa-bookmark meta-icon saved" title="Saved"></i>';
            /* 
            if (item.liked) iconsHtml += '<i class="fa-solid fa-thumbs-up meta-icon liked"></i>';
            if (item.disliked) iconsHtml += '<i class="fa-solid fa-thumbs-down meta-icon disliked"></i>';
            if (item.edited) iconsHtml += '<i class="fa-solid fa-pen meta-icon" title="Edited"></i>';
            */

            el.innerHTML = `
                <div class="meta-icons">
                    ${iconsHtml}
                </div>
                <div class="history-content-row">
                    <div class="lang-label">From: ${item.source_lang || '?'}</div>
                    <div class="text-content">${escapeHtml(item.original_text)}</div>
                </div>
                <div class="history-content-row">
                    <div class="lang-label">To: ${item.target_lang || '?'}</div>
                    <div class="text-content" style="color: var(--primary-color)">${escapeHtml(item.translated_text)}</div>
                </div>
                <div style="font-size: 0.8rem; color: var(--text-muted); text-align: right;">
                    ${new Date(item.created_at).toLocaleString()}
                </div>
            `;
            fullHistoryList.appendChild(el);
        });
    }

    async function loadSavedTranslations() {
        if (!token) return;
        try {
            const response = await fetch(`${API_BASE_URL}/saved-translations`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                const items = await response.json();
                renderSavedList(items);
            }
        } catch (e) {
            savedList.innerHTML = 'Error loading saved items';
        }
    }

    function renderSavedList(items) {
        savedList.innerHTML = '';
        if (items.length === 0) {
            savedList.innerHTML = '<div style="text-align:center; padding:1rem; color: var(--text-muted)">No saved translations.</div>';
            return;
        }
        items.forEach(item => {
            const el = document.createElement('div');
            el.className = 'history-card'; // Reuse style
            el.innerHTML = `
                <div class="history-content-row">
                    <div class="lang-label">From: ${item.source_lang || '?'}</div>
                    <div class="text-content">${escapeHtml(item.original_text)}</div>
                </div>
                <div class="history-content-row">
                    <div class="lang-label">To: ${item.target_lang || '?'}</div>
                    <div class="text-content" style="color: var(--primary-color)">${escapeHtml(item.translated_text)}</div>
                </div>
                <button class="btn-secondary" style="font-size: 0.8rem; padding: 0.5rem;" onclick="deleteSavedItem(${item.id})">
                    <i class="fa-solid fa-trash"></i> Remove
                </button>
             `;
            savedList.appendChild(el);
        });
    }

    window.deleteSavedItem = async (id) => {
        if (!confirm("Remove from saved?")) return;
        try {
            await fetch(`${API_BASE_URL}/saved-translations/${id}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            loadSavedTranslations();
        } catch (e) { alert("Error removing item"); }
    }

    // Auto-switch languages
    const sourceLang = document.getElementById('sourceLang');

    const targetLang = document.getElementById('targetLang');

    if (sourceLang && targetLang) {
        sourceLang.addEventListener('change', () => {
            if (sourceLang.value === 'en') {
                targetLang.value = 'vi';
            } else if (sourceLang.value === 'vi') {
                targetLang.value = 'en';
            }
        });

        targetLang.addEventListener('change', () => {
            if (targetLang.value === 'en') {
                sourceLang.value = 'vi';
            } else if (targetLang.value === 'vi') {
                sourceLang.value = 'en';
            }
        });
    }


});
