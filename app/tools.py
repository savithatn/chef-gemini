import json
from typing import Optional
from google.adk.tools import ToolContext
from google.cloud import firestore




# Hardcode project ID as a string for Firestore client as required to ensure
# compatibility across local and Agent Platform runtimes.
FIRESTORE_PROJECT = "qwiklabs-gcp-02-851ad8720399"

_db_client = None


def get_db() -> firestore.Client:
    """Lazy initializer for Firestore client."""
    global _db_client
    if _db_client is None:
        _db_client = firestore.Client(project=FIRESTORE_PROJECT)
    return _db_client


def search_recipes(query: str = "", cuisine: str = "") -> str:
    """Search for recipes in the Firestore database by title, ingredient keyword, or cuisine.

    Args:
        query: Optional search keyword to match against recipe titles or ingredients.
        cuisine: Optional cuisine type (e.g. Italian, Mediterranean, American) to filter recipes.

    Returns:
        A JSON string containing matching recipes with ingredients, instructions, and metadata.
    """
    db = get_db()
    docs = db.collection("recipes").stream()
    results = []

    q_lower = query.lower().strip()
    c_lower = cuisine.lower().strip()

    for doc in docs:
        data = doc.to_dict()
        title = data.get("title", "").lower()
        r_cuisine = data.get("cuisine", "").lower()
        ingredients = [str(ing).lower() for ing in data.get("ingredients", [])]

        matches_cuisine = not c_lower or (c_lower in r_cuisine)
        matches_query = not q_lower or (
            q_lower in title or any(q_lower in ing for ing in ingredients)
        )

        if matches_cuisine and matches_query:
            results.append(data)

    if not results:
        return f"No recipes found matching query='{query}' and cuisine='{cuisine}'."
    return json.dumps(results, indent=2)


def add_recipe(
    title: str,
    cuisine: str,
    prep_time_minutes: int,
    cook_time_minutes: int,
    ingredients: list[str],
    instructions: list[str],
    dietary_flags: Optional[list[str]] = None,
    calories: int = 0,
) -> str:
    """Add a new recipe to the Firestore database.

    Args:
        title: The title/name of the recipe.
        cuisine: Cuisine style (e.g., Italian, Mexican, Asian).
        prep_time_minutes: Preparation time in minutes.
        cook_time_minutes: Cooking time in minutes.
        ingredients: List of ingredient strings (e.g., ["2 eggs", "1 cup flour"]).
        instructions: Step-by-step cooking instruction strings.
        dietary_flags: Optional list of dietary flags (e.g. ["vegetarian", "gluten-free"]).
        calories: Estimated calorie count per serving.

    Returns:
        Confirmation string indicating successful addition to Firestore.
    """
    db = get_db()
    doc_id = title.lower().replace(" ", "-").replace("/", "-")
    recipe_data = {
        "id": doc_id,
        "title": title,
        "cuisine": cuisine,
        "prep_time_minutes": prep_time_minutes,
        "cook_time_minutes": cook_time_minutes,
        "ingredients": ingredients,
        "instructions": instructions,
        "dietary_flags": dietary_flags or [],
        "calories": calories,
    }

    db.collection("recipes").document(doc_id).set(recipe_data)
    return f"Successfully added recipe '{title}' to Firestore with ID '{doc_id}'."


def get_pantry_items() -> str:
    """Fetch all current pantry items and their quantities from the Firestore database.

    Returns:
        A JSON string listing pantry ingredients, quantities, and units.
    """
    db = get_db()
    docs = db.collection("pantry_items").stream()
    items = [doc.to_dict() for doc in docs]
    if not items:
        return "Your pantry is currently empty."
    return json.dumps(items, indent=2)


def update_pantry_item(item_name: str, quantity: float, unit: str, category: str = "General") -> str:
    """Add or update an ingredient item quantity in the pantry collection in Firestore.

    Args:
        item_name: Name of the pantry item (e.g. Eggs, Olive Oil, Flour).
        quantity: Current available quantity.
        unit: Measurement unit (e.g. pieces, grams, ml).
        category: Category of the item (e.g. Dairy, Grains, Produce).

    Returns:
        Confirmation string indicating successful pantry update in Firestore.
    """
    db = get_db()
    doc_id = item_name.lower().replace(" ", "_")
    pantry_data = {
        "id": doc_id,
        "item_name": item_name,
        "quantity": float(quantity),
        "unit": unit,
        "category": category,
    }
    db.collection("pantry_items").document(doc_id).set(pantry_data)
    return f"Successfully updated pantry item '{item_name}' (Quantity: {quantity} {unit}) in Firestore."


