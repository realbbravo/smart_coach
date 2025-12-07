import pandas as pd
import json
import os

# Define paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
# Updated filename to match your upload
INPUT_FILE = os.path.join(DATA_DIR, 'kaggle_exercises.csv') 
OUTPUT_FILE = os.path.join(DATA_DIR, 'exercises.json')

# MAPPING: Group detailed body parts into major muscle groups
# This ensures our "Context Menu" for Gemini covers the full body
BODY_PART_MAPPING = {
    'Abdominals': 'Core',
    'Adductors': 'Legs',
    'Abductors': 'Legs',
    'Biceps': 'Arms',
    'Calves': 'Legs',
    'Chest': 'Chest',
    'Forearms': 'Arms',
    'Glutes': 'Legs',
    'Hamstrings': 'Legs',
    'Lats': 'Back',
    'Lower Back': 'Back',
    'Middle Back': 'Back',
    'Traps': 'Back',
    'Neck': 'Shoulders', # Or 'Other'
    'Quadriceps': 'Legs',
    'Shoulders': 'Shoulders',
    'Triceps': 'Arms',
    'Cardio': 'Cardio' # Just in case
}

def clean_exercises():
    print(f"Loading data from {INPUT_FILE}...")
    
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found. Please ensure the file is in the data/ folder.")
        return

    df = pd.read_csv(INPUT_FILE)

    # 1. Clean Column Names (remove spaces)
    df.columns = [c.strip() for c in df.columns]
    
    # 2. Map Body Parts to broader groups
    # We use .map() and fill unknown values with 'Other'
    df['MajorGroup'] = df['BodyPart'].map(BODY_PART_MAPPING).fillna('Other')
    
    # 3. Convert to Dictionary format grouped by MAJOR GROUP
    exercises_dict = {}
    
    for _, row in df.iterrows():
        # Use the new Major Group (e.g., 'Legs') instead of specific part (e.g., 'Adductors')
        group = row['MajorGroup']
        
        if group not in exercises_dict:
            exercises_dict[group] = []
        
        # We append the specific info so Gemini still knows it's an "Adductor" move
        exercises_dict[group].append({
            "name": row['Title'],
            "specific_target": row['BodyPart'], # Keep original part as metadata
            "equipment": row.get('Equipment', 'Unknown'),
            "level": row.get('Level', 'Intermediate')
        })

    # 4. Save to JSON
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(exercises_dict, f, indent=2)
    
    print(f"Success! Cleaned exercises saved to {OUTPUT_FILE}")
    print(f"Groups created: {list(exercises_dict.keys())}")

if __name__ == "__main__":
    clean_exercises()