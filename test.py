import re
def extract_answer(output, item, dataset, interfere_mode=0):
    # print("output: ", output)
    # print("item: ", item)
    # print("datasetL: ", dataset)
    # print("interfere_mode: ", interfere_mode)
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
            # print('output', output)
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

    
print(extract_answer("provided as calculated.", "", 'Addition', 5))
