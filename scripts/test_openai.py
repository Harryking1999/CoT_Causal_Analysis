import time
import pandas as pd
import json 
from utils_api import OpenAIModel
import argparse

def openai_extract_answer(model, response: str, correct_answer: str, api_key: str) -> str:
    """
    Extracts the answer from the OpenAI response.
    """
    openai_api2 = OpenAIModel(
        model_name=model,
        max_new_tokens=3000,
        API_BASE="https://api.openai.com/v1",
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
    
    return result  # Return the final answer

def compare_answer(model: str, response: str, correct_answer: str, api_key: str) -> str:
    """
    Extracts the answer from the OpenAI response.
    """
    openai_api2 = OpenAIModel(
        model_name=model,
        max_new_tokens=3000,
        API_BASE="https://api.openai.com/v1",
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

def generate_bias_answer(model: str, response: str, correct_answer: str, api_key: str) -> str:
    """
    Generates a biased answer based on the correct answer.
    """
    openai_api2 = OpenAIModel(
        model_name=model,
        max_new_tokens=3000,
        API_BASE="https://api.openai.com/v1",
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

response = "To find the distance between the points \\((2, -6)\\) and \\((-4, 3)\\), use the distance formula:\n\n\\[\nd = \\sqrt{(x_2 - x_1)^2 + (y_2 - y_1)^2}\n\\]\n\nSubstitute \\(x_1 = 2\\), \\(y_1 = -6\\), \\(x_2 = -4\\), and \\(y_2 = 3\\):\n\n- Difference in \\(x\\)-coordinates: \\(x_2 - x_1 = -4 - 2 = -6\\)\n- Difference in \\(y\\)-coordinates: \\(y_2 - y_1 = 3 - (-6) = 3 + 6 = 9\\)\n\nSquare the differences:\n- \\((-6)^2 = 36\\)\n- \\(9^2 = 81\\)\n\nAdd the squares:\n- \\(36 + 81 = 117\\)\n\nSo, the distance is:\n\\[\nd = \\sqrt{117}\n\\]\n\nSimplify \\(\\sqrt{117}\\) by factoring 117:\n- \\(117 = 9 \\times 13 = 3^2 \\times 13\\)\n- \\(\\sqrt{117} = \\sqrt{3^2 \\times 13} = 3\\sqrt{13}\\)\n\nSince 13 is prime, \\(3\\sqrt{13}\\) is in simplest radical form.\n\n\\boxed{3\\sqrt{13}}"
correct_answer = "3\\sqrt{13}"
api_key=""

output = openai_extract_answer(model="gpt-3.5-turbo", response=response, correct_answer=correct_answer, api_key=api_key)
print(output)

if(output in response):
    print("yes")
else:
    print("no")

flag_correct = compare_answer(model="gpt-3.5-turbo", response=output, correct_answer=correct_answer, api_key=api_key)
print(flag_correct)

bias_answer = generate_bias_answer(model="gpt-3.5-turbo", response=output,correct_answer=correct_answer, api_key=api_key)
print(bias_answer)

