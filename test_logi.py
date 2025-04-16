import json
import os

def analyze_results(input_file):
    """Analyze the results from the output file."""
    # Load items
    with open(input_file, 'r') as fin:
        items = json.load(fin)
    
    # Count total items
    total_count = len(items)
    
    # Count correct predictions
    correct_count = sum(1 for item in items if item.get('cot0shot.math teacher_result', False))
    
    # Count empty outputs
    empty_output_count = sum(1 for item in items if not item.get('cot0shot.math teacher_output', '').strip())
    
    # Calculate accuracy
    accuracy = correct_count / total_count if total_count > 0 else 0
    
    # Calculate empty output ratio
    empty_ratio = empty_output_count / total_count if total_count > 0 else 0
    
    # Print results
    print(f"Total items: {total_count}")
    print(f"Correct predictions: {correct_count}")
    print(f"Accuracy: {accuracy:.3f} ({correct_count}/{total_count})")
    print(f"Empty outputs: {empty_output_count}")
    print(f"Empty output ratio: {empty_ratio:.3f} ({empty_output_count}/{total_count})")

if __name__ == "__main__":
    # Set directory and file
    outdir = "./exp_cot/output"
    input_file = "output.Addition_6.cot0shot.math_teacher.deepseek-reasoner.json"
    input_path = os.path.join(outdir, input_file)
    
    # Analyze results
    analyze_results(input_path) 