# 🌐 English-Vietnamese Machine Translation Web Application

A comprehensive machine translation web application with user authentication, translation history management, and community-driven improvements. Built with FastAPI backend, PostgreSQL database, and vanilla JavaScript frontend with a modern glassmorphism UI.

**Languages Supported:**
- 🇬🇧 English → 🇻🇳 Vietnamese (En-Vi)
- 🇻🇳 Vietnamese → 🇬🇧 English (Vi-En)

---

## 📋 Table of Contents

1. [Features](#features)
2. [System Architecture](#system-architecture)
3. [Tech Stack](#tech-stack)
4. [Project Structure](#project-structure)
5. [Setup & Installation](#setup--installation)
6. [Running the Application](#running-the-application)
7. [Model Training Details](#model-training-details)
8. [API Endpoints](#api-endpoints)
9. [Database Schema](#database-schema)
10. [Frontend Features](#frontend-features)
11. [Troubleshooting](#troubleshooting)

---

## ✨ Features

### 🎯 Core Translation
- Real-time English ↔ Vietnamese translation
- Fine-tuned mBART model with LoRA adapters
- Support for both logged-in users and guest mode
- Automatic duplicate detection in translation history

### 👤 User Management
- User registration with password confirmation
- Secure JWT-based authentication
- 30-minute session expiry for security
- Guest mode for anonymous translation

### 📚 Translation Management
- **History**: View all previous translations with metadata
- **Saved Translations**: Bookmark important translations
- **Smart Search**: Case-insensitive search across original text and translated text
- **Ratings**: Like/Dislike translations for quality feedback
- **Suggestions**: Community-contributed translation improvements
- **Metadata Display**: Shows ratings, saved status, and suggestions on all items

### 🔍 Search & Filter
- **Server-side search** (case-insensitive with `ilike`)
- Search both source and target languages simultaneously
- Real-time filtering with backend integration
- Consistent search behavior across all pages

### 🎨 User Interface
- **Glassmorphism Design**: Modern, semi-transparent card UI
- **Dark/Light Theme Toggle**: Persistent theme preference
- **Responsive Layout**: Works on desktop and mobile devices
- **Real-time Metadata Sync**: Changes immediately reflect across all pages
- **Character Counter**: Shows input text length limit (0/1000)

### 📱 Multi-Page Architecture
- **translate.html**: Main translation interface with quick history sidebar
- **saved.html**: Comprehensive saved translations view with search
- **history.html**: Complete translation history with metadata
- **login.html**: Authentication (Login/Register/Guest mode)

---

## 🏗️ System Architecture

```
┌───────────────────────────────────────────────────────────┐
│                     Frontend (Browser)                    │
│  translate.html | saved.html | history.html | login.html  │
│              JavaScript (vanilla, no framework)           │
│  - Token Management (localStorage)                        │
│  - API Communication (fetch with Bearer auth)             │
│  - DOM Rendering & User Interaction                       │
└──────────────────┬────────────────────────────────────────┘
                   │ HTTP/REST API
                   ↓
┌───────────────────────────────────────────────────────────┐
│                   FastAPI Backend (Port 8000)             │
├───────────────────────────────────────────────────────────┤
│ ├─ Auth Module (JWT, Password Hashing)                    │
│ ├─ Translation Module (inference.py)                      │
│ │   ├─ Load mBART base model                              │
│ │   ├─ Load LoRA adapters                                 │
│ │   └─ Perform translation inference                      │
│ ├─ History Management                                     │
│ ├─ Saved Translations                                     │
│ ├─ Ratings (Like/Dislike)                                 │
│ ├─ Community Contributions                                │
│ └─ Search (server-side filtering)                         │
└──────────────────┬────────────────────────────────────────┘
                   │ SQL ORM (SQLAlchemy)
                   ↓
┌───────────────────────────────────────────────────────────┐
│          PostgreSQL Database (Port 5435)                  │
├───────────────────────────────────────────────────────────┤
│ ├─ users (id, username, hashed_password)                  │
│ ├─ translation_history (id, user_id, original_text,       │
│ │                       translated_text, metadata...)     │
│ ├─ saved_translations (id, user_id, original_text...)     │
│ ├─ translation_ratings (id, user_id, rating)              │
│ └─ translation_contributions (id, user_id, suggestion)    │
└───────────────────────────────────────────────────────────┘

AI Model Stack:
├─ Base Model: vinai/vinai-translate-en2vi (mBART)
├─ LoRA Adapter: lora-vinai-en2vi/ and lora-vinai-vi2en/
│  ├─ Rank (r): 32
│  ├─ Alpha (α): 64
│  ├─ Dropout: 0.1
│  └─ Target Modules: q_proj, v_proj, k_proj, o_proj
└─ Training Framework: Hugging Face Transformers + PEFT
```

---

## 💻 Tech Stack

### Backend
- **Framework**: FastAPI (Python async web framework)
- **Database**: PostgreSQL 15
- **ORM**: SQLAlchemy (database abstraction)
- **Authentication**: JWT tokens with python-jose
- **Security**: Password hashing with passlib & argon2

### AI/ML
- **Base Model**: mBART (Multilingual Denoising Auto-Encoder Transformer)
- **Fine-tuning**: PEFT (Parameter-Efficient Fine-Tuning) with LoRA
- **Deep Learning**: PyTorch
- **Model Hub**: Hugging Face Transformers
- **Tokenizer**: SentencePiece

### Frontend
- **HTML5**: Semantic markup
- **CSS3**: Glassmorphism design, custom themes, animations
- **JavaScript**: Vanilla JS (no frameworks - faster performance)
- **Icons**: FontAwesome 6
- **Data Storage**: Browser localStorage for JWT tokens

### DevOps
- **Containerization**: Docker & Docker Compose
- **Container Image**: PostgreSQL 15-alpine (lightweight)
- **Port Mapping**: 
  - Frontend: `localhost:5500` (HTTP server)
  - Backend: `localhost:8000` (FastAPI)
  - Database: `localhost:5435` (PostgreSQL)

---

## 📂 Project Structure

```
machine-translation-project/
│
├── backend/                          # Python FastAPI Backend
│   ├── main.py                       # FastAPI app, routes, endpoints
│   ├── inference.py                  # AI translation logic
│   ├── fine_tuning.py               # Model training script
│   ├── model.py                      # Model & LoRA config
│   ├── dataset_utils.py              # Dataset loading & preprocessing
│   │
│   ├── auth.py                       # JWT, password hashing
│   ├── database.py                   # PostgreSQL connection
│   ├── db_models.py                  # SQLAlchemy table definitions
│   ├── schemas.py                    # Pydantic validation models
│   │
│   ├── train-en2vi.ipynb            # Training notebook (En→Vi)
│   ├── train-vi2en.ipynb            # Training notebook (Vi→En)
│   │
│   ├── lora-vinai-en2vi/            # En→Vi LoRA adapter weights
│   │   ├── adapter_config.json
│   │   ├── adapter_model.safetensors
│   │   ├── tokenizer files...
│   │   └── checkpoint-28000/        # Final checkpoint
│   │
│   ├── lora-vinai-vi2en/            # Vi→En LoRA adapter weights
│   │   ├── adapter_config.json
│   │   ├── adapter_model.safetensors
│   │   ├── tokenizer files...
│   │   └── checkpoint-22500/        # Final checkpoint
│   │
│   └── __pycache__/
│
├── frontend/                         # Web UI (HTML/CSS/JS)
│   ├── index.html                    # Landing page
│   ├── login.html                    # Authentication
│   ├── translate.html                # Main translation interface
│   ├── saved.html                    # Saved translations
│   ├── history.html                  # Full translation history
│   │
│   ├── css/
│   │   ├── style.css                 # Global styles, theme, glassmorphism
│   │   └── history_card.css          # Card component styles
│   │
│   ├── js/
│   │   ├── script.js                 # Main logic (API calls, rendering)
│   │   └── theme-init.js             # Theme initialization
│   │
│   └── assets/                       # Images, icons (if any)
│
├── docker-compose.yml                # Docker services config
├── requirements.txt                  # Python dependencies
├── PROJECT_STRUCTURE.md              # Detailed structure docs
└── README.md                         # This file

```

---

## 🚀 Setup & Installation

### Prerequisites
- **Python 3.9+**
- **Docker & Docker Compose** (recommended for database)
- **Git**
- **Conda or venv** (Python virtual environment)
- **GPU recommended** (training only; inference works on CPU)

### Step 1: Clone Repository

```bash
git clone <your-repo-url>
cd machine-translation-project
```

### Step 2: Create Python Environment

#### Using Conda (Recommended)
```bash
conda create -n translator_env python=3.9
conda activate translator_env
pip install -r requirements.txt
```

#### Using venv
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 3: Setup PostgreSQL Database

#### Option A: Using Docker Compose (Easiest)
```bash
docker-compose up -d
```

This starts PostgreSQL on `localhost:5435` with:
- Username: `postgres`
- Password: `123456`
- Database: `translation_db`

#### Option B: Install PostgreSQL Locally
1. Download PostgreSQL 15+
2. Create database:
```sql
CREATE DATABASE translation_db;
```
3. Create user:
```sql
CREATE USER postgres WITH PASSWORD '123456';
ALTER ROLE postgres SUPERUSER;
```

### Step 4: Configure Backend

Create `.env` file in `backend/` directory:
```env
DATABASE_URL=postgresql://postgres:123456@localhost:5435/translation_db
SECRET_KEY=your-secret-key-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Step 5: Verify Dependencies

Check `requirements.txt` has all packages:
```bash
pip install fastapi uvicorn sqlalchemy psycopg2-binary python-jose python-multipart torch transformers peft sentencepiece
```

---

## ▶️ Running the Application

### 1. Start PostgreSQL Database
```bash
docker-compose up -d
# Wait ~5 seconds for DB to initialize
```

Verify database is running:
```bash
psql -h localhost -p 5435 -U postgres -d translation_db
# Password: 123456
```

### 2. Start Backend (FastAPI)

```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

API will be available at:
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/

### 3. Start Frontend (HTTP Server)

Open new terminal:

#### Using Python (Simple)
```bash
cd frontend
python -m http.server 5500
# Navigate to: http://localhost:5500
```

#### Using Node.js (If installed)
```bash
cd frontend
npx http-server -p 5500
```

#### Using Live Server (VS Code Extension)
- Install "Live Server" extension
- Right-click `index.html` → "Open with Live Server"
- Opens at `http://127.0.0.1:5500`

### Verify Everything Works

1. **Frontend loads**: http://localhost:5500
2. **Backend API**: http://localhost:8000/docs
3. **Database connected**: Check backend console for connection logs

---

## 🤖 Model Training Details

### Overview

The application uses **mBART** (multilingual Denoising Auto-Encoder Transformer) as the base model, fine-tuned using **LoRA** (Low-Rank Adaptation) for parameter efficiency.

### Base Model

- **Model**: `vinai/vinai-translate-en2vi` (mBART variant by VinAI)
- **Type**: Seq2Seq Transformer (Encoder-Decoder)
- **Purpose**: Multilingual neural machine translation
- **Pre-training**: Denoising autoencoder on 100+ languages

### LoRA Configuration

**Why LoRA?**
- Reduces trainable parameters from **370M → ~6M** (98% reduction)
- Faster training and inference
- Lower memory requirements
- Can switch between language pairs with adapter swapping

**LoRA Hyperparameters:**

| Parameter | Value | Explanation |
|-----------|-------|-------------|
| **Rank (r)** | 32 | Dimensionality of low-rank decomposition. Higher = more expressivity, slower training |
| **Alpha (α)** | 64 | Scaling factor. α/r = 2.0 (standard recommendation) |
| **Dropout** | 0.1 | Regularization: 10% of LoRA weights dropped during training |
| **Target Modules** | `q_proj`, `v_proj`, `k_proj`, `o_proj` | Fine-tune all attention heads (query, value, key, output projections) |

**LoRA Math:**
```
W = W₀ + (α/r) × B × A^T

Where:
- W₀ = original weight matrix (frozen)
- B, A = learnable low-rank matrices
- Only B and A are trained (~6M params vs 370M)
```

### Dataset

**Source**: Helsinki-NLP/OPUS-100

| Aspect | Details |
|--------|---------|
| **Dataset Size** | 400,000 sentence pairs (capped) |
| **Language Pair** | English-Vietnamese |
| **Train/Test Split** | 90% train / 10% validation |
| **Sentence Length** | Max 128 tokens (padded/truncated) |
| **Domain** | Diverse (news, subtitles, legal, web) |

**Dataset Statistics:**
```
Total Pairs: 400,000
Training Set: 360,000 pairs
Validation Set: 40,000 pairs
Vocabulary Size: 250K+ (from mBART)
```

### Training Configuration

**Training Arguments:**

| Parameter | Value | Purpose |
|-----------|-------|---------|
| Learning Rate | 2e-4 | Adam optimizer learning rate |
| Batch Size | 16 | Samples per gradient update |
| Gradient Accumulation | 2 | Effective batch size = 32 |
| Epochs | 3 | Full dataset passes |
| Max Sequence Length | 128 | Token limit per sentence |
| Weight Decay | 0.01 | L2 regularization |
| FP16 (Mixed Precision) | Enabled | Reduces memory, faster training |
| Evaluation Strategy | Steps-based | Evaluate every 500 steps |
| Save Strategy | Steps-based | Save checkpoint every 500 steps |
| Keep Best | 1 checkpoint | Save only best validation loss |

**Training Metrics:**
```
Total Training Steps: ~7,500 steps per epoch × 3 epochs = 22,500 steps
Evaluation Interval: Every 500 steps = 45 evaluations
Logging Interval: Every 100 steps
Total Time: ~4-6 hours on GPU (A100/V100)
```

### Training Pipeline

**1. Data Loading** (`dataset_utils.py`)
```python
# Load from HuggingFace datasets
dataset = load_dataset("Helsinki-NLP/opus-100", "en-vi", split="train")
dataset = dataset.select(range(400000))  # Cap at 400K

# Split into train/val (90/10)
dataset_split = dataset.train_test_split(test_size=0.1)
```

**2. Model Setup** (`model.py`)
```python
# Load base model
model = AutoModelForSeq2SeqLM.from_pretrained(
    "vinai/vinai-translate-en2vi",
    device_map="auto",
    dtype=torch.float16  # FP16 for memory efficiency
)

# Apply LoRA
lora_config = LoraConfig(
    task_type=TaskType.SEQ_2_SEQ_LM,
    r=32,
    lora_alpha=64,
    lora_dropout=0.1,
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj"]
)
model = get_peft_model(model, lora_config)
```

**3. Tokenization** (`dataset_utils.py`)
```python
# Set language codes for mBART
tokenizer.src_lang = "en_XX"
tokenizer.tgt_lang = "vi_VN"

# Tokenize (create input_ids, attention_mask, labels)
model_inputs = tokenizer(
    inputs,
    text_target=targets,
    max_length=128,
    truncation=True
)
# Output: {"input_ids": [...], "attention_mask": [...], "labels": [...]}
```

**4. Training Loop** (`fine_tuning.py`)
```python
trainer = Seq2SeqTrainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_train,
    eval_dataset=tokenized_eval,
    data_collator=DataCollatorForSeq2Seq(tokenizer, model=model)
)

trainer.train()  # Start training
```

**5. Evaluation**
- **Metric**: Validation Loss (lower is better)
- **Frequency**: Every 500 steps
- **Best Model**: Checkpoint with lowest validation loss is automatically selected

**6. Checkpoint Saving**
```
Saves at: lora-vinai-en2vi/checkpoint-<step>/
  ├── adapter_config.json       # LoRA configuration
  ├── adapter_model.safetensors # Trained LoRA weights
  ├── trainer_state.json        # Training metadata
  ├── tokenizer.json            # Tokenizer files
  └── special_tokens_map.json
```

### Training Results

**Final Models Saved:**

1. **En→Vi Model** (`lora-vinai-en2vi/`)
   - Checkpoint: `checkpoint-28000/`
   - Total Steps: 28,000
   - Epochs: ~2.3

2. **Vi→En Model** (`lora-vinai-vi2en/`)
   - Checkpoint: `checkpoint-22500/`
   - Total Steps: 22,500
   - Epochs: ~1.9

### Running Training Yourself

#### Option 1: Google Colab (Free GPU)

1. Upload `train-en2vi.ipynb` to Google Colab
2. Mount Google Drive:
```python
from google.colab import drive
drive.mount('/content/drive')
```
3. Install dependencies:
```python
!pip install -r requirements.txt
```
4. Run the notebook (all cells)
5. Download trained model from Colab

#### Option 2: Kaggle Notebooks

1. Upload dataset and code as dataset
2. Create notebook in Kaggle
3. Reference dataset in code:
```python
src = '/kaggle/input/finetuning-models'
dst = '/kaggle/working/lora-vinai-en2vi'
shutil.copytree(src, dst)
```
4. Run notebook with Kaggle GPU

#### Option 3: Local Machine with GPU

```bash
# Install CUDA toolkit (if not already)
# https://developer.nvidia.com/cuda-downloads

# Activate environment
conda activate translator_env

# Run training notebook
cd backend
jupyter notebook train-en2vi.ipynb
```

**Expected Training Time:**
- **With A100 GPU**: 4-6 hours
- **With V100 GPU**: 8-10 hours
- **With T4 GPU**: 12-16 hours
- **With CPU Only**: 24+ hours (not recommended)

---

## 📡 API Endpoints

### Authentication

#### Register
```http
POST /register
Content-Type: application/json

{
  "username": "myusername",
  "password": "mypassword123",
  "confirm_password": "mypassword123"
}

Response 200:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### Login
```http
POST /login
Content-Type: application/json

{
  "username": "myusername",
  "password": "mypassword123"
}

Response 200:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Translation

#### Translate Text
```http
POST /translate
Authorization: Bearer <token> (optional)
Content-Type: application/json

{
  "text": "Hello, how are you?",
  "source_lang": "en",
  "target_lang": "vi"
}

Response 200:
{
  "original": "Hello, how are you?",
  "translated": "Xin chào, bạn khỏe không?"
}
```

### History Management

#### Get Translation History
```http
GET /history?search=<optional_search_term>
Authorization: Bearer <token>

Response 200:
[
  {
    "id": 1,
    "original_text": "Hello",
    "translated_text": "Xin chào",
    "source_lang": "en",
    "target_lang": "vi",
    "created_at": "2024-01-05T10:30:00",
    "is_saved": false,
    "rating": null,
    "suggestion": null
  },
  ...
]
```

#### Delete Single History Item
```http
DELETE /history/{history_id}
Authorization: Bearer <token>

Response 200:
{
  "message": "Deleted"
}
```

#### Clear All History
```http
DELETE /history
Authorization: Bearer <token>

Response 200:
{
  "message": "All history and saved translations cleared"
}
```

### Saved Translations

#### Save Translation
```http
POST /saved-translations
Authorization: Bearer <token>
Content-Type: application/json

{
  "original_text": "Hello",
  "translated_text": "Xin chào",
  "source_lang": "en",
  "target_lang": "vi"
}

Response 200:
{
  "id": 5,
  "original_text": "Hello",
  "translated_text": "Xin chào",
  "source_lang": "en",
  "target_lang": "vi",
  "created_at": "2024-01-05T10:30:00"
}
```

#### Get Saved Translations
```http
GET /saved-translations?search=<optional_search_term>
Authorization: Bearer <token>

Response 200:
[
  {
    "id": 5,
    "original_text": "Hello",
    "translated_text": "Xin chào",
    "source_lang": "en",
    "target_lang": "vi",
    "created_at": "2024-01-05T10:30:00"
  },
  ...
]
```

#### Unsave Translation
```http
POST /saved-translations/unsave
Authorization: Bearer <token>
Content-Type: application/json

{
  "original_text": "Hello",
  "translated_text": "Xin chào",
  "source_lang": "en",
  "target_lang": "vi"
}

Response 200:
{
  "message": ""  # Empty for silent operation
}
```

#### Delete Saved Item
```http
DELETE /saved-translations/{saved_id}
Authorization: Bearer <token>

Response 200:
{
  "message": "Deleted"
}
```

#### Clear All Saved
```http
DELETE /saved-translations
Authorization: Bearer <token>

Response 200:
{
  "message": "All saved translations cleared"
}
```

### Ratings

#### Rate Translation
```http
POST /rate
Authorization: Bearer <token>
Content-Type: application/json

{
  "original_text": "Hello",
  "translated_text": "Xin chào",
  "rating": 5  # 5 = like, 1 = dislike
}

Response 200:
{
  "message": "Thank you for your feedback!"
}
```

#### Remove Rating
```http
POST /rate/undo
Authorization: Bearer <token>
Content-Type: application/json

{
  "original_text": "Hello",
  "translated_text": "Xin chào",
  "rating": 5
}

Response 200:
{
  "message": ""  # Empty for silent operation
}
```

### Community Contributions

#### Contribute Translation
```http
POST /contribute
Authorization: Bearer <token>
Content-Type: application/json

{
  "original_text": "Hello",
  "suggested_translation": "Chào bạn",
  "source_lang": "en",
  "target_lang": "vi"
}

Response 200:
{
  "message": "Contribution received. Thank you!"
}
```

### Search

All search endpoints use **case-insensitive** filtering with `ilike`:
- Searches both original and translated text
- `?search=hello` matches "Hello", "HELLO", "hElLo"
- Empty search returns all items
- Server-side processing (no client-side filtering)

---

## 🗄️ Database Schema

### Users Table
```sql
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  username VARCHAR(255) UNIQUE NOT NULL,
  hashed_password VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Translation History Table
```sql
CREATE TABLE translation_history (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  original_text TEXT NOT NULL,
  translated_text TEXT NOT NULL,
  source_lang VARCHAR(10) NOT NULL,  -- 'en' or 'vi'
  target_lang VARCHAR(10) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Saved Translations Table
```sql
CREATE TABLE saved_translations (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  original_text TEXT NOT NULL,
  translated_text TEXT NOT NULL,
  source_lang VARCHAR(10) NOT NULL,
  target_lang VARCHAR(10) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Translation Ratings Table
```sql
CREATE TABLE translation_ratings (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  original_text TEXT NOT NULL,
  translated_text TEXT NOT NULL,
  rating INTEGER NOT NULL,  -- 5 = like, 1 = dislike
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Translation Contributions Table
```sql
CREATE TABLE translation_contributions (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  original_text TEXT NOT NULL,
  suggested_translation TEXT NOT NULL,
  source_lang VARCHAR(10) NOT NULL,
  target_lang VARCHAR(10) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Indexes for Performance
```sql
CREATE INDEX idx_history_user ON translation_history(user_id);
CREATE INDEX idx_history_text ON translation_history(original_text);
CREATE INDEX idx_saved_user ON saved_translations(user_id);
CREATE INDEX idx_rating_user ON translation_ratings(user_id);
CREATE INDEX idx_contrib_user ON translation_contributions(user_id);
```

---

## 🎨 Frontend Features

### Pages

#### 1. **index.html** - Landing Page
- Project introduction
- Feature highlights
- Quick access buttons to login/translate

#### 2. **login.html** - Authentication Page
- **Login Tab**: Username + Password
- **Register Tab**: Username + Password + Confirm Password
- **Guest Mode**: Anonymous translation access
- Form validation and error messages

#### 3. **translate.html** - Main Translation Interface
```
┌───────────────────────────────────────────────────┐
│ [Language Selector ▼] [Language Selector ▼]       │
├───────────────────────────────────────────────────┤
│ Input Text (0/1000)        │  Output Text         │
│ [Type or click history]    │  [Translated]        │
├───────────────────────────────────────────────────┤
│ [Translate] [Save] [👍] [👎] [Suggest]           │
├───────────────────────────────────────────────────┤
│ Recent History                                    │
│ [Search history...]                               │
│ • Hello → Xin chào                                │
│ • How are you? → Bạn khỏe không?                  │
│ [Clear All History]                               │
└───────────────────────────────────────────────────┘
```

**Features:**
- Auto-switch language pairs (En→Vi auto-switches to Vi→En)
- Real-time character counter
- One-click language swap
- Quick history sidebar (10 recent items)
- Click any history item to fill input/output
- Save/Like/Dislike buttons
- Suggestion modal

#### 4. **saved.html** - Saved Translations Page
```
┌───────────────────────────────────────────┐
│ [Search saved translations...]            │
├───────────────────────────────────────────┤
│ Saved Translations                        │
│                                           │
│ ┌──────────────────────────────────────┐  │
│ │ From: en                             │  │
│ │ Hello world                          │  │
│ │ To: vi                               │  │
│ │ Xin chào thế giới                    │  │
│ └──────────────────────────────────────┘  │
│                                           │
│ [Clear All Saved Translations]            │
└───────────────────────────────────────────┘
```

**Features:**
- Grid/card view of saved items
- Metadata icons (like, suggestion, saved status)
- Server-side search (case-insensitive)
- Batch delete option
- Suggestion display

#### 5. **history.html** - Full Translation History Page
```
┌─────────────────────────────────────┐
│ [Search all history...]             │
├─────────────────────────────────────┤
│ Translation History                 │
│                                     │
│ ┌────────────────────────────────┐  │
│ │ From: en                       │  │
│ │ Hello                          │  │
│ │ To: vi                         │  │
│ │ Xin chào                       │  │
│ │ Suggested: Xin chào anh        │  │
│ │ 2024-01-05 10:30               │  │
│ └────────────────────────────────┘  │
│                                     │
│ [Clear All History]                 │
└─────────────────────────────────────┘
```

**Features:**
- Comprehensive history view
- Full metadata (timestamps, suggestions, ratings)
- Server-side search across both languages
- Delete individual or all items
- Sync with saved translations (auto-updates)

### UI Components

#### Search Bar
- Real-time search as you type
- Server-side filtering (case-insensitive `ilike`)
- Searches original_text AND translated_text
- Instant results rendering

#### Metadata Icons
```
👍 Like (solid/regular toggle)
👎 Dislike (solid/regular toggle)
📝 Suggestion exists
📌 Saved (solid/regular toggle)
```

#### Buttons
- **Translate**: Submit translation request
- **Save/Unsave**: Bookmark translation (toggle)
- **Like/Dislike**: Rate translation (toggle)
- **Suggest**: Propose alternative translation
- **Remove**: Delete item
- **Clear All**: Delete all items with confirmation

#### Theme Toggle
- Dark mode (default) / Light mode
- Persistent preference (localStorage)
- Smooth transitions

### UI Styling

**Color Scheme (Dark Mode):**
- Primary: Ocean Blue (#0A66C2)
- Background: Deep Blue-Gray (#0F1419)
- Cards: Semi-transparent white (glassmorphism)
- Text: White/Light Gray

**Design System:**
- Glassmorphism (frosted glass effect)
- Smooth animations (200-300ms transitions)
- Responsive grid layout
- Accent colors for interactive elements

---

## 🔧 Troubleshooting

### Database Connection Issues

**Error:** `psycopg2.OperationalError: could not connect to server`

**Solutions:**
1. Check Docker is running:
```bash
docker ps
```

2. Check PostgreSQL container status:
```bash
docker logs translation_db
```

3. Verify port 5435 is available:
```bash
# Linux/Mac
lsof -i :5435

# Windows
netstat -ano | findstr :5435
```

4. Restart Docker containers:
```bash
docker-compose down
docker-compose up -d
```

### Model Loading Issues

**Error:** `FileNotFoundError: [Errno 2] No such file or directory: 'lora-vinai-en2vi'`

**Solutions:**
1. Verify model files exist:
```bash
ls backend/lora-vinai-en2vi/
ls backend/lora-vinai-vi2en/
```

2. Download models if missing:
```bash
cd backend
git lfs pull  # If using Git LFS
```

3. Train models yourself:
```bash
jupyter notebook backend/train-en2vi.ipynb
```

### API Connection Errors

**Error:** `Failed to fetch http://localhost:8000/translate`

**Solutions:**
1. Check backend is running:
```bash
curl http://localhost:8000/
```

2. Check CORS configuration in `backend/main.py`

3. Verify port 8000 is free

### Authentication Issues

**Error:** `401 Unauthorized`

**Solutions:**
1. Token may be expired (30-min limit) - refresh by re-login
2. Token not stored properly - check browser localStorage:
```javascript
localStorage.getItem('accessToken')
```

3. Wrong authorization header format - should be:
```
Authorization: Bearer <token>
```

### Frontend Not Loading

**Error:** `Cannot GET /translate.html`

**Solutions:**
1. Verify HTTP server is running on port 5500
2. Navigate to `http://localhost:5500/translate.html` directly
3. Check frontend files exist:
```bash
ls frontend/*.html
```

### Translation Quality Issues

**Slow/Poor Translations:**
1. Ensure GPU available (check NVIDIA driver):
```bash
nvidia-smi
```

2. Check model loaded correctly in backend logs

3. Verify LoRA adapters are loaded (check `inference.py`)

4. Re-train with more data if needed

### Memory Issues During Training

**Error:** `CUDA out of memory`

**Solutions:**
1. Reduce batch size in `fine_tuning.py`:
```python
batch_size=8  # from 16
```

2. Reduce max_length:
```python
max_length=64  # from 128
```

3. Use gradient accumulation:
```python
grad_accumulation=4  # increase from 2
```

4. Use CPU (slower):
```python
device_map="cpu"
```

---

## 📝 Development Notes

### Code Quality

- **Type Hints**: Used throughout for better IDE support
- **Error Handling**: Try-catch with proper HTTP exceptions
- **SQL Injection Prevention**: SQLAlchemy ORM handles escaping
- **CORS**: Configured for localhost only

### Best Practices

1. **Frontend**: No frameworks, vanilla JS for performance
2. **Backend**: Async/await for better concurrency
3. **Database**: Indexes on frequently queried columns
4. **Security**: Password hashing, JWT tokens, HTTPS ready
5. **Testing**: Manual API testing via `/docs`

### Future Enhancements

- [ ] WebSocket for real-time collaboration
- [ ] Translation memory/caching
- [ ] Batch translation API
- [ ] Language detection (auto-detect source language)
- [ ] Export history (CSV/PDF)
- [ ] User analytics dashboard
- [ ] Multi-language support (more than En-Vi)
- [ ] Spell-check integration
- [ ] Pronunciation audio output
- [ ] Mobile app (React Native)

---

## 📄 License

MIT License - Feel free to use in personal/commercial projects

---

## 👥 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

---

## 📞 Support

For issues or questions:
1. Check [Troubleshooting](#troubleshooting) section
2. Review API documentation: http://localhost:8000/docs
3. Check backend logs for error details
4. Review code comments in respective files

---

## 🎓 Learning Resources

**Machine Translation:**
- [Sequence-to-Sequence with Attention](https://arxiv.org/abs/1409.0473)
- [mBART Paper](https://arxiv.org/abs/2001.08210)
- [LoRA Paper](https://arxiv.org/abs/2106.09685)

**Tools & Frameworks:**
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Hugging Face Transformers](https://huggingface.co/docs/transformers/)
- [PEFT Documentation](https://huggingface.co/docs/peft/)

**Deployment:**
- [Docker Documentation](https://docs.docker.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

---

**Last Updated**: January 5, 2026  
**Version**: 1.0.0
