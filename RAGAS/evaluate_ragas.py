from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, answer_correctness
from datasets import Dataset
import pandas as pd
import json
from pathlib import Path
import logging
import time
from langchain_core.language_models import BaseLLM
from langchain_core.outputs import LLMResult, Generation
from langchain_huggingface import HuggingFaceEmbeddings
from assistant.assistant import sdk, model
from pydantic.v1 import Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize embeddings
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")


class YandexGPTLLM(BaseLLM):
    sdk: object = Field(default=None, exclude=True)
    model: object = Field(default=None, exclude=True)

    def __init__(self, sdk, model, **kwargs):
        super().__init__(**kwargs)
        self.model = model.configure(temperature=0.5) if hasattr(model, 'configure') else model
        self.sdk = sdk

    def _call(self, prompt: str, stop=None, **kwargs) -> str:
        try:
            # Add instruction for JSON response
            json_prompt = f"{prompt}\nReturn the response in valid JSON format with proper escaping."
            result = self.model.run(json_prompt)
            text = result[0].text if result and result[0].text else "No response"

            # Clean up the response text
            text = text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

            # Validate JSON response
            try:
                json.loads(text)
                return text
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON response: {text}")
                # Fallback for specific metrics
                if "answer_correctness" in prompt.lower():
                    return json.dumps({"TP": [], "FP": [], "FN": []})
                elif "answer_relevance" in prompt.lower():
                    return json.dumps({"question": prompt, "noncommittal": False})
                return text
        except Exception as e:
            logger.error(f"Error calling YandexGPT: {str(e)}")
            if "RESOURCE_EXHAUSTED" in str(e):
                logger.warning("API quota exceeded, pausing for 60 seconds...")
                time.sleep(60)  # Pause to respect API limits
            if "answer_correctness" in prompt.lower():
                return json.dumps({"TP": [], "FP": [], "FN": []})
            elif "answer_relevance" in prompt.lower():
                return json.dumps({"question": prompt, "noncommittal": False})
            return "Error generating response"

    def _generate(self, prompts: list[str], *args, **kwargs) -> LLMResult:
        try:
            generations = []
            for prompt in prompts:
                text = self._call(prompt, **kwargs)
                generations.append([Generation(text=text)])
                time.sleep(1)  # Small delay to avoid hitting API limits
            return LLMResult(generations=generations)
        except Exception as e:
            logger.error(f"Error in batch generation: {str(e)}")
            return LLMResult(generations=[[Generation(text="Error generating response")] for _ in prompts])

    @property
    def _llm_type(self) -> str:
        return "yandexgpt"


def load_json_file(file_path: Path):
    """Load JSON file with error handling."""
    try:
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        logger.warning(f"File {file_path} not found")
        return []
    except Exception as e:
        logger.error(f"Error loading {file_path}: {str(e)}")
        return []


def main():
    # Initialize LLM
    yandex_llm = YandexGPTLLM(sdk=sdk, model=model)

    # Load logs and ground truth
    log_path = Path('../RAGAS_data/interaction_logs.json')
    ground_truth_path = Path('../RAGAS_data/ground_truth.json')

    logs = load_json_file(log_path)
    ground_truth = load_json_file(ground_truth_path)

    if not logs:
        logger.error("No interaction logs found. Please ensure the logs file exists and contains RAGAS_data.")
        return

    # Prepare RAGAS_data for RAGAS
    data = []
    for log in logs:
        if not all(key in log for key in ['question', 'context', 'answer']):
            logger.warning(f"Skipping log entry due to missing required fields: {log}")
            continue

        entry = {
            'question': log['question'],
            'contexts': log['context'] if isinstance(log['context'], list) else [log['context']],
            'answer': log['answer']
        }

        if isinstance(ground_truth, list) and any(item['question'] == log['question'] for item in ground_truth):
            for item in ground_truth:
                if item['question'] == log['question']:
                    entry['ground_truth'] = item['ground_truth']
                    break

        data.append(entry)

    if not data:
        logger.error("No valid RAGAS_data entries found for evaluation")
        return

    dataset = Dataset.from_pandas(pd.DataFrame(data))

    metrics = [
        faithfulness,
        answer_relevancy,
        answer_correctness
    ]

    try:
        result = evaluate(
            dataset=dataset,
            metrics=metrics,
            llm=yandex_llm,
            embeddings=embeddings
        )

        results_path = Path('../RAGAS_data/ragas_results.json')
        results_path.parent.mkdir(parents=True, exist_ok=True)

        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(dict(result), f, ensure_ascii=False, indent=4)

        logger.info("Evaluation completed successfully")
        logger.info("Results:")
        for metric, value in result.items():
            logger.info(f"{metric}: {value}")

    except Exception as e:
        logger.error(f"Error during evaluation: {str(e)}")


if __name__ == "__main__":
    main()