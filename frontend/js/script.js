// --- CONFIGURATION ---
const API_BASE_URL = "http://127.0.0.1:8000";

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
    const historySearch = document.getElementById('historySearch');
    const saveBtn = document.getElementById('saveBtn');
    const likeBtn = document.getElementById('likeBtn');
    const dislikeBtn = document.getElementById('dislikeBtn');
    const suggestBtn = document.getElementById('suggestBtn');

    // --- NEW CONTROLS ---
    const savedSearch = document.getElementById('savedSearch');
    const clearSavedBtn = document.getElementById('clearSavedBtn');
    const fullHistorySearch = document.getElementById('fullHistorySearch');
    const clearAllHistoryBtn = document.getElementById('clearAllHistoryBtn');

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

    function formatError(detail) {
        if (Array.isArray(detail)) return detail.map(e => e.msg).join('\n');
        if (typeof detail === 'object') return JSON.stringify(detail);
        return detail;
    }

    // --- LOGOUT LOGIC ---
    window.logout = () => {
        localStorage.removeItem('accessToken');
        window.location.href = 'index.html'; // Redirect to login
    };

    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            window.logout();
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
                alert(formatError(err.detail));
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
                alert(formatError(err.detail));
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
            if (saveBtn) saveBtn.querySelector('i').className = 'fa-regular fa-bookmark'; // Reset save icon
            if (likeBtn) likeBtn.querySelector('i').className = 'fa-regular fa-thumbs-up';
            if (dislikeBtn) dislikeBtn.querySelector('i').className = 'fa-regular fa-thumbs-down';
            if (suggestBtn) suggestBtn.querySelector('i').className = 'fa-solid fa-pen-to-square';

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

    // --- FEATURE LOGIC ---
    if (saveBtn) {
        saveBtn.addEventListener('click', async () => {
            if (!token) return alert("Please login to save.");
            const oText = inputText.value;
            const tText = outputText.value;
            if (!oText || !tText) return;

            const isSaved = saveBtn.querySelector('i').classList.contains('fa-solid');

            try {
                if (isSaved) {
                    // UNSAVE Logic
                    const response = await fetch(`${API_BASE_URL}/saved-translations/unsave`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                        body: JSON.stringify({
                            original_text: oText,
                            translated_text: tText,
                            source_lang: document.getElementById('sourceLang').value,
                            target_lang: document.getElementById('targetLang').value
                        })
                    });
                    if (response.ok) {
                        saveBtn.querySelector('i').className = 'fa-regular fa-bookmark';
                        // Optional: alert("Removed from saved.");
                    } else {
                        throw new Error("Failed to unsave");
                    }
                } else {
                    // SAVE Logic
                    const response = await fetch(`${API_BASE_URL}/saved-translations`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                        body: JSON.stringify({
                            original_text: oText,
                            translated_text: tText,
                            source_lang: document.getElementById('sourceLang').value,
                            target_lang: document.getElementById('targetLang').value
                        })
                    });
                    if (response.ok) {
                        saveBtn.querySelector('i').className = 'fa-solid fa-bookmark';
                        alert("Saved successfully!");
                    } else {
                        throw new Error("Failed to save");
                    }
                }
            } catch (e) { alert("Error: " + e.message); }
        });
    }

    async function handleRating(score, btn) {
        if (!token) return alert("Please login to rate.");
        const oText = inputText.value;
        const tText = outputText.value;
        if (!oText || !tText) return;

        try {
            await fetch(`${API_BASE_URL}/rate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify({ original_text: oText, translated_text: tText, rating: score })
            });

            // Visual Feedback
            // Reset both first
            likeBtn.querySelector('i').className = 'fa-regular fa-thumbs-up';
            dislikeBtn.querySelector('i').className = 'fa-regular fa-thumbs-down';

            // Set active
            if (score === 5) {
                btn.querySelector('i').className = 'fa-solid fa-thumbs-up';
            } else {
                btn.querySelector('i').className = 'fa-solid fa-thumbs-down';
            }

            alert("Thanks for your feedback!");
        } catch (e) { alert("Error sending feedback"); }
    }

    if (likeBtn) likeBtn.addEventListener('click', () => handleRating(5, likeBtn));
    if (dislikeBtn) dislikeBtn.addEventListener('click', () => handleRating(1, dislikeBtn));

    if (suggestBtn) {
        suggestBtn.addEventListener('click', async () => {
            if (!token) return alert("Please login to suggest.");
            const oText = inputText.value;
            if (!oText) return;

            const suggestion = prompt("Enter a better translation:");
            if (!suggestion) return;

            try {
                const response = await fetch(`${API_BASE_URL}/contribute`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                    body: JSON.stringify({
                        original_text: oText,
                        suggested_translation: suggestion,
                        source_lang: document.getElementById('sourceLang').value,
                        target_lang: document.getElementById('targetLang').value
                    })
                });
                if (response.ok) {
                    // Visual Feedback: persistent checkmark until next translation
                    const icon = suggestBtn.querySelector('i');
                    icon.className = 'fa-solid fa-check';
                    // removed timeout/revert
                    alert("Suggestion sent. Thank you!");
                }
            } catch (e) { alert("Error sending suggestion"); }
        });
    }

    // --- SEARCH LOGIC ---
    if (historySearch) {
        historySearch.addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase();
            const items = document.querySelectorAll('.history-item');
            items.forEach(item => {
                const text = item.textContent.toLowerCase();
                item.style.display = text.includes(term) ? 'flex' : 'none';
            });
        });
    }

    // --- HISTORY LOGIC ---
    async function loadHistory() {
        if (!historyList || !token) return; // Only load if logged in and on translate page

        try {
            const response = await fetch(`${API_BASE_URL}/history`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (response.status === 401) {
                console.warn("Session expired. Logging out...");
                window.logout();
                return;
            }

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
            // Pass metadata to fillTranslation
            el.onclick = () => fillTranslation(
                item.original_text,
                item.translated_text,
                item.is_saved,
                item.rating,
                !!item.suggestion
            );
            el.style.cursor = 'pointer';
            el.innerHTML = `
                <div class="history-content">
                    <div class="history-source" style="font-weight: 600; color: var(--text-color);">${escapeHtml(item.original_text)}</div>
                    <div class="history-target" style="color: var(--text-muted); font-size: 0.9rem;">${escapeHtml(item.translated_text)}</div>
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

    window.fillTranslation = (src, tgt, isSaved, rating, hasSuggestion) => {
        if (inputText) inputText.value = src;
        if (outputText) outputText.value = tgt;

        // Sync Icons
        if (saveBtn) saveBtn.querySelector('i').className = isSaved ? 'fa-solid fa-bookmark' : 'fa-regular fa-bookmark';

        if (likeBtn) likeBtn.querySelector('i').className = (rating === 5) ? 'fa-solid fa-thumbs-up' : 'fa-regular fa-thumbs-up';
        if (dislikeBtn) dislikeBtn.querySelector('i').className = (rating === 1) ? 'fa-solid fa-thumbs-down' : 'fa-regular fa-thumbs-down';

        if (suggestBtn) suggestBtn.querySelector('i').className = hasSuggestion ? 'fa-solid fa-check' : 'fa-solid fa-pen-to-square';
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
            if (charCount) charCount.textContent = `${inputText.value.length} / 1000`;
        });
    }



    // --- FULL HISTORY & SAVED LOGIC ---
    const fullHistoryList = document.getElementById('fullHistoryList');
    const savedList = document.getElementById('savedList');

    // 1. Saved Translations Logic
    if (savedList) {
        loadSavedTranslations();

        // Search
        if (savedSearch) {
            savedSearch.addEventListener('input', (e) => {
                const term = e.target.value.toLowerCase();
                const items = savedList.querySelectorAll('.history-card');
                items.forEach(item => {
                    const text = item.textContent.toLowerCase();
                    item.style.display = text.includes(term) ? 'block' : 'none';
                });
            });
        }

        // Delete All
        if (clearSavedBtn) {
            clearSavedBtn.addEventListener('click', async () => {
                if (!confirm("Are you sure you want to delete ALL saved translations?")) return;
                try {
                    const res = await fetch(`${API_BASE_URL}/saved-translations`, {
                        method: 'DELETE',
                        headers: { 'Authorization': `Bearer ${token}` }
                    });
                    if (res.ok) {
                        loadSavedTranslations();
                        alert("All saved translations deleted.");
                    } else {
                        alert("Failed to delete all.");
                    }
                } catch (e) { alert("Error: " + e.message); }
            });
        }
    }

    // 2. Full History Logic
    if (fullHistoryList) {
        loadFullHistory();

        // Search
        if (fullHistorySearch) {
            fullHistorySearch.addEventListener('input', (e) => {
                const term = e.target.value.toLowerCase();
                const items = fullHistoryList.querySelectorAll('.history-card');
                items.forEach(item => {
                    const text = item.textContent.toLowerCase();
                    item.style.display = text.includes(term) ? 'block' : 'none';
                });
            });
        }

        // Delete All
        if (clearAllHistoryBtn) {
            clearAllHistoryBtn.addEventListener('click', async () => {
                if (!confirm("Are you sure you want to delete ALL history?")) return;
                try {
                    const res = await fetch(`${API_BASE_URL}/history`, {
                        method: 'DELETE',
                        headers: { 'Authorization': `Bearer ${token}` }
                    });
                    if (res.ok) {
                        loadFullHistory();
                        alert("History cleared.");
                    } else {
                        alert("Failed to clear history.");
                    }
                } catch (e) { alert("Error: " + e.message); }
            });
        }
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

    // --- HELPER: Unified Card Renderer ---
    function renderCardHTML(item, isSaved, deleteFunctionStr) {
        // Collect Metadata Icons
        let metaIcons = '';
        if (item.rating === 5) metaIcons += '<i class="fa-solid fa-thumbs-up" title="Liked"></i>';
        if (item.rating === 1) metaIcons += '<i class="fa-solid fa-thumbs-down" title="Disliked"></i>';
        if (item.suggestion) metaIcons += '<i class="fa-solid fa-pen-to-square" title="Edited"></i>';
        if (isSaved) metaIcons += '<i class="fa-solid fa-bookmark" title="Saved"></i>';

        // Suggestion display
        let suggestionHtml = '';
        if (item.suggestion) {
            suggestionHtml = `
                <div style="margin-top: 0.5rem; padding: 0.5rem; background: rgba(var(--primary-rgb), 0.1); border-left: 3px solid var(--primary-color); font-size: 0.9rem; color: var(--text-color);">
                    <strong style="color: var(--primary-color);">Edit:</strong> ${escapeHtml(item.suggestion)}
                </div>
            `;
        }

        return `
            <div class="history-content-row">
                <div class="lang-label">From: ${item.source_lang || '?'}</div>
                <div class="text-content">${escapeHtml(item.original_text)}</div>
            </div>
            <div class="history-content-row">
                <div class="lang-label">To: ${item.target_lang || '?'}</div>
                <div class="text-content" style="color: var(--primary-color)">${escapeHtml(item.translated_text)}</div>
            </div>
            
            ${suggestionHtml}

            <div style="font-size: 0.8rem; color: var(--text-muted); text-align: right; margin-bottom: 0.5rem;">
                ${new Date(item.created_at).toLocaleString()}
            </div>
            
            <!-- Bottom Action Row -->
            <div style="display: flex; gap: 1rem; align-items: center; justify-content: space-between; margin-top: 0.5rem;">
                <!-- Status Icons (Neutral) -->
                <div style="flex: 1; display: flex; align-items: center; justify-content: flex-start; gap: 1rem; font-size: 1.2rem; color: var(--text-color);">
                    ${metaIcons}
                </div>

                <!-- Remove Button (Neutral) -->
                <button style="width: auto; min-width: 140px; padding: 0.75rem 1.5rem; background-color: transparent; color: var(--text-color); border: 1px solid var(--glass-border); border-radius: 8px; font-weight: 600; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 0.5rem; transition: background 0.2s;" 
                    onclick="${deleteFunctionStr}"
                    onmouseover="this.style.background='rgba(255, 255, 255, 0.1)'" 
                    onmouseout="this.style.background='transparent'">
                    <i class="fa-solid fa-trash"></i> Remove
                </button>
            </div>
        `;
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
            el.innerHTML = renderCardHTML(item, isSaved, `deleteHistoryItem(${item.id})`);
            fullHistoryList.appendChild(el);
        });
    }

    // Export delete function for Full History items
    window.deleteHistoryItem = async (id) => {
        if (!confirm("Delete this history record?")) return;
        try {
            const res = await fetch(`${API_BASE_URL}/history/${id}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                loadFullHistory(); // Refresh list
            } else {
                alert("Failed to delete item.");
            }
        } catch (e) { alert("Error: " + e.message); }
    };

    // Export delete function for Saved items (existing logic needs to be globally accessible if inline onclick used)
    window.deleteSavedItem = async (id) => {
        if (!confirm("Remove from saved?")) return;
        try {
            // Saved items are deleted by ID
            const res = await fetch(`${API_BASE_URL}/saved-translations/${id}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                loadSavedTranslations();
            } else {
                alert("Failed to remove saved item.");
            }
        } catch (e) { alert("Error: " + e.message); }
    };

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
            el.className = 'history-card';
            el.innerHTML = renderCardHTML(item, true, `deleteSavedItem(${item.id})`);
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
