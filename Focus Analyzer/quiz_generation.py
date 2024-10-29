import openai
import json
import subprocess
import os
import whisper
import streamlit as st

def generate_quiz_from_text(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": """Generate a multiple choice quiz as JSON with this exact structure: 
                 {"questions": [{"question": "Q1?", "options": ["A", "B", "C"], "correct_answer": "A"}]}.
                 Make questions short, general, simple, clear, easy, and focus on main points and key takeaways from the content, Make sure questions and multiple choices are as short as possible.
                 Ensure questions are straightforward and test understanding rather than specific details.
                 Include some questions about the overall theme or main message."""},
                {"role": "user", "content": f"Create a 5-question quiz covering the main points and general understanding of this text:\n\n{text}"}
            ]
        )
        quiz_data = json.loads(response.choices[0].message['content'])
        if not isinstance(quiz_data, dict) or 'questions' not in quiz_data:
            raise ValueError("Invalid quiz format")
        return quiz_data
    except Exception as e:
        st.error(f"Error generating quiz: {e}")
        return None

def process_video_to_text(video_file):
    temp_dir = "temp"
    os.makedirs(temp_dir, exist_ok=True)
    
    temp_video_path = os.path.join(temp_dir, video_file.name)
    audio_file_path = os.path.join(temp_dir, 'output_audio.mp3')
    
    try:
        with open(temp_video_path, "wb") as f:
            f.write(video_file.getbuffer())
        
        command = ["ffmpeg", "-i", temp_video_path, "-vn", "-acodec", "libmp3lame", audio_file_path]
        subprocess.run(command, check=True)
        
        result = whisper.load_model("base").transcribe(audio_file_path)
        return result['text']
    except Exception as e:
        st.error(f"Error processing video: {e}")
        return None
    finally:
        if os.path.exists(temp_video_path):
            os.remove(temp_video_path)
        if os.path.exists(audio_file_path):
            os.remove(audio_file_path)

def display_quiz(quiz):
    st.subheader("Quiz")
    user_answers = []
    
    for i, question in enumerate(quiz['questions']):
        st.write(f"Question {i+1}: {question['question']}")
        user_answer = st.radio(
            "",  # Empty label
            question['options'],
            key=f"q{i}",
            label_visibility="collapsed"
        )
        st.write("---")

        user_answers.append(user_answer)
    return user_answers

def calculate_score(quiz, user_answers):
    score = sum(1 for ua, q in zip(user_answers, quiz['questions'])
                if ua == q['correct_answer'])
    
    st.write("\n### Quiz Results")
    for i, (user_answer, question) in enumerate(zip(user_answers, quiz['questions']), 1):
        is_correct = user_answer == question['correct_answer']
        result_color = "green" if is_correct else "red"
        st.markdown(f"**Question {i}:** :{result_color}[{'✓' if is_correct else '✗'}]")
        st.write(f"Your answer: {user_answer}")
        st.write(f"Correct answer: {question['correct_answer']}")
        st.write("---")
    
    final_score = (score / len(quiz['questions'])) * 10
    st.success(f"Final score: {final_score:.2f}/10")
    return final_score, score

def adjust_focus_score_based_on_quiz(quiz, user_answers, focus_score):
    adjustment = 0
    for ua, q in zip(user_answers, quiz['questions']):
        if ua == q['correct_answer']:
            focus_score = min(100, focus_score + 5)
            adjustment += 5
        else:
            focus_score = max(0, focus_score - 5)
            adjustment -= 5
    return focus_score, adjustment