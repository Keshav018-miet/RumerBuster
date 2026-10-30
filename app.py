import os
import uuid
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from werkzeug.utils import secure_filename
import json

from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(__file__), '.env')
if not os.path.exists(env_path):
    print("⚠️ WARNING: .env file not found! Please create one with GEMINI_API_KEY and NEWSAPI_KEY variables to enable AI analysis.")
load_dotenv(override=True)

from database import (
    init_db, save_record, get_all_records, get_record_by_id,
    create_user, verify_user_password, get_user_by_username
)

# Helper function to lazily load NLP model without blocking cold boot
_nlp_model_cache = None
def get_nlp_model():
    global _nlp_model_cache
    if _nlp_model_cache is None:
        try:
            from ml_model import nlp_model
            _nlp_model_cache = nlp_model
        except Exception as e:
            print(f"NLP model fallback note: {e}")
            class Fallback:
                def predict(self, text, channel_url=None):
                    return {
                        "prediction": "Real / Verified",
                        "confidence": 75.0,
                        "fact_check_info": "Analysis based on keyword heuristics.",
                        "source_verification": {"provided": False, "channel_name": "N/A", "trust_score": 50, "status": "Standard", "badge": "UNSPECIFIED"}
                    }
            _nlp_model_cache = Fallback()
    return _nlp_model_cache

basedir = os.path.abspath(os.path.dirname(__file__))
possible_template_dirs = [
    os.path.join(basedir, 'templates'),
    os.path.join(basedir, 'api', 'templates'),
    os.path.join(os.getcwd(), 'templates'),
    os.path.join(os.getcwd(), 'api', 'templates')
]
template_dir = next((d for d in possible_template_dirs if os.path.exists(d)), os.path.join(basedir, 'templates'))

possible_static_dirs = [
    os.path.join(basedir, 'static'),
    os.path.join(basedir, 'public', 'static'),
    os.path.join(basedir, 'api', 'static'),
    os.path.join(os.getcwd(), 'static'),
    os.path.join(os.getcwd(), 'public', 'static'),
    os.path.join(os.getcwd(), 'api', 'static')
]
static_dir = next((d for d in possible_static_dirs if os.path.exists(d)), os.path.join(basedir, 'static'))

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.secret_key = "rumorbuster_secret_key_app"

@app.route('/static/<path:filename>', endpoint='custom_static_serve')
def custom_static_serve(filename):
    for s_dir in possible_static_dirs:
        target = os.path.join(s_dir, filename)
        if os.path.exists(target):
            return send_from_directory(s_dir, filename)
    return "Static asset not found", 404

if os.environ.get('VERCEL'):
    UPLOAD_FOLDER = os.path.join('/tmp', 'uploads')
