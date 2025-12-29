from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List, Optional
from jose import JWTError, jwt

# Import modules
import db_models
import schemas
import auth
import database
import inference

# Initialize DB Tables
db_db_models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="En - Vi Translator Backend")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# --- DEPENDENCIES ---

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
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


def get_current_user_optional(token: Optional[str] = Depends(OAuth2PasswordBearer(tokenUrl="login", auto_error=False)), db: Session = Depends(database.get_db)):
    # Helper để lấy user nếu có token, nếu không thì trả về None (cho phép khách dùng dịch vụ)
    if not token:
        return None
    try:
        return get_current_user(token, db)
    except HTTPException:
        return None

# --- ROUTES ---

@app.get("/")
async def root():
    return {"message": "Welcome to LinguaFlow API. Use /translate to translate text."}


@app.post("/register", response_model=schemas.Token)
async def register(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    if user.password != user.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    
    db_user = db.query(db_models.User).filter(db_models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = auth.get_password_hash(user.password)
    new_user = db_models.User(username=user.username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    access_token = auth.create_access_token(data={"sub": new_user.username}, expires_delta=timedelta(minutes=30))
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/login", response_model=schemas.Token)
async def login(user: schemas.UserLogin, db: Session = Depends(database.get_db)):
    db_user = db.query(db_models.User).filter(db_models.User.username == user.username).first()
    if not db_user or not auth.verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    access_token = auth.create_access_token(data={"sub": db_user.username}, expires_delta=timedelta(minutes=30))
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/translate")
async def translate_text(
    request: schemas.TranslationRequest, 
    db: Session = Depends(database.get_db),
    current_user: Optional[db_models.User] = Depends(get_current_user_optional)
):
    try:
        translated_text, error = inference.perform_translation(
            text=request.text,
            source_lang=request.source_lang,
            target_lang=request.target_lang
        )
        
        if error:
             raise HTTPException(status_code=500, detail=error)

        # AUTO-SAVE HISTORY if user is logged in
        if current_user:
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

# --- FEATURES ROUTES ---

# 1. HISTORY
@app.get("/history", response_model=List[schemas.HistoryResponse])
async def get_history(
    search: Optional[str] = None,
    current_user: db_models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    query = db.query(db_models.TranslationHistory).filter(db_models.TranslationHistory.user_id == current_user.id)
    if search:
        query = query.filter(db_models.TranslationHistory.original_text.contains(search))
    return query.order_by(db_models.TranslationHistory.created_at.desc()).all()


@app.delete("/history/{history_id}")
async def delete_history_item(history_id: int, current_user: db_models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    item = db.query(db_models.TranslationHistory).filter(db_models.TranslationHistory.id == history_id, db_models.TranslationHistory.user_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
    return {"message": "Deleted"}


@app.delete("/history")
async def clear_all_history(current_user: db_models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    db.query(db_models.TranslationHistory).filter(db_models.TranslationHistory.user_id == current_user.id).delete()
    db.commit()
    return {"message": "All history cleared"}


# 2. SAVED TRANSLATIONS (Bookmarks)
@app.post("/saved-translations", response_model=schemas.SavedTranslationResponse)
async def save_translation(item: schemas.SavedTranslationCreate, current_user: db_models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    new_item = db_models.SavedTranslation(**item.dict(), user_id=current_user.id)
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item


@app.get("/saved-translations", response_model=List[schemas.SavedTranslationResponse])
async def get_saved_translations(current_user: db_models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    return db.query(db_models.SavedTranslation).filter(db_models.SavedTranslation.user_id == current_user.id).order_by(db_models.SavedTranslation.created_at.desc()).all()


@app.delete("/saved-translations/{id}")
async def delete_saved_translation(id: int, current_user: db_models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    item = db.query(db_models.SavedTranslation).filter(db_models.SavedTranslation.id == id, db_models.SavedTranslation.user_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
    return {"message": "Deleted"}

# 3. CONTRIBUTE
@app.post("/contribute")
async def contribute_translation(item: schemas.ContributionCreate, current_user: db_models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    new_contrib = db_models.TranslationContribution(**item.dict(), user_id=current_user.id)
    db.add(new_contrib)
    db.commit()
    return {"message": "Contribution received. Thank you!"}

# 4. RATING
@app.post("/rate")
async def rate_translation(item: schemas.RatingCreate, current_user: db_models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    new_rating = db_models.TranslationRating(**item.dict(), user_id=current_user.id)
    db.add(new_rating)
    db.commit()
    return {"message": "Rating received"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
