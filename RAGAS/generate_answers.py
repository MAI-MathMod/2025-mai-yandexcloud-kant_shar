import json
from pathlib import Path
import logging
from assistant.assistant import sdk, model, search_index, create_instruction
from assistant.funcs import Agent, SearchProgramsList, HandOver

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

instruction = create_instruction('Русский')

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

def save_json_file(file_path: Path, data):
    """Save JSON file with error handling."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logger.info(f"Successfully saved {file_path}")
    except Exception as e:
        logger.error(f"Error saving {file_path}: {str(e)}")

def generate_answers():
    # Initialize Agent with tools and instruction
    tools = [SearchProgramsList, HandOver]
    agent = Agent(sdk=sdk, model=model, instruction=instruction, search_index=search_index, tools=tools)

    # Load interaction logs
    log_path = Path('../RAGAS_data/interaction_logs.json')
    logs = load_json_file(log_path)

    if not logs:
        logger.error("No interaction logs found. Please ensure the logs file exists.")
        return

    # Process each log entry
    for log in logs:
        if not all(key in log for key in ['question', 'context', 'answer']):
            logger.warning(f"Skipping log entry due to missing required fields: {log}")
            continue

        # Skip if answer already exists (optional, can be removed)
        # if log['answer']:
        #     logger.info(f"Answer already exists for question: {log['question']}")
        #     continue

        # Create prompt combining context and question
        prompt = f"{instruction}\n\nКонтекст: {log['context']}\nВопрос: {log['question']}"

        try:
            # Generate answer using Agent
            answer = agent(prompt)
            log['answer'] = answer
            logger.info(f"Generated answer for question: {log['question']}")
        except Exception as e:
            logger.error(f"Error generating answer for question {log['question']}: {str(e)}")
            log['answer'] = "Error generating response"

    # Save updated logs
    # save_qa_file(log_path, logs)
    logger.info("Answer generation completed")

    # Clean up
    agent.done()

if __name__ == "__main__":
    generate_answers()