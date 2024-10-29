import altair as alt
import streamlit as st

def create_dashboard(df, avg_focus_score_before_quiz, avg_focus_score_after_quiz):
    # Focus Score Trend
    # Create an Altair chart with custom axis labels
    chart = alt.Chart(df).mark_line().encode(
        x=alt.X('timestamp_min', title='Time (minutes)'),
        y=alt.Y('focus_score', title='Focus Score')
    )

    # Display the chart in Streamlit
    st.altair_chart(chart, use_container_width=True)
    # Display Average Focus Scores
    st.markdown(
    f"""
    <div style="text-align: center; border: 1px solid #ddd; padding: 5px; border-radius: 5px; margin-bottom: 15px;">
        <h4 style="margin: 0; font-weight: bold;">Average Focus Score Before Quiz</h4>
        <h6 style="margin: 0; font-size: 16px;">{avg_focus_score_before_quiz:.2f}%</h6>
    </div>
    """, 
    unsafe_allow_html=True
    )
    st.markdown(
    f"""
    <div style="text-align: center; border: 1px solid #ddd; padding: 5px; border-radius: 5px; margin-top: 15px;">
        <h4 style="margin: 0; font-weight: bold;">Average Focus Score After Quiz</h4>
        <h6 style="margin: 0; font-size: 16px;">{avg_focus_score_after_quiz:.2f}%</h6>
    </div>
    """, 
    unsafe_allow_html=True
    )

    return avg_focus_score_after_quiz  # Return the final average focus score