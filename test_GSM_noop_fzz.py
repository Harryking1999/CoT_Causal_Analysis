import json
import re
import time
from tqdm import tqdm
import openai
import argparse
import random
import numpy as np
import os

def extract_final_answer(model_resp: str) -> float:
    """Extract the final numerical answer from model response."""
    # Remove commas so for example 5,000 becomes 5000
    model_resp = model_resp.replace(",", "")
    # Find the last number
    extracted_num = re.findall(r"-?\d+\.?\d*", model_resp)[-1]
    # Use float to ensure 3.0 and 3 are the same.
    return float(extracted_num)

class VLLMModel:
    def __init__(self, api_base, model_name, max_new_tokens=2000):
        self.api_base = api_base
        self.model_name = model_name
        self.max_new_tokens = max_new_tokens
        
        # Configure OpenAI client to connect to local vLLM service
        openai.api_base = api_base
        openai.api_key = "EMPTY"  # vLLM doesn't need real API key
        
        # Define models that need system prompt
        self.models_with_system_prompt_distill = ['Qwen2.5-3B-Distill-22000']
        self.models_with_system_prompt_RL_openr1 = ['Qwen2.5-3B-GRPO-2000', 'Qwen2.5-3B-SFT-GRPO-2000']
        
        # System prompt for specific models
        self.system_prompt_distill = (
            "You are Open-R1, a language model trained by Hugging Face to help users. Your role as an assistant involves thoroughly exploring questions through a systematic thinking process before providing the final precise and accurate solutions. This requires engaging in a comprehensive cycle of analysis, summarizing, exploration, reassessment, reflection, backtracing, and iteration to develop well-considered thinking process. Please structure your response into two main sections: Thought and Solution using the specified format: <think> Thought section </think> Solution section. In the Thought section, detail your reasoning process in steps. Each step should include detailed considerations such as analysing questions, summarizing relevant findings, brainstorming new ideas, verifying the accuracy of the current steps, refining any errors, and revisiting previous steps. In the Solution section, based on various attempts, explorations, and reflections from the Thought section, systematically present the final solution that you deem correct. The Solution section should be logical, accurate, and concise and detail necessary steps needed to reach the conclusion. Now, try to solve the following question through the above guidelines."
        )
        self.system_prompt_RL_openr1 = (
            "You are a helpful AI Assistant that provides well-reasoned and detailed responses. You first think about the reasoning process as an internal monologue and then provide the user with the answer. Respond in the following format: <think>\n...\n</think>\n<answer>\n...\n</answer>"
        )
        
        print(f'VLLM API with {api_base}, {model_name}, {max_new_tokens}')
    
    def generate(self, prompt, temperature=0.0):
        """Generate response using vLLM API."""
        try:
            # Check if this model needs system prompt
            if self.model_name in self.models_with_system_prompt_distill:
                # Use Chat Completion API for models with system prompt
                messages = [
                    {"role": "system", "content": self.models_with_system_prompt_distill},
                    {"role": "user", "content": prompt}
                ]
                
                response = openai.ChatCompletion.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=self.max_new_tokens,
                    stop=None,
                    stream=False
                )
                return response.choices[0].message.content.strip()
            elif self.model_name in self.models_with_system_prompt_RL_openr1:
                messages = [
                    {"role": "system", "content": self.system_prompt_RL_openr1},
                    {"role": "user", "content": prompt}
                ]
                
                response = openai.ChatCompletion.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=self.max_new_tokens,
                    stop=None,
                    stream=False
                )
                return response.choices[0].message.content.strip()
            elif self.model_name in ['Qwen2.5-3B']:
                messages = [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ]
                
                response = openai.ChatCompletion.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=self.max_new_tokens,
                    stop=None,
                    stream=False
                )
                return response.choices[0].message.content.strip()
            elif self.model_name in ['Qwen2.5-3B-Instruct']:
                messages = [
                    {"role": "system", "content": "You are Qwen, created by Alibaba Cloud. You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ]
                
                response = openai.ChatCompletion.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=self.max_new_tokens,
                    stop=None,
                    stream=False
                )
                return response.choices[0].message.content.strip()
            else:
                # Use original Completion API for other models
                response = openai.Completion.create(
                    model=self.model_name,
                    prompt=prompt,
                    temperature=temperature,
                    max_tokens=self.max_new_tokens,
                    stop=None,
                    stream=False
                )
                return response.choices[0].text.strip()
                
        except Exception as e:
            print(f"Generation error: {e}")
            return ""

def format_prompt(question):
    """Format the prompt for mathematical problem solving."""
    return f"As an expert problem solver, solve step by step the following mathematical questions. {question}"

def load_jsonl_data(file_path):
    """Load data from JSONL file."""
    data = []
    print(f"Loading data from: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line.strip()))
    print(f"Loaded {len(data)} items")
    return data

def load_json_data(file_path):
    """Load data from JSON file."""
    print(f"Loading data from: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"Loaded {len(data)} items")
    return data

def evaluate_distracted_dataset(model, data, log_file, test_mode=False):
    """Evaluate model performance on distracted dataset."""
    dataset_name = "GSM_Distracted"
    print(f"\n=== Evaluating {dataset_name} ===")
    
    correct = 0
    total = 0
    results = []
    
    # Determine how many items to process
    if test_mode:
        items_to_process = data[:3]  # Only test 3 cases
        print(f"Test mode: evaluating only 3 cases")
    else:
        items_to_process = data  # Test all cases
        print(f"Full mode: evaluating all {len(items_to_process)} cases")
    
    # Process each item individually
    for i, item in enumerate(tqdm(items_to_process, desc=f"Processing {dataset_name}")):
        # Generate response for this item
        prompt = format_prompt(item['question'])
        response = model.generate(prompt)
        
        try:
            # Extract model's answer
            model_answer = extract_final_answer(response)
            
            # Extract ground truth answer
            gt_answer = None
            if 'answer' in item:
                if isinstance(item['answer'], str):
                    # Handle cases where answer might be in format "#### 42"
                    if '####' in item['answer']:
                        gt_answer = float(item['answer'].split('####')[-1].strip())
                    else:
                        # Try to extract number from string
                        ans_str = item['answer'].replace(',', '').strip()
                        extracted_num = re.findall(r"-?\d+\.?\d*", ans_str)
                        if extracted_num:
                            gt_answer = float(extracted_num[-1])
                        else:
                            gt_answer = float(item['answer'])
                else:
                    gt_answer = float(item['answer'])
            
            if gt_answer is None:
                print(f"Warning: Could not find answer for item {i} in {dataset_name}")
                continue
            
            # Check if answer is correct
            is_correct = abs(model_answer - gt_answer) < 1e-6
            if is_correct:
                correct += 1
            
            total += 1
            
            # Log result
            result = {
                'dataset': dataset_name,
                'item_id': i,
                'question': item['question'],
                'prompt': prompt,
                'model_response': response,
                'model_answer': model_answer,
                'ground_truth': gt_answer,
                'is_correct': is_correct
            }
            results.append(result)
            
            # Write to log file
            log_file.write(json.dumps(result, ensure_ascii=False) + '\n')
            log_file.flush()
            
        except Exception as e:
            print(f"Error processing item {i} in {dataset_name}: {e}")
            # Log error case
            result = {
                'dataset': dataset_name,
                'item_id': i,
                'question': item['question'],
                'prompt': prompt,
                'model_response': response,
                'model_answer': None,
                'ground_truth': None,
                'is_correct': False,
                'error': str(e)
            }
            log_file.write(json.dumps(result, ensure_ascii=False) + '\n')
            log_file.flush()
            continue
    
    accuracy = correct / total if total > 0 else 0
    print(f"{dataset_name} Accuracy: {accuracy:.4f} ({correct}/{total})")
    
    return accuracy, correct, total, results

def create_original_gsm_dataset(sampled_data):
    """Create original GSM dataset from sampled data by extracting and deduplicating."""
    print("\n=== Creating Original GSM Dataset ===")
    
    # Extract original questions and answers
    original_items = []
    seen_questions = set()
    
    for item in sampled_data:
        # Get original question and answer
        original_question = item.get('question', '')  # 原始采样数据中的question字段
        original_answer = item.get('answer', '')  # 原始采样数据中的answer字段
        
        # Create tuple for deduplication
        question_answer_tuple = (original_question, original_answer)
        
        if original_question and original_question not in seen_questions:
            seen_questions.add(original_question)
            
            # Extract ground truth answer using extract_final_answer
            try:
                if isinstance(original_answer, str):
                    if '####' in original_answer:
                        gt_answer = float(original_answer.split('####')[-1].strip())
                    else:
                        gt_answer = extract_final_answer(original_answer)
                else:
                    gt_answer = float(original_answer)
                
                original_items.append({
                    'question': original_question,
                    'answer_text': original_answer,
                    'ground_truth': gt_answer
                })
            except Exception as e:
                print(f"Error processing original answer: {e}")
                continue
    
    print(f"Created original GSM dataset with {len(original_items)} unique items")
    print(f"Deduplication: {len(sampled_data)} -> {len(original_items)}")
    
    return original_items

def evaluate_original_gsm_dataset(model, data, log_file, test_mode=False):
    """Evaluate model performance on original GSM dataset."""
    dataset_name = "GSM_Original"
    print(f"\n=== Evaluating {dataset_name} ===")
    
    correct = 0
    total = 0
    results = []
    
    # Determine how many items to process
    if test_mode:
        items_to_process = data[:3]  # Only test 3 cases
        print(f"Test mode: evaluating only 3 cases")
    else:
        items_to_process = data  # Test all cases
        print(f"Full mode: evaluating all {len(items_to_process)} cases")
    
    # Process each item individually
    for i, item in enumerate(tqdm(items_to_process, desc=f"Processing {dataset_name}")):
        # Generate response for this item
        prompt = format_prompt(item['question'])
        response = model.generate(prompt)
        
        try:
            # Extract model's answer
            model_answer = extract_final_answer(response)
            gt_answer = item['ground_truth']
            
            # Check if answer is correct
            is_correct = abs(model_answer - gt_answer) < 1e-6
            if is_correct:
                correct += 1
            
            total += 1
            
            # Log result
            result = {
                'dataset': dataset_name,
                'item_id': i,
                'question': item['question'],
                'prompt': prompt,
                'model_response': response,
                'model_answer': model_answer,
                'ground_truth': gt_answer,
                'is_correct': is_correct,
                'original_answer_text': item['answer_text']
            }
            results.append(result)
            
            # Write to log file
            log_file.write(json.dumps(result, ensure_ascii=False) + '\n')
            log_file.flush()
            
        except Exception as e:
            print(f"Error processing item {i} in {dataset_name}: {e}")
            # Log error case
            result = {
                'dataset': dataset_name,
                'item_id': i,
                'question': item['question'],
                'prompt': prompt,
                'model_response': response,
                'model_answer': None,
                'ground_truth': item['ground_truth'],
                'is_correct': False,
                'error': str(e),
                'original_answer_text': item['answer_text']
            }
            log_file.write(json.dumps(result, ensure_ascii=False) + '\n')
            log_file.flush()
            continue
    
    accuracy = correct / total if total > 0 else 0
    print(f"{dataset_name} Accuracy: {accuracy:.4f} ({correct}/{total})")
    
    return accuracy, correct, total, results

def main():
    parser = argparse.ArgumentParser(description='Evaluate vLLM model on GSM distracted and original datasets')
    parser.add_argument('--api_base', type=str, default='http://localhost:8080/v1', 
                       help='vLLM API base URL')
    parser.add_argument('--model_name', type=str, required=True, 
                       help='Model name to use')
    parser.add_argument('--max_tokens', type=int, default=2000, 
                       help='Maximum tokens to generate')
    parser.add_argument('--seed', type=int, default=42, 
                       help='Random seed')
    parser.add_argument('--log_file', type=str, default='vllm_gsm_distracted_evaluation.log',
                       help='Log file path')
    parser.add_argument('--test_mode', action='store_true', 
                       help='Test mode: only evaluate 3 cases per dataset')
    parser.add_argument('--data_dir', type=str, 
                       default='/home/fuzhizhang.fzz/CoT_Causal_Analysis/data/GSM-Symbolic-extended',
                       help='Directory containing the datasets')
    
    args = parser.parse_args()
    
    # Set random seeds
    random.seed(args.seed)
    np.random.seed(args.seed)
    
    # Initialize model
    model = VLLMModel(args.api_base, args.model_name, args.max_tokens)
    
    # Define file paths
    distracted_dataset_path = os.path.join(args.data_dir, 'gsm_final_dataset.jsonl')
    sampled_data_path = os.path.join(args.data_dir, 'sampled_data_42.json')
    
    # Load datasets
    print("Loading datasets...")
    try:
        # Load distracted dataset
        distracted_data = load_jsonl_data(distracted_dataset_path)
        
        # Load sampled data for creating original dataset
        sampled_data = load_json_data(sampled_data_path)
        
        # Create original GSM dataset
        original_gsm_data = create_original_gsm_dataset(sampled_data)
        
        print("All datasets loaded successfully!")
    except Exception as e:
        print(f"Error loading datasets: {e}")
        return
    
    # Open log file
    with open(args.log_file, 'w', encoding='utf-8') as log_file:
        # Write header
        log_file.write(f"VLLM GSM Distracted vs Original Evaluation Log\n")
        log_file.write(f"Model: {args.model_name}\n")
        log_file.write(f"API Base: {args.api_base}\n")
        log_file.write(f"Data Directory: {args.data_dir}\n")
        log_file.write(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        log_file.write("="*50 + "\n\n")
        
        # Evaluate distracted dataset
        acc_distracted, correct_distracted, total_distracted, results_distracted = evaluate_distracted_dataset(
            model, distracted_data, log_file, args.test_mode
        )
        
        # Evaluate original GSM dataset
        acc_original, correct_original, total_original, results_original = evaluate_original_gsm_dataset(
            model, original_gsm_data, log_file, args.test_mode
        )
        
        # Calculate robustness score (distracted accuracy / original accuracy)
        if acc_original > 0:
            robustness_score = acc_distracted / acc_original
        else:
            robustness_score = 0.0
        
        # Print final results
        print("\n" + "="*60)
        print("FINAL EVALUATION RESULTS")
        print("="*60)
        print(f"GSM Original:   {acc_original:.4f} ({correct_original}/{total_original})")
        print(f"GSM Distracted: {acc_distracted:.4f} ({correct_distracted}/{total_distracted})")
        print(f"Robustness Score: {robustness_score:.4f} (Distracted/Original)")
        print(f"Performance Drop: {(acc_original - acc_distracted):.4f} ({((acc_original - acc_distracted)/acc_original*100):.1f}%)" if acc_original > 0 else "N/A")
        print("="*60)
        
        # Write summary to log file
        log_file.write("\n" + "="*60 + "\n")
        log_file.write("FINAL EVALUATION RESULTS\n")
        log_file.write("="*60 + "\n")
        log_file.write(f"GSM Original:   {acc_original:.4f} ({correct_original}/{total_original})\n")
        log_file.write(f"GSM Distracted: {acc_distracted:.4f} ({correct_distracted}/{total_distracted})\n")
        log_file.write(f"Robustness Score: {robustness_score:.4f} (Distracted/Original)\n")
        if acc_original > 0:
            log_file.write(f"Performance Drop: {(acc_original - acc_distracted):.4f} ({((acc_original - acc_distracted)/acc_original*100):.1f}%)\n")
        log_file.write("="*60 + "\n")
    
    print(f"\nEvaluation completed! Results saved to {args.log_file}")

if __name__ == '__main__':
    main()