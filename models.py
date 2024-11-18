from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSON
from werkzeug.security import generate_password_hash, check_password_hash
import logging

logger = logging.getLogger(__name__)
db = SQLAlchemy()

class TouristSpot(db.Model):
    __tablename__ = 'tourist_spots'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(JSON, nullable=False)
    description = db.Column(JSON, nullable=False)
    coordinates = db.Column(JSON, nullable=False)
    images = db.Column(JSON, nullable=False)

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
    password_hash = db.Column(db.String(255))

    def __init__(self, username=None):
        super().__init__()
        if username:
            self.username = username

    def set_password(self, password):
        if not password:
            raise ValueError("Password cannot be empty")
        try:
            self.password_hash = generate_password_hash(password)
            logger.debug(f"Password hash generated for user: {self.username}")
        except Exception as e:
            logger.error(f"Error generating password hash: {str(e)}")
            raise

    def check_password(self, password):
        if not password or not self.password_hash:
            logger.warning("Password check failed: missing password or hash")
            return False
        try:
            return check_password_hash(self.password_hash, password)
        except Exception as e:
            logger.error(f"Error checking password: {str(e)}")
            return False
