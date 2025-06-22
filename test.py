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
    pattern2 = r"correct option is: (true|false|unknown)"
    pattern3 = r"([A-C])\)\s*(True|False|Unknown)"
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
print("extract_logic: ", extract_logic("Based on the context provided, the text primarily emphasizes the importance of having an attitude of awe and respect for the history and culture behind historical relics, rather than focusing solely on their physical protection or reconstruction. The text argues that forced demolition and reconstruction, without regard for the cultural significance, can reduce relics to mere playthings of modern society, as the true historical and cultural essence is difficult to reproduce.\n\nNow, evaluating the options:\n- **A) Protecting cultural relics requires awe and respect for the history and culture behind them.**  \n  This directly aligns with the core message of the text, which states that \"what is more indispensable is to be in awe of the history of our ancestors\" and criticizes actions that ignore the \"cultural blood\" behind relics. The text emphasizes that cultural inheritance is not about technical reconstruction but about reverence for history.\n\n- **B) All historical relics should not be torn down or rebuilt.**  \n  The text criticizes forced demolition and reconstruction but does not make an absolute statement against all such actions. Instead, it focuses on the attitude behind these actions, implying that reconstruction might be possible but is insufficient without cultural respect. Thus, this is not the main point.\n\n- **C) Historical relics are the carrier of history and culture.**  \n  While the text mentions that relics carry history and culture (e.g., \"the history and culture it carries are difficult to reproduce\"), this is presented as a supporting detail rather than the primary focus. The main argument is about the required attitude for protection, not just the role of relics as carriers.\n\n- **D) Historical relics that have disappeared can be restored through reconstruction.**  \n  The text explicitly contradicts this by stating that while rebuilding is technically possible with drawings, the history and culture are \"difficult to reproduce\" and that such efforts may not genuinely connect to or continue historical context. Therefore, this is not supported.\n\nThe correct option is **A**, as it best captures the text's main explanation that protecting cultural relics necessitates awe and respect for their underlying history and culture.\n\n**Answer: A**"))
