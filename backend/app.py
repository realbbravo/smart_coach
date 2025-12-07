import os
import json
import joblib
import pandas as pd
import google.generativeai as genai
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import numpy as np
from lime.lime_tabular import LimeTabularExplainer
import warnings

# Filter FutureWarnings from LIME library (pandas Series deprecation warnings)
warnings.filterwarnings('ignore', category=FutureWarning, module='lime')
warnings.filterwarnings('ignore', category=UserWarning, message='.*does not have valid feature names.*')

load_dotenv()  # Load environment variables from .env file
app = Flask(__name__)
CORS(app)  # Allow frontend to talk to backend

# Define Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
MODEL_PATH = os.path.join(DATA_DIR, 'workout_classifier.pkl')
TRAINING_DATA_PATH = os.path.join(DATA_DIR, 'X_train.pkl')
EXERCISE_PATH = os.path.join(DATA_DIR, 'exercises.json')

# --- DEFINITIONS & MAPPINGS ---
# We define these globally so they are available for LIME and the API
GOAL_MAPPING = {"health": 0, "strength": 1, "hypertrophy": 2}
GENDER_MAPPING = {"male": 0, "female": 1}
ENV_MAPPING = {"gym": 0, "home": 1, "mix": 2}
SPLIT_MAPPING = {0: "Full Body Split", 1: "Upper/Lower Split", 2: "Push/Pull/Legs (PPL)", 3: "Body Part Split"}

# Helpers for LIME (Index -> String Name)
GOAL_NAMES = ['Health', 'Strength', 'Hypertrophy']
GENDER_NAMES = ['Male', 'Female']
ENV_NAMES = ['Gym', 'Home', 'Mix']

# --- LOAD AI ASSETS ---
# Only load once in the reloader process (not in parent process)
print("Loading Classifier...")
clf = joblib.load(MODEL_PATH)

print("Loading LIME Explainer...")
X_train = joblib.load(TRAINING_DATA_PATH)

# Define which columns are categorical (indices)
# 0:days, 1:exp, 2:goal, 3:age, 4:gender, 5:env
CATEGORICAL_FEATURES_IDX = [2, 4, 5] 

# Categorical Names Map for LIME
# This tells LIME that Col 2 (Goal) has values ['Health', 'Strength'...]
categorical_names = {
    2: GOAL_NAMES,
    4: GENDER_NAMES,
    5: ENV_NAMES
}

explainer = LimeTabularExplainer(
    training_data=np.array(X_train),
    feature_names=X_train.columns.tolist(),
    categorical_features=CATEGORICAL_FEATURES_IDX,
    categorical_names=categorical_names,
    class_names=['Full Body', 'Upper/Lower', 'PPL', 'Body Part'],
    mode='classification'
)

with open(EXERCISE_PATH, 'r') as f:
    EXERCISE_DB = json.load(f)

# Load Gemini
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("No API Key found. Please set GEMINI_API_KEY in your .env file.")
else: print("Gemini API Key loaded.")

genai.configure(api_key=api_key)

def calculate_duration(experience_years, goal):
    """
    Determines how long a program should last before changing.
    - Beginners need consistency (longer).
    - Advanced athletes need novelty (shorter).
    """
    if experience_years < 1:
        return "8-12 Weeks (Focus on learning form)"
    elif experience_years < 3:
        return "6-8 Weeks (Progressive Overload)"
    else:
        # Advanced
        if goal == "strength":
            return "4-6 Weeks (Peaking Cycle)"
        else:
            return "4-6 Weeks (Prevent Adaptation)"

def clean_lime_feature(lime_rule, all_columns):
    """
    Parses LIME output strings like '2.00 < days_available <= 5.00' 
    and returns just the readable feature name 'Days Available'.
    """
    # 1. Sort columns by length (descending) to ensure we match 'days_available' 
    # before 'days' (if both existed) to avoid partial matches.
    sorted_cols = sorted(all_columns, key=len, reverse=True)
    
    for col in sorted_cols:
        # Check if the column name exists inside the LIME rule string
        if col in lime_rule:
            return col.replace('_', ' ').title()
            
    return "Complex Factor"

