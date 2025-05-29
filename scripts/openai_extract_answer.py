import time
import pandas as pd
import json 
from utils_api import OpenAIModel

def compare_answer(response: str, correct_answer: str) -> str:
    """
    Extracts the answer from the OpenAI response.
    """
    openai_api = OpenAIModel(
        model_name="gpt-4o",
        max_new_tokens=1000,
        API_BASE="https://api.openai.com/v1",
        API_KEY="replace_with_key",
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
            result = openai_api.chat_generate(prompt, temperature=0.0)
            print(result)
            print("success id: ", cnt_total)
            cnt_total += 1
            break
        except Exception as ex:
            print(ex)
            print('Sleep 10 seconds before retry ...')
            time.sleep(10)
            cnt_exp += 1
    
    return result.strip()  # Return the final answer


if __name__ =="__main__":

    df = pd.read_json("exp_cot/output/output.MATH500.cot0shot.math_teacher.deepseek-reasoner.json")
    for i, row in df.iterrows():
        raw_response = row['cot0shot.math teacher_output']
        correct_answer = row['answer']
        try:
            extracted_answer = compare_answer(raw_response, correct_answer)
            print(f"Extracted answer: {extracted_answer}")
        except Exception as e:
            print(f"Error extracting answer from response: {e}")
            continue

        if extracted_answer is not None:
            if "True" in extracted_answer:
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
        
        # time.sleep(10)
        # break
            # df.at[i, 'cot0shot.math teacher_result'] = 'true' if answer == row['gold'] else 'false'

    df.to_json("exp_cot/output/output.MATH500.cot0shot.math_teacher.deepseek-reasoner.gpt-4o-updated.json", orient='records', indent=4)