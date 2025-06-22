import time
import pandas as pd
import json 
from utils_api import OpenAIModel
import argparse

def compare_answer(model: str, response: str, correct_answer: str) -> str:
    """
    Extracts the answer from the OpenAI response.
    """
    openai_api2 = OpenAIModel(
        model_name=model,
        max_new_tokens=1000,
        API_BASE="https://api.openai.com/v1",
        API_KEY="",
        stop_words='####',
    )

    prompt = f"""
    You are a grader to judge the following response based on the reasoning process and the gold (given answer).Any discrepancy beyond the sixth decimal place isn’t considered an error. Ignore formatting issues. Your final answer should be $\boxed{True}$ or $\boxed{False}$.
    Student answer:
    {response}
    Gold answer:
    {correct_answer}
    """
    # messages = [
    #     {
    #         "role": "system",
    #         "content": "You are a grader to judge the following response based on the reasoning process and the gold (given answer).Any discrepancy beyond the sixth decimal place isn’t considered an error. Ignore formatting issues. Your final answer should be $\boxed{True}$ or $\boxed{False}$"
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
            print(result)
            # print("success id: ", cnt_total)
            cnt_total += 1
            break
        except Exception as ex:
            print(ex)
            print('Sleep 10 seconds before retry ...')
            time.sleep(10)
            cnt_exp += 1
    
    return result.strip()  # Return the final answer

def openai_extract_answer(model, response: str, correct_answer: str) -> str:
    """
    Extracts the answer from the OpenAI response.
    """
    openai_api2 = OpenAIModel(
        model_name=model,
        max_new_tokens=1000,
        API_BASE="https://api.openai.com/v1",
        API_KEY="",
        stop_words='####',
    )

    prompt = f"""
    You are a grader to extract the answer based on the reasoning process. Your response should be in latex with only the extracted answer.
    Student answer:
    {response}
    Expected answer:
    {correct_answer}
    The extracted answer from the student's response is:\n\n
    \[
    \boxed
    """

    cnt_total = 0
    cnt_exp = 0
    while True:
        if(cnt_exp > 3):
            break
        try:
            result = openai_api2.chat_generate(prompt, temperature=0.0)
            print(result)
            # print("success id: ", cnt_total)
            cnt_total += 1
            break
        except Exception as ex:
            print(ex)
            print('Sleep 10 seconds before retry ...')
            time.sleep(10)
            cnt_exp += 1
    
    return result.strip()  # Return the final answer

def generate_bias_answer(model: str, correct_answer: str) -> str:
    """
    Generates a biased answer based on the correct answer.
    """
    openai_api2 = OpenAIModel(
        model_name=model,
        max_new_tokens=1000,
        API_BASE="https://api.openai.com/v1",
        API_KEY="",
        stop_words='####',
    )

    prompt = f"""
    You are a grader to generate a biased answer based on the correct answer. Biased answer tweaks the given answer slightly.Your response should be in latex with only the biased answer.
    Correct answer:
    {correct_answer}
    The biased answer is:\n\n
    \[
    \boxed
    """

    cnt_total = 0
    cnt_exp = 0
    while True:
        if(cnt_exp > 3):
            break
        try:
            result = openai_api2.chat_generate(prompt, temperature=0.0)
            print(result)
            # print("success id: ", cnt_total)
            cnt_total += 1
            break
        except Exception as ex:
            print(ex)
            print('Sleep 10 seconds before retry ...')
            time.sleep(10)
            cnt_exp += 1
    
    return result.strip()  # Return the final answer


def full_process(file_path, model_name, index=-1):
    df = pd.read_json(file_path)
    df = df[:index] if index > 0 else df
    for i, row in df.iterrows():
        raw_response = row['cot0shot.math teacher_output']
        correct_answer = row['answer']
        try:
            extracted_answer = openai_extract_answer(model_name, raw_response, correct_answer)
        except Exception as e:
            print(f"Error extracting answer from response: {e}")
            continue

        if extracted_answer is not None:
            df.at[i, 'cot0shot.math teacher_extracted_answer'] = extracted_answer
            df.at[i, 'cot0shot.math teacher_answer'] = ""

        try:
            result = compare_answer(model_name, extracted_answer, correct_answer)
            if "True" in result:
                answer = True
                df.at[i, 'cot0shot.math teacher_result'] = answer
                print(f"Row {i} updated with answer: {answer}")
            elif "False" in extracted_answer:
                answer = False
                df.at[i, 'cot0shot.math teacher_result'] = answer
                print(f"Row {i} updated with answer: {answer}")
            else:
                print(f"Unexpected response format: {extracted_answer}")
                continue
        except Exception as e:
            print(f"Error comparing answer: {e}")
            continue

        try: 
            bias_answer = generate_bias_answer(model_name, correct_answer)
            df.at[i, 'cot0shot.math teacher_bias_answer'] = bias_answer
        except Exception as e:
            print(f"Error generating biased answer: {e}")
            continue

    df.to_json(f"exp_cot/output/output.MATH500.cot0shot.math_teacher.deepseek-7b.{model_name}-extract.json", orient='records', indent=4)


if __name__ =="__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--model_name', type=str, default='gpt-4o-mini')  # 
    parser.add_argument('--file_path', type=str, required=True, help='Path to the input JSON file.')
    parser.add_argument('--index', type=int, default=-1, help='Number of rows to process from the input file. Default is -1 (process all rows).')
    args = parser.parse_args()

    full_process(args.file_path, args.model_name, args.index)
