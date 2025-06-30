import time
import pandas as pd
import json 
import re
from utils_api import OpenAIModel
import argparse
from tqdm import tqdm

def extract_boxed_content(text):
    """
    Extract content from \boxed{} tags
    Handles nested braces properly using stack-based approach
    """
    # Find the start of \boxed{
    print("text_before_extract: ", text)
    start = text.find('\\boxed{')
    if start == -1:
        # Fallback: try to find "oxed{" in case \b was interpreted as backspace
        start = text.find('oxed{')
        if start == -1:
            return text
        else:
            # Adjust start position to account for missing \b
            start += 5  # length of 'oxed{'
    else:
        start += 7  # length of '\boxed{'
    
    brace_count = 1
    i = start
    
    while i < len(text) and brace_count > 0:
        if text[i] == '{':
            brace_count += 1
        elif text[i] == '}':
            brace_count -= 1
        i += 1
    
    if brace_count == 0:
        print("text_after_extract: ", text[start:i-1])
        return text[start:i-1]  # Return content between braces, excluding the closing brace
    else:
        print("text_after_extract: ", text)
        return text  # Return original text if braces are not balanced

def is_answer_in_sentence(sentence, target_answer):
    """
    Check if target_answer appears in sentence with proper boundaries
    For numeric answers, ensure they are not part of larger numbers
    """
    # If target_answer is numeric, check for word boundaries
    if target_answer.replace('.', '').replace('-', '').isdigit():
        # Use word boundary matching for numeric answers
        import re
        pattern = r'\b' + re.escape(target_answer) + r'\b'
        return bool(re.search(pattern, sentence))
    else:
        # For non-numeric answers, use simple string matching
        return target_answer in sentence

def split_and_restore_sentences(text, target_answer, find_last=False):
    """
    Split text by sentences and restore CoT content
    find_last: True to find last occurrence, False to find first occurrence
    """
    # Split by both \n\n and .
    sentences = []
    current_sentence = ""
    
    # First split by \n\n
    parts = text.split('\n\n')
    for part in parts:
        if '.' in part:
            # Further split by .
            sub_parts = part.split('.')
            for i, sub_part in enumerate(sub_parts):
                if i == 0:
                    current_sentence = sub_part
                else:
                    current_sentence += '.' + sub_part
                if current_sentence.strip():
                    sentences.append(current_sentence.strip())
                    current_sentence = ""
        else:
            if part.strip():
                sentences.append(part.strip())
    
    # Find the target sentence
    target_index = -1
    if find_last:
        # Find last occurrence
        for i in range(len(sentences) - 1, -1, -1):
            if is_answer_in_sentence(sentences[i], target_answer):
                target_index = i
                break
    else:
        # Find first occurrence
        for i, sentence in enumerate(sentences):
            if is_answer_in_sentence(sentence, target_answer):
                target_index = i
                break
    
    if target_index == -1:
        return text  # Return original text if not found
    
    # Restore content before target sentence
    if find_last:
        # For _output_CoT: include everything up to (but not including) the last occurrence
        # If the meaningful sentence before the answer sentence also contains the answer, remove it too
        result_sentences = sentences[:target_index]
        
        # Find the meaningful previous sentence (skip sentences with only symbols)
        meaningful_prev_index = target_index - 1
        while meaningful_prev_index >= 0:
            # Check if sentence contains meaningful content (not just symbols)
            sentence_content = sentences[meaningful_prev_index].strip()
            # Remove common symbols and check if there's meaningful content left
            meaningful_content = ''.join(c for c in sentence_content if c.isalnum() or c.isspace())
            if meaningful_content.strip():  # If there's meaningful content
                if is_answer_in_sentence(sentences[meaningful_prev_index], target_answer):
                    result_sentences = sentences[:meaningful_prev_index]
                break
            meaningful_prev_index -= 1
    else:
        # For _thinking_CoT: include everything up to (but not including) the first occurrence
        result_sentences = sentences[:target_index]
    
    # Restore original formatting
    result = '\n\n'.join(result_sentences)
    return result

