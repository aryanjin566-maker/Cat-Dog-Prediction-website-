from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from config import Config
from database import db
from utils.model_loader import initialize_model
from dependencies import get_current_user
from schemas import HealthResponse, SignupRequest, LoginRequest, ProfileUpdateRequest
import logging
from datetime import datetime
import os
import sys

# ============================================================================
# LOGGING SETUP
# ============================================================================
log_format = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# LIFESPAN EVENT HANDLERS
# ============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ===== STARTUP =====
    logger.info("=" * 60)
    logger.info("🚀 STARTING DOG-CAT CLASSIFIER SERVER (FastAPI)")
    logger.info("=" * 60)
    
    # Create uploads folder
    if not os.path.exists(Config.UPLOAD_FOLDER):
        os.makedirs(Config.UPLOAD_FOLDER)
        logger.info(f"✓ Created uploads folder: {Config.UPLOAD_FOLDER}")
    
    # Connect to database
    if not db.connect():
        logger.error("✗ Failed to connect to database")
        raise Exception("Database connection failed")
    
    # Load ML model
    logger.info("Loading Deep Learning Model...")
    if not initialize_model(Config.MODEL_PATH):
        logger.error("✗ Failed to load model")
        raise Exception("Model loading failed")
    
    logger.info("=" * 60)
    logger.info("✓ ALL SYSTEMS READY")
    logger.info(f"✓ Server running on {Config.HOST}:{Config.PORT}")
    logger.info("=" * 60)
    
    yield
    
    # ===== SHUTDOWN =====
    logger.info("Shutting down...")
    db.disconnect()
    logger.info("✓ Shutdown complete")

# ============================================================================
# FASTAPI APP INITIALIZATION
# ============================================================================
app = FastAPI(
    title="Dog-Cat Classifier API",
    description="Production-ready API for dog-cat image classification",
    version="1.0.0",
    lifespan=lifespan
)

# ============================================================================
# CORS SETUP
# ============================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# HEALTH CHECK ENDPOINT
# ============================================================================
@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        success=True,
        message="Server is running",
        timestamp=datetime.now().isoformat()
    )

# ============================================================================
# AUTH ENDPOINTS (UNPROTECTED)
# ============================================================================

@app.post("/api/auth/signup")
async def signup_route(request: SignupRequest):
    """User signup endpoint"""
    try:
        from utils.security import security
        
        # Convert email to lowercase
        email = request.email.lower()
        
        # Validate password strength
        is_valid_pwd, pwd_msg = security.validate_password(request.password)
        if not is_valid_pwd:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=pwd_msg
            )
        
        # Validate phone number if provided
        if request.phone_number and not security.validate_phone(request.phone_number):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid phone number format"
            )
        
        # Check existing user
        existing_user_query = "SELECT id FROM users WHERE email = %s OR username = %s"
        existing_user = db.execute_query(existing_user_query, (email, request.username))
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered or username taken"
            )
        
        # Create user
        unique_id = security.generate_unique_id()
        password_hash = security.hash_password(request.password)
        
        insert_query = """
        INSERT INTO users (unique_id, username, email, password_hash, name, phone_number, address)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        result = db.execute_insert_update(
            insert_query,
            (unique_id, request.username, email, password_hash, request.name, 
             request.phone_number or None, request.address or None)
        )
        
        if result is None or result == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )
        
        logger.info(f"✓ New user registered: {request.username} ({unique_id})")
        
        return {
            "success": True,
            "message": "User registered successfully",
            "data": {
                "unique_id": unique_id,
                "username": request.username,
                "email": email
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server error"
        )


@app.post("/api/auth/login")
async def login_route(request: LoginRequest):
    """User login endpoint"""
    try:
        from utils.security import security
        
        email = request.email.lower()
        
        # Fetch user
        query = "SELECT * FROM users WHERE email = %s"
        user = db.execute_query(query, (email,))
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        user = user[0]
        
        # Verify password
        if not security.verify_password(user['password_hash'], request.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Create JWT token
        token = security.create_access_token(
            data={
                "user_id": user['id'],
                "unique_id": user['unique_id'],
                "username": user['username'],
                "email": user['email']
            }
        )
        
        logger.info(f"✓ User logged in: {user['username']} ({user['unique_id']})")
        
        return {
            "success": True,
            "message": "Login successful",
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user['id'],
                "unique_id": user['unique_id'],
                "username": user['username'],
                "email": user['email'],
                "name": user['name']
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server error"
        )

# ============================================================================
# AUTH ENDPOINTS (PROTECTED)
# ============================================================================

@app.get("/api/auth/profile")
async def get_profile_route(current_user: dict = Depends(get_current_user)):
    """Get current user profile"""
    try:
        user_id = current_user['user_id']
        
        query = "SELECT id, unique_id, username, email, name, phone_number, address, created_at FROM users WHERE id = %s"
        user = db.execute_query(query, (user_id,))
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {
            "success": True,
            "data": user[0]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server error"
        )


@app.put("/api/auth/profile/update")
async def update_profile_route(
    request: ProfileUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update user profile"""
    try:
        from utils.security import security
        
        user_id = current_user['user_id']
        
        # Validate phone if provided
        if request.phone_number and not security.validate_phone(request.phone_number):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid phone number"
            )
        
        update_query = "UPDATE users SET name = %s, phone_number = %s, address = %s WHERE id = %s"
        result = db.execute_insert_update(
            update_query,
            (request.name, request.phone_number, request.address, user_id)
        )
        
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update profile"
            )
        
        logger.info(f"✓ Profile updated for user: {current_user['username']}")
        
        return {
            "success": True,
            "message": "Profile updated successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server error"
        )

