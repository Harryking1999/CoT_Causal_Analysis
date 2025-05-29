import json
import argparse

def process_files(file1_name):

    file1_path = './exp_cot/output/' + file1_name


    with open(file1_path, 'r') as f:
        data = json.load(f)

    replace_field = 'cot0shot.math teacher_thinking_CoT'
    new_field = 'cot0shot.math teacher_othercot'
    # Circular shift of 'field_name'
    field_values = [d[replace_field] for d in data]
    results = [d['answer'] for d in data]

    for i in range(len(data)):
        data[i]['cot0shot.randomreason_othercot_answer'] = results[i - 1]
        data[i][new_field] = field_values[i - 1]  # previous item's value (circular)

    # output_file = f"{file1_name}.replaced.json"
    # output_path = './exp_cot/output/' + output_file

    with open(file1_path, 'w') as f:
        json.dump(data, f, indent=2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', type=str, required=True, help='input JSON file (will have its reason field replaced)')
    args = parser.parse_args()
    
    # Process files
    process_files(args.file) 