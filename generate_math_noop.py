import json
import os
from pathlib import Path
import time
import openai
from tqdm import tqdm

# =============================================================================
# API CONFIGURATION - MODIFY HERE
# =============================================================================
OPENAI_API_KEY = "sk-q3Uf5DW0HY4HKLiw7EJNNkyErdxfXXAN6CZARkXyArNLitxa"  # Replace with your actual API key
OPENAI_API_BASE = "https://api.chatanywhere.tech/v1"  # Custom API base URL
MODEL_NAME = "gpt-4.1-mini"  # Model to use
REQUEST_DELAY = 1.0  # Delay between requests in seconds
# =============================================================================

class MATH500Rewriter:
    def __init__(self):
        # Set up OpenAI API (version 0.28.0 style)
        openai.api_key = OPENAI_API_KEY
        openai.api_base = OPENAI_API_BASE  # Set custom API base here
        
        self.rewrite_prompt = """Please rewrite the following MATH500 problem with these requirements:

1. **Keep Original Text Intact**: All original sentences must remain completely unchanged. Only INSERT additional numerical conditions or constraints where appropriate
2. **Only Add Numerical Distractors**: Add 1-2 extra numerical values that seem mathematically relevant but are not needed for the solution
3. **No Scenario Changes**: Do NOT change the setting, add physics contexts, or wrap in real-world applications
4. **Maintain Original Voice**: Keep the same mathematical language and problem presentation style

Guidelines:
- Add distractors like: extra coordinates, unused constants, additional measurements, irrelevant parameters
- Do NOT add: physics backgrounds, engineering contexts, real-world stories, or scenario changes
- Do NOT explicitly state that information is unused or irrelevant
- The added information should integrate naturally into the existing mathematical framework

Original Problem: {problem}

Solution: {solution}

Please provide ONLY the rewritten problem, without any explanation or additional text."""

    def rewrite_problem(self, problem, solution):
        """Rewrite problem using OpenAI API (version 0.28.0)"""
        try:
            response = openai.ChatCompletion.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "user", "content": self.rewrite_prompt.format(problem=problem, solution=solution)}
                ],
                temperature=0.7,
                max_tokens=1500,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
            
            rewritten = response.choices[0].message.content.strip()
            return rewritten
            
        except openai.error.RateLimitError:
            print("\n[WARNING] Rate limit exceeded, waiting 60 seconds...")
            time.sleep(60)
            return self.rewrite_problem(problem, solution)  # Retry
            
        except openai.error.APIError as e:
            print(f"\n[ERROR] OpenAI API error: {e}")
            return f"[ERROR - API FAILED] {problem}"
            
        except openai.error.AuthenticationError:
            print("\n[ERROR] Authentication failed. Please check your API key.")
            return f"[ERROR - AUTH FAILED] {problem}"
            
        except Exception as e:
            print(f"\n[ERROR] Unexpected error rewriting problem: {e}")
            return f"[ERROR - UNKNOWN] {problem}"

    def count_lines(self, file_path):
        """Count total lines in the file for progress bar"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return sum(1 for _ in f)
        except Exception as e:
            print(f"[ERROR] Error counting lines: {e}")
            return 0

    def process_jsonl_file(self, input_path, output_path):
        """Process the entire JSONL file with tqdm progress bar"""
        # Create output directory if it doesn't exist
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Count total lines for progress bar
        total_lines = self.count_lines(input_path)
        if total_lines == 0:
            print("[ERROR] Could not count lines in input file")
            return False
        
        processed_count = 0
        error_count = 0
        
        print("=" * 60)
        print("MATH500 Problem Rewriter")
        print("=" * 60)
        print(f"Input file: {input_path}")
        print(f"Output file: {output_path}")
        print(f"API Base: {OPENAI_API_BASE}")
        print(f"Model: {MODEL_NAME}")
        print(f"Total problems to process: {total_lines}")
        print(f"Delay between requests: {REQUEST_DELAY}s")
        print("=" * 60)
        
        try:
            with open(input_path, 'r', encoding='utf-8') as infile, \
                 open(output_path, 'w', encoding='utf-8') as outfile:
                
                # Create progress bar
                pbar = tqdm(
                    total=total_lines,
                    desc="Processing problems",
                    unit="problem",
                    ncols=100,
                    bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]"
                )
                
                for line_num, line in enumerate(infile, 1):
                    try:
                        # Parse JSON line
                        item = json.loads(line.strip())
                        
                        # Store original problem
                        original_problem = item['problem']
                        original_solution = item['solution']
                        item['original_problem'] = original_problem
                        
                        # Update progress bar description with current item info
                        subject = item.get('subject', 'Unknown')
                        level = item.get('level', '?')
                        pbar.set_description(f"Processing {subject} L{level}")
                        
                        # Rewrite the problem
                        rewritten_problem = self.rewrite_problem(original_problem, original_solution)
                        item['problem'] = rewritten_problem
                        
                        # Write to output file
                        outfile.write(json.dumps(item, ensure_ascii=False) + '\n')
                        outfile.flush()  # Ensure data is written immediately
                        
                        processed_count += 1
                        
                        # Update progress bar with additional info
                        pbar.set_postfix({
                            'Success': processed_count,
                            'Errors': error_count,
                            'Len': f"{len(original_problem)}->{len(rewritten_problem)}"
                        })
                        pbar.update(1)
                        
                        # Add delay to respect rate limits
                        if REQUEST_DELAY > 0:
                            time.sleep(REQUEST_DELAY)
                        
                    except json.JSONDecodeError as e:
                        error_count += 1
                        pbar.set_postfix({
                            'Success': processed_count,
                            'Errors': error_count,
                            'Last_Error': 'JSON_Parse'
                        })
                        pbar.update(1)
                        continue
                        
                    except KeyboardInterrupt:
                        pbar.close()
                        print(f"\n[INTERRUPTED] Process interrupted by user")
                        print(f"Processed {processed_count} items before interruption")
                        break
                        
                    except Exception as e:
                        error_count += 1
                        pbar.set_postfix({
                            'Success': processed_count,
                            'Errors': error_count,
                            'Last_Error': 'Processing'
                        })
                        pbar.update(1)
                        continue
                
                pbar.close()
                        
        except FileNotFoundError:
            print(f"[ERROR] Input file not found: {input_path}")
            return False
            
        except Exception as e:
            print(f"[ERROR] Error processing file: {e}")
            return False
            
        print("\n" + "=" * 60)
        print("PROCESSING COMPLETE")
        print("=" * 60)
        print(f"[SUCCESS] Successfully processed: {processed_count} items")
        print(f"[ERROR] Errors encountered: {error_count} items")
        print(f"[STATS] Success rate: {processed_count/(processed_count+error_count)*100:.1f}%" if (processed_count+error_count) > 0 else "N/A")
        print(f"[OUTPUT] Output saved to: {output_path}")
        print("=" * 60)
        
        return True

def main():
    """Main execution function"""
    
    # Check tqdm installation
    try:
        from tqdm import tqdm
    except ImportError:
        print("[ERROR] tqdm is not installed")
        print("        Please install it with: pip install tqdm")
        return
    
    # Check API key configuration
    if OPENAI_API_KEY == "YOUR_API_KEY_HERE":
        print("[ERROR] Please set your OpenAI API key in the OPENAI_API_KEY variable")
        print("        Find the line: OPENAI_API_KEY = \"YOUR_API_KEY_HERE\"")
        print("        Replace with: OPENAI_API_KEY = \"sk-your-actual-key-here\"")
        return
    
    # Initialize the rewriter
    rewriter = MATH500Rewriter()
    
    # File paths
    input_file = "./data/MATH500/test.jsonl"
    output_file = "./data/MATH500_noop/test.jsonl"
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"[ERROR] Input file not found: {input_file}")
        print("        Please make sure the file exists and try again.")
        return
    
    # Process the file
    success = rewriter.process_jsonl_file(
        input_path=input_file,
        output_path=output_file
    )
    
    if success:
        print("[COMPLETE] All done! The rewritten problems are ready.")
    else:
        print("[FAILED] Processing failed! Check the error messages above.")

if __name__ == "__main__":
    main()