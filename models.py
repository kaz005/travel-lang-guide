import json
from typing import List, Dict, Any
import os

class TouristSpot:
    def __init__(self, id: int, name: Dict, description: Dict, coordinates: Dict, images: List):
        self.id = id
        self.name = name
        self.description = description
        self.coordinates = coordinates
        self.images = images

    @staticmethod
    def load_spots() -> List['TouristSpot']:
        try:
            with open('static/data/spots.json', 'r', encoding='utf-8') as f:
                spots_data = json.load(f)
                return [
                    TouristSpot(
                        id=spot.get('id', i),
                        name=spot['name'],
                        description=spot['description'],
                        coordinates=spot['coordinates'],
                        images=spot['images']
                    )
                    for i, spot in enumerate(spots_data, 1)
                ]
        except FileNotFoundError:
            return []

    @staticmethod
    def save_spots(spots: List['TouristSpot']):
        spots_data = [
            {
                'id': spot.id,
                'name': spot.name,
                'description': spot.description,
                'coordinates': spot.coordinates,
                'images': spot.images
            }
            for spot in spots
        ]
        with open('static/data/spots.json', 'w', encoding='utf-8') as f:
            json.dump(spots_data, f, ensure_ascii=False, indent=2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'coordinates': self.coordinates,
            'images': self.images
        }

    @staticmethod
    def create(data: Dict) -> 'TouristSpot':
        spots = TouristSpot.load_spots()
        new_id = max([spot.id for spot in spots], default=0) + 1
        new_spot = TouristSpot(
            id=new_id,
            name=data['name'],
            description=data['description'],
            coordinates=data['coordinates'],
            images=data['images']
        )
        spots.append(new_spot)
        TouristSpot.save_spots(spots)
        return new_spot

    @staticmethod
    def update(spot_id: int, data: Dict) -> 'TouristSpot':
        spots = TouristSpot.load_spots()
        for spot in spots:
            if spot.id == spot_id:
                spot.name = data['name']
                spot.description = data['description']
                spot.coordinates = data['coordinates']
                spot.images = data['images']
                TouristSpot.save_spots(spots)
                return spot
        raise ValueError(f"Spot with id {spot_id} not found")

    @staticmethod
    def delete(spot_id: int) -> bool:
        spots = TouristSpot.load_spots()
        original_length = len(spots)
        spots = [spot for spot in spots if spot.id != spot_id]
        if len(spots) < original_length:
            TouristSpot.save_spots(spots)
            return True
        return False
