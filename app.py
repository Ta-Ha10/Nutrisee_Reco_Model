import flask
from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
import pickle
import json
import os

app = Flask(__name__)

# Global variables to store loaded data
df_clean = None
df_ids = None
metadata = None
similarity_index = None

def load_data():
    """Load all recommendation system data"""
    global df_clean, df_ids, metadata, similarity_index
    
    print('[LOADING] Initializing recommendation system...')
    
    try:
        # Load cleaned data
        df_clean = pd.read_csv('final_recipes_cleaned.csv')
        df_ids = pd.read_csv('recipe_identifiers.csv')
        
        # Load recommendation models
        with open('recommendation_metadata.pkl', 'rb') as f:
            metadata = pickle.load(f)
        
        with open('recipe_similarity_index.pkl', 'rb') as f:
            similarity_index = pickle.load(f)
        
        print('[OK] Data loaded successfully!')
        print(f'[OK] Total recipes: {len(df_clean):,}')
        
    except Exception as e:
        print(f'[ERROR] Failed to load data: {e}')
        raise

# Load data on app startup
@app.before_request
def initialize():
    """Initialize data on first request"""
    global df_clean
    if df_clean is None:
        load_data()

@app.route('/', methods=['GET'])
def home():
    """Home endpoint"""
    return jsonify({
        'message': 'Nutrisee Recipe Recommendation API',
        'version': '1.0',
        'endpoints': {
            'GET /': 'This help message',
            'POST /search': 'Search recipes by nutrition and meal type',
            'GET /recipe/<recipe_id>': 'Get recipe details',
            'GET /recommend/<recipe_id>': 'Get similar recipe recommendations',
            'GET /stats': 'Get system statistics'
        }
    }), 200

