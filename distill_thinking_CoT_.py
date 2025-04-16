import json
import os
import re
import argparse

def normalize_number(number_str):
    """Normalize number string by removing commas and spaces."""
    return re.sub(r'[,\s]', '', number_str)

def find_answer_in_text(text, answer, find_first=True):
    """Find the answer in the text, handling different number formats.
    Args:
        text: The text to search in
        answer: The answer to find
        find_first: If True, find first occurrence; if False, find last occurrence
    """
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
        if normalized_answer in normalize_number(part):
            answer_positions.append(i)
    
    if not answer_positions:
        return None
    
    # For thinking, use first occurrence; for output, use last occurrence
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
    with open(input_file, 'r') as fin:
        items = json.load(fin)
    
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
        result = find_answer_in_text(thinking, answer, find_first=True)
        if result is None:
            item['cot0shot.math teacher_thinking_CoT'] = ""
        else:
            item['cot0shot.math teacher_thinking_CoT'] = result
        
        # Process output field - find last occurrence
        if output:
            result = find_answer_in_text(output, answer, find_first=False)
            if result is None:
                item['cot0shot.math teacher_output_CoT'] = ""
            else:
                item['cot0shot.math teacher_output_CoT'] = result
    
    # Create output filename
    base_name = os.path.splitext(input_file)[0]
    output_file = f"{base_name}.thinking.json"
    
    # Write to new file
    with open(output_file, 'w') as fout:
        json.dump(items, fout, indent=2)
    
    print(f"Processed {len(items)} items and wrote to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_file', type=str, required=True, help='Input JSON file to process')
    args = parser.parse_args()
    
    # Process file
    process_file(args.input_file) 