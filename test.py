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

    match = re.search(pattern1, answer)
    option = None
    # extract pattern
    if match:
        option = match.group(1)
    
    if not option:
        match = re.search(pattern2, answer, re.IGNORECASE)
        if match:
            word_to_option = {"true": "A", "false": "B", "unknown": "C"}
            option = word_to_option.get(match.group(1).lower())

    if not option:
        match = re.search(pattern3, answer, re.IGNORECASE)
        if match:
            option = match.group(1)

    if not option:
        match = re.search(pattern6, answer)
        if match:
            option = match.group(1)

    if not option:
        match = re.search(pattern7, answer)
        if match:
            option = match.group(1)

    if not option:
        match = re.search(pattern8, answer)
        if match:
            option = match.group(1)

    if not option:
        match = re.search(pattern9, answer)
        if match:
            option = match.group(1)
    if not option:
        match = re.search(pattern10, answer)
        if match:
            option = match.group(1)

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
print("extract_logic: ", extract_logic("Based on the context, the company president's reasoning contains a flaw in that it presents only two specific actions\u2014reducing planned expansion or eliminating less profitable operations\u2014as the \"only options\" to prevent any further decrease in profits and thus avoid bankruptcy. However, the president does not consider or justify why other potential strategies to stop the profit decrease are not viable. For example, alternatives could include increasing demand through marketing, improving product offerings, reducing costs in other areas, seeking new markets, or enhancing operational efficiency.\n\nThis oversight is accurately described in option D: \"It does not take into account that there may be other ways to stop the decrease in profits.\" The president's reasoning commits a false dilemma by limiting the options without evidence that no other approaches exist.\n\nThe other options are less accurate:\n- **A** is incorrect because the reasoning does not presume the survival of the company is good without justification; in a business context, avoiding bankruptcy is a reasonable implicit goal.\n- **B** is incorrect because the reasoning is focused on preventing any further decrease in profits, regardless of magnitude, to avoid bankruptcy; a slight decrease could still lead to bankruptcy if sustained.\n- **C** is incorrect because the reasoning does not ignore alternatives to declaring bankruptcy; instead, it focuses on preventing bankruptcy by addressing the profit decrease, but it fails to consider all possible ways to achieve that prevention.\n\nThus, the correct answer is **D**."))
