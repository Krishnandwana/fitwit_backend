import requests
from typing import Optional, Dict
from app.config import settings


def search_food_by_barcode(barcode: str) -> Optional[Dict]:
    """
    Search for food item by barcode using OpenFoodFacts API.

    Args:
        barcode: Product barcode

    Returns:
        Dictionary with food information or None if not found
    """
    try:
        url = f"https://world.openfoodfacts.org/api/v2/product/{barcode}.json"
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            return None

        data = response.json()

        if data.get("status") != 1:
            return None

        product = data.get("product", {})

        # Extract nutritional information per 100g
        nutriments = product.get("nutriments", {})

        return {
            "name": product.get("product_name", "Unknown Product"),
            "barcode": barcode,
            "calories_per_100g": nutriments.get("energy-kcal_100g", 0),
            "protein": nutriments.get("proteins_100g", 0),
            "carbs": nutriments.get("carbohydrates_100g", 0),
            "fat": nutriments.get("fat_100g", 0),
        }

    except Exception as e:
        print(f"Error fetching barcode {barcode}: {str(e)}")
        return None


def search_food_by_name(query: str, limit: int = 10) -> list:
    """
    Search for food items by name using OpenFoodFacts API.

    Args:
        query: Search query
        limit: Maximum number of results

    Returns:
        List of food items
    """
    try:
        url = f"https://world.openfoodfacts.org/cgi/search.pl"
        params = {
            "search_terms": query,
            "page_size": limit,
            "json": 1,
            "action": "process"
        }

        response = requests.get(url, params=params, timeout=10)

        if response.status_code != 200:
            return []

        data = response.json()
        products = data.get("products", [])

        results = []
        for product in products:
            nutriments = product.get("nutriments", {})

            results.append({
                "name": product.get("product_name", "Unknown Product"),
                "barcode": product.get("code"),
                "calories_per_100g": nutriments.get("energy-kcal_100g", 0),
                "protein": nutriments.get("proteins_100g", 0),
                "carbs": nutriments.get("carbohydrates_100g", 0),
                "fat": nutriments.get("fat_100g", 0),
            })

        return results

    except Exception as e:
        print(f"Error searching for {query}: {str(e)}")
        return []