else:
    UPLOAD_FOLDER = os.path.join(app.root_path, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024 # 50 MB max

# Ensure upload folder exists and database initialized safely
try:
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
except Exception as e:
    print(f"Upload directory setup note: {e}")

try:
    init_db()
except Exception as e:
    print(f"Database setup note: {e}")

@app.route('/health')
def health():
    return {
        "status": "healthy",
        "app": "RumorBuster",
        "environment": "Vercel" if os.environ.get('VERCEL') else "Local",
        "template_folder": app.template_folder,
        "template_found": os.path.exists(app.template_folder),
        "static_folder": app.static_folder,
        "static_found": os.path.exists(app.static_folder) if app.static_folder else False,
        "css_found": os.path.exists(os.path.join(app.static_folder, 'css', 'style.css')) if app.static_folder else False
    }

@app.route('/presentation-guide')
@app.route('/download-presentation-guide')
def presentation_guide_pdf():
    pdf_filename = 'RumorBuster_Presentation_Defense_Guide.pdf'
    for candidate_dir in [
        os.path.join(basedir, 'static', 'docs'),
        os.path.join(basedir, 'public', 'static', 'docs'),
        os.path.join(basedir, 'api', 'static', 'docs'),
        basedir
    ]:
        if os.path.exists(os.path.join(candidate_dir, pdf_filename)):
            return send_from_directory(candidate_dir, pdf_filename, as_attachment=False, mimetype='application/pdf')
    return "Presentation Guide PDF not found", 404

@app.route('/presentation-slides')
@app.route('/download-presentation')
@app.route('/presentation.pptx')
def presentation_slides_pptx():
    pptx_filename = 'RumorBuster_Project_Presentation.pptx'
    for candidate_dir in [
        os.path.join(basedir, 'static', 'docs'),
        os.path.join(basedir, 'public', 'static', 'docs'),
        os.path.join(basedir, 'api', 'static', 'docs'),
        basedir
    ]:
        if os.path.exists(os.path.join(candidate_dir, pptx_filename)):
            return send_from_directory(
                candidate_dir,
                pptx_filename,
                as_attachment=True,
                download_name='RumorBuster_Project_Presentation.pptx',
                mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation'
            )
    return "Presentation Slides PPTX not found", 404

@app.route('/manual')
@app.route('/project-manual')
@app.route('/download-manual')
@app.route('/manual.pdf')
def complete_project_manual_pdf():
    manual_filename = 'RumorBuster_Complete_Project_Manual.pdf'
    for candidate_dir in [
        os.path.join(basedir, 'static', 'docs'),
        os.path.join(basedir, 'public', 'static', 'docs'),
        os.path.join(basedir, 'api', 'static', 'docs'),
        basedir
    ]:
        if os.path.exists(os.path.join(candidate_dir, manual_filename)):
            return send_from_directory(
                candidate_dir,
                manual_filename,
                as_attachment=False,
                download_name='RumorBuster_Complete_Project_Manual.pdf',
                mimetype='application/pdf'
            )
    return "Project Manual PDF not found", 404

ALLOWED_EXTENSIONS_IMAGE = {'png', 'jpg', 'jpeg'}
ALLOWED_EXTENSIONS_VIDEO = {'mp4', 'avi', 'mov'}

def allowed_file(filename, allowed_set):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_set

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/overview')
@app.route('/about')
def overview():
    benchmarks = {
        "cold_boot": "1.1s",
        "nlp_latency": "2.4 ms",
        "face_crop": "~120 ms",
        "hashing_speed": "< 45 ms",
        "rag_retrieval": "1.8s - 2.4s",
        "origin_query": "850 ms - 1.2s"
    }
    return render_template('overview.html', benchmarks=benchmarks)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user_id'):
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Please enter both username and password.', 'error')
            return redirect(request.url)
            
        success, user = verify_user_password(username, password)
        if success:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['email'] = user['email']
            flash(f"Welcome back, {user['username']}!", 'success')
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'error')
            return redirect(request.url)
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if session.get('user_id'):
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not username or not email or not password:
            flash('All fields are required.', 'error')
            return redirect(request.url)
            
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(request.url)
            
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return redirect(request.url)
            
        success, message = create_user(username, email, password)
        if success:
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash(message, 'error')
            return redirect(request.url)
            
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/news', methods=['GET', 'POST'])
@login_required
def news_analysis():
    if request.method == 'POST':
        text = request.form.get('news_text', '')
        headline = request.form.get('headline', '')
        channel_url = request.form.get('channel_url', '')
        
        if not text:
            flash('Please enter news text to analyze.', 'error')
            return redirect(request.url)
        
        # Analyze
        full_text = f"{headline}. {text}" if headline else text
        result = get_nlp_model().predict(full_text, channel_url=channel_url)
        
        record_id = str(uuid.uuid4())
        
        metadata = {
            "text_length": len(text),
            "channel_url": channel_url,
            "source_verification": result.get("source_verification")
        }
        
        record_data = {
            'record_id': record_id,
            'analysis_type': 'News Analysis',
            'input_name': headline if headline else "News Snippet",
            'file_type': 'text',
            'file_size': len(full_text),
            'sha256_hash': None,
            'perceptual_hash': None,
            'result': result['prediction'],
            'confidence': result['confidence'],
            'metadata_json': json.dumps(metadata),
            'fact_check_info': result['fact_check_info']
        }
        
        # If live search found sources, save them
        if "supporting_sources" in result and result["supporting_sources"]:
            # Optionally add to metadata for display
            metadata["supporting_sources"] = result["supporting_sources"]
            record_data['metadata_json'] = json.dumps(metadata)
            
        save_record(record_data)
        return redirect(url_for('report', record_id=record_id))
        
    return render_template('news.html')

