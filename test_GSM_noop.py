import json
import re
import time
from tqdm import tqdm
from datasets import load_dataset
import openai
import argparse
import random
import numpy as np

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
        
        print(f'VLLM API with {api_base}, {model_name}, {max_new_tokens}')
    
    def generate(self, prompt, temperature=0.0):
        """Generate response using vLLM API."""
        try:
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

def evaluate_dataset(model, dataset, dataset_name, log_file, test_mode=False):
    """Evaluate model performance on a dataset."""
    print(f"\n=== Evaluating {dataset_name} ===")
    
    correct = 0
    total = 0
    results = []
    
    # Determine how many items to process
    # test_mode = False
    if test_mode:
        items_to_process = dataset['test'].select(range(3))  # Only test 3 cases
        print(f"Test mode: evaluating only 3 cases")
    else:
        items_to_process = dataset['test']  # Test all cases
        print(f"Full mode: evaluating all {len(items_to_process)} cases")
    
    # Process each item individually
    for i, item in enumerate(tqdm(items_to_process, desc=f"Processing {dataset_name}")):
        # Generate response for this item
        # print(item)
        prompt = format_prompt(item['question'])
        response = model.generate(prompt)
        
        try:
            # Extract model's answer
            model_answer = extract_final_answer(response)
            
            # Extract ground truth answer
            if 'answer' in item:
                # For datasets with direct answer field
                if isinstance(item['answer'], str):
                    # Handle cases where answer might be in format "#### 42"
                    if '####' in item['answer']:
                        gt_answer = float(item['answer'].split('####')[-1].strip())
                    else:
                        gt_answer = float(item['answer'])
                else:
                    gt_answer = float(item['answer'])
            else:
                # For datasets with different answer field names
                gt_answer = None
                for key in ['final_answer', 'result', 'solution']:
                    if key in item:
                        gt_answer = float(item[key])
                        break
            
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
            continue
    
    accuracy = correct / total if total > 0 else 0
    print(f"{dataset_name} Accuracy: {accuracy:.4f} ({correct}/{total})")
    
    return accuracy, correct, total, results

