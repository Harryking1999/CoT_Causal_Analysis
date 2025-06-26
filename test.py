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
    pattern16 = r"Correct option:\s*([A-D])"
    # pattern17 = r"^([A-D])[.)]?.*"
    pattern17 = r'(?:^|\n|\.)\s*([A-D])[)\s\.]?'
    # pattern18 = r'\s([A-D])\)?\s'
    pattern18 = r'[^A-Za-z0-9]([A-D])\)?\s'
    pattern19 = r'[^A-Za-z0-9]([A-D])\)?(?:$|\.)'

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
    if not option:
        match = re.search(pattern16, answer)
        if match:
            option = match.group(1)
            print(pattern16)
    if not option:
        match = re.search(pattern17, answer)
        if match:
            option = match.group(1)
            print(pattern17)
    if not option:
        match = re.search(pattern18, answer)
        if match:
            option = match.group(1)
            print(pattern18)
    if not option:
        match = re.search(pattern19, answer)
        if match:
            option = match.group(1)
            print(pattern19)


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

# def extract_answer(output, item, dataset, interfere_mode=0):
#     # print("output: ", output)
#     # print("item: ", item)
#     # print("datasetL: ", dataset)
#     # print("interfere_mode: ", interfere_mode)
#     if(len(output) == 0):
#         return ""
#     if(output[0] == "."):
#         output = output[1:]
#     if interfere_mode == 1:
#         output = output.split("</think>")[0].split(".")[0]
#     elif interfere_mode == 2 or interfere_mode == 4:
#         output = output.split(".")[0]
#     elif interfere_mode == 3:
#         if("." in output):
#             output = output.split(".")[0]
#         if("</think>" in output):
#             output = output.split("</think>")[0]
#     elif interfere_mode in [5,6,8]:
#         if("<｜end▁of▁thinking｜>" in output):
#             output = output.split("<｜end▁of▁thinking｜>")[0]
#         if('<think>' in output):
#             output = output.split("<think>")[0]
#         if('</think>' in output):
#             output = output.split("</think>")[0]
#         # 按句号分割，取第一个有意义的句子
#         paragraphs = output.split("\n")
#         flag = 0
#         cnt_meaningful_sentences = 0
#         output_ls = []
#         for paragraph in paragraphs:
#             sentences = paragraph.split(".")
#             for sentence in sentences:
#                 # 去除空白字符后，如果句子不全是* \n \ 等符号，则认为有意义
#                 if(cnt_meaningful_sentences > 3):
#                     break
#                 cleaned_sentence = sentence.strip()
#                 if cleaned_sentence and not all(c in ['*', '\n', '\\', ' ', '\t', '|', '｜'] for c in cleaned_sentence):
#                     output_ls.append(cleaned_sentence)
#                     cnt_meaningful_sentences += 1
#                 else:
#                     # 如果没有找到有意义的句子，保持原样
#                     pass
#     final_ans = None
#     for i in output_ls:
#         tmp_ans = extract_logic(i)
#         if(tmp_ans != None and tmp_ans != "None"):
#             print("output_tmp: ", i)
#             final_ans = tmp_ans
#             break
#     # print("output: ", output)
#     print("extract logic: ", final_ans)

def extract_answer(output, item, dataset, interfere_mode=0):
    # print("output: ", output)
    # print("item: ", item)
    # print("datasetL: ", dataset)
    # print("interfere_mode: ", interfere_mode)
    if(len(output) == 0):
        return ""
    if(output[0] == "."):
        output = output[1:]
    if interfere_mode == 1:
        output = output.split("</think>")[0].split(".")[0]
    elif interfere_mode == 2 or interfere_mode == 4:
        output = output.split(".")[0]
    elif interfere_mode == 3:
        if("." in output):
            output = output.split(".")[0]
        if("</think>" in output):
            output = output.split("</think>")[0]
    elif interfere_mode in [5,6,8]:
        if("<｜end▁of▁thinking｜>" in output):
            output = output.split("<｜end▁of▁thinking｜>")[0]
        if('<think>' in output):
            output = output.split("<think>")[0]
        if('</think>' in output):
            output = output.split("</think>")[0]
        # 按句号分割，取第一个有意义的句子
    try:
        dataset = dataset.split(':')[0]
        if dataset in ['Addition', 'Product', 'GSM8K']:
            gold = item['answer']
            # Handle interfere_mode 1
            output = output.split('\n')
            # tmp_output0 = output[1]
            # print('output', output)
            output = [line for line in output if len(re.findall('\d+', line)) > 0]
            if(len(output) == 0):
                return ""
            elif interfere_mode in [5,6,8]:
                output = output[0]
            else:
                output = output[-1]
            answer = output.replace(',', '').replace('\\!', '').replace('\\', '').replace(" ", "")  # remove middle ',' from numbers like '1,234'
            answer = re.findall('\d+', answer)
            answer = gold if gold in answer else answer[-1]
            answer = answer.strip()
            return str(int(answer))  # expect integer only
        elif dataset.startswith('MATH500'):
            return ""
        else:
            paragraphs = output.split("\n")
            cnt_meaningful_sentences = 0
            output_ls = []
            for paragraph in paragraphs:
                sentences = paragraph.split(".")
                for sentence in sentences:
                    # 去除空白字符后，如果句子不全是* \n \ 等符号，则认为有意义
                    if(cnt_meaningful_sentences > 3):
                        break
                    cleaned_sentence = sentence.strip()
                    if cleaned_sentence and not all(c in ['*', '\n', '\\', ' ', '\t', '|', '｜'] for c in cleaned_sentence):
                        output_ls.append(cleaned_sentence)
                        cnt_meaningful_sentences += 1
                    else:
                        # 如果没有找到有意义的句子，保持原样
                        pass
            final_ans = None
            for i in output_ls:
                tmp_ans = extract_logic(i)
                if(tmp_ans != None and tmp_ans != "None"):
                    # print("output_tmp: ", i)
                    final_ans = tmp_ans
                    break
            print("final_ans: ", final_ans)
            return final_ans
    except Exception as ex:
        # LLMs may constantly generate wrong output, let's skip the retry and give it a None result.
        print('extract_answer error:', ex)
        # raise NotImplemented
        return ""

# print("extract_ans: ", extract_answer(". \nSo, the final computed product is .", "24", 'Addition'))
# print("extract_logic: ", extract_logic("D"))

extract_answer("A\n<｜end▁of▁thinking｜>\nBased on the given context, the statement \"Fiona is smart\" is true. Here's the reasoning step by step:\n\n1. Fiona is stated to be quiet (from the context: \"Fiona is quiet\").\n2. The context includes the rule: \"All quiet things are cold.\" Therefore, since Fiona is quiet, she must be cold.\n3. The context also includes the rule: \"All cold, quiet things are smart.\" Since Fiona is both cold (from step 2) and quiet, she must be smart.\n\nThus, Fiona is smart, making the statement true.\n\n**Correct Option: A) True**", 1, "ProofWriter", 5)

# print(all(c in ['*', '\n', '\\', ' ', '\t'] for c in "B"))