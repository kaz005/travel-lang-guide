from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSON

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

    @staticmethod
    def from_json(data):
        return TouristSpot(
            id=data.get('id'),
            name=data.get('name'),
            description=data.get('description'),
            coordinates=data.get('coordinates'),
            images=data.get('images')
        )