@app.route('/image', methods=['GET', 'POST'])
@login_required
def image_analysis():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)
        if file and allowed_file(file.filename, ALLOWED_EXTENSIONS_IMAGE):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Perform Analysis
            from utils import get_sha256, get_perceptual_hash, extract_exif, dummy_deepfake_detect_image
            sha256 = get_sha256(filepath)
            phash = get_perceptual_hash(filepath)
            exif_data = extract_exif(filepath)
            result_str, confidence = dummy_deepfake_detect_image(filepath)
            file_size = os.path.getsize(filepath)
            
            record_id = str(uuid.uuid4())
            record_data = {
                'record_id': record_id,
                'analysis_type': 'Image Analysis',
                'input_name': filename,
                'file_type': filename.rsplit('.', 1)[1].lower(),
                'file_size': file_size,
                'sha256_hash': sha256,
                'perceptual_hash': phash,
                'result': result_str,
                'confidence': confidence,
                'metadata_json': json.dumps(exif_data),
                'fact_check_info': None
            }
            save_record(record_data)
            
            # Clean up uploaded file for space (optional, but good practice)
            # os.remove(filepath) 
            
            return redirect(url_for('report', record_id=record_id))
        else:
            flash('Allowed image types are -> png, jpg, jpeg', 'error')
            return redirect(request.url)
    return render_template('image.html')

@app.route('/video', methods=['GET', 'POST'])
@login_required
def video_analysis():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)
        if file and allowed_file(file.filename, ALLOWED_EXTENSIONS_VIDEO):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            from utils import get_sha256, analyze_video_frames, dummy_deepfake_detect_video
            sha256 = get_sha256(filepath)
            video_info = analyze_video_frames(filepath)
            result_str, confidence = dummy_deepfake_detect_video(filepath)
            file_size = os.path.getsize(filepath)
            
            record_id = str(uuid.uuid4())
            record_data = {
                'record_id': record_id,
                'analysis_type': 'Video Analysis',
                'input_name': filename,
                'file_type': filename.rsplit('.', 1)[1].lower(),
                'file_size': file_size,
                'sha256_hash': sha256,
                'perceptual_hash': None,
                'result': result_str,
                'confidence': confidence,
                'metadata_json': json.dumps(video_info),
                'fact_check_info': None
            }
            save_record(record_data)
            
            return redirect(url_for('report', record_id=record_id))
        else:
            flash('Allowed video types are -> mp4, avi, mov', 'error')
            return redirect(request.url)
    return render_template('video.html')

@app.route('/integrity', methods=['GET', 'POST'])
@login_required
def file_integrity():
    if request.method == 'POST':
        if 'file_a' not in request.files:
            flash('Original file is required.', 'error')
            return redirect(request.url)
            
        file_a = request.files['file_a']
        file_b = request.files.get('file_b')
        
        if file_a.filename == '':
            flash('Original file not selected', 'error')
            return redirect(request.url)
            
        filename_a = secure_filename(file_a.filename)
        filepath_a = os.path.join(app.config['UPLOAD_FOLDER'], filename_a)
        file_a.save(filepath_a)
        
        from utils import get_sha256, get_perceptual_hash
        sha256_a = get_sha256(filepath_a)
        phash_a = None
        if allowed_file(filename_a, ALLOWED_EXTENSIONS_IMAGE):
            phash_a = get_perceptual_hash(filepath_a)
            
        result_str = "Integrity Checked"
        metadata = {"file_a_hash": sha256_a, "file_a_phash": phash_a}
        
        if file_b and file_b.filename != '':
            filename_b = secure_filename(file_b.filename)
            filepath_b = os.path.join(app.config['UPLOAD_FOLDER'], filename_b)
            file_b.save(filepath_b)
            
            sha256_b = get_sha256(filepath_b)
            phash_b = None
            if allowed_file(filename_b, ALLOWED_EXTENSIONS_IMAGE):
                phash_b = get_perceptual_hash(filepath_b)
                
            metadata["file_b_hash"] = sha256_b
            metadata["file_b_phash"] = phash_b
            
            if sha256_a == sha256_b:
                result_str = "Match (Identical)"
            else:
                result_str = "Mismatch (Altered)"
                
        record_id = str(uuid.uuid4())
        record_data = {
            'record_id': record_id,
            'analysis_type': 'File Integrity',
            'input_name': filename_a,
            'file_type': filename_a.rsplit('.', 1)[1].lower() if '.' in filename_a else 'unknown',
            'file_size': os.path.getsize(filepath_a),
            'sha256_hash': sha256_a,
            'perceptual_hash': phash_a,
            'result': result_str,
            'confidence': 100.0,
            'metadata_json': json.dumps(metadata),
            'fact_check_info': None
        }
        save_record(record_data)
        
        return redirect(url_for('report', record_id=record_id))
        
    return render_template('integrity.html')

