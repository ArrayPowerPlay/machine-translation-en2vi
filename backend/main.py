from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
from jose import JWTError, jwt

from . import db_models
from . import schemas
from . import auth
from . import database
from . import inference

# Khởi tạo kết nối tới database và tạo các bảng dữ liệu
db_models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="En - Vi Translator Backend")

# Cấu hình CORS
origins = [
    "http://localhost",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Khởi tạo phương pháp lấy token từ các request
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Tạo các dependencies phục vụ cho dependency injection
def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(database.get_db)
):
    """Xác thực token từ request và return user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Chuyển đổi token thành data
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(db_models.User).filter(db_models.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user


def get_current_user_optional(
    token: Optional[str] = Depends(OAuth2PasswordBearer(tokenUrl="login", auto_error=False)), 
    db: Session = Depends(database.get_db)
):
    """Trả về user nếu tồn tại token, nếu không trả về None (cho phép đăng nhập không có token - chế độ khách)"""
    if not token:
        return None
    try:
        return get_current_user(token, db)
    except HTTPException:
        return None


@app.get("/")
async def root():
    return {"message": "Welcome to En - Vi Translator API!"}


# 1. ĐĂNG KÝ
@app.post("/register", response_model=schemas.Token)
async def register(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    """Đăng ký tài khoản, trả về access token"""
    # Xác thực mật khẩu lần 2 phải giống lần 1
    if user.password != user.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    
    # Kiểm tra username hiện tại đã có trong database chưa
    db_user = db.query(db_models.User).filter(db_models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already taken. Please choose another one.")
    
    hashed_password = auth.get_password_hash(user.password)
    new_user = db_models.User(username=user.username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    access_token = auth.create_access_token(data={"sub": new_user.username}, expires_delta=timedelta(minutes=30))
    return {"access_token": access_token, "token_type": "bearer"}


# 2.1. ĐĂNG NHẬP
@app.post("/login", response_model=schemas.Token)
async def login(user: schemas.UserLogin, db: Session = Depends(database.get_db)):
    """Đăng nhập vào tài khoản, trả về access token"""
    db_user = db.query(db_models.User).filter(db_models.User.username == user.username).first()
    if not db_user or not auth.verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    access_token = auth.create_access_token(data={"sub": db_user.username}, expires_delta=timedelta(minutes=30))
    return {"access_token": access_token, "token_type": "bearer"}


# 2.2. ĐĂNG NHẬP CHO SWAGGER UI
@app.post("/token", response_model=schemas.Token)
async def login_for_swagger(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(database.get_db)
):
    """Đăng nhập cho Swagger UI"""
    db_user = db.query(db_models.User).filter(db_models.User.username == form_data.username).first()
    if not db_user or not auth.verify_password(form_data.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    access_token = auth.create_access_token(data={"sub": db_user.username}, expires_delta=timedelta(minutes=30))
    return {"access_token": access_token, "token_type": "bearer"}


# 3. DỊCH
@app.post("/translate")
async def translate_text(
    request: schemas.TranslationRequest, 
    db: Session = Depends(database.get_db),
    current_user: Optional[db_models.User] = Depends(get_current_user_optional)
):
    """Tiến hành dịch bản dịch"""
    try:
        translated_text, error = inference.perform_translation(
            text=request.text,
            source_lang=request.source_lang,
            target_lang=request.target_lang
        )
        
        if error:
            raise HTTPException(status_code=500, detail=error)

        # Lưu bản dịch nếu người dùng đăng nhập
        if current_user:
            # Kiểm tra bản ghi trùng lặp trong toàn bộ lịch sử dịch
            existing_item = db.query(db_models.TranslationHistory).filter(
                db_models.TranslationHistory.user_id == current_user.id,
                db_models.TranslationHistory.original_text == request.text,
                db_models.TranslationHistory.target_lang == request.target_lang
            ).first()
            
            if existing_item:
                # Cập nhật thời gian để đưa lên đầu lịch sử dịch
                existing_item.created_at = datetime.now()
                # Cập nhật bản dịch mới nhất
                existing_item.translated_text = translated_text
                db.commit()
                return {"id": existing_item.id, "original": request.text, "translated": translated_text}

            else:
                history_item = db_models.TranslationHistory(
                    user_id=current_user.id,
                    original_text=request.text,
                    translated_text=translated_text,
                    source_lang=request.source_lang,
                    target_lang=request.target_lang
                )
                db.add(history_item)
                db.commit()
                db.refresh(history_item)
                return {"id": history_item.id, "original": request.text, "translated": translated_text}
        # Không trả về id bản dịch khi người dùng đăng nhập với tư cách khách
        return {"original": request.text, "translated": translated_text}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 4. LỊCH SỬ DỊCH
@app.get("/history", response_model=List[schemas.HistoryResponse])
async def get_history(
    search: Optional[str] = None,
    current_user: db_models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    """Trả về tất cả bản dịch"""
    query = db.query(db_models.TranslationHistory).filter(db_models.TranslationHistory.user_id == current_user.id)
    if search:
        query = query.filter(
            (db_models.TranslationHistory.original_text.ilike(f"%{search}%")) | 
            (db_models.TranslationHistory.translated_text.ilike(f"%{search}%"))
        )
    
    return query.order_by(db_models.TranslationHistory.created_at.desc()).all()


@app.delete("/history/{history_id}")
async def delete_history_item(
    history_id: int, 
    current_user: db_models.User = Depends(get_current_user), 
    db: Session = Depends(database.get_db)
):  
    """Xóa một bản dịch"""
    item = db.query(db_models.TranslationHistory).filter(
        db_models.TranslationHistory.id == history_id, 
        db_models.TranslationHistory.user_id == current_user.id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    db.delete(item)
    db.commit()
    return {"message": "Deleted"}


@app.delete("/history")
async def clear_all_history(
    current_user: db_models.User = Depends(get_current_user), 
    db: Session = Depends(database.get_db)
):
    """Xóa tất cả lịch sử dịch"""
    db.query(db_models.TranslationHistory).filter(
        db_models.TranslationHistory.user_id == current_user.id
    ).delete()
    db.commit()
    return {"message": "All history cleared"}


# 5. BẢN DỊCH ĐÃ LƯU
@app.get("/saved", response_model=List[schemas.HistoryResponse])
async def get_saved_translations(
    search: Optional[str] = None,
    current_user: db_models.User = Depends(get_current_user), 
    db: Session = Depends(database.get_db)
):
    """Trả về tất cả bản dịch đã lưu"""
    query = db.query(db_models.TranslationHistory).filter(
        db_models.TranslationHistory.user_id == current_user.id,
        db_models.TranslationHistory.is_saved == True
    )
    if search:
        query = query.filter(
            (db_models.TranslationHistory.original_text.ilike(f"%{search}%")) | 
            (db_models.TranslationHistory.translated_text.ilike(f"%{search}%"))
        )
    return query.order_by(db_models.TranslationHistory.created_at.desc()).all()


@app.post("/saved/{item_id}")
async def save_translation(
    item_id: int, 
    current_user: db_models.User = Depends(get_current_user), 
    db: Session = Depends(database.get_db)
):
    """Lưu một bản dịch theo ID"""
    history_item = db.query(db_models.TranslationHistory).filter(
        db_models.TranslationHistory.id == item_id,
        db_models.TranslationHistory.user_id == current_user.id
    ).first()
    
    if not history_item:
        raise HTTPException(status_code=404, detail="Translation not found in history")
    
    history_item.is_saved = True
    db.commit()
    return {"message": "Translation saved"}


@app.delete("/saved/{saved_id}")
async def unsave_translation(
    saved_id: int, 
    current_user: db_models.User = Depends(get_current_user), 
    db: Session = Depends(database.get_db)
):
    """Bỏ lưu một bản dịch theo ID"""
    item = db.query(db_models.TranslationHistory).filter(
        db_models.TranslationHistory.id == saved_id, 
        db_models.TranslationHistory.user_id == current_user.id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    item.is_saved = False
    db.commit()
    return {"message": "Removed from saved"}


@app.delete("/saved")
async def clear_all_saved_translations(
    current_user: db_models.User = Depends(get_current_user), 
    db: Session = Depends(database.get_db)
):
    """Bỏ lưu tất cả bản dịch đã lưu"""
    db.query(db_models.TranslationHistory).filter(
        db_models.TranslationHistory.user_id == current_user.id,
        db_models.TranslationHistory.is_saved == True
    ).update({db_models.TranslationHistory.is_saved: False})
    db.commit()
    return {"message": "All saved translations cleared"}


# 6. ĐÁNH GIÁ BẢN DỊCH
@app.post("/rate/{item_id}")
async def rate_translation(
    item_id: int,
    rating: int = Query(..., ge=0, le=1, description="0: dislike, 1: like"),
    current_user: db_models.User = Depends(get_current_user), 
    db: Session = Depends(database.get_db)
):
    """Đánh giá bản dịch theo ID. Ghi đè nếu đã rate trước đó."""
    history_item = db.query(db_models.TranslationHistory).filter(
        db_models.TranslationHistory.id == item_id,
        db_models.TranslationHistory.user_id == current_user.id
    ).first()
    
    if not history_item:
        raise HTTPException(status_code=404, detail="Translation not found in history")
    
    history_item.rating = rating
    db.commit()
    return {"message": "Thank you for your feedback!"}


@app.delete("/rate/{item_id}")
async def undo_rating(
    item_id: int,
    current_user: db_models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    """Hủy đánh giá bản dịch theo ID"""
    history_item = db.query(db_models.TranslationHistory).filter(
        db_models.TranslationHistory.id == item_id,
        db_models.TranslationHistory.user_id == current_user.id
    ).first()
    
    if not history_item:
        raise HTTPException(status_code=404, detail="Translation not found")
    
    history_item.rating = None
    db.commit()
    return {"message": "Rating removed"}


# 7. ĐÓNG GÓP BẢN DỊCH
@app.post("/contribute/{item_id}")
async def contribute_translation(
    item_id: int,
    item: schemas.ContributionRequest, 
    current_user: db_models.User = Depends(get_current_user), 
    db: Session = Depends(database.get_db)
):
    """Đóng góp bản dịch tốt hơn theo ID. Ghi đè nếu đã đóng góp trước đó."""
    history_item = db.query(db_models.TranslationHistory).filter(
        db_models.TranslationHistory.id == item_id,
        db_models.TranslationHistory.user_id == current_user.id
    ).first()
    
    if not history_item:
        raise HTTPException(status_code=404, detail="Translation not found in history")
    
    # Ghi đè suggestion
    history_item.suggestion = item.suggestion
    db.commit()
    return {"message": "Contribution received. Thank you!"}