def check_missing_ingredients(recipe_title: str) -> str:
    """Compare ingredients required for a recipe against available pantry inventory in Firestore.

    Args:
        recipe_title: Name of the recipe to check (e.g. Spaghetti Carbonara).

    Returns:
        A JSON string listing available vs missing ingredients for the recipe.
    """
    db = get_db()
    docs = db.collection("recipes").stream()
    target_recipe = None
    title_lower = recipe_title.lower().strip()

    for doc in docs:
        data = doc.to_dict()
        if title_lower in data.get("title", "").lower():
            target_recipe = data
            break

    if not target_recipe:
        return f"Recipe '{recipe_title}' was not found in the database."

    pantry_docs = db.collection("pantry_items").stream()
    pantry_names = [doc.to_dict().get("item_name", "").lower() for doc in pantry_docs]

    req_ingredients = target_recipe.get("ingredients", [])
    available = []
    missing = []

    for ing in req_ingredients:
        ing_lower = ing.lower()
        if any(p_name in ing_lower or ing_lower in p_name for p_name in pantry_names if p_name):
            available.append(ing)
        else:
            missing.append(ing)

    result = {
        "recipe": target_recipe.get("title"),
        "available_ingredients": available,
        "missing_ingredients": missing,
        "status": "All ingredients in stock!" if not missing else f"Missing {len(missing)} item(s).",
    }
    return json.dumps(result, indent=2)


def fetch_online_recipe(query: str = "") -> str:
    """Fetch external recipe ideas, ingredients, and instructions from TheMealDB public API.

    Args:
        query: Optional meal name or main ingredient (e.g., 'Chicken', 'Arrabiata', 'Tacos'). If blank, returns a random recipe.

    Returns:
        A JSON string containing recipe details (title, category, cuisine area, ingredients, instructions, thumbnail image URL).
    """
    import os
    import urllib.parse
    import urllib.request

    api_key = os.getenv("THEMEALDB_API_KEY", "1")
    if query.strip():
        url = f"https://www.themealdb.com/api/json/v1/{api_key}/search.php?s={urllib.parse.quote(query.strip())}"
    else:
        url = f"https://www.themealdb.com/api/json/v1/{api_key}/random.php"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ChefGeminiAgent/1.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))

        meals = data.get("meals")
        if not meals:
            return f"No online recipes found matching query '{query}'."

        results = []
        for meal in meals[:3]:
            ingredients = []
            for i in range(1, 21):
                ing = meal.get(f"strIngredient{i}")
                meas = meal.get(f"strMeasure{i}")
                if ing and ing.strip():
                    ingredients.append(f"{meas.strip() if meas else ''} {ing.strip()}".strip())

            results.append({
                "meal_name": meal.get("strMeal"),
                "category": meal.get("strCategory"),
                "area": meal.get("strArea"),
                "instructions": meal.get("strInstructions"),
                "ingredients": ingredients,
                "image_url": meal.get("strMealThumb"),
                "youtube_url": meal.get("strYoutube"),
            })

        return json.dumps(results, indent=2)
    except Exception as e:
        return f"Error querying online recipe API: {str(e)}"


def geocode_address(address: str) -> str:
    """Convert an address, landmark, or location string into geographical coordinates (latitude/longitude).

    Args:
        address: The street address, city, or landmark string (e.g., '1600 Amphitheatre Pkwy, Mountain View, CA').

    Returns:
        A JSON string containing the formatted address, location coordinates (lat/lng), and place ID.
    """
    import os
    import urllib.parse
    import urllib.request

    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return "Error: GOOGLE_MAPS_API_KEY environment variable is not configured."

    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={urllib.parse.quote(address)}&key={api_key}"

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))

        if data.get("status") != "OK" or not data.get("results"):
            return f"Geocoding failed for address '{address}'. Status: {data.get('status')}"

        first = data["results"][0]
        location = first["geometry"]["location"]
        result = {
            "formatted_address": first.get("formatted_address"),
            "location": {
                "latitude": location.get("lat"),
                "longitude": location.get("lng"),
            },
            "place_id": first.get("place_id"),
        }
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error executing Geocoding request: {str(e)}"


def find_nearby_places(
    latitude: float,
    longitude: float,
    place_type: str = "grocery_store",
    radius_meters: float = 5000.0,
) -> str:
    """Find nearby places (e.g., grocery stores, supermarkets, restaurants) around a location using Places API (New).

    Args:
        latitude: Latitude coordinate of center point.
        longitude: Longitude coordinate of center point.
        place_type: Primary place type to filter (e.g. 'grocery_store', 'supermarket', 'restaurant', 'bakery').
        radius_meters: Search radius in meters (default: 5000.0).

    Returns:
        A JSON string listing nearby places with name, formatted address, and location coordinates.
    """
    import os
    import urllib.request

    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return "Error: GOOGLE_MAPS_API_KEY environment variable is not configured."

    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location,places.types",
    }

    body = json.dumps({
        "includedTypes": [place_type],
        "maxResultCount": 5,
        "locationRestriction": {
            "circle": {
                "center": {"latitude": latitude, "longitude": longitude},
                "radius": float(radius_meters),
            }
        },
    }).encode("utf-8")

    try:
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))

        raw_places = data.get("places", [])
        if not raw_places:
            return f"No nearby places of type '{place_type}' found within {radius_meters}m."

        results = []
        for p in raw_places:
            display_name = p.get("displayName", {}).get("text", "Unknown")
            results.append({
                "name": display_name,
                "address": p.get("formattedAddress"),
                "location": p.get("location"),
                "types": p.get("types", []),
            })

        return json.dumps(results, indent=2)
    except Exception as e:
        return f"Error executing Places API request: {str(e)}"


