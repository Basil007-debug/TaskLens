# main.py
import streamlit as st
from model_interface import TaskEvaluator
import os
import getpass

# Set API key if not already set
if "GROQ_API_KEY" not in os.environ:
    api_key = st.text_input("Enter your Groq API key:", type="password")
    if api_key:
        os.environ["GROQ_API_KEY"] = api_key
    else:
        st.warning("Please enter your Groq API key to proceed.")
        st.stop()

# Set up the Streamlit app
st.title("Task Evaluator")
st.write("Enter the task submission and criteria below to generate an evaluation report.")

# Input fields
task_content = st.text_area("Task Submission", placeholder="Enter the task content here...")
criteria = st.text_area("Evaluation Criteria", placeholder="Enter the criteria here...")

# Button to evaluate and generate report
if st.button("Evaluate Task"):
    if task_content and criteria:
        try:
            # Initialize the evaluator
            evaluator = TaskEvaluator()

            # Evaluate the task
            with st.spinner("Evaluating task..."):
                evaluation_result = evaluator.evaluate_task(task_content, criteria)

            # Display results
            st.subheader("Evaluation Results")
            st.write(f"**Feedback:** {evaluation_result['feedback']}")
            st.write(f"**Performance Score:** {evaluation_result['performance_score']}/100")
            st.write(f"**Suggestions:** {evaluation_result['suggestions']}")

            # Generate and provide download link for PDF
            with st.spinner("Generating PDF report..."):
                pdf_path = evaluator.generate_pdf_report(evaluation_result, "task_evaluation_report.pdf")
            
            with open(pdf_path, "rb") as file:
                st.download_button(
                    label="Download PDF Report",
                    data=file,
                    file_name="task_evaluation_report.pdf",
                    mime="application/pdf"
                )
        except Exception as e:
            st.error(f"An error occurred: {e}")
    else:
        st.warning("Please fill in both the task submission and criteria.")

# Run with: streamlit run main.py