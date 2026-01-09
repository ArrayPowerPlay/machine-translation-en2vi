// --- CẤU HÌNH ---
const API_BASE_URL = "http://127.0.0.1:8000";

// --- LOGIC GIAO DIỆN (Giữ nguyên logic cũ) ---
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
    const text = document.getElementById('themeText');

    if (theme === 'dark') {
        // Hiện tại là Dark, chuyển sang Light (Icon: Mặt trời, Text: Light)
        icon.classList.remove('fa-moon');
        icon.classList.add('fa-sun');
        if (text) text.textContent = "Light";
    } else {
        // Hiện tại là Light, chuyển sang Dark (Icon: Mặt trăng, Text: Dark)
        icon.classList.remove('fa-sun');
        icon.classList.add('fa-moon');
        if (text) text.textContent = "Dark";
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // --- KHỞI TẠO ---
    const savedTheme = localStorage.getItem('theme') || 'dark';
    // document.documentElement.setAttribute('data-theme', savedTheme); // Handled by theme-init.js
    updateThemeIcon(savedTheme);

    // --- CÁC PHẦN TỬ ---
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

    // --- CÁC ĐIỀU KHIỂN MỚI ---
    const savedSearch = document.getElementById('savedSearch');
    const clearSavedBtn = document.getElementById('clearSavedBtn');
    const fullHistorySearch = document.getElementById('fullHistorySearch');
    const clearAllHistoryBtn = document.getElementById('clearAllHistoryBtn');

    // --- TRẠNG THÁI ---
    let token = localStorage.getItem('accessToken');

    checkAuth();

    // --- CÁC HÀM XÁC THỰC ---
    function checkAuth() {
        const path = window.location.pathname;
        const isAuthPage = path.includes('login.html');
        // Kiểm tra đơn giản: nếu có token, giả định đã đăng nhập (backend sẽ xác thực khi request)
        if (token) {
            if (logoutBtn) logoutBtn.style.display = 'flex';
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

    // --- LOGIC ĐĂNG XUẤT ---
    window.logout = () => {
        localStorage.removeItem('accessToken');
        window.location.href = 'index.html'; // Chuyển về trang login
    };

    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            window.logout();
        });
    }

    // Xuất hàm cho login.html
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
            localStorage.setItem('accessToken', data.access_token); // Đăng nhập tự động
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

    // --- LOGIC DỊCH ---
    if (translateBtn) {
        translateBtn.addEventListener('click', async () => {
            const text = inputText.value.trim();
            const sourceLang = document.getElementById('sourceLang').value;
            const targetLang = document.getElementById('targetLang').value;

            if (!text) return;

            translateBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Translating...';
            translateBtn.disabled = true;
            if (saveBtn) saveBtn.querySelector('i').className = 'fa-regular fa-bookmark'; // Đặt lại icon lưu
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
                    if (headers['Authorization']) loadHistory(); // Tải lại lịch sử nếu đã đăng nhập
                }
            } catch (e) {
                outputText.value = "Network Error: " + e.message;
            } finally {
                translateBtn.innerHTML = 'Translate';
                translateBtn.disabled = false;
            }
        });
    }

    // --- LOGIC TÍNH NĂNG ---
    if (saveBtn) {
        saveBtn.addEventListener('click', async () => {
            if (!token) return alert("Please login to save.");
            const oText = inputText.value;
            const tText = outputText.value;
            if (!oText || !tText) return;

            const isSaved = saveBtn.querySelector('i').classList.contains('fa-solid');

            try {
                if (isSaved) {
                    // Logic HỦY LƯU
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
                    if (!response.ok) {
                        const err = await response.json();
                        alert("Error: " + formatError(err.detail));
                        return;
                    }
                    const data = await response.json();
                    saveBtn.querySelector('i').className = 'fa-regular fa-bookmark';
                    // Không hiện thông báo khi hủy lưu (im lặng)
                } else {
                    // Logic LƯU
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
                    if (!response.ok) {
                        const err = await response.json();
                        alert("Error: " + formatError(err.detail));
                        return;
                    }
                    const data = await response.json();
                    saveBtn.querySelector('i').className = 'fa-solid fa-bookmark';
                    alert(data.message || "Saved successfully");
                }
            } catch (e) { alert("Error: " + e.message); }
        });
    }

    async function handleRating(score, btn) {
        if (!token) return alert("Please login to rate.");
        const oText = inputText.value;
        const tText = outputText.value;
        if (!oText || !tText) return;

        // Kiểm tra xem nút đã active chưa (để toggle tắt)
        const isActive = btn.querySelector('i').classList.contains('fa-solid');

        try {
            let url = `${API_BASE_URL}/rate`;
            if (isActive) {
                url = `${API_BASE_URL}/rate/undo`;  // Gọi endpoint hoàn tác
            }

            const response = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify({ original_text: oText, translated_text: tText, rating: score })
            });

            if (!response.ok) {
                const err = await response.json();
                alert("Error: " + formatError(err.detail));
                return;
            }

            const data = await response.json();

            // Phản hồi hình ảnh: Logic toggle
            if (isActive) {
                // Người dùng click lại để bỏ chọn - bỏ class solid (unlike/undislike)
                btn.querySelector('i').className = score === 5 ? 'fa-regular fa-thumbs-up' : 'fa-regular fa-thumbs-down';
            } else {
                // Người dùng click để chọn - reset cả hai rồi set cái này
                likeBtn.querySelector('i').className = 'fa-regular fa-thumbs-up';
                dislikeBtn.querySelector('i').className = 'fa-regular fa-thumbs-down';
                btn.querySelector('i').className = score === 5 ? 'fa-solid fa-thumbs-up' : 'fa-solid fa-thumbs-down';
            }

            // Chỉ hiện thông báo nếu không rỗng (rỗng = unlike/undislike)
            if (data.message) {
                alert(data.message);
            }

            // Tải lại lịch sử đầy đủ để đồng bộ thay đổi rating
            if (fullHistoryList) {
                loadFullHistory();
            }
        } catch (e) { alert("Error sending feedback: " + e.message); }
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
                if (!response.ok) {
                    const err = await response.json();
                    alert("Error: " + formatError(err.detail));
                    return;
                }
                const data = await response.json();
                // Phản hồi hình ảnh: dấu tích đến khi dịch tiếp theo
                const icon = suggestBtn.querySelector('i');
                icon.className = 'fa-solid fa-check';
                alert(data.message || "Suggestion sent");
            } catch (e) { alert("Error sending suggestion: " + e.message); }
        });
    }

    // --- LOGIC TÌM KIẾM (đã bỏ - dùng tìm kiếm phía server) ---
    if (historySearch) {
        historySearch.addEventListener('input', (e) => {
            const term = e.target.value;
            loadHistory(term);
        });
    }

    // --- LOGIC LỊCH SỬ ---
    async function loadHistory(searchTerm = '') {
        if (!historyList || !token) return; // Chỉ tải nếu đã đăng nhập và ở trang dịch

        try {
            let url = `${API_BASE_URL}/history`;
            if (searchTerm) {
                url += `?search=${encodeURIComponent(searchTerm)}`;
            }
            const response = await fetch(url, {
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
            // Truyền metadata cho fillTranslation
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
            const response = await fetch(`${API_BASE_URL}/history/${id}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!response.ok) {
                const err = await response.json();
                alert("Error: " + formatError(err.detail));
                return;
            }
            const data = await response.json();
            loadHistory();
            // Cũng tải lại lịch sử đầy đủ và đã lưu nếu đang ở các trang đó
            if (fullHistoryList) loadFullHistory();
            if (savedList) loadSavedTranslations();
            alert(data.message || "Item deleted");
        } catch (e) {
            alert("Error deleting item: " + e.message);
        }
    }

    window.deleteSavedItem = async (id) => {
        if (!confirm("Delete this item?")) return;
        try {
            const response = await fetch(`${API_BASE_URL}/saved-translations/${id}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!response.ok) {
                const err = await response.json();
                alert("Error: " + formatError(err.detail));
                return;
            }
            const data = await response.json();
            if (savedList) loadSavedTranslations();
            // Cũng tải lại lịch sử đầy đủ nếu ở trang đó
            if (fullHistoryList) loadFullHistory();
            alert(data.message || "Item deleted");
        } catch (e) {
            alert("Error deleting item: " + e.message);
        }
    }

    window.fillTranslation = (src, tgt, isSaved, rating, hasSuggestion) => {
        if (inputText) inputText.value = src;
        if (outputText) outputText.value = tgt;

        // Đồng bộ Icon
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
                const response = await fetch(`${API_BASE_URL}/history`, {
                    method: 'DELETE',
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (!response.ok) {
                    const err = await response.json();
                    alert("Error: " + formatError(err.detail));
                    return;
                }
                const data = await response.json();
                loadHistory();
                alert(data.message || "History cleared");
            } catch (e) {
                alert("Error clearing history: " + e.message);
            }
        });
    }

    function escapeHtml(text) {
        if (!text) return "";
        return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
    }

    // Tải ban đầu
    if (historyList) loadHistory();

    // --- CÁC TIỆN ÍCH UI KHÁC ---
    if (inputText) {
        inputText.addEventListener('input', () => {
            const charCount = document.getElementById('charCount');
            if (charCount) charCount.textContent = `${inputText.value.length} / 1000`;
        });
    }



    // --- LOGIC LỊCH SỬ ĐẦY ĐỦ & ĐÃ LƯU ---
    const fullHistoryList = document.getElementById('fullHistoryList');
    const savedList = document.getElementById('savedList');

    // 1. Logic Bản dịch đã lưu
    if (savedList) {
        loadSavedTranslations();

        // Tìm kiếm - phía server
        if (savedSearch) {
            savedSearch.addEventListener('input', (e) => {
                const term = e.target.value;
                loadSavedTranslations(term);
            });
        }

        // Xóa tất cả
        if (clearSavedBtn) {
            clearSavedBtn.addEventListener('click', async () => {
                if (!confirm("Are you sure you want to delete ALL saved translations?")) return;
                try {
                    const res = await fetch(`${API_BASE_URL}/saved-translations`, {
                        method: 'DELETE',
                        headers: { 'Authorization': `Bearer ${token}` }
                    });
                    if (!res.ok) {
                        const err = await res.json();
                        alert("Error: " + formatError(err.detail));
                        return;
                    }
                    const data = await res.json();
                    loadSavedTranslations();
                    alert(data.message || "All saved translations deleted");
                } catch (e) { alert("Error: " + e.message); }
            });
        }
    }

    // 2. Logic Lịch sử đầy đủ
    if (fullHistoryList) {
        loadFullHistory();

        // Search - server-side
        if (fullHistorySearch) {
            fullHistorySearch.addEventListener('input', (e) => {
                const term = e.target.value;
                loadFullHistory(term);
            });
        }

        // Xóa tất cả
        if (clearAllHistoryBtn) {
            clearAllHistoryBtn.addEventListener('click', async () => {
                if (!confirm("Are you sure you want to delete ALL history?")) return;
                try {
                    const res = await fetch(`${API_BASE_URL}/history`, {
                        method: 'DELETE',
                        headers: { 'Authorization': `Bearer ${token}` }
                    });
                    if (!res.ok) {
                        const err = await res.json();
                        alert("Error: " + formatError(err.detail));
                        return;
                    }
                    const data = await res.json();
                    loadFullHistory();
                    alert(data.message || "History cleared");
                } catch (e) { alert("Error: " + e.message); }
            });
        }
    }

    async function loadFullHistory(searchTerm = '') {
        if (!token) {
            fullHistoryList.innerHTML = `
                <div style="text-align:center; padding:2rem; color: var(--text-muted)">
                    <p style="margin-bottom:1rem;">Please login to view and save your translation history.</p>
                    <a href="login.html" class="btn-primary">Login Now</a>
                </div>`;
            return;
        }

        try {
            // Fetch lịch sử và mục đã lưu để kiểm tra trạng thái
            let histUrl = `${API_BASE_URL}/history`;
            if (searchTerm) {
                histUrl += `?search=${encodeURIComponent(searchTerm)}`;
            }
            const [histRes, savedRes] = await Promise.all([
                fetch(histUrl, { headers: { 'Authorization': `Bearer ${token}` } }),
                fetch(`${API_BASE_URL}/saved-translations`, { headers: { 'Authorization': `Bearer ${token}` } })
            ]);

            if (histRes.ok) {
                const history = await histRes.json();
                const savedItems = savedRes.ok ? await savedRes.json() : [];

                // Tạo Set các text gốc đã lưu để tra cứu nhanh
                const savedTexts = new Set(savedItems.map(i => i.original_text));

                renderFullHistory(history, savedTexts);
            }
        } catch (e) {
            fullHistoryList.innerHTML = '<div style="text-align:center; padding:1rem;">Error loading history</div>';
        }
    }

    // --- HELPER: Render thẻ thống nhất ---
    function renderCardHTML(item, isSaved, deleteFunctionStr) {
        // Thu thập Icon Metadata
        let metaIcons = '';
        if (item.rating === 5) metaIcons += '<i class="fa-solid fa-thumbs-up" title="Liked"></i>';
        if (item.rating === 1) metaIcons += '<i class="fa-solid fa-thumbs-down" title="Disliked"></i>';
        if (item.suggestion) metaIcons += '<i class="fa-solid fa-pen-to-square" title="Edited"></i>';
        if (isSaved) metaIcons += '<i class="fa-solid fa-bookmark" title="Saved"></i>';

        // Hiển thị gợi ý
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
            
            <!-- Hàng hành động dưới cùng -->
            <div style="display: flex; gap: 1rem; align-items: center; justify-content: space-between; margin-top: 0.5rem;">
                <!-- Icon trạng thái (Trung tính) -->
                <div style="flex: 1; display: flex; align-items: center; justify-content: flex-start; gap: 1rem; font-size: 1.2rem; color: var(--text-color);">
                    ${metaIcons}
                </div>

                <!-- Nút xóa (Trung tính) -->
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



    async function loadSavedTranslations(searchTerm = '') {
        if (!token) return;
        try {
            let url = `${API_BASE_URL}/saved-translations`;
            if (searchTerm) {
                url += `?search=${encodeURIComponent(searchTerm)}`;
            }
            const response = await fetch(url, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (response.status === 401) {
                console.warn("Session expired. Logging out...");
                window.logout();
                return;
            }

            if (response.ok) {
                const items = await response.json();
                renderSavedList(items);
            }
        } catch (e) {
            if (savedList) savedList.innerHTML = 'Error loading saved items';
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

    // Tự động chuyển đổi ngôn ngữ
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
