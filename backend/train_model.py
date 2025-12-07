import pandas as pd
import numpy as np
import os
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
MODEL_FILE = os.path.join(DATA_DIR, 'workout_classifier.pkl')
TRAINING_DATA_FILE = os.path.join(DATA_DIR, 'X_train.pkl') # <--- NEW: Save this for LIME

def generate_synthetic_data(num_samples=2000):
    print("Generating synthetic training data...")
    data = []
    
    # MAPPINGS (for reference):
    # GENDER: 0=Male, 1=Female
    # GOAL: 0=Health, 1=Strength, 2=Hypertrophy
    # ENV: 0=Gym, 1=Home, 2=Mix
    
    for _ in range(num_samples):
        days_available = np.random.randint(1, 8) 
        experience_years = np.random.randint(0, 40)
        age = np.random.randint(18, 75)
        gender = np.random.choice([0, 1])
        goal = np.random.choice([0, 1, 2])
        environment = np.random.choice([0, 1, 2])
        
        # --- LOGIC RULES ---
        split_label = 0 # Default Full Body
        
        if days_available <= 3:
            split_label = 0 
        elif days_available == 4:
            # 80% chance Upper/Lower, 20% chance Body Part Split
            split_label = np.random.choice([1, 3], p=[0.8, 0.2])
        elif days_available >= 5:
            if age > 50:
                split_label = 1 
            elif goal == 2:
                split_label = 2 
            elif goal == 1:
                split_label = 1 
            else:
                split_label = 0 

        data.append([days_available, experience_years, goal, age, gender, environment, split_label])

    columns = ['days_available', 'experience_years', 'goal', 'age', 'gender', 'environment', 'split_label']
    return pd.DataFrame(data, columns=columns)

def train_classifier():
    df = generate_synthetic_data(2000)
    
    # Features (X)
    X = df[['days_available', 'experience_years', 'goal', 'age', 'gender', 'environment']]
    y = df['split_label']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)
    
    acc = accuracy_score(y_test, clf.predict(X_test))
    print(f"Model Accuracy: {acc * 100:.2f}%")
    
    # Save Model
    joblib.dump(clf, MODEL_FILE)
    print(f"Model saved to {MODEL_FILE}")
    
    # NEW: Save Training Data for LIME
    # We save the dataframe to preserve column names and value distributions
    joblib.dump(X_train, TRAINING_DATA_FILE) 
    print(f"Training data saved to {TRAINING_DATA_FILE} (Required for LIME)")

if __name__ == "__main__":
    train_classifier()