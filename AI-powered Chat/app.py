from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
import google.generativeai as genai
import os
import json
import base64
import requests
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import time
import urllib.parse
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///presentations.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
CORS(app)

# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Configure upload settings
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create upload folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    presentations = db.relationship('Presentation', backref='user', lazy=True, cascade='all, delete-orphan')


class Presentation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    slides_data = db.Column(db.Text, nullable=False)  # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def fetch_image_from_unsplash(query, index=0):
    """
    Fetch a relevant image from Unsplash based on search query
    Returns: image URL or None
    """
    try:
        # Using Unsplash Source API (no API key required)
        # Format: https://source.unsplash.com/{WIDTH}x{HEIGHT}/?{KEYWORD}
        
        # Clean and improve search query
        # Remove common words and use top keywords
        stop_words = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'about']
        words = [w.lower() for w in query.split() if w.lower() not in stop_words]
        
        # Use top 3-4 most relevant keywords
        search_term = ','.join(words[:4])
        
        # Build URL - Unsplash Source uses comma-separated keywords
        image_url = f"https://source.unsplash.com/800x600/?{search_term}"
        
        print(f"   → Testing URL: {image_url}")
        
        # Test if image is accessible
        response = requests.get(image_url, timeout=10, allow_redirects=True)
        
        if response.status_code == 200:
            # Get the final redirected URL
            final_url = response.url
            print(f"   → Redirected to: {final_url[:60]}...")
            return final_url
        elif response.status_code == 503:
            # Unsplash unavailable, use fallback
            print(f"   → Unsplash unavailable (503), using fallback...")
            return fetch_image_fallback(query, index)
        else:
            print(f"   → Status code: {response.status_code}")
            return fetch_image_fallback(query, index)
        
    except Exception as e:
        print(f"   → Error: {str(e)}")
        print(f"   → Using fallback service...")
        return fetch_image_fallback(query, index)


def fetch_image_fallback(query, index=0):
    """
    Fallback image service using Lorem Picsum (always available)
    Returns: image URL
    """
    try:
        # Lorem Picsum provides random images with optional seed
        # Format: https://picsum.photos/seed/{SEED}/800/600
        seed = f"{query.replace(' ', '-')}-{index}"
        fallback_url = f"https://picsum.photos/seed/{seed}/800/600"
        
        print(f"   → Fallback URL: {fallback_url}")
        
        # Test if accessible
        response = requests.head(fallback_url, timeout=5)
        if response.status_code == 200:
            return fallback_url
        
        # If even fallback fails, use basic Lorem Picsum
        return f"https://picsum.photos/800/600?random={index}"
        
    except Exception as e:
        print(f"   → Fallback error: {str(e)}")
        # Last resort: basic random image
        return f"https://picsum.photos/800/600?random={index}"


def download_and_save_image(image_url, slide_index):
    """
    Download image from URL and save to uploads folder
    Returns: local file path or None
    """
    try:
        print(f"   → Downloading image...")
        response = requests.get(image_url, timeout=15, stream=True)
        
        if response.status_code == 200:
            # Generate filename
            timestamp = int(time.time())
            filename = f"slide_{slide_index}_{timestamp}.jpg"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Save image
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Verify file was saved
            file_size = os.path.getsize(filepath)
            print(f"   → Saved {file_size} bytes to {filename}")
            
            # Return relative URL for frontend
            return f"/static/uploads/{filename}"
        else:
            print(f"   → Download failed: Status {response.status_code}")
            return None
        
    except Exception as e:
        print(f"   → Download error: {str(e)}")
        return None

# Configure Gemini AI
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

genai.configure(api_key=GEMINI_API_KEY)

# Initialize Gemini model - using gemini-2.5-pro-preview-05-06
model = genai.GenerativeModel('gemini-2.0-flash-exp')

# Store current presentation data
current_presentation = {"slides": []}

# Store uploaded images
uploaded_images = []