def openai_extract_answer(model, response: str, correct_answer: str, api_key: str) -> str:
    """
    Extracts the answer from the OpenAI response.
    """
    openai_api2 = OpenAIModel(
        model_name=model,
        max_new_tokens=3000,
        API_BASE="https://api.chatanywhere.tech/v1",
        API_KEY=api_key,
        stop_words='####',
    )

    prompt = f"""You are tasked with extracting the final answer from a mathematical solution. Your job is to identify the model's final answer and place it inside \boxed{{}} tags. 

    Important requirements:
    1. Extract ONLY the final answer - do not output \boxed{{}} anywhere else in your response
    2. The extracted answer must maintain the EXACT same format as it appears in the original text (preserve all formatting, spacing, symbols, etc.)
    3. The extracted string must be searchable in the original text - it should be a direct copy
    4. Do not modify, simplify, or reformat the answer in any way

    Please read the following solution and extract the final answer:

    {response}

    Place the final answer in \boxed{{}} format."""

    cnt_total = 0
    cnt_exp = 0
    result = None
    while True:
        if(cnt_exp > 3):
            break
        try:
            result = openai_api2.chat_generate(prompt, temperature=0.0)
            # print(result)
            # print("success id: ", cnt_total)
            cnt_total += 1
            break
        except Exception as ex:
            print(ex)
            print('Sleep 10 seconds before retry ...')
            time.sleep(10)
            cnt_exp += 1
    
    # Extract content from \boxed{} tags
    if result is None:
        return ""
    return extract_boxed_content(result)

def openai_extract_thinking_answer(model, response: str, correct_answer: str, api_key: str) -> str:
    """
    Extracts the answer from the OpenAI response.
    """
    openai_api2 = OpenAIModel(
        model_name=model,
        max_new_tokens=3000,
        API_BASE="https://api.chatanywhere.tech/v1",
        API_KEY=api_key,
        stop_words='####',
    )

    prompt = f"""You are tasked with extracting the final answer from a mathematical thinking process. Your job is to:

    1. First, identify the final answer in the thinking process (usually at the end)
    2. Then, find the FIRST occurrence of this answer (or its equivalent form) in the thinking process
    3. Extract that first occurrence exactly as it appears, preserving all formatting and notation
    4. Place it in \boxed{{}} tags

    Important requirements:
    1. The final answer and first occurrence may have slightly different formats but represent the same mathematical value
    2. Examples of equivalent forms:
       - "1/2" and "0.5" and "\\frac{{1}}{{2}}"
       - "2x + 3" and "3 + 2x"
       - "\\sqrt{{4}}" and "2"
    3. For infinite decimals and fractions: if the difference is within 3 decimal places (0.001), they are considered equivalent
       - "0.333..." and "1/3" are equivalent
       - "0.666..." and "2/3" are equivalent
       - "3.14159" and "\\pi" are equivalent
    4. Extract ONLY the first occurrence - do not output \boxed{{}} anywhere else
    5. The extracted string must be searchable in the original text - it should be a direct copy
    6. Do not modify, simplify, or reformat the answer in any way
    7. Preserve the exact notation, spacing, and formatting as it appears in the first occurrence

    Please read the following thinking process and extract the first occurrence of the final answer:

    {response}

    Place the first occurrence of the final answer in \boxed{{}} format."""

    cnt_total = 0
    cnt_exp = 0
    result = None
    while True:
        if(cnt_exp > 3):
            break
        try:
            result = openai_api2.chat_generate(prompt, temperature=0.0)
            # print(result)
            # print("success id: ", cnt_total)
            cnt_total += 1
            break
        except Exception as ex:
            print(ex)
            print('Sleep 10 seconds before retry ...')
            time.sleep(10)
            cnt_exp += 1
    
    # Extract content from \boxed{} tags
    if result is None:
        return ""
    return extract_boxed_content(result)

def compare_answer(model: str, response: str, correct_answer: str, api_key: str) -> str:
    """
    Extracts the answer from the OpenAI response.
    """
    openai_api2 = OpenAIModel(
        model_name=model,
        max_new_tokens=3000,
        API_BASE="https://api.chatanywhere.tech/v1",
        API_KEY=api_key,
        stop_words='####',
    )

    # prompt = f"""
    # You are a grader to judge the following response based on the reasoning process and the gold (given answer).Any discrepancy beyond the sixth decimal place isn’t considered an error. Ignore formatting issues. Your final answer should be $\boxed{True}$ or $\boxed{False}$.
    # Student answer:
    # {response}
    # Gold answer:
    # {correct_answer}
    # """
    prompt = f"""
    You are tasked with comparing two mathematical expressions to determine if they are equivalent. 

    Comparison rules:
    1. For numerical values: Allow up to 3 decimal places of error tolerance (differences within 0.001 are acceptable)
    2. For fractions: Compare after reducing to lowest terms
    3. For expressions with variables: Check algebraic equivalence
    4. Consider different but equivalent representations (e.g., 0.5 and 1/2, or 2π and 2*pi)

    I will provide you with:
    - Standard answer
    - Model answer

    Determine if these two answers are mathematically equivalent according to the rules above. Respond with either "true" (if equivalent) or "false" (if not equivalent) inside \boxed{{}} tags.

    Standard answer: {correct_answer}
    Model answer: {response}

    Place your judgment (true or false) in \boxed{{}} format."""
    # messages = [
    #     {
    #         "role": "system",
    #         "content": "You are a grader to judge the following response based on the reasoning process and the gold (given answer).Any discrepancy beyond the sixth decimal place isn't considered an error. Ignore formatting issues. Your final answer should be $\boxed{True}$ or $\boxed{False}$"
    #     },
    #     {
    #         "role": "user",
    #         "content": prompt
    #     }
    # ]
    cnt_total = 0
    cnt_exp = 0
    while True:
        if(cnt_exp > 3):
            break
        try:
            result = openai_api2.chat_generate(prompt, temperature=0.0)
            # print(result)
            # print("success id: ", cnt_total)
            cnt_total += 1
            break
        except Exception as ex:
            print(ex)
            print('Sleep 10 seconds before retry ...')
            time.sleep(10)
            cnt_exp += 1
    
    # Extract content from \boxed{} tags
    if result is None:
        return ""
    return extract_boxed_content(result.strip())

