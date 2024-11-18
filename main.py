from flask import Flask, render_template, request, redirect, url_for
import json

app = Flask(__name__)

def load_spots_data():
    with open('static/data/spots.json', 'r', encoding='utf-8') as file:
        return json.load(file)

@app.route('/')
def index():
    lang = request.args.get('lang', 'en')
    spots = load_spots_data()
    return render_template('index.html', spots=spots, current_lang=lang)

@app.route('/spot/<int:spot_id>')
def spot_detail(spot_id):
    lang = request.args.get('lang', 'en')
    spots = load_spots_data()
    spot = next((spot for spot in spots if spot['id'] == spot_id), None)
    if spot is None:
        return redirect(url_for('index'))
    return render_template('detail.html', spot=spot, current_lang=lang)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
