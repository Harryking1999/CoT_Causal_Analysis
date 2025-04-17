import json
import os
import argparse
import shutil
import re
from utils import extract_logic

def calculate_accuracy(data, prompt, role):
    total = len(data)
    correct = 0
    for item in data:
        answer_field = f"{prompt}.{role}_answer"
        # print(answer_field)
        if item.get(answer_field) is not None and item.get('answer') is not None:
            if item[answer_field] == item['answer']:
                correct += 1
    return correct, total

def reprocess_file(input_file):
    # Check if the file is for ProofWriter or LOGIQA
    if 'ProofWriter' not in input_file and 'LOGIQA' not in input_file:
        print(f"Error: Only ProofWriter and LOGIQA datasets are allowed. Skipping {input_file}")
        return

    # Extract prompt and role from filename
    filename = os.path.basename(input_file)
    parts = filename.split('.')
    if len(parts) < 4:
        print(f"Error: Invalid filename format. Expected format: output.dataset.prompt.role.model.json")
        return
    prompt = parts[2]
    role = parts[3].replace('_', ' ')  # Keep the original role with underscores

    # Create backup file
    backup_file = input_file + '.bak'
    # if not os.path.exists(backup_file):
    shutil.copy2(input_file, backup_file)
    print(f"Created backup file: {backup_file}")

    # Load the data
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Calculate initial accuracy
    initial_correct, total = calculate_accuracy(data, prompt, role)
    print(f"Initial accuracy: {initial_correct/total:.3f} ({initial_correct}/{total})")

    # Load and calculate source file accuracy
    with open(backup_file, 'r', encoding='utf-8') as f:
        source_data = json.load(f)
    source_correct, source_total = calculate_accuracy(source_data, prompt, role)
    print(f"Source file accuracy: {source_correct/source_total:.3f} ({source_correct}/{source_total})")

    # Process each item
    modified_count = 0
    for item in data:
        # Check if answer is string "None" or empty
        answer_field = f"{prompt}.{role}_answer"
        if item.get(answer_field) in ["None", ""]:
            # Get the output field
            output_field = f"{prompt}.{role}_output"
            output = item.get(output_field, '')
            if output:
                try:
                    # Extract new answer using extract_logic
                    new_answer = extract_logic(output)
                    if new_answer is not None:
                        item[answer_field] = str(new_answer)
                        modified_count += 1
                except Exception as e:
                    print(f"Error processing item: {e}")

    # Save the modified data back to the file
    if modified_count > 0:
        with open(input_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Processed {input_file}: Modified {modified_count} items")
        
        # Calculate final accuracy
        final_correct, total = calculate_accuracy(data, prompt, role)
        print(f"Final accuracy: {final_correct/total:.3f} ({final_correct}/{total})")
        print(f"Accuracy improvement: {(final_correct - initial_correct)/total:.3f}")
    else:
        print(f"Processed {input_file}: No modifications needed")

def main():
    parser = argparse.ArgumentParser(description='Reprocess logic answers for ProofWriter and LOGIQA datasets')
    parser.add_argument('input_file', type=str, help='Path to the input JSON file')
    args = parser.parse_args()

    # Check if the file exists
    if not os.path.exists(args.input_file):
        print(f"Error: File {args.input_file} does not exist")
        return

    # Process the file
    reprocess_file(args.input_file)

if __name__ == '__main__':
    main() 