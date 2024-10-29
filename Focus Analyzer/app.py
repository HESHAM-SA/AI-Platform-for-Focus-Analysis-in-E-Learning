import tempfile
import streamlit as st
from streamlit_webrtc import WebRtcMode, webrtc_streamer
import focus_detection as fd
import quiz_generation as qg
import dashboard as db
import constants as const
from constants import config
import html_integration as hi


def app():
    st.title("📊 AI Platform for Focus Analysis")
    st.sidebar.header("🔧 Configuration")

    # Sidebar for configuration
    config.SIDE_THRESHOLD = st.sidebar.slider("Side Look Threshold (seconds)", 1, 50, 5, key="side_threshold")
    config.DISCOUNT_SIDE = st.sidebar.slider("Side Look Discount (%)", 1, 50, 1, key="discount_side")
    config.BLINK_THRESHOLD = st.sidebar.slider("Blink Threshold (seconds)", 1, 50, 3, key="blink_threshold")
    config.DISCOUNT_EYES = st.sidebar.slider("Closed Eyes Discount (%)", 5, 50, 1, key="discount_eyes")

    # Initialize session state variables
    if 'quiz_generated' not in st.session_state:
        st.session_state.quiz_generated = False
    if 'quiz_submitted' not in st.session_state:
        st.session_state.quiz_submitted = False
    if 'quiz' not in st.session_state:
        st.session_state.quiz = None
    if 'user_answers' not in st.session_state:
        st.session_state.user_answers = None
    if 'focus_score' not in st.session_state:
        st.session_state.focus_score = 50  # Initialized start focus from 50
    if 'results_df' not in st.session_state:
        st.session_state.results_df = None
    if 'avg_focus_score_before_quiz' not in st.session_state:
        st.session_state.avg_focus_score_before_quiz = None
    if 'avg_focus_score_after_quiz' not in st.session_state:
        st.session_state.avg_focus_score_after_quiz = None
    if 'quiz_score' not in st.session_state:
        st.session_state.quiz_score = None
    if 'uploaded_filename' not in st.session_state:
        st.session_state.uploaded_filename = None

    # Ask for OpenAI API key
    const.openai_api_key = st.text_input("Enter your OpenAI API key:", type="password")
    if const.openai_api_key:
        qg.openai.api_key = const.openai_api_key
        # Load the Whisper model if not already loaded
        if const.model is None:
            const.model = qg.whisper.load_model("base")
    else:
        st.warning("Please enter your OpenAI API key to proceed.")

    # Tabs for Live Video and Upload Video
    tab1, tab2 = st.tabs(["🎥 Live Video", "📤 Upload Video"])

    with tab1:
        st.header("🔴 Webcam Feed")
        st.write(f"Current Focus Score: {st.session_state.focus_score}%")
        webrtc_streamer(
            key="camera",
            mode=WebRtcMode.SENDRECV,
            media_stream_constraints={
                "video": True,
                "audio": False,
            },
            video_frame_callback=fd.video_frame_callback,
        )

    with tab2:
        st.header("📥 Upload Video for Analysis and Quiz")
        uploaded_file = st.file_uploader("Choose a video file", type=["mp4", "avi", "mov"])

        if uploaded_file is not None:
            if st.session_state.uploaded_filename != uploaded_file.name:
                # New file uploaded, reset stored data
                st.session_state.results_df = None
                st.session_state.avg_focus_score_before_quiz = None
                st.session_state.avg_focus_score_after_quiz = None
                st.session_state.quiz = None
                st.session_state.quiz_generated = False
                st.session_state.quiz_submitted = False
                st.session_state.user_answers = None
                st.session_state.uploaded_filename = uploaded_file.name
                st.session_state.focus_score = 50  # Reset focus score to 50
            st.video(uploaded_file)

            if st.button("🔍 Analyze Video and Generate Quiz"):
                # Process video only if not already processed
                if st.session_state.results_df is None:
                    with st.spinner("Analyzing video..."):
                        results_df = fd.process_uploaded_video(uploaded_file)
                        st.session_state.results_df = results_df  # Store in session state
                        st.success("✅ Analysis complete!")
                        st.session_state.avg_focus_score_before_quiz = results_df['focus_score'].mean()
                else:
                    st.success("Video already analyzed.")
                    results_df = st.session_state.results_df
                    st.session_state.avg_focus_score_before_quiz = results_df['focus_score'].mean()

                # Generate quiz only if not already generated
                if st.session_state.quiz is None:
                    with st.spinner("Processing video for quiz generation..."):
                        transcription = qg.process_video_to_text(uploaded_file)
                        if transcription:
                            with st.spinner("Generating quiz..."):
                                st.session_state.quiz = qg.generate_quiz_from_text(transcription)
                                if st.session_state.quiz:
                                    st.session_state.quiz_generated = True
                else:
                    st.success("Quiz already generated.")
                    st.session_state.quiz_generated = True

        if st.session_state.quiz_generated and not st.session_state.quiz_submitted:
            st.session_state.user_answers = qg.display_quiz(st.session_state.quiz)

            # Inside the app function
            if st.button("Submit Quiz"):
                final_score, correct_answers = qg.calculate_score(st.session_state.quiz, st.session_state.user_answers)
                st.session_state.focus_score, adjustment = qg.adjust_focus_score_based_on_quiz(st.session_state.quiz, st.session_state.user_answers, st.session_state.focus_score)
                st.session_state.quiz_submitted = True
                st.session_state.quiz_score = final_score  # Store quiz score

                # Calculate average focus score after quiz
                avg_focus_score_before_quiz = st.session_state.avg_focus_score_before_quiz
                total_adjustment = adjustment  # Total adjustment based on quiz
                avg_focus_score_after_quiz = min(100, max(0, avg_focus_score_before_quiz + total_adjustment))
                st.session_state.avg_focus_score_after_quiz = avg_focus_score_after_quiz

                # Display dashboard after quiz completion
                st.write(f"Quiz Score: {final_score:.2f}/10")
                    
                st.markdown(
                    """
                    <div style="text-align: center; margin-top: 20px; margin-bottom: 20px;">
                        <h2 style="margin: 0; font-weight: bold;">
                            <span style="font-size: 1.5em;">📈</span> Focus Score Over Time <span style="font-size: 1.5em;">📈</span>
                        </h2>
                        <hr style="width: 50%; margin: auto; border: 1px solid #ddd;">
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                # Show detailed dashboard
                db.create_dashboard(st.session_state.results_df, avg_focus_score_before_quiz, avg_focus_score_after_quiz)

                # Prepare data for HTML report
                df = st.session_state.results_df

                # Line chart data
                labels_linechart = df['timestamp_min'].round(2).tolist()
                data_linechart = df['focus_score'].tolist()

                # Eye direction pie chart data
                eye_detected_df = df[~df['eye_direction'].isin(['Not Detected', 'Unknown', 'Blink'])]
                total_eye_detected_time = eye_detected_df['delta_time'].sum()
                eye_direction_times = eye_detected_df.groupby('eye_direction')['delta_time'].sum()
                eye_direction_percentages = ((eye_direction_times / total_eye_detected_time) * 100).round(2).tolist()
                eye_direction_labels = eye_direction_times.index.tolist()

                # Face position pie chart data
                face_detected_df = df[df['face_position'] != 'Not Detected']
                total_face_detected_time = face_detected_df['delta_time'].sum()
                face_position_times = face_detected_df.groupby('face_position')['delta_time'].sum()
                face_position_percentages = ((face_position_times / total_face_detected_time) * 100).round(2).tolist()
                face_position_labels = face_position_times.index.tolist()

                # Front camera vs not front camera pie chart data
                front_camera_time = df[df['is_front_camera']]['delta_time'].sum()
                not_front_camera_time = df[~df['is_front_camera']]['delta_time'].sum()
                total_time = front_camera_time + not_front_camera_time
                front_camera_percentage = (front_camera_time / total_time * 100).round(2)
                not_front_camera_percentage = (not_front_camera_time / total_time * 100).round(2)

                # Scores
                max_focus_score = df['focus_score'].max()
                min_focus_score = df['focus_score'].min()
                avg_focus_score_before_quiz = st.session_state.avg_focus_score_before_quiz
                avg_focus_score_after_quiz = st.session_state.avg_focus_score_after_quiz

                # Quiz results
                table_data = []
                for i, (user_answer, question) in enumerate(zip(st.session_state.user_answers, st.session_state.quiz['questions']), 1):
                    is_correct = user_answer == question['correct_answer']
                    status = "Correct" if is_correct else "Wrong"
                    score = "100%" if is_correct else "0%"
                    table_data.append({
                        "question": question['question'],
                        "status": status,
                        "score": score
                    })

                # Generate HTML report
                template_path = "templates/index.html"  # Path to your HTML template
                chart_data = {
                    "line_chart": {"labels": labels_linechart, "data": data_linechart},
                    "pie_chart1": {"labels": eye_direction_labels, "data": eye_direction_percentages},
                    "pie_chart2": {"labels": face_position_labels, "data": face_position_percentages},
                    "pie_chart3": {"labels": ["Front Camera", "Not Front Camera"], "data": [front_camera_percentage, not_front_camera_percentage]},
                }
                scores = {
                    "final": f"{avg_focus_score_after_quiz:.2f}%",
                    "highest_continuous": f"{max_focus_score:.2f}%",
                    "min": f"{min_focus_score:.2f}%",
                    "after_quiz": f"{avg_focus_score_after_quiz:.2f}%",
                }
                populated_html = hi.generate_html_from_template(template_path, chart_data, scores, table_data)

                # Provide Download Button
                with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp_file:
                    tmp_file.write(populated_html.encode("utf-8"))
                    tmp_file_path = tmp_file.name

                st.download_button(
                    label="💾 Download HTML Report",
                    data=open(tmp_file_path, "rb").read(),
                    file_name="focus_analysis_report.html",
                    mime="text/html",
                )

                # Allow users to retake the quiz
                if st.button("Retake Quiz"):
                    # Reset quiz variables to allow retaking
                    for i in range(len(st.session_state.quiz['questions'])):
                        if f"q{i}" in st.session_state:
                            del st.session_state[f"q{i}"]
                    st.session_state.quiz_submitted = False
                    st.session_state.user_answers = None

        elif st.session_state.quiz_submitted:
            # If quiz already submitted, show the dashboard and allow retake
            avg_focus_score_before_quiz = st.session_state.avg_focus_score_before_quiz
            avg_focus_score_after_quiz = st.session_state.avg_focus_score_after_quiz
            final_score = st.session_state.quiz_score

            # Show detailed dashboard
            db.create_dashboard(st.session_state.results_df, avg_focus_score_before_quiz, avg_focus_score_after_quiz)

            # Generate HTML report
            df = st.session_state.results_df

            # Line chart data
            labels_linechart = df['timestamp_min'].round(2).tolist()
            data_linechart = df['focus_score'].tolist()

            # Eye direction pie chart data
            eye_detected_df = df[~df['eye_direction'].isin(['Not Detected', 'Unknown', 'Blink'])]
            total_eye_detected_time = eye_detected_df['delta_time'].sum()
            eye_direction_times = eye_detected_df.groupby('eye_direction')['delta_time'].sum()
            eye_direction_percentages = ((eye_direction_times / total_eye_detected_time) * 100).round(2).tolist()
            eye_direction_labels = eye_direction_times.index.tolist()

            # Face position pie chart data
            face_detected_df = df[df['face_position'] != 'Not Detected']
            total_face_detected_time = face_detected_df['delta_time'].sum()
            face_position_times = face_detected_df.groupby('face_position')['delta_time'].sum()
            face_position_percentages = ((face_position_times / total_face_detected_time) * 100).round(2).tolist()
            face_position_labels = face_position_times.index.tolist()

            # Front camera vs not front camera pie chart data
            front_camera_time = df[df['is_front_camera']]['delta_time'].sum()
            not_front_camera_time = df[~df['is_front_camera']]['delta_time'].sum()
            total_time = front_camera_time + not_front_camera_time
            front_camera_percentage = (front_camera_time / total_time * 100).round(2)
            not_front_camera_percentage = (not_front_camera_time / total_time * 100).round(2)

            # Scores
            max_focus_score = df['focus_score'].max()
            min_focus_score = df['focus_score'].min()
            avg_focus_score_before_quiz = st.session_state.avg_focus_score_before_quiz
            avg_focus_score_after_quiz = st.session_state.avg_focus_score_after_quiz

            # Quiz results
            table_data = []
            for i, (user_answer, question) in enumerate(zip(st.session_state.user_answers, st.session_state.quiz['questions']), 1):
                is_correct = user_answer == question['correct_answer']
                status = "Correct" if is_correct else "Wrong"
                score = "100%" if is_correct else "0%"
                table_data.append({
                    "question": question['question'],
                    "status": status,
                    "score": score
                })

            # Generate HTML report
            template_path = "templates/index.html"  # Path to your HTML template
            chart_data = {
                "line_chart": {"labels": labels_linechart, "data": data_linechart},
                "pie_chart1": {"labels": eye_direction_labels, "data": eye_direction_percentages},
                "pie_chart2": {"labels": face_position_labels, "data": face_position_percentages},
                "pie_chart3": {"labels": ["Front Camera", "Not Front Camera"], "data": [front_camera_percentage, not_front_camera_percentage]},
            }
            scores = {
                "final": f"{avg_focus_score_after_quiz:.2f}%",
                "highest_continuous": f"{max_focus_score:.2f}%",
                "min": f"{min_focus_score:.2f}%",
                "after_quiz": f"{avg_focus_score_after_quiz:.2f}%",
            }
            populated_html = hi.generate_html_from_template(template_path, chart_data, scores, table_data)

            # Provide Download Button
            with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp_file:
                tmp_file.write(populated_html.encode("utf-8"))
                tmp_file_path = tmp_file.name

            st.download_button(
                label="💾 Download HTML Report",
                data=open(tmp_file_path, "rb").read(),
                file_name="focus_analysis_report.html",
                mime="text/html",
            )

            # Allow users to retake the quiz
            if st.button("Retake Quiz"):
                # Reset quiz variables to allow retaking
                for i in range(len(st.session_state.quiz['questions'])):
                    if f"q{i}" in st.session_state:
                        del st.session_state[f"q{i}"]
                st.session_state.quiz_submitted = False
                st.session_state.user_answers = None

    st.sidebar.write(f"Focus Score: {st.session_state.focus_score}%")

if __name__ == "__main__":
    app()