# Hardcode Cloud Storage bucket name for media assets as required
IMAGE_BUCKET = "chef-gemini-media-851ad872"


def generate_dish_image(item_name: str, tool_context: ToolContext) -> str:
    """Generate an image for a dish, recipe, or food item using gemini-3.1-flash-lite-image model in global region.

    Saves the image as an artifact via tool_context.save_artifact for Playground display,
    and uploads the image bytes directly to public Cloud Storage, returning its public HTTPS URL.

    Args:
        item_name: Name or description of the dish or recipe (e.g., 'Spaghetti Carbonara', 'Avocado Toast').
        tool_context: ADK ToolContext injected automatically by the agent framework.

    Returns:
        A string containing the public HTTPS URL of the generated image in Cloud Storage.
    """
    import uuid
    from google import genai
    from google.cloud import storage
    from google.genai import types

    prompt = f"A professional, appetizing studio food photograph of {item_name}, beautifully plated and ready to serve."

    client = genai.Client(vertexai=True, project=FIRESTORE_PROJECT, location="global")
    res = client.models.generate_content(
        model="gemini-3.1-flash-lite-image",
        contents=prompt,
    )

    image_bytes = None
    mime_type = "image/jpeg"
    if res.candidates and res.candidates[0].content and res.candidates[0].content.parts:
        for p in res.candidates[0].content.parts:
            if p.inline_data:
                image_bytes = p.inline_data.data
                mime_type = p.inline_data.mime_type or "image/jpeg"
                break

    if not image_bytes:
        return f"Failed to generate image for '{item_name}'."

    ext = "jpg" if "jpeg" in mime_type or "jpg" in mime_type else "png"
    safe_name = "".join(c if c.isalnum() else "_" for c in item_name.lower())
    filename = f"{safe_name}_{uuid.uuid4().hex[:6]}.{ext}"

    # 1. Save with tool_context.save_artifact for Playground Artifacts panel
    artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    tool_context.save_artifact(filename=filename, artifact=artifact_part)

    # 2. Upload same image bytes directly to public Cloud Storage bucket (without writing local file)
    storage_client = storage.Client(project=FIRESTORE_PROJECT)
    bucket = storage_client.bucket(IMAGE_BUCKET)
    blob = bucket.blob(filename)
    blob.upload_from_string(image_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{IMAGE_BUCKET}/{filename}"
    return f"Successfully generated image for '{item_name}'. Public URL: {public_url}"


def generate_dish_video(item_name: str, tool_context: ToolContext) -> str:
    """Generate a short video for a dish, recipe, or food item using gemini-omni-flash-preview model in global region.

    Saves the video as an artifact via tool_context.save_artifact for Playground display,
    and uploads the video bytes directly to public Cloud Storage, returning its public HTTPS URL.

    Args:
        item_name: Name or description of the dish or recipe (e.g., 'Spaghetti Carbonara', 'Sizzling Steak').
        tool_context: ADK ToolContext injected automatically by the agent framework.

    Returns:
        A string containing the public HTTPS URL of the generated video in Cloud Storage.
    """
    import uuid
    from google import genai
    from google.cloud import storage
    from google.genai import types

    prompt = f"A short video showing {item_name}, beautifully prepared, cooked, and plated."

    client = genai.Client(vertexai=True, project=FIRESTORE_PROJECT, location="global")
    res = client.interactions.create(
        model="gemini-omni-flash-preview",
        input=prompt,
    )

    video_bytes = None
    mime_type = "video/mp4"

    if hasattr(res, "output_video") and res.output_video:
        if isinstance(res.output_video, dict):
            video_bytes = res.output_video.get("data")
            mime_type = res.output_video.get("mime_type", "video/mp4") or "video/mp4"
        else:
            video_bytes = getattr(res.output_video, "data", None)
            mime_type = getattr(res.output_video, "mime_type", "video/mp4") or "video/mp4"

    if not video_bytes:
        return f"Failed to generate video for '{item_name}'."

    ext = "mp4"
    safe_name = "".join(c if c.isalnum() else "_" for c in item_name.lower())
    filename = f"{safe_name}_{uuid.uuid4().hex[:6]}.{ext}"

    # 1. Save with tool_context.save_artifact for Playground Artifacts panel
    artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
    tool_context.save_artifact(filename=filename, artifact=artifact_part)

    # 2. Upload same video bytes directly to public Cloud Storage bucket (without writing local file)
    storage_client = storage.Client(project=FIRESTORE_PROJECT)
    bucket = storage_client.bucket(IMAGE_BUCKET)
    blob = bucket.blob(filename)
    blob.upload_from_string(video_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{IMAGE_BUCKET}/{filename}"
    return f"Successfully generated video for '{item_name}'. Public URL: {public_url}"





