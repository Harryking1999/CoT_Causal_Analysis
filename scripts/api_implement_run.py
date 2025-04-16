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

def needs_retry(item, prompt):
    """Check if an item needs retry based on empty output or answer fields."""
    output_key = f'{prompt}_output'
    answer_key = f'{prompt}_answer'
    print(output_key)
    return (output_key in item and (not item[output_key] or item[output_key].strip() == '')) or \
           (answer_key in item and (not item[answer_key] or item[answer_key].strip() == ''))

def retry_item(args, item, prompt, openai_api):
    """Retry API call for a single item if needed."""
    if not needs_retry(item, prompt):
        return item
        
    message = item[f'{prompt}_input']
    cnt_exp = 0
    
    while True:
        if cnt_exp > 5:
            print(f"Failed to get response after 5 retries for item {item['id']}")
            return item
            
        try:
            output = openai_api.generate(message)
            
            # Extract answer
            if args.model_name in ['deepseek-reasoner', 'deepseek-r1', 'Pro/deepseek-ai/DeepSeek-R1']:
                pred = extract_answer(output[0], item, args.dataset)
                item[f'{prompt}_output'] = output[0]
                item[f'{prompt}_thinking'] = output[1]
            else:
                pred = extract_answer(output, item, args.dataset)
                item[f'{prompt}_output'] = output
                
            item[f'{prompt}_answer'] = pred
            item[f'{prompt}_result'] = (pred == item['answer'])
            return item
            
        except Exception as ex:
            print(ex)
            print('Sleep 10 seconds before retry ...')
            time.sleep(10)
            cnt_exp += 1

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
    
    # Initialize API
    openai_api = OpenAIModel(args.api_base, args.api_key, args.model_name, args.stop_words, args.max_new_tokens)
    
    # Process items
    retry_count = 0
    for item in tqdm(items):
        if needs_retry(item, prompt):
            retry_count += 1
            retry_item(args, item, prompt, openai_api)
    
    if retry_count > 0:
        # Write updated results back to file
        with open(input_file, 'w') as fout:
            json.dump(items, fout, indent=2)
        print(f'Updated {retry_count} items in {input_file}')
    else:
        print(f'No items needed retry in {input_file}')
    
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
    parser.add_argument('--max_new_tokens', type=int, default=2048)
    parser.add_argument('--input_file', type=str, required=True)
    parser.add_argument('--seed', type=int, default=1)
    parser.add_argument('--dataset', type=str, default='GSM8K')

    args = parser.parse_args()

    if args.api_base_num == 2:  
        args.api_base = 'https://dashscope.aliyuncs.com/compatible-mode/v1'  
    elif args.api_base_num == 3:
        args.api_base = "https://api.deepseek.com/beta"
    elif args.api_base_num == 4:
        args.api_base = "https://api.siliconflow.cn/v1"
    else:
        args.api_base = 'https://api.chatanywhere.tech/v1'
    
    print(args.api_base)
    print(args.api_key)
    random.seed(args.seed)
    np.random.seed(args.seed)

    process_file(args, args.input_file)

if __name__ == '__main__':
    main() 