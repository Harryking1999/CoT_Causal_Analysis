import json
import os
import re
import argparse

def normalize_number(number_str):
    """Normalize number string by removing commas and spaces."""
    return re.sub(r'[,\s]', '', number_str)

def find_answer_in_text(text, answer, find_first=True, dataset=None):
    """Find the answer in the text, handling different number formats.
    Args:
        text: The text to search in
        answer: The answer to find
        find_first: If True, find first occurrence; if False, find last occurrence
        dataset: The dataset name to handle special cases
    """
    # Check if answer is an option (A, B, C, D)
    is_option = answer in ['A', 'B', 'C', 'D', 'a', 'b', 'c', 'd']
    
    # Handle ProofWriter special case
    if dataset == 'ProofWriter':
        # Map between options and their meanings
        option_to_meaning = {
            'A': ['True', 'true'],
            'B': ['False', 'false'],
            'C': ['Unknown', 'unknown'],
            'a': ['True', 'true'],
            'b': ['False', 'false'],
            'c': ['Unknown', 'unknown']
        }
        meaning_to_option = {
            'True': 'A',
            'true': 'A',
            'False': 'B',
            'false': 'B',
            'Unknown': 'C',
            'unknown': 'C'
        }
        
        # If answer is an option, get its meanings
        if is_option:
            answer_meanings = option_to_meaning.get(answer.upper(), [])
        # If answer is a meaning, get its option
        elif answer.lower() in ['true', 'false', 'unknown']:
            answer_meanings = [answer]
            is_option = True
        else:
            answer_meanings = []
    else:
        answer_meanings = []
    
    # Normalize the answer for comparison
    normalized_answer = normalize_number(answer)
    
    # Split text into sentences while preserving separators
    # First split by double newlines
    parts = []
    for part in text.split('\n\n'):
        # Then split by single newlines
        for line in part.split('\n'):
            # Finally split by periods
            sentences = line.split('.')
            sentences_new = []
            for i in sentences:
                sentences_new.append(i)
                sentences_new.append('.')
            parts.extend(sentences_new)
            parts.append('\n')  # Add back the period
        parts.append('\n')  # Add back the double newline
    parts = parts[:-1]  # Remove the last separator
    
    # Find the sentence containing the answer
    answer_positions = []
    for i, part in enumerate(parts):
        if is_option:
            # For options, look for standalone occurrences
            # Match patterns like " A ", " A.", " A,", " A\n", " A" at end of string, or "A)"
            if re.search(rf'(^|\s){answer}(\s|\.|,|\n|$|\))', part):
                answer_positions.append(i)
            # For ProofWriter, also check for True/False/Unknown
            if dataset == 'ProofWriter' and answer_meanings:
                for meaning in answer_meanings:
                    if re.search(rf'(^|\s){meaning}(\s|\.|,|\n|$|\))', part, re.IGNORECASE):
                        answer_positions.append(i)
        else:
            # For non-options (numbers), use the original matching logic
            if normalized_answer in normalize_number(part):
                answer_positions.append(i)
    
    if not answer_positions:
        return None
    
    # Select target position based on answer type
    if answer in ['A', 'B', 'C', 'D']:
        # For ABCD options, always use the last occurrence
        target_pos = answer_positions[-1]
    else:
        # For other types (numbers, True/False/Unknown), use first or last based on find_first
        target_pos = answer_positions[0] if find_first else answer_positions[-1]
    
    # Return all parts before the target position
    ret = ''.join(parts[:target_pos])
    while True:
        if(len(ret) < 2):
            break
        if(ret[-1] in ['\n', '.', ' ']):
            ret = ret[:-1]
        else:
            break
    return ret

def process_file(input_file):
    """Process the input file and create a new file with distilled thinking process."""
    # Load items
    with open(input_file, 'r', encoding='utf-8') as fin:
        items = json.load(fin)
    
    # Extract dataset name from filename
    dataset = None
    if 'ProofWriter' in input_file:
        dataset = 'ProofWriter'
    
    # Process each item
    for item in items:
        thinking = item.get('cot0shot.math teacher_thinking', '')
        answer = item.get('cot0shot.math teacher_answer', '')
        output = item.get('cot0shot.math teacher_output', '')
        
        if not thinking or not answer:
            item['cot0shot.math teacher_thinking_CoT'] = ''
            item['cot0shot.math teacher_output_CoT'] = ''
            continue
        
        # Process thinking field - find first occurrence
        result = find_answer_in_text(thinking, answer, find_first=True, dataset=dataset)
        if result is None:
            item['cot0shot.math teacher_thinking_CoT'] = ""
        else:
            item['cot0shot.math teacher_thinking_CoT'] = result.replace("..", ".")
        
        # Process output field - find last occurrence
        if output:
            result = find_answer_in_text(output, answer, find_first=False, dataset=dataset)
            if result is None:
                item['cot0shot.math teacher_output_CoT'] = ""
            else:
                item['cot0shot.math teacher_output_CoT'] = result.replace("..", ".")
    
    # Create output filename
    base_name = os.path.splitext(input_file)[0]
    output_file = f"{base_name}.thinking.json"
    
    # Write to new file
    with open(output_file, 'w', encoding='utf-8') as fout:
        json.dump(items, fout, indent=2)
    
    print(f"Processed {len(items)} items and wrote to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_file', type=str, required=True, help='Input JSON file to process')
    args = parser.parse_args()
    
    # Process file
    process_file(args.input_file) 