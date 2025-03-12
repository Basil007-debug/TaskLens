# model_interface.py
import os
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

class TaskEvaluator:
    def __init__(self):
        """Initialize the Groq LLM via LangChain."""
        if "GROQ_API_KEY" not in os.environ:
            raise ValueError("GROQ_API_KEY environment variable not set.")
        
        self.llm = ChatGroq(
            model="llama-3.1-8b-instant",
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2,
        )

    def evaluate_task(self, task_content, criteria):
        """
        Evaluate the task content against given criteria using the LLM.
        
        Args:
            task_content (str): The submitted task description or content.
            criteria (str): The expected standards or requirements for the task.
        
        Returns:
            dict: Evaluation results including feedback, metrics, and suggestions.
        """
        # Define the prompt template
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
                    You are an expert task evaluator. Evaluate the provided task submission based on the given criteria.
                    Provide detailed feedback, a performance score (0-100), and suggestions for improvement.

                    Format your response as follows:
                    - Feedback: [Your detailed feedback]
                    - Performance Score: [Score as a number between 0 and 100, e.g., 85]
                    - Suggestions: [Your suggestions]
                    """
                ),
                (
                    "human",
                    "Task Submission: {task_content}\nEvaluation Criteria: {criteria}"
                ),
            ]
        )

        # Chain the prompt with the LLM
        chain = prompt | self.llm

        # Invoke the chain with the inputs
        response = chain.invoke({"task_content": task_content, "criteria": criteria})

        # Parse the response
        try:
            content = response.content
            feedback_start = content.index("Feedback:") + len("Feedback:")
            score_start = content.index("Performance Score:") + len("Performance Score:")
            suggestions_start = content.index("Suggestions:") + len("Suggestions:")

            feedback = content[feedback_start:content.index("Performance Score:")].strip()
            score_str = content[score_start:content.index("Suggestions:")].strip()
            suggestions = content[suggestions_start:].strip()

            # Handle score parsing (e.g., "85/100" or "85")
            if '/' in score_str:
                score = int(score_str.split('/')[0])  # Extract the numerator
            else:
                score = int(score_str)  # Direct integer

            return {
                "feedback": feedback,
                "performance_score": score,
                "suggestions": suggestions
            }
        except Exception as e:
            raise ValueError(f"Error parsing LLM response: {e}")

    def generate_pdf_report(self, evaluation_result, output_path="task_evaluation_report.pdf"):
        """
        Generate a PDF report from the evaluation result.
        
        Args:
            evaluation_result (dict): The result from evaluate_task.
            output_path (str): Path to save the PDF.
        """
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph("Task Evaluation Report", styles["Title"]))
        story.append(Spacer(1, 12))

        story.append(Paragraph("Feedback:", styles["Heading2"]))
        story.append(Paragraph(evaluation_result["feedback"], styles["BodyText"]))
        story.append(Spacer(1, 12))

        story.append(Paragraph(f"Performance Score: {evaluation_result['performance_score']}/100", styles["Heading2"]))
        story.append(Spacer(1, 12))

        story.append(Paragraph("Suggestions for Improvement:", styles["Heading2"]))
        story.append(Paragraph(evaluation_result["suggestions"], styles["BodyText"]))

        doc.build(story)
        return output_path


if __name__ == "__main__":
    import getpass
    if "GROQ_API_KEY" not in os.environ:
        os.environ["GROQ_API_KEY"] = getpass.getpass("Enter your Groq API key: ")

    evaluator = TaskEvaluator()
    task_content = "Completed the project with all features implemented but missed the deadline."
    criteria = "Complete all features on time with high quality."
    result = evaluator.evaluate_task(task_content, criteria)
    pdf_path = evaluator.generate_pdf_report(result, "test_report.pdf")
    print(f"PDF report generated at: {pdf_path}")