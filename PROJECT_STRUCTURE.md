# Cấu Trúc Dự Án: En-Vi Translator

Tài liệu này mô tả chi tiết vai trò và chức năng của từng file/thư mục trong dự án Dịch Máy Anh-Việt (En-Vi Translator).

## 📂 Tổng Quan Cấu Trúc File

```text
machine-translation-project/
├── backend/                  # Chứa toàn bộ mã nguồn phía Server (API & AI)
│   ├── auth.py               # Xử lý bảo mật: Hash mật khẩu, tạo Token JWT
│   ├── database.py           # Thiết lập kết nối PostgreSQL (Session, Engine)
│   ├── dataset_utils.py      # Hàm tiện ích xử lý dữ liệu để Train AI
│   ├── fine_tuning.py        # Core logic để fine-tune model (Trainer, TrainingArgs)
│   ├── inference.py          # Logic AI: Load model, Tokenize, Hàm dịch thực tế
│   ├── main.py               # Entry Point: Khởi chạy FastAPI server, định nghĩa API Endpoints
│   ├── model.py              # Cấu hình Model & LoRA (dùng cho lúc Train)
│   ├── db_models.py          # Định nghĩa bảng Database (User, History, Saved...)
│   ├── schemas.py            # Pydantic Models: Validate dữ liệu đầu vào/ra API
│   ├── train_en2vi.ipynb     # Notebook chạy train chiều Anh - Việt
│   └── train_vi2en.ipynb     # Notebook chạy train chiều Việt - Anh
│
├── frontend/                 # Chứa giao diện người dùng (Website)
│   ├── css/
│   │   └── style.css         # CSS giao diện (Theme Xanh/Trắng, Glassmorphism)
│   ├── js/
│   │   └── script.js         # Logic Frontend: Gọi API, Xử lý Đăng nhập, Hiển thị Lịch sử...
│   ├── index.html            # Trang chủ (Landing Page) giới thiệu
│   ├── login.html            # Trang Đăng nhập / Đăng ký
│   └── translate.html        # Trang ứng dụng chính (Dịch thuật)
│
├── docker-compose.yml        # Cấu hình Docker để chạy nhanh Database PostgreSQL
├── requirements.txt          # Danh sách các thư viện Python cần cài đặt
└── README.md                 # Hướng dẫn chung của dự án
```

---

## 🛠️ Chi Tiết Backend (FastAPI)

Thư mục `backend/` được thiết kế theo kiến trúc Modular (chia nhỏ chức năng) để dễ bảo trì và mở rộng.

*   **`main.py`**: "Bộ não" điều khiển.
    *   Khởi tạo ứng dụng `app = FastAPI()`.
    *   Kết nối các thành phần lại với nhau.
    *   Định nghĩa các đường dẫn API (`/login`, `/register`, `/translate`, `/history`...).
*   **`inference.py`**: "Core AI".
    *   Chịu trách nhiệm load Model `vinai/evaluate` nặng nề.
    *   Sử dụng `PeftModel` để load LoRA adapter.
    *   Chứa hàm `perform_translation` thực hiện việc dịch văn bản.
*   **`auth.py`**: "Người gác cổng".
    *   Chứa hàm `get_password_hash` để mã hóa mật khẩu người dùng.
    *   Chứa hàm `create_access_token` để tạo JWT Token mỗi khi đăng nhập.
*   **`database.py`**: "Cầu nối dữ liệu".
    *   Tạo kết nối đến PostgreSQL thông qua SQLAlchemy.
    *   Cung cấp `get_db` để các API khác có thể truy cập Database.
*   **`db_models.py`**: "Bản vẽ Database".
    *   Định nghĩa các bảng (Table): `users`, `translation_history`, `saved_translations`,...
*   **`schemas.py`**: "Bộ lọc dữ liệu".
    *   Định nghĩa format dữ liệu khi Frontend gửi lên (ví dụ: đăng ký phải có password > 6 ký tự).
    *   Định nghĩa format dữ liệu trả về cho Frontend.

---

## 🎨 Chi Tiết Frontend (HTML/CSS/JS)

Giao diện người dùng được viết bằng **Vanilla JS** (không dùng framework nặng) để đảm bảo tốc độ tối đa.

*   **`translate.html`**: Trang quan trọng nhất. Chứa khung nhập liệu, nút dịch, và sidebar lịch sử.
*   **`js/script.js`**: File logic duy nhất xử lý:
    *   Gọi API đăng nhập/đăng ký.
    *   Lưu Token vào `localStorage` trình duyệt.
    *   Gửi request dịch lên Server và hiển thị kết quả.
    *   Tự động tải lịch sử dịch từ Server khi mở trang.
*   **`css/style.css`**: Chứa toàn bộ giao diện, hiệu ứng kính (Glassmorphism), và bộ màu chủ đạo Xanh Biển (Ocean Blue).

---

## 🤖 Chi Tiết Training (AI Model)

Các file này dùng để huấn luyện mô hình (Fine-tuning), thường chạy trên Google Colab hoặc Kaggle GPU, không liên quan trực tiếp đến việc chạy Web Server.

*   **`fine_tuning.py`**: Script chính chứa logic training (Vòng lặp, tối ưu hóa, lưu checkpoint).
*   **`train_en2vi.ipynb` / `train_vi2en.ipynb`**: Notebook tương tác, dùng để bấm nút chạy train dễ dàng trên các nền tảng đám mây.
