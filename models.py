from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSON
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class TouristSpot(db.Model):
    __tablename__ = 'tourist_spots'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(JSON, nullable=False)  # Stores multilingual names
    description = db.Column(JSON, nullable=False)  # Stores multilingual descriptions
    coordinates = db.Column(JSON, nullable=False)  # Stores lat/lng
    images = db.Column(JSON, nullable=False)  # Stores array of image objects

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'coordinates': self.coordinates,
            'images': self.images
        }

    @classmethod
    def from_json(cls, data):
        return cls(
            name=data.get('name'),
            description=data.get('description'),
            coordinates=data.get('coordinates'),
            images=data.get('images')
        )

class Admin(db.Model):
    __tablename__ = 'admins'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))  # Increased length to 255

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
