# Nutrisee Recipe Recommendation API

A Flask-based REST API for personalized recipe recommendations using TF-IDF ingredient similarity and nutrition matching.

## Features

- 🍽️ **23,904+ recipes** with halal-compliant filtering
- 📊 **Nutrition-based search** (calories, protein, carbs, etc.)
- 🔍 **Smart recommendations** using weighted TF-IDF similarity
- 🎯 **Meal-type filtering** (breakfast, lunch, dinner, snacks, desserts, etc.)
- ⚡ **Fast API** with optimized similarity indexing

## Installation

### Local Development

1. **Clone the repository:**
```bash
git clone <your-github-repo>
cd Nutrisee_Reco_Model
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Run the app:**
```bash
python app.py
```

The API will be available at `http://localhost:5000`

## API Endpoints

### 1. Home & Documentation
```
GET /
```
Returns API documentation and available endpoints.

### 2. System Statistics
```
GET /stats
```
Returns system info, total recipes, available meal types.

### 3. Get Recipe Details
```
GET /recipe/<recipe_id>
```
**Example:** `GET /recipe/0`

Returns:
- Recipe name, URL, source
- Full ingredients with weights
- Complete nutrition breakdown
- Total weight

### 4. Get Similar Recipes
```
GET /recommend/<recipe_id>?top_k=5&min_similarity=0.1
```
**Example:** `GET /recommend/42?top_k=5`

Returns:
- Top N similar recipes based on ingredients
- Similarity scores
- Key ingredients of each recommendation

### 5. Search by Nutrition & Meal Type
```
POST /search
```

**Request body:**
```json
{
  "meal_type": "lunch/dinner",
  "target_calories": 500,
  "target_protein": 30,
  "top_k": 10
}
```

**Response:**
- Ranked recipes matching your criteria
- Nutrition match scores
- Similar recipes for each result

**Available meal types:**
- breakfast
- lunch/dinner
- snack
- desserts
- soup
- brunch
- appetizers
- main course
- bread
- condiments and sauces
- preps
- teatime

## Deployment on Render

### Step 1: Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/Nutrisee_Reco_Model.git
git push -u origin main
```

**Ensure you push these files:**
- ✅ `app.py`
- ✅ `requirements.txt`
- ✅ `final_recipes_cleaned.csv`
- ✅ `recipe_identifiers.csv`
- ✅ `recommendation_metadata.pkl`
- ✅ `recipe_similarity_index.pkl`
- ✅ `tfidf_vectorizer.pkl`
- ✅ `README.md`
- ✅ `.gitignore`

### Step 2: Deploy on Render

1. Go to [render.com](https://render.com)
2. Sign in with GitHub
3. Click **New +** → **Web Service**
4. Select your GitHub repository
5. Configure:
   - **Name:** `nutrisee-reco-api`
   - **Environment:** Python
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python app.py`
   - **Instance Type:** Free (or Starter)
6. Click **Create Web Service**

### Step 3: Access Your API

Render will give you a URL like:
```
https://nutrisee-reco-api.onrender.com
```

Test it:
```bash
curl https://nutrisee-reco-api.onrender.com/
curl https://nutrisee-reco-api.onrender.com/stats
```

## File Size Considerations

**⚠️ Important:** Render has a 500 MB limit for free tier deployments.

Your files:
- `final_recipes_cleaned.csv` - ~XX MB
- `recommendation_metadata.pkl` - ~7 MB
- `recipe_similarity_index.pkl` - ~50 MB
- Total: ~XX MB ✅ (Should fit on Render free tier)

If files are too large, consider:
1. Compress the CSV (gzip)
2. Use cloud storage (AWS S3) and load data from there
3. Use Render's paid tier (500 GB storage)

## Project Structure

```
Nutrisee_Reco_Model/
├── app.py                           # Flask application
├── requirements.txt                 # Python dependencies
├── README.md                        # This file
├── .gitignore                       # Git ignore rules
├── final_recipes_cleaned.csv        # Clean recipe features
├── recipe_identifiers.csv           # Recipe metadata
├── recommendation_metadata.pkl      # Recommendation system data
├── recipe_similarity_index.pkl      # Pre-computed similarity scores
└── reco_model.ipynb                 # Data processing notebook
```

## Example Usage

### Python Client

```python
import requests

BASE_URL = "https://nutrisee-reco-api.onrender.com"

# Search for lunch recipes with 500 calories, 30g protein
response = requests.post(
    f"{BASE_URL}/search",
    json={
        "meal_type": "lunch/dinner",
        "target_calories": 500,
        "target_protein": 30,
        "top_k": 10
    }
)

results = response.json()
for recipe in results['results']:
    print(f"{recipe['recipe_name']} - Match: {recipe['nutrition']['match_score']:.3f}")
```

### JavaScript/cURL

```bash
curl -X POST https://nutrisee-reco-api.onrender.com/search \
  -H "Content-Type: application/json" \
  -d '{
    "meal_type": "breakfast",
    "target_calories": 400,
    "target_protein": 20,
    "top_k": 5
  }'
```

## Data Processing

The recommendation system was built from:
1. **Source:** `recipes-with-nutrition.csv` (raw data)
2. **Processing Pipeline:**
   - Dropped junk columns & duplicates
   - Halal-compliant filtering (removed alcohol, pork, non-halal fats)
   - Per-serving nutrition extraction (8 key nutrients)
   - Categorical data cleaning & encoding
   - Simplified ingredient mapping (4,700+ → ~700 categories)
   - TF-IDF vectorization with cosine similarity
   - Compact similarity indexing (98% file size reduction)

See `reco_model.ipynb` for detailed processing steps.

## Performance

- **Recipe Database:** 23,904 halal-compliant recipes
- **Search Time:** ~100ms per query
- **Recommendation Time:** ~10ms per recipe
- **API Response:** <500ms end-to-end
- **Model Size:** ~50 MB (optimized)

## License

MIT License - Feel free to use and modify

## Support

For issues or questions:
1. Check `/stats` endpoint for system status
2. Verify recipe IDs are in valid range (0-23,903)
3. Check `/` endpoint for API documentation