# ============================================================================
# PREDICTION ENDPOINTS (PROTECTED)
# ============================================================================

@app.post("/api/predict/upload-and-predict")
async def upload_and_predict_route(
    files: list[UploadFile] = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload images and get predictions"""
    try:
        from utils.image_processor import image_processor
        from utils.model_loader import get_model
        
        user_id = current_user['user_id']
        unique_id = current_user['unique_id']
        
        # Validate file count
        if len(files) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No files selected"
            )
        
        if len(files) > Config.MAX_UPLOAD_FILES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum {Config.MAX_UPLOAD_FILES} files per upload"
            )
        
        # Get DL model
        model = get_model()
        if not model or not model.is_loaded:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Model not available"
            )
        
        # Process each file
        results = []
        upload_folder = Config.UPLOAD_FOLDER
        
        for file in files:
            if file.filename == '':
                results.append({
                    "filename": "unknown",
                    "success": False,
                    "error": "Empty filename"
                })
                continue
            
            # Save file
            success, filename, error = await image_processor.save_uploaded_file(
                file, unique_id, upload_folder
            )
            
            if not success:
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "error": error
                })
                continue
            
            # Predict
            file_path = os.path.join(upload_folder, filename)
            prediction_result = model.predict(file_path)
            
            if not prediction_result['success']:
                try:
                    os.remove(file_path)
                except:
                    pass
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "error": prediction_result['error']
                })
                continue
            
            # Save to database
            insert_query = """
            INSERT INTO images (user_id, image_filename, image_path, prediction_result, confidence_score)
            VALUES (%s, %s, %s, %s, %s)
            """
            
            db_result = db.execute_insert_update(
                insert_query,
                (
                    user_id,
                    filename,
                    file_path,
                    prediction_result['prediction'],
                    prediction_result['confidence']
                )
            )
            
            if db_result is None or db_result == 0:
                try:
                    os.remove(file_path)
                except:
                    pass
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "error": "Failed to save prediction"
                })
                continue
            
            logger.info(f"✓ Prediction saved: {filename} -> {prediction_result['prediction']} ({prediction_result['confidence']}%)")
            
            results.append({
                "filename": filename,
                "original_filename": file.filename,
                "success": True,
                "prediction": prediction_result['prediction'],
                "confidence": prediction_result['confidence'],
                "raw_output": prediction_result['raw_output']
            })
        
        # Check if any predictions were successful
        successful = [r for r in results if r.get('success')]
        
        return JSONResponse(
            status_code=status.HTTP_200_OK if successful else status.HTTP_400_BAD_REQUEST,
            content={
                "success": len(successful) > 0,
                "message": f"{len(successful)} out of {len(files)} files processed successfully",
                "results": results
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server error"
        )


@app.post("/api/predict/history")
async def get_history_route(
    request_data: dict = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all predictions for current user"""
    try:
        # Default values
        limit = 50
        offset = 0
        
        # If request_data provided, use those values
        if request_data:
            limit = request_data.get('limit', 50)
            offset = request_data.get('offset', 0)
        
        # Validate limits
        if limit > 500:
            limit = 500
        if limit < 1:
            limit = 1
        if offset < 0:
            offset = 0
        
        user_id = current_user['user_id']
        
        # Fetch predictions
        query = """
        SELECT id, image_filename, image_path, prediction_result, confidence_score, uploaded_at
        FROM images
        WHERE user_id = %s
        ORDER BY uploaded_at DESC
        LIMIT %s OFFSET %s
        """
        
        images = db.execute_query(query, (user_id, limit, offset))
        
        # Fetch total count
        count_query = "SELECT COUNT(*) as total FROM images WHERE user_id = %s"
        count_result = db.execute_query(count_query, (user_id,))
        total_count = count_result[0]['total'] if count_result else 0
        
        if not images:
            images = []
        
        logger.info(f"✓ Fetched {len(images)} predictions for user: {current_user['username']}")
        
        return {
            "success": True,
            "data": images,
            "pagination": {
                "total": total_count,
                "limit": limit,
                "offset": offset
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"History fetch error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server error"
        )


@app.post("/api/predict/get-image")
async def get_image_route(
    request: dict,
    current_user: dict = Depends(get_current_user)
):
    """Get details of a specific prediction - Image ID from request body"""
    try:
        image_id = request.get('image_id')
        
        if not image_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="image_id is required"
            )
        
        user_id = current_user['user_id']
        
        query = "SELECT * FROM images WHERE id = %s AND user_id = %s"
        image = db.execute_query(query, (image_id, user_id))
        
        if not image:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found"
            )
        
        return {
            "success": True,
            "data": image[0]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get prediction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server error"
        )


