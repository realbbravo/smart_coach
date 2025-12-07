# Smart Coach - AI-Powered Workout Plan Generator

An intelligent fitness application that uses machine learning to recommend personalized workout splits and generates detailed weekly plans using Google's Gemini AI.

## Features
- 🤖 ML-based workout split recommendation (Full Body, Upper/Lower, PPL, Body Part)
- 📊 LIME explainability for transparent AI decisions
- 🏋️ Personalized weekly workout plans via Gemini AI
- 📏 Support for both metric and imperial measurements
- 🎯 Tailored to experience level, goals, and available equipment

## Live Demo
🌐 [Visit Smart Coach](https://a5-2-ai-tasks-demo.web.app/)

## Local Development Setup

### Prerequisites
- Python 3.10+
- Git
- A Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/realbbravo/smart_coach.git
   cd smart_coach
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API Key**
   ```bash
   # Copy the example file
   cp .env.example .env
   
   # Edit .env and add your Gemini API key
   # GEMINI_API_KEY=your_actual_key_here
   ```

4. **Train the ML model** (if `.pkl` files are missing)
   ```bash
   python backend/train_model.py
   ```

5. **Start the backend server**
   ```bash
   python backend/app.py
   ```
   Backend runs on `http://localhost:8080`

6. **Start the frontend** (in a new terminal)
   ```bash
   cd frontend
   python3 -m http.server 3000
   ```
   Frontend runs on `http://localhost:3000`

7. **Open your browser**
   Navigate to `http://localhost:3000`

## Project Structure
```
smart_coach/
├── backend/
│   ├── app.py              # Flask API server
│   └── train_model.py      # ML model training
├── frontend/
│   ├── index.html          # UI
│   ├── app.js             # Frontend logic
│   └── style.css          # Styling
├── data/
│   ├── exercises.json      # Exercise database
│   ├── workout_classifier.pkl  # Trained model
│   └── X_train.pkl        # Training data for LIME
├── requirements.txt        # Python dependencies
└── .env.example           # Environment template
```

## Tech Stack
- **Backend**: Flask, scikit-learn, LIME, Google Gemini AI
- **Frontend**: Vanilla JavaScript, Tailwind CSS, Marked.js
- **Deployment**: Google Cloud Run (backend), Firebase Hosting (frontend)

## Usage
1. Select your measurement system (Metric/Imperial)
2. Fill in your fitness profile
3. Click "Generate My Plan"
4. Receive your personalized workout split with AI explanation
5. Get a detailed 7-day workout plan

## License
MIT License - Feel free to use for educational purposes

## Author
Developed for INFO 692 Applied Artificial Intelligence
Drexel University - Fall 2025