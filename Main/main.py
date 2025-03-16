# main.py
import streamlit as st
from data_extract import PDFExtractor
from preprocess import TextPreprocessor
from model_interface import TaskEvaluator
import os

# Set API key
if "GROQ_API_KEY" not in os.environ:
    api_key = st.text_input("Enter your Groq API key:", type="password")
    if api_key:
        os.environ["GROQ_API_KEY"] = api_key
    else:
        st.warning("Please enter your Groq API key to proceed.")
        st.stop()

# Streamlit UI
st.title("Task Evaluator (ML)")
st.write("Upload a PDF containing the answer and provide the question for ML evaluation.")

# Input fields
question = st.text_area("Question", placeholder="Enter the question here...")
uploaded_file = st.file_uploader("Upload Answer (PDF)", type=["pdf"])

# Button to process and evaluate
if st.button("Evaluate Answer"):
    if not question or not uploaded_file:
        st.warning("Please provide both a question and upload a PDF.")
    else:
        with st.spinner("Processing..."):
            # Step 1: Extract text from the uploaded PDF (in memory)
            extractor = PDFExtractor(uploaded_file)
            extracted_data = extractor.extract_pdf_data()

            # Print extracted data to terminal
            print("=== Extracted Data ===")
            print("Text Descriptions:")
            for text in extracted_data["text_descriptions"]:
                print(f"- {text}")
            print("Code Blocks:")
            for code in extracted_data["code_blocks"]:
                print(f"- {code}")
            print("=====================")

            # Step 2: Preprocess the extracted text
            preprocessor = TextPreprocessor()
            preprocessed_data = preprocessor.preprocess(extracted_data)

            # Step 3: Evaluate the answer using the LLM
            evaluator = TaskEvaluator()
            result = evaluator.evaluate_task(
                question,
                preprocessed_data["text_descriptions"],
                preprocessed_data["code_blocks"]
            )

            # Display formatted raw LLM response
            st.subheader("Evaluation Results")
            raw_response = result["raw"]
            
            # Create expandable sections for different parts of the evaluation
            with st.expander("📊 Detailed Evaluation", expanded=True):
                # Split the response into sections and format them
                sections = raw_response.split('\n\n')
                for section in sections:
                    if section.strip():
                        # Format headers
                        if section.startswith('#'):
                            st.markdown(section)
                        # Format lists
                        elif section.startswith('- '):
                            st.markdown(section)
                        # Format regular paragraphs
                        else:
                            st.write(section)

            # Generate PDF report using both parsed results and raw response
            pdf_buffer = evaluator.generate_pdf_report({
                "parsed": result["parsed"],
                "raw": result["raw"]
            })

            # # Display results
            # st.subheader("ML Evaluation Report")
            # st.write(f"**Model Selection:** [Score: {result['model_selection']['score']}/10] {result['model_selection']['explanation']}")
            # st.write(f"**Data Preprocessing:** [Score: {result['data_preprocessing']['score']}/10] {result['data_preprocessing']['explanation']}")
            # st.write(f"**Explainability:** [Score: {result['explainability']['score']}/10] {result['explainability']['explanation']}")
            # st.write(f"**Performance Metrics:** [Score: {result['performance_metrics']['score']}/10] {result['performance_metrics']['explanation']}")
            # st.write(f"**Suggested Improvements:** {result['suggestions']}")
            print("++++++++++++++++++++++++")
            print(result)
            print("++++++++++++++++++++++++")


            # Provide download button for report
            st.download_button(
                label="Download PDF Report",
                data=pdf_buffer,
                file_name="ml_evaluation_report.pdf",
                mime="application/pdf"
            )