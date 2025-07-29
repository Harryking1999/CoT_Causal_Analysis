import json
import os
import re
import argparse

def normalize_number(number_str):
    """Normalize number string by removing commas and spaces."""
    # return re.sub(r'[,\s]', '', number_str)
    return re.sub(r'[,!\s\\]', '', number_str)

def find_answer_in_text(text, answer, find_first=True, dataset=None):
    """Find the answer in the text, handling different number formats.
    Args:
        text: The text to search in
        answer: The answer to find
        find_first: If True, find first occurrence; if False, find last occurrence
        dataset: The dataset name to handle special cases
    """
    # Check if answer is an option (A, B, C, D)
    # print("answer: ", answer)
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
    elif dataset == 'LOGIQA':
        # LOGIQA has ABCD options, need to handle them specially
        # For LOGIQA, we need to ensure we match the exact option letter
        # and handle cases where the answer might be in different formats
        if is_option:
            # LOGIQA options are just A, B, C, D - no meaning mapping needed
            answer_meanings = []
            # Ensure answer is uppercase for consistent matching
            answer = answer.upper()
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
    # print(parts)
    
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
            # For LOGIQA, also check for option patterns like "A)", "A.", "A," etc.
            elif dataset == 'LOGIQA':
                # print("part: ", part)
                # print("answer: ", answer)
                # LOGIQA specific patterns: "A)", "A.", "A,", "A ", "A\n", "A" at end, "**Answer: A**"
                # print(re.search(rf'(^|\s|:|\*){answer}(\s|\.|,|\n|$|\)|\*)', part, re.IGNORECASE))
                if re.search(rf'(^|\s|:|\*){answer}(\s|\.|,|\n|$|\)|\*)', part, re.IGNORECASE):
                    answer_positions.append(i)
        else:
            # For non-options (numbers), use the original matching logic
            if normalized_answer in normalize_number(part):
                # print("ind: ", i)
                # print("part: ", normalize_number(part))
                # print("normalized_answer: ", normalized_answer)
                answer_positions.append(i)
    
    if not answer_positions:
        # print("no answer")
        return text
    
    # Select target position based on answer type
    if answer in ['A', 'B', 'C', 'D']:
        # For ABCD options, always use the last occurrence
        find_first = False
    
    if find_first:
        # For find_first=True, use first occurrence
        target_pos = answer_positions[0]
        # Return all parts before the target position
        ret = ''.join(parts[:target_pos])
    else:
        # For find_first=False, implement new logic
        # Start with the last occurrence
        target_pos = answer_positions[-1]
        
        # Function to check if a part contains the answer
        def contains_answer(part):
            # if len(part.strip()) < 5:
            #     return False
            if is_option:
                if re.search(rf'(^|\s){answer}(\s|\.|,|\n|$|\))', part):
                    return True
                if dataset == 'ProofWriter' and answer_meanings:
                    for meaning in answer_meanings:
                        if re.search(rf'(^|\s){meaning}(\s|\.|,|\n|$|\))', part, re.IGNORECASE):
                            return True
                elif dataset == 'LOGIQA':
                    # LOGIQA specific option matching with case-insensitive search
                    if re.search(rf'(^|\s|:|\*){answer}(\s|\.|,|\n|$|\)|\*)', part, re.IGNORECASE):
                        return True
                return False
            else:
                return normalized_answer in normalize_number(part)
        
        # Start from the last answer position and go backwards
        final_pos = target_pos
        # print("target_pos: ", parts[target_pos])
        for i in range(target_pos - 1, -1, -1):
            # print("parts: ", parts[i])
            if contains_answer(parts[i]):
                final_pos = i
                # print("final_pos: ", i)
                break
            elif len(parts[i]) > 5:
                break
        
        # Return all parts before the final position
        ret = ''.join(parts[:final_pos])
    
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
    key_prefix = None
    if('newdirectbase' in input_file):
        key_prefix = 'newdirectbase'
    elif('newdirect' in input_file):
        key_prefix = 'newdirect'
    else:
        key_prefix = 'cot0shot'

    flag_openr1_pattern = False
    # if(".Qwen2.5-3B-GRPO" in input_file or ".Qwen2.5-3B-SFT-GRPO" in input_file):
    #     flag_openr1_pattern = True
    # if("Qwen2.5-3B-SFT-GRPO-200." in input_file or "Qwen2.5-3B-SFT-GRPO-400." in input_file):
    #     flag_openr1_pattern = False
    
    # Extract dataset name from filename
    # print(items[0:2])
    dataset = None
    if 'ProofWriter' in input_file:
        dataset = 'ProofWriter'
    elif 'LOGIQA' in input_file:
        dataset = 'LOGIQA'
    
    # Process each item
    for item in items:
        thinking = item.get(key_prefix + '.math teacher_thinking', '')
        answer = item.get(key_prefix + '.math teacher_answer', '')
        output = item.get(key_prefix + '.math teacher_output', '')
        
        if not thinking and not answer:
            item[key_prefix + '.math teacher_thinking_CoT'] = ''
            item[key_prefix + '.math teacher_output_CoT'] = ''
            # print("continue")
            continue

        if not thinking:
            item[key_prefix + '.math teacher_thinking_CoT'] = ''
        else:
            # Process thinking field - find first occurrence
            result = find_answer_in_text(thinking, answer, find_first=True, dataset=dataset)
            if result is None:
                item[key_prefix + '.math teacher_thinking_CoT'] = ""
            else:
                item[key_prefix + '.math teacher_thinking_CoT'] = result.replace("..", ".")
        
        # Process output field - find last occurrence
        if output:
            if(flag_openr1_pattern):
                output = output.split("</think>")[0]
            result = find_answer_in_text(output, answer, find_first=False, dataset=dataset)
            if result == "." or result == ".." and len(output.split(".") > 1):
                result = output.split(".")[0]
            if result is None:
                item[key_prefix + '.math teacher_output_CoT'] = ""
            else:
                item[key_prefix + '.math teacher_output_CoT'] = result.replace("..", ".")
        else:
            item[key_prefix + '.math teacher_output_CoT'] = ""
    
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