@app.route('/stats', methods=['GET'])
def stats():
    """Get system statistics"""
    try:
        return jsonify({
            'total_recipes': len(metadata['recipe_names']),
            'nutrition_features': 8,
            'categorical_features': 121,
            'available_meal_types': list(set([col.replace('meal_type_', '') 
                                              for col in df_clean.columns 
                                              if col.startswith('meal_type_')])),
            'status': 'operational'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/recipe/<int:recipe_id>', methods=['GET'])
def get_recipe(recipe_id):
    """Get detailed recipe information"""
    try:
        if recipe_id < 0 or recipe_id >= len(metadata['recipe_names']):
            return jsonify({'error': f'Recipe ID {recipe_id} not found'}), 404
        
        # Build full dataframe if needed
        df_full = df_ids.copy()
        df_full['total_weight_g'] = df_clean['total_weight_g'].values
        df_full['calories_per_serving'] = df_clean['calories_per_serving'].values
        df_full['protein_g_per_serving'] = df_clean['protein_g_per_serving'].values
        
        for col in df_clean.columns:
            if col not in df_full.columns and col not in ['total_weight_g']:
                df_full[col] = df_clean[col].values
        
        recipe_row = df_full.iloc[recipe_id]
        
        # Get ingredients
        ingredients = metadata['normalized_ingredients'][recipe_id]
        sorted_ings = sorted(ingredients, key=lambda x: x[1], reverse=True)
        
        # Format ingredients
        formatted_ingredients = []
        for ing_name, weight_ratio in sorted_ings:
            weight_g = weight_ratio * metadata['total_weights'][recipe_id]
            formatted_ingredients.append({
                'name': ing_name,
                'weight_ratio': round(weight_ratio, 4),
                'weight_g': round(weight_g, 2)
            })
        
        # Get nutrition columns
        nutrition_data = {}
        nutrition_cols = [col for col in df_clean.columns if col.endswith('_per_serving')]
        for col in nutrition_cols:
            nutrition_data[col.replace('_per_serving', '')] = round(float(recipe_row[col]), 2)
        
        return jsonify({
            'recipe_id': recipe_id,
            'recipe_name': metadata['recipe_names'][recipe_id],
            'source': metadata['sources'][recipe_id],
            'url': metadata['urls'][recipe_id],
            'total_weight_g': round(metadata['total_weights'][recipe_id], 1),
            'nutrition': nutrition_data,
            'ingredients': formatted_ingredients,
            'num_ingredients': len(formatted_ingredients)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/recommend/<int:recipe_id>', methods=['GET'])
def get_recommendations(recipe_id):
    """Get similar recipe recommendations"""
    try:
        top_k = request.args.get('top_k', 5, type=int)
        min_similarity = request.args.get('min_similarity', 0.1, type=float)
        
        if recipe_id < 0 or recipe_id >= len(metadata['recipe_names']):
            return jsonify({'error': f'Recipe ID {recipe_id} not found'}), 404
        
        # Get similar recipes from index
        similar_recipes = similarity_index.get(recipe_id, [])
        filtered = [(idx, score) for idx, score in similar_recipes if score >= min_similarity]
        top_recipes = filtered[:top_k]
        
        recommendations = []
        for recipe_idx, sim_score in top_recipes:
            # Get top ingredients
            ings = metadata['normalized_ingredients'][recipe_idx]
            top_ings = sorted(ings, key=lambda x: x[1], reverse=True)[:3]
            
            recommendations.append({
                'recipe_id': recipe_idx,
                'recipe_name': metadata['recipe_names'][recipe_idx],
                'similarity_score': round(float(sim_score), 4),
                'calories': round(metadata['calories'][recipe_idx], 1),
                'total_weight_g': round(metadata['total_weights'][recipe_idx], 1),
                'top_ingredients': [name for name, _ in top_ings]
            })
        
        return jsonify({
            'query_recipe_id': recipe_id,
            'query_recipe_name': metadata['recipe_names'][recipe_id],
            'recommendations': recommendations,
            'count': len(recommendations)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/search', methods=['POST'])
def search_recipes():
    """
    Search recipes by meal type and nutrition targets.
    
    Request JSON:
    {
        "meal_type": "lunch/dinner",  # or breakfast, snack, desserts, etc.
        "target_calories": 500,
        "target_protein": 30,
        "top_k": 10
    }
    """
    try:
        data = request.get_json()
        
        meal_type = data.get('meal_type', 'lunch/dinner')
        target_calories = float(data.get('target_calories', 500))
        target_protein = float(data.get('target_protein', 30))
        top_k = int(data.get('top_k', 10))
        
        # Build full dataframe
        df_full = df_ids.copy()
        df_full['total_weight_g'] = df_clean['total_weight_g'].values
        df_full['calories_per_serving'] = df_clean['calories_per_serving'].values
        df_full['protein_g_per_serving'] = df_clean['protein_g_per_serving'].values
        
        for col in df_clean.columns:
            if col not in df_full.columns and col not in ['total_weight_g']:
                df_full[col] = df_clean[col].values
        
        # Filter by meal type
        meal_type_col = f'meal_type_{meal_type.lower()}'
        
        if meal_type_col in df_full.columns:
            filtered_df = df_full[df_full[meal_type_col] == 1].copy()
        else:
            # If meal type not found, use all recipes
            filtered_df = df_full.copy()
        
        if len(filtered_df) == 0:
            return jsonify({'error': f'No recipes found for meal type: {meal_type}'}), 404
        
        # Score recipes by nutrition proximity
        calorie_diff = np.abs(filtered_df['calories_per_serving'] - target_calories)
        protein_diff = np.abs(filtered_df['protein_g_per_serving'] - target_protein)
        
        calorie_score = np.exp(-calorie_diff / (target_calories * 0.3))
        protein_score = np.exp(-protein_diff / (target_protein * 0.3))
        
        nutrition_score = (calorie_score + protein_score) / 2
        filtered_df['nutrition_match_score'] = nutrition_score
        
        # Get top results
        top_candidates = filtered_df.nlargest(top_k, 'nutrition_match_score')
        
        results = []
        for idx, (_, row) in enumerate(top_candidates.iterrows()):
            recipe_id = row.name
            
            # Get similar recipes
            similar_recipes = similarity_index.get(recipe_id, [])[:3]
            
            similar_recs = []
            for sim_id, sim_score in similar_recipes:
                similar_recs.append({
                    'recipe_id': sim_id,
                    'recipe_name': metadata['recipe_names'][sim_id],
                    'similarity_score': round(float(sim_score), 4),
                    'calories': round(metadata['calories'][sim_id], 1)
                })
            
            result = {
                'rank': idx + 1,
                'recipe_id': recipe_id,
                'recipe_name': row['recipe_name'],
                'url': row['url'],
                'source': row['source'],
                'nutrition': {
                    'calories_per_serving': round(row['calories_per_serving'], 1),
                    'protein_g_per_serving': round(row['protein_g_per_serving'], 1),
                    'match_score': round(row['nutrition_match_score'], 4)
                },
                'total_weight_g': round(row['total_weight_g'], 1),
                'similar_recipes': similar_recs
            }
            
            results.append(result)
        
        return jsonify({
            'search_criteria': {
                'meal_type': meal_type,
                'target_calories': target_calories,
                'target_protein': target_protein
            },
            'results': results,
            'count': len(results)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
