import os
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session
from models import db, TouristSpot, Admin
from functools import wraps
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24)  # For session management
db.init_app(app)

def init_db():
    with app.app_context():
        db.create_all()
        # Load initial data if the database is empty
        if TouristSpot.query.count() == 0:
            with open('static/data/spots.json', 'r', encoding='utf-8') as file:
                spots_data = json.load(file)
                for spot_data in spots_data:
                    spot = TouristSpot.from_json(spot_data)
                    db.session.add(spot)
                db.session.commit()
        
        # Create default admin if none exists
        if Admin.query.count() == 0:
            admin = Admin(username='admin')
            admin.set_password('admin')  # Default password, should be changed
            db.session.add(admin)
            db.session.commit()

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    lang = request.args.get('lang', 'en')
    spots = [spot.to_dict() for spot in TouristSpot.query.all()]
    return render_template('index.html', spots=spots, current_lang=lang)

@app.route('/spot/<int:spot_id>')
def spot_detail(spot_id):
    lang = request.args.get('lang', 'en')
    spot = TouristSpot.query.get_or_404(spot_id)
    return render_template('detail.html', spot=spot.to_dict(), current_lang=lang)

@app.route('/map')
def map_view():
    lang = request.args.get('lang', 'en')
    spots = [spot.to_dict() for spot in TouristSpot.query.all()]
    return render_template('map.html', spots=spots, current_lang=lang)

# Admin routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        admin = Admin.query.filter_by(username=request.form['username']).first()
        if admin and admin.check_password(request.form['password']):
            session['admin_id'] = admin.id
            return redirect(url_for('admin_dashboard'))
        flash('Invalid username or password', 'error')
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_id', None)
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    spots = [spot.to_dict() for spot in TouristSpot.query.all()]
    return render_template('admin/dashboard.html', spots=spots)

@app.route('/admin/spots/create', methods=['GET', 'POST'])
@admin_required
def admin_create_spot():
    if request.method == 'POST':
        spot_data = {
            'name': {
                'en': request.form['name_en'],
                'ja': request.form['name_ja'],
                'zh': request.form['name_zh']
            },
            'description': {
                'en': request.form['desc_en'],
                'ja': request.form['desc_ja'],
                'zh': request.form['desc_zh']
            },
            'coordinates': {
                'lat': float(request.form['lat']),
                'lng': float(request.form['lng'])
            },
            'images': []
        }
        
        # Process images
        urls = request.form.getlist('image_urls[]')
        captions_en = request.form.getlist('image_captions_en[]')
        captions_ja = request.form.getlist('image_captions_ja[]')
        captions_zh = request.form.getlist('image_captions_zh[]')
        
        for i in range(len(urls)):
            spot_data['images'].append({
                'url': urls[i],
                'caption': {
                    'en': captions_en[i],
                    'ja': captions_ja[i],
                    'zh': captions_zh[i]
                }
            })
        
        spot = TouristSpot.from_json(spot_data)
        db.session.add(spot)
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/spot_form.html', spot=None)

@app.route('/admin/spots/<int:spot_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_spot(spot_id):
    spot = TouristSpot.query.get_or_404(spot_id)
    
    if request.method == 'POST':
        spot.name = {
            'en': request.form['name_en'],
            'ja': request.form['name_ja'],
            'zh': request.form['name_zh']
        }
        spot.description = {
            'en': request.form['desc_en'],
            'ja': request.form['desc_ja'],
            'zh': request.form['desc_zh']
        }
        spot.coordinates = {
            'lat': float(request.form['lat']),
            'lng': float(request.form['lng'])
        }
        
        # Process images
        urls = request.form.getlist('image_urls[]')
        captions_en = request.form.getlist('image_captions_en[]')
        captions_ja = request.form.getlist('image_captions_ja[]')
        captions_zh = request.form.getlist('image_captions_zh[]')
        
        spot.images = []
        for i in range(len(urls)):
            spot.images.append({
                'url': urls[i],
                'caption': {
                    'en': captions_en[i],
                    'ja': captions_ja[i],
                    'zh': captions_zh[i]
                }
            })
        
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/spot_form.html', spot=spot.to_dict())

# API Endpoints
@app.route('/api/spots', methods=['GET'])
def get_spots():
    spots = TouristSpot.query.all()
    return jsonify([spot.to_dict() for spot in spots])

@app.route('/api/spots/<int:spot_id>', methods=['GET'])
def get_spot(spot_id):
    spot = TouristSpot.query.get_or_404(spot_id)
    return jsonify(spot.to_dict())

@app.route('/api/spots', methods=['POST'])
@admin_required
def create_spot():
    data = request.get_json()
    spot = TouristSpot.from_json(data)
    db.session.add(spot)
    db.session.commit()
    return jsonify(spot.to_dict()), 201

@app.route('/api/spots/<int:spot_id>', methods=['PUT'])
@admin_required
def update_spot(spot_id):
    spot = TouristSpot.query.get_or_404(spot_id)
    data = request.get_json()
    for key, value in data.items():
        setattr(spot, key, value)
    db.session.commit()
    return jsonify(spot.to_dict())

@app.route('/api/spots/<int:spot_id>', methods=['DELETE'])
@admin_required
def delete_spot(spot_id):
    spot = TouristSpot.query.get_or_404(spot_id)
    db.session.delete(spot)
    db.session.commit()
    return '', 204

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