@app.post("/api/predict/delete-image")
async def delete_image_route(
    request: dict,
    current_user: dict = Depends(get_current_user)
):
    """Delete a prediction and its image file - Image ID from request body"""
    try:
        image_id = request.get('image_id')
        
        if not image_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="image_id is required"
            )
        
        user_id = current_user['user_id']
        
        # Fetch image info
        query = "SELECT * FROM images WHERE id = %s AND user_id = %s"
        image = db.execute_query(query, (image_id, user_id))
        
        if not image:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found"
            )
        
        image_data = image[0]
        
        # Delete from database
        delete_query = "DELETE FROM images WHERE id = %s AND user_id = %s"
        result = db.execute_insert_update(delete_query, (image_id, user_id))
        
        if result is None or result == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete"
            )
        
        # Delete file from filesystem
        if os.path.exists(image_data['image_path']):
            try:
                os.remove(image_data['image_path'])
                logger.info(f"✓ Image file deleted: {image_data['image_filename']}")
            except Exception as e:
                logger.warning(f"Could not delete image file: {e}")
        
        logger.info(f"✓ Prediction deleted: {image_id}")
        
        return {
            "success": True,
            "message": "Prediction deleted successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete prediction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server error"
        )


# ============================================================================
# SERVE UPLOADED IMAGES
# ============================================================================

@app.get("/api/uploads/{filename}")
async def serve_image(filename: str):
    """Serve uploaded image files"""
    try:
        file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
        
        # Security check - prevent directory traversal
        if not os.path.abspath(file_path).startswith(os.path.abspath(Config.UPLOAD_FOLDER)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        from fastapi.responses import FileResponse
        return FileResponse(file_path, media_type="image/jpeg")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image serve error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error serving image"
        )
    
    
# ============================================================================
# ERROR HANDLERS
# ============================================================================
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "Internal server error"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=Config.HOST,
        port=Config.PORT
    )