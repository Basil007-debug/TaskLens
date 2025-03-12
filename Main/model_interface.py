# model_inference.py
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
import os
import re

class TaskEvaluator:
    def __init__(self):
        if "GROQ_API_KEY" not in os.environ:
            raise ValueError("GROQ_API_KEY environment variable not set.")
        
        self.llm = ChatGroq(
            model="llama-3.1-8b-instant",
            temperature=0.3,
            max_tokens=None,
            timeout=None,
            max_retries=2,
        )

    def evaluate_task(self, question, text_descriptions, code_blocks=None):
        """Evaluate an ML answer based on a question using the ML-specific prompt."""
        code_blocks = code_blocks or []
        answer_text = "\n".join(text_descriptions)
        answer_code = "\n".join(code_blocks) if code_blocks else "No code provided."

        content = (
            f"QUESTION: {question}\n"
            f"ANSWER TEXT: {answer_text}\n"
            f"ANSWER CODE: {answer_code}"
        )

        system_prompt = (
            "YOU ARE AN ML EVALUATION AGENT, TASKED WITH ASSESSING MACHINE LEARNING RESPONSES FOR MODEL SELECTION, EXPLAINABILITY, AND PERFORMANCE.\n\n"
            "###### INSTRUCTIONS\n"
            "- **CHECK MODEL SELECTION**: Ensure the chosen model is appropriate for the task.\n"
            "- **VERIFY DATA PREPROCESSING**: Confirm data is properly cleaned and prepared.\n"
            "- **ASSESS EXPLAINABILITY**: Evaluate if the model's decisions are interpretable.\n"
            "- **CHECK PERFORMANCE METRICS**: Ensure relevant metrics (e.g., accuracy, F1) are reported.\n"
            "- **PROVIDE ACTIONABLE FEEDBACK** for any errors or improvements.\n\n"
            "###### STRUCTURED RESPONSE FORMAT\n"
            "**ML Evaluation Report:**\n"
            "- **Model Selection:** [Score: 0-10] [Explanation]\n"
            "- **Data Preprocessing:** [Score: 0-10] [Explanation]\n"
            "- **Explainability:** [Score: 0-10] [Explanation]\n"
            "- **Performance Metrics:** [Score: 0-10] [Explanation]\n"
            "- **Suggested Improvements:** [If applicable]"
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", "{content}")
            ]
        )

        chain = prompt | self.llm
        response = chain.invoke({"content": content})
        print("=== Raw LLM Response ===")
        print(response.content)
        print("=====================")
        return self._parse_response(response.content)

    def _parse_response(self, response_text):
        """Parse LLM response into a structured dictionary."""
        report = {
            "model_selection": {"score": 0, "explanation": "Not evaluated."},
            "data_preprocessing": {"score": 0, "explanation": "Not evaluated."},
            "explainability": {"score": 0, "explanation": "Not evaluated."},
            "performance_metrics": {"score": 0, "explanation": "Not evaluated."},
            "suggestions": "No suggestions provided."
        }

        # Relaxed regex to handle potential formatting issues
        model_selection = re.search(r"Model Selection:\s*\[Score:\s*(\d+)\]\s*\[(.*?)\](?=(Data Preprocessing:|$))", response_text, re.DOTALL)
        data_preprocessing = re.search(r"Data Preprocessing:\s*\[Score:\s*(\d+)\]\s*\[(.*?)\](?=(Explainability:|$))", response_text, re.DOTALL)
        explainability = re.search(r"Explainability:\s*\[Score:\s*(\d+)\]\s*\[(.*?)\](?=(Performance Metrics:|$))", response_text, re.DOTALL)
        performance_metrics = re.search(r"Performance Metrics:\s*\[Score:\s*(\d+)\]\s*\[(.*?)\](?=(Suggested Improvements:|$))", response_text, re.DOTALL)
        suggestions = re.search(r"Suggested Improvements:\s*\[(.*?)\](?=$)", response_text, re.DOTALL)

        if model_selection:
            report["model_selection"] = {"score": int(model_selection.group(1)), "explanation": model_selection.group(2).strip()}
        if data_preprocessing:
            report["data_preprocessing"] = {"score": int(data_preprocessing.group(1)), "explanation": data_preprocessing.group(2).strip()}
        if explainability:
            report["explainability"] = {"score": int(explainability.group(1)), "explanation": explainability.group(2).strip()}
        if performance_metrics:
            report["performance_metrics"] = {"score": int(performance_metrics.group(1)), "explanation": performance_metrics.group(2).strip()}
        if suggestions:
            report["suggestions"] = suggestions.group(1).strip()

        return report

    def generate_pdf_report(self, evaluation_result):
        """Generate PDF report in memory."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph("ML Evaluation Report", styles["Title"]))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"Model Selection: [Score: {evaluation_result['model_selection']['score']}/10] {evaluation_result['model_selection']['explanation']}", styles["BodyText"]))
        story.append(Spacer(1, 6))
        story.append(Paragraph(f"Data Preprocessing: [Score: {evaluation_result['data_preprocessing']['score']}/10] {evaluation_result['data_preprocessing']['explanation']}", styles["BodyText"]))
        story.append(Spacer(1, 6))
        story.append(Paragraph(f"Explainability: [Score: {evaluation_result['explainability']['score']}/10] {evaluation_result['explainability']['explanation']}", styles["BodyText"]))
        story.append(Spacer(1, 6))
        story.append(Paragraph(f"Performance Metrics: [Score: {evaluation_result['performance_metrics']['score']}/10] {evaluation_result['performance_metrics']['explanation']}", styles["BodyText"]))
        story.append(Spacer(1, 6))
        story.append(Paragraph(f"Suggested Improvements: {evaluation_result['suggestions']}", styles["BodyText"]))

        doc.build(story)
        buffer.seek(0)
        return buffer