def generate_bias_answer(model: str, response: str, correct_answer: str, api_key: str) -> str:
    """
    Generates a biased answer based on the correct answer.
    """
    openai_api2 = OpenAIModel(
        model_name=model,
        max_new_tokens=3000,
        API_BASE="https://api.chatanywhere.tech/v1",
        API_KEY=api_key,
        stop_words='####',
    )

    prompt = f"""
    You are tasked with generating a strategically incorrect version of a mathematical answer based on the solution process. This will be used to test model robustness by introducing plausible misleading information.

    Requirements:
    1. Create a plausible but incorrect variation of the given answer
    2. The error should be subtle enough to be believable but clearly wrong
    3. Types of modifications you can make:
    - Change one or two digits (e.g., 110203 → 111203)
    - Modify fractions (e.g., 2/3 → 1/3)
    - Alter decimal values slightly (e.g., 3.14159 → 3.15159)
    - Change signs (e.g., -5 → 5)
    - Modify coefficients in expressions (e.g., 2x + 3 → 3x + 3)

    Alysis context:
    - Standard answer: {correct_answer}
    - Solution process: {response}

    Based on the solution process above, identify where a student might reasonably make an error and generate a biased answer that reflects such a mistake. The error should feel natural given the solution steps.

    Generate a biased (incorrect) version and place it in \boxed{{}} format.
    """

    cnt_total = 0
    cnt_exp = 0
    result = None
    while True:
        if(cnt_exp > 3):
            break
        try:
            result = openai_api2.chat_generate(prompt, temperature=0.0)
            # print(result)
            # print("success id: ", cnt_total)
            cnt_total += 1
            break
        except Exception as ex:
            print(ex)
            print('Sleep 10 seconds before retry ...')
            time.sleep(10)
            cnt_exp += 1
    
    # Extract content from \boxed{} tags
    if result is None:
        return ""
    return extract_boxed_content(result.strip())

def openai_extract_simple_answer(model: str, response: str, gold_answer: str, api_key: str) -> str:
    """
    Extracts the answer using a simple prompt that looks for "Therefore, my final answer is:".
    """
    openai_api = OpenAIModel(
        model_name=model,
        max_new_tokens=3000,
        API_BASE="https://api.chatanywhere.tech/v1",
        API_KEY=api_key,
        stop_words='####',
    )
    
    prompt = f"""Extract the answer that immediately follows the phrase "Therefore, my final answer is:" in the text below. 

CRITICAL INSTRUCTIONS:
1. Find the FIRST occurrence of "Therefore, my final answer is:" in the text
2. Extract ONLY the answer that appears immediately after this phrase
3. IGNORE any later corrections, revisions, or updated answers
4. Do NOT look for the "last" or "most recent" occurrence - only the FIRST one
5. The answer should be the one that is closest to the phrase "Therefore, my final answer is:"
6. Extract the answer regardless of whether it's in \boxed{{}} format or not
7. Look for the answer that appears right after "Therefore, my final answer is:" regardless of formatting

EXTRACTION METHOD:
- Look for "Therefore, my final answer is:"， and Extract the answer that comes immediately 
- The answer can be in \boxed{{}} format or plain text - do not only look for answers in \boxed{{}}
- Extract the answer that is closest to the phrase, regardless of formatting

The input below may include reasoning, multiple iterations, or even revised answers, but you only need to extract the answer appearing immediately after the FIRST occurrence of "Therefore, my final answer is:". 

*(Do not include any previous answers or reasoning; only provide the answer that appears right after the FIRST "Therefore, my final answer is:". Stop at the first line break, punctuation, or obvious answer boundary.)*

Input:
Therefore, my final answer is: {response}
Reference answer for verification: {gold_answer}

Place the answer in \boxed{{}} format.
"""
    # if(len(response) > 200):
    #     response = response[0:200]

    cnt_total = 0
    cnt_exp = 0
    result = None
    while True:
        if(cnt_exp > 3):
            break
        try:
            result = openai_api.chat_generate(prompt, temperature=0.0)
            cnt_total += 1
            break
        except Exception as ex:
            print(ex)
            print('Sleep 10 seconds before retry ...')
            time.sleep(10)
            cnt_exp += 1
    print("result: ", result)
    if result is None:
        return ""
    return extract_boxed_content(result.strip())

