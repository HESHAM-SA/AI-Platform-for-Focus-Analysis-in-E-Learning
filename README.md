# AI Platform for Focus Analysis in E-Learning

## Overview

This project is an AI-powered platform designed to analyze focus in e-learning environments. It leverages facial recognition and machine learning to assess focus based on four key parameters: face direction, eye blink, person detection, and quiz performance. The platform generates a focus score and allows users to download an HTML report summarizing their focus statistics.

## Key Features

1. **Face Direction Analysis**: Monitors the direction in which the user's face is oriented (e.g., forward, left, right, up, down).
2. **Eye Blink Detection**: Detects and tracks eye blinks to assess attention and focus.
3. **Person Detection**: Ensures that the user is present and engaged in the learning activity.
4. **Quiz Integration**: Generates quizzes based on the content being studied and adjusts the focus score based on quiz performance.
5. **HTML Report**: Provides a downloadable HTML report summarizing focus statistics, including charts and detailed analysis.

## How It Works

### Steps

1. **Upload Video**: Users upload a video of themselves during an e-learning session.
2. **System Analysis**: The platform analyzes the video to determine focus based on the four parameters.
3. **Download Report**: Users can download an HTML report summarizing their focus statistics.

### Demo Video

[<video controls src="Demo.mp4" title="Title"></video>]

## Detailed Overview

### 1. `app.py`

This is the main application file that handles the user interface and interaction. It uses Streamlit to create a web-based interface where users can upload videos, configure settings, and view results.

- **Configuration**: Users can adjust parameters such as side look threshold, blink threshold, and discount rates using sliders.
- **Video Upload**: Users can upload a video file for analysis.
- **Live Video**: Users can also use their webcam for real-time focus analysis.
- **Quiz Generation**: After video analysis, the system generates a quiz based on the content.
- **Report Download**: Users can download an HTML report summarizing their focus statistics.

### 2. `focus_detection.py`

This file contains the core logic for detecting focus based on facial landmarks and eye movements.

- **Face Mesh**: Uses MediaPipe's Face Mesh to detect facial landmarks.
- **Eye Direction**: Calculates the direction of the eyes (e.g., left, right, center).
- **Blink Detection**: Detects blinks and calculates the blink ratio.
- **Focus Scoring**: Adjusts the focus score based on face direction, eye direction, and blink detection.

### 3. `quiz_generation.py`

This file handles the generation of quizzes based on the content of the video.

- **OpenAI Integration**: Uses OpenAI's GPT-3.5 Turbo model to generate quiz questions.
- **Video Processing**: Converts the video to text using the Whisper model for quiz generation.
- **Quiz Display**: Displays the generated quiz to the user and collects their answers.
- **Score Calculation**: Calculates the quiz score and adjusts the focus score based on performance.

### 4. `dashboard.py`

This file creates a dashboard to visualize the focus analysis results.

- **Focus Score Trend**: Displays a line chart showing the focus score over time.
- **Average Focus Scores**: Shows the average focus score before and after the quiz.

### 5. `constants.py`

This file contains constants and configuration settings used across the project.

- **Thresholds and Discounts**: Defines thresholds for face direction, blink detection, and discount rates.
- **Landmark Indices**: Lists the indices for facial landmarks used in detection.

### 6. `html_integration.py`

This file handles the generation of the HTML report.

- **Template Integration**: Uses a predefined HTML template and replaces placeholders with actual data.
- **Chart Data**: Inserts chart data into the HTML template.
- **Score Cards**: Updates score cards with the final focus scores.
- **Quiz Results**: Populates the quiz results table with user answers and correctness.

## Conclusion

This AI platform provides a comprehensive solution for analyzing focus in e-learning environments. By leveraging facial recognition and machine learning, it offers a detailed analysis of user engagement and provides actionable insights through downloadable reports. The integration of quizzes further enhances the learning experience by reinforcing key concepts and adjusting focus scores based on performance.