@app.route('/')
def index():
    """Render the main chat interface or login page"""
    if current_user.is_authenticated:
        return render_template('index.html', username=current_user.username)
    return redirect(url_for('login'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Handle user registration"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        # Validation
        if not username or not email or not password:
            if request.is_json:
                return jsonify({"error": "All fields are required"}), 400
            flash('All fields are required', 'error')
            return render_template('signup.html')
        
        # Check if user exists
        if User.query.filter_by(username=username).first():
            if request.is_json:
                return jsonify({"error": "Username already exists"}), 400
            flash('Username already exists', 'error')
            return render_template('signup.html')
        
        if User.query.filter_by(email=email).first():
            if request.is_json:
                return jsonify({"error": "Email already registered"}), 400
            flash('Email already registered', 'error')
            return render_template('signup.html')
        
        # Create new user
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        if request.is_json:
            return jsonify({"success": True, "message": "Account created successfully"})
        
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            if request.is_json:
                return jsonify({"error": "Username and password required"}), 400
            flash('Username and password required', 'error')
            return render_template('login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            if request.is_json:
                return jsonify({"success": True, "username": user.username})
            return redirect(url_for('index'))
        else:
            if request.is_json:
                return jsonify({"error": "Invalid username or password"}), 401
            flash('Invalid username or password', 'error')
            return render_template('login.html')
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """Handle user logout"""
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))


@app.route('/history')
@login_required
def history():
    """Show user's presentation history"""
    presentations = Presentation.query.filter_by(user_id=current_user.id).order_by(Presentation.updated_at.desc()).all()
    return render_template('history.html', presentations=presentations, username=current_user.username)


@app.route('/chat', methods=['POST'])
@login_required
def chat():
    """
    Handle chat requests for generating PowerPoint slides
    Expects: {"prompt": "user message", "include_images": []}
    Returns: {"slides": [...], "message": "AI response"}
    """
    global current_presentation
    
    try:
        data = request.get_json()
        user_prompt = data.get('prompt', '')
        include_images = data.get('include_images', [])
        
        if not user_prompt:
            return jsonify({"error": "No prompt provided"}), 400
        
        # Add image context to prompt if images are included
        image_context = ""
        if include_images:
            image_context = f"\n\nNote: User wants to include {len(include_images)} image(s) in the presentation. Add 'image_placeholder' field to slides where images should appear."
        
        # Create a detailed prompt for Gemini to generate slide content
        # Add personalized greeting with user's name
        user_greeting = f"Hello {current_user.username}! "
        
        system_prompt = user_greeting + """You are an AI assistant specialized in creating PowerPoint presentations with images.
        
        CRITICAL: You MUST add image_search_query to EVERY slide (except pure text conclusion slides).
        
        Your response MUST be in this exact JSON format:
        {
          "slides": [
            {
              "title": "Slide Title",
              "content": ["Point 1", "Point 2", "Point 3"],
              "image_search_query": "specific descriptive search terms",
              "image_position": "right"
            }
          ],
          "message": "A brief confirmation message to the user"
        }
        
        MANDATORY RULES:
        - EVERY slide MUST have "image_search_query" field (cannot be empty or null)
        - Use very specific, descriptive search terms for images
        - For title slides: use dramatic, relevant background images
        - For content slides: use illustrative, topic-related images
        - image_position options: "right" (default), "left", "center", "background" (for title slides)
        
        EXAMPLES OF GOOD image_search_query:
        - "artificial intelligence neural network visualization"
        - "climate change melting glacier arctic"
        - "healthy food colorful vegetables fruits"
        - "modern office teamwork collaboration"
        - "space exploration rocket launch"
        
        Guidelines:
        - Create 5-7 slides unless specified otherwise
        - Each slide needs clear title and 3-5 bullet points
        - First slide (title): use "background" position
        - Content slides: use "right" or "left" position
        - Last slide (conclusion): use "center" or "background"
        - Make image searches highly specific to slide content
        
        User request: """ + user_prompt
        
        # Generate content using Gemini
        print(f"\n🤖 Sending prompt to Gemini AI...")
        response = model.generate_content(system_prompt)
        response_text = response.text.strip()
        print(f"\n📝 AI Response (first 500 chars):\n{response_text[:500]}...\n")
        
        # Extract JSON from response (handle markdown code blocks)
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        
        # Parse JSON response
        try:
            result = json.loads(response_text)
        except json.JSONDecodeError:
            # If JSON parsing fails, create a structured response
            result = {
                "slides": [
                    {
                        "title": "Generated Content",
                        "content": response_text.split('\n')[:5]
                    }
                ],
                "message": "Slides generated successfully!"
            }
        
        # Fetch images for slides that have image_search_query
        slides_with_images = result.get("slides", [])
        print(f"\n🖼️ Processing {len(slides_with_images)} slides for images...")
        
        for index, slide in enumerate(slides_with_images):
            image_query = slide.get("image_search_query", "")
            
            if image_query and image_query.strip():
                query = image_query.strip()
                print(f"\n📸 Slide {index + 1}: Searching for '{query}'")
                
                # Fetch image from Unsplash
                image_url = fetch_image_from_unsplash(query, index)
                
                if image_url:
                    print(f"   ✓ Found image URL: {image_url[:50]}...")
                    # Download and save image
                    local_url = download_and_save_image(image_url, index)
                    if local_url:
                        slide["image_url"] = local_url
                        slide["has_image"] = True
                        print(f"   ✅ Image saved: {local_url}")
                    else:
                        slide["has_image"] = False
                        print(f"   ❌ Failed to save image")
                else:
                    slide["has_image"] = False
                    print(f"   ❌ No image found for query")
            else:
                slide["has_image"] = False
                print(f"\n⚠️ Slide {index + 1}: No image_search_query provided by AI")
        
        # Count successful images
        images_added = sum(1 for s in slides_with_images if s.get("has_image", False))
        print(f"\n✅ Successfully added {images_added}/{len(slides_with_images)} images\n")
        
        result["slides"] = slides_with_images
        
        # Store the current presentation
        current_presentation = {"slides": result.get("slides", [])}
        
        # Save presentation to database
        try:
            # Extract title from first slide or use default
            title = result.get("slides", [{}])[0].get("title", "Untitled Presentation") if result.get("slides") else "Untitled Presentation"
            slides_json = json.dumps(result.get("slides", []))
            
            presentation = Presentation(
                title=title,
                user_id=current_user.id,
                slides_data=slides_json
            )
            db.session.add(presentation)
            db.session.commit()
            
            result["presentation_id"] = presentation.id
            print(f"\n💾 Presentation saved: ID={presentation.id}, Title='{title}'")
        except Exception as save_error:
            print(f"Warning: Could not save presentation: {save_error}")
        
        # Add personalized message
        if "message" not in result or not result["message"]:
            result["message"] = f"Great work, {current_user.username}! Your slides are ready!"
        else:
            result["message"] = f"{current_user.username}, " + result["message"]
        
        return jsonify(result)
    
    except Exception as e:
        print(f"Error in /chat: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/update', methods=['POST'])
def update():
    """
    Handle slide update requests
    Expects: {"prompt": "edit instruction", "slides": [current slides]}
    Returns: {"slides": [...], "message": "AI response"}
    """
    global current_presentation
    
    try:
        data = request.get_json()
        user_prompt = data.get('prompt', '')
        current_slides = data.get('slides', current_presentation.get("slides", []))
        
        if not user_prompt:
            return jsonify({"error": "No prompt provided"}), 400
        
        # Create prompt for updating slides
        system_prompt = f"""You are an AI assistant helping to edit PowerPoint presentations.
        
        Current slides:
        {json.dumps(current_slides, indent=2)}
        
        User wants to: {user_prompt}
        
        Please provide the UPDATED complete slide deck in this JSON format:
        {{
          "slides": [
            {{
              "title": "Slide Title",
              "content": ["Point 1", "Point 2", "Point 3"]
            }}
          ],
          "message": "Brief description of changes made"
        }}
        
        Important:
        - Return ALL slides, including unchanged ones
        - Make only the changes requested by the user
        - Maintain the same structure and format
        - If editing a specific slide number, count from 1 (not 0)
        """
        
        # Generate updated content
        response = model.generate_content(system_prompt)
        response_text = response.text.strip()
        
        # Extract JSON from response
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        
        # Parse JSON response
        try:
            result = json.loads(response_text)
        except json.JSONDecodeError:
            return jsonify({"error": "Failed to parse AI response"}), 500
        
        # Update stored presentation
        current_presentation = {"slides": result.get("slides", [])}
        
        return jsonify(result)
    
    except Exception as e:
        print(f"Error in /update: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/get-slides', methods=['GET'])
@login_required
def get_slides():
    """Get current presentation slides"""
    return jsonify(current_presentation)


@app.route('/load-presentation/<int:presentation_id>')
@login_required
def load_presentation(presentation_id):
    """Load a specific presentation from history"""
    presentation = Presentation.query.filter_by(id=presentation_id, user_id=current_user.id).first()
    
    if not presentation:
        return jsonify({"error": "Presentation not found"}), 404
    
    slides = json.loads(presentation.slides_data)
    return jsonify({
        "slides": slides,
        "title": presentation.title,
        "created_at": presentation.created_at.isoformat(),
        "updated_at": presentation.updated_at.isoformat()
    })


@app.route('/delete-presentation/<int:presentation_id>', methods=['DELETE'])
@login_required
def delete_presentation(presentation_id):
    """Delete a presentation"""
    presentation = Presentation.query.filter_by(id=presentation_id, user_id=current_user.id).first()
    
    if not presentation:
        return jsonify({"error": "Presentation not found"}), 404
    
    db.session.delete(presentation)
    db.session.commit()
    
    return jsonify({"success": True, "message": "Presentation deleted"})


@app.route('/upload-image', methods=['POST'])
def upload_image():
    """
    Handle image uploads for slides
    Returns: {"success": true, "filename": "...", "url": "..."}
    """
    global uploaded_images
    
    try:
        if 'image' not in request.files:
            return jsonify({"error": "No image file provided"}), 400
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Add timestamp to avoid conflicts
            import time
            timestamp = str(int(time.time()))
            filename = f"{timestamp}_{filename}"
            
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Store image info
            image_url = f"/static/uploads/{filename}"
            uploaded_images.append({
                "filename": filename,
                "url": image_url,
                "path": filepath
            })
            
            return jsonify({
                "success": True,
                "filename": filename,
                "url": image_url
            })
        else:
            return jsonify({"error": "Invalid file type. Allowed: png, jpg, jpeg, gif, bmp, webp"}), 400
    
    except Exception as e:
        print(f"Error in /upload-image: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/get-images', methods=['GET'])
def get_images():
    """Get list of uploaded images"""
    return jsonify({"images": uploaded_images})


if __name__ == '__main__':
    # Create database tables
    with app.app_context():
        db.create_all()
        print("✅ Database tables created")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
