import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
from models import db, TouristSpot
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
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

@app.route('/')
def index():
    lang = request.args.get('lang', 'en')
    spots = [spot.to_dict() for spot in TouristSpot.query.all()]
    return render_template('index.html', spots=spots, current_lang=lang)

@app.route('/spot/<int:spot_id>')
def spot_detail(spot_id):
    lang = request.args.get('lang', 'en')
    spot = TouristSpot.query.get_or_404(spot_id)
    return render_template('detail.html', spot=spot, current_lang=lang)

@app.route('/map')
def map_view():
    lang = request.args.get('lang', 'en')
    spots = [spot.to_dict() for spot in TouristSpot.query.all()]
    return render_template('map.html', spots=spots, current_lang=lang)

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
def create_spot():
    data = request.get_json()
    spot = TouristSpot.from_json(data)
    db.session.add(spot)
    db.session.commit()
    return jsonify(spot.to_dict()), 201

@app.route('/api/spots/<int:spot_id>', methods=['PUT'])
def update_spot(spot_id):
    spot = TouristSpot.query.get_or_404(spot_id)
    data = request.get_json()
    for key, value in data.items():
        setattr(spot, key, value)
    db.session.commit()
    return jsonify(spot.to_dict())

@app.route('/api/spots/<int:spot_id>', methods=['DELETE'])
def delete_spot(spot_id):
    spot = TouristSpot.query.get_or_404(spot_id)
    db.session.delete(spot)
    db.session.commit()
    return '', 204

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