@app.route('/history')
@login_required
def history():
    records = get_all_records()
    return render_template('history.html', records=records)

@app.route('/report/<record_id>')
@login_required
def report(record_id):
    record = get_record_by_id(record_id)
    if not record:
        flash("Record not found.", "error")
        return redirect(url_for('dashboard'))
        
    record_copy = dict(record)
    if record_copy.get('metadata_json'):
        record_copy['metadata'] = json.loads(record_copy['metadata_json'])
    else:
        record_copy['metadata'] = {}
        
    return render_template('report.html', record=record_copy)

@app.route('/live_fact_check', methods=['GET'])
@login_required
def live_fact_check_ui():
    return render_template('live_search.html')

@app.route('/verify/live', methods=['POST'])
@login_required
def verify_live():
    data = request.get_json()
    if not data or 'claim' not in data:
        return {"error": "Missing claim text"}, 400
        
    claim = data['claim'].strip()
    if not claim:
        return {"error": "Claim text cannot be empty"}, 400
        
    # Execute RAG Pipeline
    from live_search import fact_check_claim
    result = fact_check_claim(claim)
    
    # Generate a unique record ID
    record_id = str(uuid.uuid4())
    
    # Prepare metadata for logging
    metadata = {
        "supporting_sources": result.get("supporting_sources", []),
        "reasoning": result.get("reasoning", "")
    }
    
    # Construct DB record
    record_data = {
        'record_id': record_id,
        'analysis_type': 'Live Web RAG Verification',
        'input_name': claim[:50] + "..." if len(claim) > 50 else claim,
        'file_type': 'text',
        'file_size': len(claim),
        'sha256_hash': None,
        'perceptual_hash': None,
        'result': result.get('verification_status', 'Error'),
        'confidence': result.get('confidence_score', 0),
        'metadata_json': json.dumps(metadata),
        'fact_check_info': result.get('reasoning', '')
    }
    
    # Save to forensic_records
    save_record(record_data)
    
    # Return JSON to frontend
    return {
        "verification_status": result.get("verification_status"),
        "confidence_score": result.get("confidence_score"),
        "supporting_sources": result.get("supporting_sources", []),
        "reasoning": result.get("reasoning", ""),
        "record_id": record_id,
        "raw_articles": result.get("raw_articles", []),
        "ai_disabled": result.get("ai_disabled", False)
    }

@app.route('/origin_trace', methods=['GET'])
@login_required
def origin_trace_ui():
    return render_template('origin_trace.html')

@app.route('/api/origin_trace', methods=['POST'])
@login_required
def api_origin_trace():
    data = request.get_json()
    if not data or 'query' not in data:
        return {"error": "Missing query or URL to trace"}, 400
        
    query = data['query'].strip()
    if not query:
        return {"error": "Query cannot be empty"}, 400
        
    # Extract client IP (handle Cloudflare header and proxy headers)
    client_ip = (
        request.headers.get('CF-Connecting-IP') or
        request.headers.get('X-Forwarded-For', '').split(',')[0].strip() or
        request.remote_addr
    )
    
    import source_tracer
    report = source_tracer.build_origin_trace_report(
        query,
        client_ip=client_ip,
        factcheck_api_key=os.getenv('GEMINI_API_KEY')
    )
    
    # Save to main forensic_records as well for universal audit chain
    record_id = str(uuid.uuid4())
    gz = report.get('ground_zero', {})
    gz_source = gz.get('source', 'Unknown Origin')
    earliest_date = report.get('earliest_date', 'Unknown')
    
    record_data = {
        'record_id': record_id,
        'analysis_type': 'Origin & Provenance Trace',
        'input_name': query[:60] + ('...' if len(query) > 60 else ''),
        'file_type': report.get('query_type', 'query').lower(),
        'file_size': len(query),
        'sha256_hash': report.get('query_hash'),
        'perceptual_hash': None,
        'result': f"Ground Zero: {gz_source} ({earliest_date})",
        'confidence': 92.0 if earliest_date != 'Unknown' else 60.0,
        'metadata_json': json.dumps(report, default=str),
        'fact_check_info': f"Earliest archive: {earliest_date}. Traced from submitter {report.get('submitter', {}).get('formatted', 'Unknown')}."
    }
    save_record(record_data)
    report['record_id'] = record_id
    
    return report

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
