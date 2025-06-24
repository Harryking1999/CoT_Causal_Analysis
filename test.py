import re
def extract_answer(output, item, dataset, interfere_mode=3):
    # print("output: ", output)
    # print("item: ", item)
    # print("datasetL: ", dataset)
    # print("interfere_mode: ", interfere_mode)
    if(output[0] == "."):
        output = output[1:]
    if interfere_mode == 1:
        output = output.split("</think>")[0].split(".")[0]
    elif interfere_mode == 2 or interfere_mode == 4 :
        output = output.split(".")[0]
    elif interfere_mode == 3:
        if("." in output):
            output = output.split(".")[0]
        if("</think>" in output):
            output = output.split("</think>")[0]
    try:
        dataset = dataset.split(':')[0]
        if dataset in ['Addition', 'Product', 'GSM8K']:
            gold = item
            # Handle interfere_mode 1
            output = output.split('\n')
            # tmp_output0 = output[1]
            output_ls = [line for line in output if len(re.findall('\d+', line)) > 0]
            if(len(output_ls) == 0):
                return ""
            print('###########################output', output_ls)
            output = [line for line in output if len(re.findall('\d+', line)) > 0][-1]
            answer = output.replace(',', '').replace('\\!', '').replace('\\', '').replace(" ", "")  # remove middle ',' from numbers like '1,234'
            answer = re.findall('\d+', answer)
            answer = gold if gold in answer else answer[-1]
            answer = answer.strip()
            return str(int(answer))  # expect integer only
            return str(answer)
    except Exception as ex:
        # LLMs may constantly generate wrong output, let's skip the retry and give it a None result.
        print('extract_answer:', ex)
        return ""
        # raise NotImplemented

def extract_logic(answer):
    pattern1 = r"correct \w+ is:?\s*[*]*\s*([A-D])" 
    pattern2 = r"correct option is: (true|false|unknown|uncertain)"
    pattern3 = r"([A-C])\)\s*(True|False|Unknown|Uncertain)"
    pattern4 = r"([A-D])\) "
    pattern5 = r"^[A-D]\.?$"
    pattern6 = r"\\boxed{([A-D])}"
    pattern7 = r"correct \w+ is:?\s*[*]*\s*\{([A-D])\}"
    pattern8 = r"which is ([A-D])([.)]?)\b"
    pattern9 = r"Answer:\s*([A-D])"
    pattern10 = r"Correct Option:\s*([A-D])"
    pattern11 = r"Answer:.*?([A-D])([).,]|$)"
    pattern12 = r"answer is ([A-D])([).,]|$)"
    pattern13 = r"answer.*?([A-D])([).,]|$)"
    pattern14 = r"\*\*([A-D])\*\*"
    pattern15 = r"\{([A-D])\}"

    match = re.search(pattern1, answer)
    option = None
    # extract pattern
    if match:
        option = match.group(1)
        print(pattern1)
    
    if not option:
        match = re.search(pattern2, answer, re.IGNORECASE)
        if match:
            word_to_option = {"true": "A", "false": "B", "unknown": "C"}
            option = word_to_option.get(match.group(1).lower())
            print(pattern2)

    if not option:
        match = re.search(pattern3, answer, re.IGNORECASE)
        if match:
            option = match.group(1)
            print(pattern3)

    if not option:
        match = re.search(pattern6, answer)
        if match:
            option = match.group(1)
            print(pattern6)

    if not option:
        match = re.search(pattern7, answer)
        if match:
            option = match.group(1)
            print(pattern7)

    if not option:
        match = re.search(pattern8, answer)
        if match:
            option = match.group(1)
            print(pattern8)

    if not option:
        match = re.search(pattern9, answer)
        if match:
            option = match.group(1)
            print(pattern9)
    if not option:
        match = re.search(pattern10, answer)
        if match:
            option = match.group(1)
            print(pattern10)
    if not option:
        match = re.search(pattern11, answer)
        if match:
            option = match.group(1)
            print(pattern11)
    if not option:
        match = re.search(pattern12, answer)
        if match:
            option = match.group(1)
            print(pattern12)
    if not option:
        match = re.search(pattern13, answer)
        if match:
            option = match.group(1)
            print(pattern13)
    if not option:
        match = re.search(pattern14, answer)
        if match:
            option = match.group(1)
            print(pattern14)
    if not option:
        match = re.search(pattern15, answer)
        if match:
            option = match.group(1)
            print(pattern15)

    if not option and len(answer)<16:
        if 'true' in answer.lower():
            option = 'A'
        elif 'false' in answer.lower():
            option = 'B'
        elif 'unknown' in answer.lower():
            option = 'C'

    if not option:
        match = re.match(pattern4, answer)
        if match:
            option = match.group(1)

    if not option:
        match = re.match(pattern5, answer)
        if match:
            option = match.group(0) 

    if not option:
        option = None
        # wrong_data.append(d)
    return option

# print("extract_ans: ", extract_answer(". \nSo, the final computed product is .", "24", 'Addition'))
print("extract_logic: ", extract_logic("\n\nThe problem requires determining whether Karen will share \"Black Mirror\" to Lisa based on the given statements. Here's the logical breakdown:\n\n1. **Premises**:\n   - \"Black Mirror\" (BM) is a Netflix show.\n   - Karen does not download BM.\n   - **Biconditional**: Karen binge-watches a Netflix show **if and only if** she downloads it. Since she doesn't download BM, she also does not binge-watch it (\u00acD \u2192 \u00acB).\n   - **If** a Netflix show is popular, Karen will binge-watch it. Since Karen did not binge-watch BM (\u00acB), BM is not popular (contrapositive: \u00acB \u2192 \u00acP).\n   - **If** Karen binge-watches a Netflix show, she shares it with Lisa. This is a **one-way implication** (B \u2192 S), meaning binge-watching guarantees sharing but does not preclude sharing under other conditions (if any existed).\n\n2. **Analysis**:\n   - Since Karen did not binge-watch BM (\u00acB), the implication (B \u2192 S) does not guarantee sharing. The statement \"Karen will share BM to Lisa\" (S) could still be true or false independently, as the premises do not provide information about sharing outside of binge-watching.\n   - The absence of binge-watching removes the **only stated condition** for sharing, but it does not logically negate the possibility of sharing through other (unmentioned) means. Thus, the truth value of S cannot be definitively determined.\n\n**Conclusion**: The statement \"Karen will share 'Black Mirror' to Lisa\" is **uncertain** because the premises neither confirm nor deny sharing in the absence of binge-watching.\n\n**Answer**: C) Uncertain"))
