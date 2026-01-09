from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import timedelta
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

# Khởi tạo phương pháp lấy token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Tạo các hàm dependencies

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


# 1. ĐĂNG NHẬP
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


# 2. ĐĂNG KÝ
@app.post("/login", response_model=schemas.Token)
async def login(user: schemas.UserLogin, db: Session = Depends(database.get_db)):
    db_user = db.query(db_models.User).filter(db_models.User.username == user.username).first()
    if not db_user or not auth.verify_password(user.password, db_user.hashed_password):
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
            # Kiểm tra bản ghi trùng lặp
            # Lấy bản ghi mới nhất
            last_item = db.query(db_models.TranslationHistory)\
                .filter(db_models.TranslationHistory.user_id == current_user.id)\
                .order_by(db_models.TranslationHistory.created_at.desc())\
                .first()
            
            should_save = True
            if last_item and last_item.original_text == request.text and last_item.target_lang == request.target_lang:
                should_save = False

            if should_save:
                history_item = db_models.TranslationHistory(
                    user_id=current_user.id,
                    original_text=request.text,
                    translated_text=translated_text,
                    source_lang=request.source_lang,
                    target_lang=request.target_lang
                )
                db.add(history_item)
                db.commit()

        return {"original": request.text, "translated": translated_text}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 4. LỊCH SỬ
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
    
    history_items = query.order_by(db_models.TranslationHistory.created_at.desc()).all()
    
    # 1. Saved status
    saved_query = db.query(db_models.SavedTranslation.original_text, db_models.SavedTranslation.translated_text)\
        .filter(db_models.SavedTranslation.user_id == current_user.id).all()
    saved_set = {(s.original_text, s.translated_text) for s in saved_query}

    # 2. Ratings
    rating_query = db.query(db_models.TranslationRating.original_text, db_models.TranslationRating.translated_text, db_models.TranslationRating.rating)\
        .filter(db_models.TranslationRating.user_id == current_user.id).all()
    rating_map = {(r.original_text, r.translated_text): r.rating for r in rating_query}

    # 3. Contributions
    contrib_query = db.query(db_models.TranslationContribution.original_text, db_models.TranslationContribution.suggested_translation)\
        .filter(db_models.TranslationContribution.user_id == current_user.id).all()
    contrib_map = {c.original_text: c.suggested_translation for c in contrib_query}

    results = []
    for item in history_items:
        results.append(schemas.HistoryResponse(
            id=item.id,
            original_text=item.original_text,
            translated_text=item.translated_text,
            source_lang=item.source_lang,
            target_lang=item.target_lang,
            created_at=item.created_at,
            is_saved=(item.original_text, item.translated_text) in saved_set,
            rating=rating_map.get((item.original_text, item.translated_text)),
            suggestion=contrib_map.get(item.original_text)
        ))
    
    return results


