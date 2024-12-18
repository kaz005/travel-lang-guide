import json
from typing import List, Dict, Any, Optional
from pathlib import Path

class TouristSpot:
    @staticmethod
    def load_spots() -> List[Dict[str, Any]]:
        """JSONファイルから観光スポット情報を読み込む"""
        try:
            with open('static/data/spots.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading spots: {e}")
            return []

    @staticmethod
    def create(data: Dict[str, Any]) -> bool:
        """新しい観光スポットを作成"""
        try:
            spots = TouristSpot.load_spots()
            # 新しいIDを生成
            new_id = max([spot.get('id', 0) for spot in spots], default=0) + 1
            data['id'] = new_id
            spots.append(data)
            
            with open('static/data/spots.json', 'w', encoding='utf-8') as f:
                json.dump(spots, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error creating spot: {e}")
            return False

    @staticmethod
    def update(spot_id: int, data: Dict[str, Any]) -> bool:
        """観光スポット情報を更新"""
        try:
            spots = TouristSpot.load_spots()
            for i, spot in enumerate(spots):
                if spot.get('id') == spot_id:
                    spots[i] = data
                    with open('static/data/spots.json', 'w', encoding='utf-8') as f:
                        json.dump(spots, f, ensure_ascii=False, indent=2)
                    return True
            return False
        except Exception as e:
            print(f"Error updating spot: {e}")
            return False

    @staticmethod
    def delete(spot_id: int) -> bool:
        """観光スポットを削除"""
        try:
            spots = TouristSpot.load_spots()
            original_length = len(spots)
            spots = [spot for spot in spots if spot.get('id') != spot_id]
            
            if len(spots) < original_length:
                with open('static/data/spots.json', 'w', encoding='utf-8') as f:
                    json.dump(spots, f, ensure_ascii=False, indent=2)
                return True
            return False
        except Exception as e:
            print(f"Error deleting spot: {e}")
            return False
