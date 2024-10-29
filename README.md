# AI Focus Analyzer for E-Learning

An AI-powered platform that analyzes student focus during e-learning sessions using facial recognition and quiz performance.

## 📈 Demo


https://github.com/user-attachments/assets/9544daf4-7e36-43cc-81da-0841f2477a06


## ✨ Features

- **Face & Eye Tracking**: Monitors face direction and eye blinking
- **Person Detection**: Identifies if a person is present in the frame
- **Quiz Integration**: Evaluates understanding through auto-generated quizzes
- **Focus Reports**: Generates downloadable HTML reports with detailed statistics

## 🚀 How to Use

1. Upload a learning session video or use live webcam
2. Let the AI analyze your focus parameters
3. Complete the auto-generated quiz
4. Download your focus analysis report

## 🛠️ Components

- `app.py`: Web interface for video upload and settings
- `focus_detection.py`: Core focus analysis logic
- `quiz_generation.py`: AI-powered quiz creation
- `dashboard.py`: Focus statistics visualization
- `html_integration.py`: Report generation

## 💻 Technical Stack

- Face Detection: MediaPipe Face Mesh
- Quiz Generation: OpenAI GPT-3.5
- Speech-to-Text: Whisper
- Frontend: Streamlit
