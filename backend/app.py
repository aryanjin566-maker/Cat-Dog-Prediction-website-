from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config import Config
from database import db
from utils.model_loader import initialize_model
import logging
import os
from datetime import datetime

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
# FLASK APP INITIALIZATION
# ============================================================================
app = Flask(__name__)
app.config.from_object(Config)

# ============================================================================
# CORS SETUP (Allow frontend to communicate)
# ============================================================================
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# ============================================================================
# JWT SETUP
# ============================================================================
jwt = JWTManager(app)

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    return jwt_data

# ============================================================================
# ERROR HANDLERS
# ============================================================================
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({
        'success': False,
        'message': 'Token has expired'
    }), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({
        'success': False,
        'message': 'Invalid token'
    }), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({
        'success': False,
        'message': 'Authorization required'
    }), 401

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'message': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'success': False,
        'message': 'Internal server error'
    }), 500

# ============================================================================
# REGISTER BLUEPRINTS
# ============================================================================
from routes.auth import auth_bp
from routes.predict import predict_bp

app.register_blueprint(auth_bp)
app.register_blueprint(predict_bp)

# ============================================================================
# HEALTH CHECK ENDPOINT
# ============================================================================
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'success': True,
        'message': 'Server is running',
        'timestamp': datetime.now().isoformat()
    }), 200

# ============================================================================
# STARTUP INITIALIZATION
# ============================================================================
@app.before_request
def startup():
    """Initialize on first request"""
    if not hasattr(app, 'initialized'):
        logger.info("=" * 60)
        logger.info("🚀 STARTING DOG-CAT CLASSIFIER SERVER")
        logger.info("=" * 60)
        
        # Create uploads folder
        if not os.path.exists(Config.UPLOAD_FOLDER):
            os.makedirs(Config.UPLOAD_FOLDER)
            logger.info(f"✓ Created uploads folder: {Config.UPLOAD_FOLDER}")
        
        # Connect to database
        if not db.connect():
            logger.error("✗ Failed to connect to database")
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
        # Load ML model
        logger.info("Loading Deep Learning Model...")
        if not initialize_model(Config.MODEL_PATH):
            logger.error("✗ Failed to load model")
            return jsonify({'success': False, 'message': 'Model loading failed'}), 500
        
        logger.info("=" * 60)
        logger.info("✓ ALL SYSTEMS READY")
        logger.info(f"✓ Server running on {Config.HOST}:{Config.PORT}")
        logger.info("=" * 60)
        
        app.initialized = True

# ============================================================================
# SHUTDOWN HANDLER
# ============================================================================
@app.teardown_appcontext
def shutdown(exception):
    """Cleanup on shutdown"""
    db.disconnect()

# ============================================================================
# RUN APP
# ============================================================================
if __name__ == '__main__':
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )