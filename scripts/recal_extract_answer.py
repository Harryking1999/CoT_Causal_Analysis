# Copyright (c) Guangsheng Bao and Hongbo Zhang.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#
import json
import os
import random
import time
import shutil
from tqdm import tqdm
from utils_api import OpenAIModel
import argparse
import numpy as np
from api_run import extract_answer

def recal_extract_answer_item(args, item, prompt):
    """Re-extract answer for a single item using the new extract_answer logic."""
    output_key = f'{prompt}_output'
    answer_key = f'{prompt}_answer'
    
    # Check if output exists
    if output_key not in item or not item[output_key] or not isinstance(item[output_key], str) or item[output_key].strip() == '':
        print(f"Missing output for item {item.get('id', 'unknown')}, skipping...")
        return item
    
    print(f"Re-extracting answer for item {item.get('id', 'unknown')}...")
    output = item[output_key]
    
    # Extract answer using the new logic
    if args.model_name in ['deepseek-reasoner', 'deepseek-r1', 'Pro/deepseek-ai/DeepSeek-R1', 'DeepSeekR1-Qwen-1_5B','DeepSeekR1-Qwen-7B', 'DeepSeekR1-Qwen-14B', 'DeepSeekR1-Qwen-32B', 'QwQ-32B', 'Qwen2.5-3B-Distill-22000']:
        # For models with thinking output, use the thinking part for extraction
        thinking_key = f'{prompt}_thinking'
        if thinking_key in item and item[thinking_key]:
            pred = extract_answer(item[thinking_key], item, args.dataset, args.interfere_mode)
        else:
            pred = extract_answer(output, item, args.dataset, args.interfere_mode)
    else:
        pred = extract_answer(output, item, args.dataset, args.interfere_mode)
        
    item[f'{prompt}_answer'] = pred
    item[f'{prompt}_result'] = (pred == item['answer'])
    return item

def process_file(args, input_file):
    """Process a single output file."""
    # Create backup of original file
    backup_file = input_file + '.bak'
    shutil.copy2(input_file, backup_file)
    print(f'Created backup file: {backup_file}')
    
    # Load items
    with open(input_file, 'r') as fin:
        items = json.load(fin)
    
    print(f'Processing {len(items)} items in {input_file}')
    
    # Extract prompt from input file name
    # Format: output.{dataset}.{prompt}.{role}.{model}.json
    filename = os.path.basename(input_file)
    parts = filename.split('.')
    if len(parts) < 5:
        print(f"Error: Invalid input file name format: {filename}")
        return
    
    prompt = f"{parts[2]}.{parts[3].replace('_', ' ')}"  # prompt.role with spaces instead of underscores
    
    # Process items
    processed_count = 0
    for item in tqdm(items):
        processed_count += 1
        recal_extract_answer_item(args, item, prompt)
    
    # Write updated results back to file
    with open(input_file, 'w') as fout:
        json.dump(items, fout, indent=2)
    print(f'Updated {processed_count} items in {input_file}')
    
    # Calculate and print accuracy
    correct_count = sum(1 for item in items if item.get(f'{prompt}_result', False))
    total_count = len(items)
    accuracy = correct_count / total_count if total_count > 0 else 0
    print(f'acc_{prompt}: {accuracy:.3f} ({correct_count}/{total_count})')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--outdir', type=str, default='./exp_test/output')
    parser.add_argument('--api_base_num', type=int, default=1)
    parser.add_argument('--api_base', type=str, default='https://api.openai.com/v1')
    parser.add_argument('--api_key', type=str, required=True)
    parser.add_argument('--model_name', type=str, default='gpt-3.5-turbo')
    parser.add_argument('--stop_words', type=str, default='####')
    parser.add_argument('--max_new_tokens', type=int, default=15000)
    parser.add_argument('--input_file', type=str, required=True)
    parser.add_argument('--seed', type=int, default=1)
    parser.add_argument('--dataset', type=str, default='GSM8K')
    parser.add_argument('--interfere_mode', type=int, default=0, help='Interference mode for answer extraction')

    args = parser.parse_args()

    if args.api_base_num == 2:  
        args.api_base = 'https://dashscope.aliyuncs.com/compatible-mode/v1'  
    elif args.api_base_num == 3:
        args.api_base = "https://api.deepseek.com/beta"
    elif args.api_base_num == 4:
        args.api_base = "https://api.siliconflow.cn/v1"
    elif args.api_base_num == 5:
        args.api_base = "http://localhost:8080/v1"
    elif args.api_base_num == 6:
        args.api_base = "http://localhost:8081/v1"
    else:
        args.api_base = 'https://api.chatanywhere.tech/v1'
    
    print(args.api_base)
    print(args.api_key)
    print(f"Using interfere_mode: {args.interfere_mode}")
    random.seed(args.seed)
    np.random.seed(args.seed)

    process_file(args, args.input_file)

if __name__ == '__main__':
    main() 