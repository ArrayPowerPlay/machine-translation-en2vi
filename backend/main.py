from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List, Optional
from jose import JWTError, jwt

# Import modules
from . import db_models
from . import schemas
from . import auth
from . import database
from . import inference

# Initialize DB Tables
db_models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="En - Vi Translator Backend")

# Configure CORS
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
            # Check duplicate (prevent saving identical consecutive translations)
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

# --- FEATURES ROUTES ---

# 1. HISTORY
@app.get("/history", response_model=List[schemas.HistoryResponse])
async def get_history(
    search: Optional[str] = None,
    current_user: db_models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    # Base query
    query = db.query(db_models.TranslationHistory).filter(db_models.TranslationHistory.user_id == current_user.id)
    if search:
        query = query.filter(db_models.TranslationHistory.original_text.contains(search))
    
    history_items = query.order_by(db_models.TranslationHistory.created_at.desc()).all()
    
    # Enrich with metadata
    results = []
    try:
        for item in history_items:
            # Check if saved
            is_saved = db.query(db_models.SavedTranslation).filter(
                db_models.SavedTranslation.user_id == current_user.id,
                db_models.SavedTranslation.original_text == item.original_text,
                db_models.SavedTranslation.translated_text == item.translated_text
            ).first() is not None

            # Check rating
            rating_obj = db.query(db_models.TranslationRating).filter(
                db_models.TranslationRating.user_id == current_user.id,
                db_models.TranslationRating.original_text == item.original_text,
                db_models.TranslationRating.translated_text == item.translated_text
            ).first()
            rating = rating_obj.rating if rating_obj else None

            # Check contribution
            contrib_obj = db.query(db_models.TranslationContribution).filter(
                db_models.TranslationContribution.user_id == current_user.id,
                db_models.TranslationContribution.original_text == item.original_text
            ).first()
            suggestion = contrib_obj.suggested_translation if contrib_obj else None

            # Construct response
            resp = schemas.HistoryResponse(
                id=item.id,
                original_text=item.original_text,
                translated_text=item.translated_text,
                source_lang=item.source_lang,
                target_lang=item.target_lang,
                created_at=item.created_at,
                is_saved=is_saved,
                rating=rating,
                suggestion=suggestion
            )
            results.append(resp)
    except Exception as e:
        print(f"Error enriching history: {e}")
        # Valid fallback: return simple list or empty list if critical, 
        # but better to log and maybe return what we have?
        # For now, let's just return basic items if enrichment fails for a specific one? 
        # No, just raise HTTP exception to see it in frontend or log it.
        # Ideally, we return the base items without metadata if metadata query fails.
        # But for debugging "failed to fetch", we want to know why.
        raise HTTPException(status_code=500, detail=f"History Load Error: {str(e)}")

    return results


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
    try:
        new_item = db_models.SavedTranslation(**item.dict(), user_id=current_user.id)
        db.add(new_item)
        db.commit()
        db.refresh(new_item)
        return new_item
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


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


@app.delete("/saved-translations")
async def clear_all_saved_translations(current_user: db_models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    db.query(db_models.SavedTranslation).filter(db_models.SavedTranslation.user_id == current_user.id).delete()
    db.commit()
    return {"message": "All saved translations cleared"}

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