def get_gemini_response(split_name, user_data, explanation_text):
    # Slice context
    sample_exercises = []
    for _, exercises in EXERCISE_DB.items():
        sample_exercises.extend(exercises[:5])
        if len(sample_exercises) > 60: break
    exercise_context = json.dumps(sample_exercises)

    # Format measurements based on system
    height_str = f"{user_data['height']}{user_data['height_unit']}"
    weight_str = f"{user_data['weight']}{user_data['weight_unit']}"

    prompt = f"""
    You are an expert fitness coach. Create a weekly workout plan for a client.
    
    CLIENT PROFILE:
    - Age: {user_data['age']} | Gender: {user_data['gender']}
    - Height: {height_str} | Weight: {weight_str}
    - Experience: {user_data['experience_years']} years
    - Goal: {user_data['goal']} | Days: {user_data['days_available']}
    - Environment: {user_data['environment_str']}
    - Assigned Structure: {split_name}
    
    AI REASONING CONTEXT:
    The classifier chose this split because: {explanation_text}
    
    INSTRUCTIONS:
    1. Start with a 1-sentence "Coach's Insight" explaining WHY this split was chosen (use the AI Reasoning Context).
    2. Write a 7-day schedule based on "{split_name}".
    3. Use ONLY equipment matching "{user_data['environment_str']}".
    4. Format output as clean Markdown.
    5. Menu: {exercise_context}
    """

    try:
        model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")
        response = model.generate_content(prompt)

        if response.text:
            print(f"Response text length: {len(response.text)} chars")
            return response.text
        else:
            error_msg = f"Error: Blocked by Gemini. Reason: {response.candidates[0].finish_reason}"
            print(error_msg)
            return error_msg

    except Exception as e:
        # If the API throws a hard error, return it
        print(f"DEBUG INFO: {str(e)}")
        if "candidate" in str(e).lower():
             return "Error: The model refused to generate content (Safety/Recitation)."
        return f"Error: {str(e)}"

@app.route('/generate', methods=['POST'])
def generate_plan():
    try:
        data = request.json
        
        # Handle measurement system
        measurement_system = data.get('measurement_system', 'metric')
        height = float(data['height'])
        weight = float(data['weight'])
        
        # Convert to metric for ML model (standardized)
        if measurement_system == 'imperial':
            height_cm = height * 2.54  # inches to cm
            weight_kg = weight * 0.453592  # lbs to kg
            data['height_unit'] = 'in'
            data['weight_unit'] = 'lbs'
        else:
            height_cm = height
            weight_kg = weight
            data['height_unit'] = 'cm'
            data['weight_unit'] = 'kg'
        
        # Store original values for display
        data['height'] = height
        data['weight'] = weight
        
        goal_enum = GOAL_MAPPING.get(data['goal'].lower(), 0)
        gender_enum = GENDER_MAPPING.get(data['gender'].lower(), 0)
        env_enum = ENV_MAPPING.get(data['environment'].lower(), 0)
        
        input_df = pd.DataFrame([{
            'days_available': int(data['days_available']),
            'experience_years': int(data['experience_years']),
            'goal': goal_enum,
            'age': int(data['age']),
            'gender': gender_enum,
            'environment': env_enum
        }])
        
        # 1. PREDICT
        prediction_prob = clf.predict_proba(input_df)[0]
        prediction_idx = np.argmax(prediction_prob)
        predicted_split = SPLIT_MAPPING.get(prediction_idx, "General Fitness")
        confidence = float(prediction_prob[prediction_idx])
        
        # 2. EXPLAIN (LIME)
        # Pass .values to match training data format (numpy array)
        exp = explainer.explain_instance(
            data_row=input_df.iloc[0].values, 
            predict_fn=clf.predict_proba,
            num_features=2,
            labels=[prediction_idx] 
        )
        
        lime_list = exp.as_list(label=prediction_idx)
        
        # 3. CLEAN OUTPUT (Fixing the "46.00" issue)
        explanation_reasons = []
        
        # We need the column names for cleaning. 
        # Since X_train is loaded inside the 'if main', we grab it from the global scope or reload if needed.
        # Ideally, passed from the explainer object itself.
        train_cols = explainer.feature_names
        
        for rule, weight in lime_list:
            # THIS IS THE FIX: Use the cleaning function instead of .split()
            clean_name = clean_lime_feature(rule, train_cols)
            explanation_reasons.append(clean_name)
            
        explanation_str = ", ".join(explanation_reasons)

        # 4. GENERATE
        data['environment_str'] = data['environment']
        duration = calculate_duration(int(data['experience_years']), data['goal'])
        workout_plan = get_gemini_response(predicted_split, data, explanation_str)
        
        return jsonify({
            "split": predicted_split, 
            "plan": workout_plan,
            "duration": duration,
            "confidence": round(confidence * 100, 1),
            "reasoning": explanation_reasons
        })

    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