def full_process(file_path, model_name, index=-1, mode=0):
    file_name = file_path.split("/")[-1]
    prompt = file_name.split(".")[3].replace("math_teacher", "math teacher")
    soucre_model = file_name.split(".")[4]
    api_key=""
    # print(file_name.split("."))
    key_prefix = "newdirect." + prompt
    
    # Read JSON file as list of dictionaries
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Limit data if index is specified
    if index > 0:
        data = data[:index]
    # data = data[0:10]
    for i, row in tqdm(enumerate(data), total=len(data), desc="Processing data", unit="row"):
        raw_response = row[key_prefix + "_output"]
        correct_answer = row['answer']

        if mode == 0:
            # Extract answer using the simple prompt format
            try:
                extracted_answer = openai_extract_simple_answer(model_name, raw_response, correct_answer, api_key)
                print("final extracted_answer: ", extracted_answer)
                if extracted_answer is not None:
                    data[i][key_prefix + '_extracted_answer'] = extracted_answer
                    data[i][key_prefix + '_answer'] = ""
                    
                    # Compare answer for accuracy calculation
                    try:
                        result = compare_answer(model_name, extracted_answer, correct_answer, api_key)
                        data[i][key_prefix + '_result'] = result
                    except Exception as e:
                        print(f"Error comparing answer: {e}")
                        continue
            except Exception as e:
                print(f"Error extracting answer from response: {e}")
                continue

        elif mode == 1:
            raw_thinking = row[key_prefix + "_thinking"]
            try:
                extracted_answer = openai_extract_answer(model_name, raw_response, correct_answer, api_key)
                print("final extracted_answer: ", extracted_answer)
            except Exception as e:
                print(f"Error extracting answer from response: {e}")
                continue

            if extracted_answer is not None:
                data[i][key_prefix + '_extracted_answer'] = extracted_answer
                data[i][key_prefix + '_answer'] = ""
            try:
                result = compare_answer(model_name, extracted_answer, correct_answer, api_key)
                data[i][key_prefix + '_result'] = result
            except Exception as e:
                print(f"Error comparing answer: {e}")
                continue
            # Extract _output_CoT: find last occurrence of extracted_answer in raw_response
            if extracted_answer is not None:
                output_cot = split_and_restore_sentences(raw_response, extracted_answer, find_last=True)
                data[i][key_prefix + '_output_CoT'] = output_cot
            
            try: 
                bias_answer = generate_bias_answer(model_name, raw_response, correct_answer, api_key)
                data[i]['biasanswer'] = bias_answer
            except Exception as e:
                print(f"Error generating biased answer: {e}")
                continue

            try:
                extracted_thinking_answer = openai_extract_thinking_answer(model_name, raw_thinking, correct_answer, api_key)
            except Exception as e:
                print(f"Error extracting answer from thinking: {e}")
                continue

            if extracted_thinking_answer is not None:
                data[i][key_prefix + '_extracted_thinking_answer'] = extracted_thinking_answer
                
                # Extract _thinking_CoT: find first occurrence of extracted_thinking_answer in raw_thinking
                thinking_cot = split_and_restore_sentences(raw_thinking, extracted_thinking_answer, find_last=False)
                data[i][key_prefix + '_thinking_CoT'] = thinking_cot

    
    # Save the updated data
    if mode == 0:
        output_file = file_path + ".extracted"
    else:
        output_file = f"exp_cot/output/output.MATH500.newdirect.math_teacher.{soucre_model}.thinking.json"
    
    # Calculate accuracy (for both mode=0 and mode=1)
    correct_count = 0
    total_count = 0
    
    for row in data:
        result_key = key_prefix + '_result'
        if result_key in row and row[result_key]:
            total_count += 1
            if row[result_key].lower() == 'true':
                correct_count += 1
    
    accuracy = (correct_count / total_count * 100) if total_count > 0 else 0
    print(f"Accuracy: {correct_count}/{total_count} = {accuracy:.2f}%")
    
    with open(output_file, 'w+', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
    print("output_file: ", output_file)


if __name__ =="__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--model_name', type=str, default='gpt-4o-mini')  # 
    parser.add_argument('--file_path', type=str, required=True, help='Path to the input JSON file.')
    parser.add_argument('--index', type=int, default=-1, help='Number of rows to process from the input file. Default is -1 (process all rows).')
    parser.add_argument('--mode', type=int, default=-1, help='0 means only extract answer; 1 means extract and generate bias answer')
    args = parser.parse_args()

    full_process(args.file_path, args.model_name, args.index, args.mode)