# 5. XÓA LỊCH SỬ
@app.delete("/history/{history_id}")
async def delete_history_item(
    history_id: int, 
    current_user: db_models.User = Depends(get_current_user), 
    db: Session = Depends(database.get_db)
):  
    """Xóa một bản dịch"""
    item = db.query(db_models.TranslationHistory).filter(db_models.TranslationHistory.id == history_id, db_models.TranslationHistory.user_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Logic: Xóa lịch sử dịch => xóa bản ghi tương ứng đã lưu trong bảng đã lưu
    db.query(db_models.SavedTranslation).filter(
        db_models.SavedTranslation.user_id == current_user.id,
        db_models.SavedTranslation.original_text == item.original_text,
        db_models.SavedTranslation.translated_text == item.translated_text,
        db_models.SavedTranslation.source_lang == item.source_lang,
        db_models.SavedTranslation.target_lang == item.target_lang
    ).delete()

    db.delete(item)
    db.commit()
    return {"message": "Deleted"}


@app.delete("/history")
async def clear_all_history(
    current_user: db_models.User = Depends(get_current_user), 
    db: Session = Depends(database.get_db)
):
    """Xóa tất cả lịch sử dịch"""
    db.query(db_models.TranslationHistory).filter(db_models.TranslationHistory.user_id == current_user.id).delete()
    # Xóa trong bảng các bản dịch đã lưu
    db.query(db_models.SavedTranslation).filter(db_models.SavedTranslation.user_id == current_user.id).delete()
    db.commit()
    return {"message": "All history and saved translations cleared"}


# 7. BẢN DỊCH ĐÃ LƯU
@app.post("/saved-translations", response_model=schemas.SavedTranslationResponse)
async def save_translation(
    item: schemas.SavedTranslationCreate, 
    current_user: db_models.User = Depends(get_current_user), 
    db: Session = Depends(database.get_db)
):
    """Lưu một bản dịch"""
    try:
        new_item = db_models.SavedTranslation(**item.dict(), user_id=current_user.id)
        db.add(new_item)
        db.commit()
        db.refresh(new_item)
        return new_item
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.post("/saved-translations/unsave")
async def unsave_translation(
    item: schemas.SavedTranslationCreate, 
    current_user: db_models.User = Depends(get_current_user), 
    db: Session = Depends(database.get_db)
):
    """Hủy lưu một bản dịch"""
    try:
        deleted_count = db.query(db_models.SavedTranslation).filter(
            db_models.SavedTranslation.user_id == current_user.id,
            db_models.SavedTranslation.original_text == item.original_text,
            db_models.SavedTranslation.translated_text == item.translated_text
        ).delete()
        db.commit()
        if deleted_count == 0:
            return {"message": "Item was not saved"}
        return {"message": ""}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/saved-translations", response_model=List[schemas.SavedTranslationResponse])
async def get_saved_translations(
    search: Optional[str] = None,
    current_user: db_models.User = Depends(get_current_user), 
    db: Session = Depends(database.get_db)
):
    """Trả về tất cả bản dịch đã lưu"""
    query = db.query(db_models.SavedTranslation).filter(db_models.SavedTranslation.user_id == current_user.id)
    if search:
        query = query.filter(
            (db_models.SavedTranslation.original_text.ilike(f"%{search}%")) | 
            (db_models.SavedTranslation.translated_text.ilike(f"%{search}%"))
        )
    return query.order_by(db_models.SavedTranslation.created_at.desc()).all()


@app.delete("/saved-translations/{saved_id}")
async def delete_saved_translation(
    saved_id: int, current_user: db_models.User = Depends(get_current_user), 
    db: Session = Depends(database.get_db)
):
    """Xóa một bản dịch đã lưu"""
    item = db.query(db_models.SavedTranslation).filter(db_models.SavedTranslation.id == saved_id, db_models.SavedTranslation.user_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
    return {"message": "Deleted"}


@app.delete("/saved-translations")
async def clear_all_saved_translations(
    current_user: db_models.User = Depends(get_current_user), 
    db: Session = Depends(database.get_db)
):
    """Xóa tất cả bản dịch đã lưu"""
    db.query(db_models.SavedTranslation).filter(db_models.SavedTranslation.user_id == current_user.id).delete()
    db.commit()
    return {"message": "All saved translations cleared"}


# 8. ĐÓNG GÓP
@app.post("/contribute")
async def contribute_translation(
    item: schemas.ContributionCreate, 
    current_user: db_models.User = Depends(get_current_user), 
    db: Session = Depends(database.get_db)
):
    """Đóng góp một bản dịch"""
    try:
        # Kiểm tra đã đóng góp cùng text này chưa
        existing = db.query(db_models.TranslationContribution).filter(
            db_models.TranslationContribution.user_id == current_user.id,
            db_models.TranslationContribution.original_text == item.original_text,
            db_models.TranslationContribution.suggested_translation == item.suggested_translation
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="You already contributed this translation")
        
        new_contrib = db_models.TranslationContribution(**item.dict(), user_id=current_user.id)
        db.add(new_contrib)
        db.commit()
        return {"message": "Contribution received. Thank you!"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# 9. ĐÁNH GIÁ
@app.post("/rate")
async def rate_translation(
    item: schemas.RatingCreate, 
    current_user: db_models.User = Depends(get_current_user), 
    db: Session = Depends(database.get_db)
):
    """Thêm hoặc cập nhật rating"""
    try:
        # Kiểm tra rating cũ
        existing_rating = db.query(db_models.TranslationRating).filter(
            db_models.TranslationRating.user_id == current_user.id,
            db_models.TranslationRating.original_text == item.original_text,
            db_models.TranslationRating.translated_text == item.translated_text
        ).first()
        
        if existing_rating:
            # Nếu rating khác nhau, cập nhật (thay đổi like thành dislike và ngược lại)
            if existing_rating.rating != item.rating:
                existing_rating.rating = item.rating
                db.commit()
                return {"message": "Thank you for your feedback!"}
        
        # Chưa có rating, thêm mới
        new_rating = db_models.TranslationRating(**item.dict(), user_id=current_user.id)
        db.add(new_rating)
        db.commit()
        return {"message": "Thank you for your feedback!"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.post("/rate/undo")
async def undo_rating(
    item: schemas.RatingCreate,
    current_user: db_models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    """Hủy rating (unlike/undislike)"""
    try:
        deleted_count = db.query(db_models.TranslationRating).filter(
            db_models.TranslationRating.user_id == current_user.id,
            db_models.TranslationRating.original_text == item.original_text,
            db_models.TranslationRating.translated_text == item.translated_text,
            db_models.TranslationRating.rating == item.rating
        ).delete()
        db.commit()
        if deleted_count == 0:
            return {"message": "No rating found"}
        return {"message": ""}  
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