def main():
    parser = argparse.ArgumentParser(description='Evaluate vLLM model on GSM datasets')
    parser.add_argument('--api_base', type=str, default='http://localhost:8080/v1', 
                       help='vLLM API base URL')
    parser.add_argument('--model_name', type=str, required=True, 
                       help='Model name to use')
    parser.add_argument('--max_tokens', type=int, default=2000, 
                       help='Maximum tokens to generate')
    parser.add_argument('--seed', type=int, default=42, 
                       help='Random seed')
    parser.add_argument('--log_file', type=str, default='vllm_gsm_evaluation.log',
                       help='Log file path')
    parser.add_argument('--test_mode', action='store_true', 
                       help='Test mode: only evaluate 3 cases per dataset')
    
    args = parser.parse_args()
    
    # Set random seeds
    random.seed(args.seed)
    np.random.seed(args.seed)
    
    # Initialize model
    model = VLLMModel(args.api_base, args.model_name, args.max_tokens)
    
    # Load datasets
    print("Loading datasets...")
    try:
        filepath = "/home/fuzhizhang.fzz/data/GSM-Symbolic"
        ds_main = load_dataset(filepath, name="main")
        ds_p1 = load_dataset(filepath, name="p1")
        ds_p2 = load_dataset(filepath, name="p2")
        print("Datasets loaded successfully!")
    except Exception as e:
        print(f"Error loading datasets: {e}")
        print("Please check the filepath and dataset availability")
        return
    
    # Open log file
    with open(args.log_file, 'w', encoding='utf-8') as log_file:
        # Write header
        log_file.write(f"VLLM GSM Evaluation Log\n")
        log_file.write(f"Model: {args.model_name}\n")
        log_file.write(f"API Base: {args.api_base}\n")
        log_file.write(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        log_file.write("="*50 + "\n\n")
        
        # Evaluate ds_main
        acc_main, correct_main, total_main, results_main = evaluate_dataset(
            model, ds_main, "ds_main", log_file, args.test_mode
        )
        
        # Evaluate ds_p1
        acc_p1, correct_p1, total_p1, results_p1 = evaluate_dataset(
            model, ds_p1, "ds_p1", log_file, args.test_mode
        )
        
        # Evaluate ds_p2
        acc_p2, correct_p2, total_p2, results_p2 = evaluate_dataset(
            model, ds_p2, "ds_p2", log_file, args.test_mode
        )
        
        # Process ds_main to find items with different original_id
        print("\n=== Processing ds_main for original GSM data ===")
        original_gsm_items = []
        
        for i, item in enumerate(ds_main['test']):
            if 'original_id' in item and item['original_id'] != item.get('id', i):
                original_gsm_items.append({
                    'question': item['original_question'],
                    'answer': item['original_answer']
                })
        
        print(f"Found {len(original_gsm_items)} items with different original_id")
        if args.test_mode and len(original_gsm_items) > 3:
            original_gsm_items = original_gsm_items[:3]
            print("Test mode: evaluating only 3 cases for original GSM")
        
        # Evaluate on original GSM data
        if original_gsm_items:
            print("\n=== Evaluating Original GSM Data ===")
            
            correct_gsm = 0
            total_gsm = 0
            
            # Process each item individually
            for i, item in enumerate(tqdm(original_gsm_items, desc="Processing Original GSM")):
                # Generate response for this item
                prompt = format_prompt(item['question'])
                response = model.generate(prompt)
                
                # Always extract model answer; log even on GT parse errors
                model_answer = None
                try:
                    model_answer = extract_final_answer(response)
                except Exception as e:
                    # If model output has no numbers, keep None
                    model_answer = None
                
                gt_answer = None
                is_correct = None
                parse_error = None
                try:
                    ans_val = item['answer']
                    if isinstance(ans_val, str):
                        ans_str = ans_val.replace(',', '').strip()
                        if '####' in ans_str:
                            ans_str = ans_str.split('####')[-1].strip()
                        # Extract last number from the ground-truth string
                        extracted_num = re.findall(r"-?\d+\.?\d*", ans_str)[-1]
                        gt_answer = float(extracted_num)
                    else:
                        gt_answer = float(ans_val)
                    
                    if model_answer is not None and gt_answer is not None:
                        is_correct = abs(model_answer - gt_answer) < 1e-6
                        if is_correct:
                            correct_gsm += 1
                except Exception as e:
                    parse_error = f"GT parse error: {e}"
                finally:
                    total_gsm += 1
                    result = {
                        'dataset': 'original_gsm',
                        'item_id': i,
                        'question': item['question'],
                        'prompt': prompt,
                        'model_response': response,
                        'model_answer': model_answer,
                        'ground_truth': gt_answer,
                        'is_correct': is_correct,
                        'error': parse_error
                    }
                    log_file.write(json.dumps(result, ensure_ascii=False) + '\n')
                    log_file.flush()
            
            acc_gsm = correct_gsm / total_gsm if total_gsm > 0 else 0
            print(f"Original GSM Accuracy: {acc_gsm:.4f} ({correct_gsm}/{total_gsm})")
        else:
            acc_gsm = 0
            correct_gsm = 0
            total_gsm = 0
        
        # Print final results
        print("\n" + "="*60)
        print("FINAL EVALUATION RESULTS")
        print("="*60)
        print(f"ds_main:     {acc_main:.4f} ({correct_main}/{total_main})")
        print(f"ds_p1:       {acc_p1:.4f} ({correct_p1}/{total_p1})")
        print(f"ds_p2:       {acc_p2:.4f} ({correct_p2}/{total_p2})")
        print(f"Original GSM: {acc_gsm:.4f} ({correct_gsm}/{total_gsm})")
        print("="*60)
        
        # Write summary to log file
        log_file.write("\n" + "="*60 + "\n")
        log_file.write("FINAL EVALUATION RESULTS\n")
        log_file.write("="*60 + "\n")
        log_file.write(f"ds_main:     {acc_main:.4f} ({correct_main}/{total_main})\n")
        log_file.write(f"ds_p1:       {acc_p1:.4f} ({correct_p1}/{total_p1})\n")
        log_file.write(f"ds_p2:       {acc_p2:.4f} ({correct_p2}/{total_p2})\n")
        log_file.write(f"Original GSM: {acc_gsm:.4f} ({correct_gsm}/{total_gsm})\n")
        log_file.write("="*60 + "\n")
    
    print(f"\nEvaluation completed! Results saved to {args.log_file}")

if __name__ == '__main__':
    main()
