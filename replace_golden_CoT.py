import json
import os
import argparse

def process_files(file1_path, file2_path):
    """Process two files and create a new file with replaced fields.
    
    Args:
        file1_path: Path to the first file (will have its reason field replaced)
        file2_path: Path to the second file (source of xxx_thinking_CoT field)
    """
    # Load both files
    file1_path = './exp_cot/output/' + file1_path
    file2_path = './exp_cot/output/' + file2_path
    with open(file1_path, 'r', encoding='utf-8') as f1:
        items1 = json.load(f1)
    
    with open(file2_path, 'r', encoding='utf-8') as f2:
        items2 = json.load(f2)
    
    # Check if both files have the same number of items
    if len(items1) != len(items2):
        print(f"Warning: Files have different number of items ({len(items1)} vs {len(items2)})")
    
    # Process each item
    for i, (item1, item2) in enumerate(zip(items1, items2)):
        # Find the xxx_thinking_CoT field in item2
        thinking_cot_field = None
        for key in item2.keys():
            if key.endswith('_thinking_CoT'):
                thinking_cot_field = key
                break
        
        if thinking_cot_field is None:
            print(f"Warning: No _thinking_CoT field found in item {i} of {file2_path}")
            continue
        
        # Replace the reason field in item1 with the thinking_cot field from item2
        item1['reason'] = item2[thinking_cot_field]
    
    # Create output filename
    base_name = os.path.splitext(file1_path)[0]
    output_file = f"{base_name}.replace_golden.json"
    
    # Write to new file
    with open(output_file, 'w', encoding='utf-8') as fout:
        json.dump(items1, fout, indent=2)
    
    print(f"Processed {len(items1)} items and wrote to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--file1', type=str, required=True, help='First input JSON file (will have its reason field replaced)')
    parser.add_argument('--file2', type=str, required=True, help='Second input JSON file (source of xxx_thinking_CoT field)')
    args = parser.parse_args()
    
    # Process files
    process_files(args.file1, args.file2) 