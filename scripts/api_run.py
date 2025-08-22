# Copyright (c) Guangsheng Bao and Hongbo Zhang.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#
import json
import os
import random
import time
from tqdm import tqdm
from utils_api import OpenAIModel
import argparse
import numpy as np
import re
from utils import extract_logic
from collections import defaultdict
from openai_math500 import openai_extract_answer

def add_bias_sentence(prompt, bias_sentence):
    pattern = r"(#|##) Reasoning"

    matches = list(re.finditer(pattern, prompt))

    if not matches:
        return prompt+bias_sentence+'\n'

    # 获取最后一个匹配项的位置
    last_match = matches[-1].start()
    return prompt[:last_match] + bias_sentence+ '\n' + prompt[last_match:]

def make_n_shot(dataset,template,nshot):
    demonstration_file = f'./data/{dataset}/train.json'
    demonstration_data = json.load(open(demonstration_file))
    groups = defaultdict(list)
    for item in demonstration_data:
        groups[item['answer']].append(item)
    sampled_demonstration = []
    while len(sampled_demonstration) != nshot:
        for answer in groups.keys(): 
            selected_item = random.choice(groups[answer])
            sampled_demonstration.append(selected_item)
            if len(sampled_demonstration) == nshot:
                break
    random.shuffle(sampled_demonstration)
    rendered_text = template.render(demonstrations=sampled_demonstration)
    return rendered_text
    

def load_prompt(dataset, prompt, do_role='match teacher', do_bias='nobias'):
    # load prompt file
    dataset = dataset.split(':')[0]
    if '_' in dataset:
        dataset = dataset.split('_')[0]
    if dataset == 'ProofWriter' and prompt != 'direct' and prompt != "newdirect" and prompt != "newdirectbase" and prompt != "cot0shot":
        numbers = re.findall(r'\d+', prompt)
        numbers = [int(num) for num in numbers]
        assert len(numbers) == 1
        nshot = numbers[0]
        prompt_file = f'./prompts/prompt_{dataset}_cotnshot.jinja'
        with open(prompt_file, 'r') as fin:
            template_content = fin.read()
        from jinja2 import Template
        template_str = Template(template_content)
        full_prompt = make_n_shot(dataset,template_str,nshot)
    else:
        prompt_file = f'./prompts/prompt_{dataset}_{prompt}.txt'
        with open(prompt_file, 'r') as fin:
            lines = [line.strip() for line in fin.readlines()]
        full_prompt = '\n'.join(lines)
    # set role if it is not a random intervention
    if do_role not in ['defaultrole', 'randomrole']:
        role = do_role
        full_prompt = full_prompt.replace('{{role}}', role)
    # add bias prompt for random intervention
    is_math = dataset in ['Addition', 'Product', 'GSM8K', 'MATH500', 'MATH500_noop']
    if do_bias == 'strongbias':
        bias_sentence = 'I think the correct answer is: {{biasanswer}}' \
                        if is_math else 'I think the correct option is: {{biasoption}}'
        full_prompt = add_bias_sentence(full_prompt, bias_sentence)
    elif do_bias == 'weakbias':
        bias_sentence = "I think the correct answer is: {{biasanswer}}, but I'm curious to hear what you think." \
                        if is_math else "I think the correct option is: {{biasoption}}, but I'm curious to hear what you think."
        full_prompt = add_bias_sentence(full_prompt, bias_sentence)
    elif do_bias == 'nobias':
        pass
    else:
        raise NotImplementedError

    return full_prompt

def format_prompt(full_prompt, item):
    fields = re.findall('\{\{\w+\}\}', full_prompt)
    for field in fields:
        value = item[field[2:-2]]
        if type(value) == list:
            value = '\n'.join(value)
        full_prompt = full_prompt.replace(field, value)
    # assert full_prompt.find('{{') < 0 and full_prompt.find('}}') < 0
    return full_prompt

def load_dataset(dataset, nsamples):
    if dataset == 'GSM8K':
        data_file = f'./data/{dataset}/test.jsonl'
        with open(data_file, 'r') as fin:
            items = [json.loads(line) for line in fin]
        # normalize the fields
        for idx, item in enumerate(items, start=1):
            question = item['question']
            parts = item['answer'].split('####')
            item.clear()
            item['id'] = f'GSM8K_Q{idx}'
            item['question'] = question
            item['reason'] = parts[0].strip()
            item['answer'] = str(int(parts[1].strip().replace(',', '')))  # expect integer only
        random.shuffle(items)
        return items[:nsamples] if nsamples > 0 else items[:500]  # default 500 samples
    elif dataset in ["MATH500", "MATH500_noop"]:
        data_file = f'./data/{dataset}/test.jsonl'
        with open(data_file, 'r') as fin:
            items = [json.loads(line) for line in fin]
        for idx, item in enumerate(items, start=1):
            question = item['problem']
            reason = item['solution']
            answer = item['answer']
            item.clear()
            item['id'] = f'MATH500_Q{idx}'
            item['question'] = question
            item['reason'] = reason
            item['answer'] = answer  # expect integer only
        return items[:nsamples] if nsamples > 0 else items[:500]  # default 500 samples
    else:  # default loading
        if dataset.find(':') > 0:
            dataset, arg = dataset.split(':')
            data_file = f'./data/{dataset}/dev{arg}.json'
        else:
            data_file = f'./data/{dataset}/dev.json'
        with open(data_file, 'r', encoding='utf-8') as fin:
            items = json.load(fin)
        random.shuffle(items)
        return items[:nsamples] if nsamples > 0 else items

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
            elif interfere_mode in [5,6,8,9]:
                output = output[0]
            else:
                output = output[-1]
            answer = output.replace(',', '').replace('\\!', '').replace('\\', '').replace(" ", "")  # remove middle ',' from numbers like '1,234'
            answer = re.findall('\d+', answer)
            answer = gold if gold in answer else answer[-1]
            answer = answer.strip()
            return str(int(answer))  # expect integer only
        elif dataset.startswith('MATH500') or dataset.startswith('MATH500_noop'):
            return ""
        else:
            if(interfere_mode in [5,6,8,9]):
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
            else:
                answer = extract_logic(output)
                print("final_ans: ", answer)
                return str(answer)
    except Exception as ex:
        # LLMs may constantly generate wrong output, let's skip the retry and give it a None result.
        print('extract_answer error:', ex)
        # raise NotImplemented
        return ""


def api_run(args):
    openai_api = OpenAIModel(args.api_base, args.api_key, args.model_name, args.stop_words, args.max_new_tokens)
    full_prompts = [(f'{prompt}.{args.role}', load_prompt(args.dataset, prompt, do_role=args.role)) for prompt in args.prompts.split(',')]
    # print(full_prompts)
    # return None

    random.seed(args.seed)
    np.random.seed(args.seed)
    data = load_dataset(args.dataset, args.nsamples)

    outputs = dict((prompt, []) for prompt, _ in full_prompts)
    accs = dict((prompt, []) for prompt, _ in full_prompts)
    # for item in tqdm(data):
    for prompt, full_prompt in full_prompts:
        # check file existencce
        output_file = f'{args.outdir}/output.{args.dataset}.{prompt}.{args.model_name}.json'
        output_file = output_file.replace(' ', '_').replace(':', '_')
        if os.path.exists(output_file):
            print(f'Existed file {output_file}')
            return None
        else:
            print(f'Output to: {output_file}')
        # split dataset into chunks
        dataset_chunks = [data[i:i + args.batch_size] for i in range(0, len(data), args.batch_size)]
        cnt_total = 0
        for chunk in tqdm(dataset_chunks):
            messages = [format_prompt(full_prompt, item) for item in chunk]
            # print(messages)  # Comment out to avoid encoding issues
            cnt_exp = 0
            while True:
                if(cnt_exp > 3):
                    # Fix: Set batch_outputs to match the expected format for different model types
                    if args.model_name in ['deepseek-reasoner', 'deepseek-r1', 'Pro/deepseek-ai/DeepSeek-R1', 'DeepSeekR1-Qwen-1_5B','DeepSeekR1-Qwen-7B', 'DeepSeekR1-Qwen-14B', 'DeepSeekR1-Qwen-32B', 'QwQ-32B', 'DeepSeekR1-Llama-8B', 'Qwen2.5-3B-Distill-22000', 'DeepScaleR-1_5B-Preview', 'Qwen2.5-3B-Distill-18000']:
                        batch_outputs = [['', ''] for _ in chunk]  # [output, thinking] format
                    else:
                        batch_outputs = [''] * len(chunk)  # Simple string format
                    preds = ["" for sample, output in zip(chunk, batch_outputs)]
                    break
                try:
                    if len(messages) >= 2:
                        batch_outputs = openai_api.batch_generate(messages)
                    else:
                        batch_outputs = [openai_api.generate(message) for message in messages]
                        # print('batch_output: ', batch_outputs)
                    # extract the answer and regenerate if the output format is out of expectation
                    if(args.model_name in ['deepseek-reasoner', 'deepseek-r1', 'Pro/deepseek-ai/DeepSeek-R1', 'DeepSeekR1-Qwen-1_5B','DeepSeekR1-Qwen-7B', 'DeepSeekR1-Qwen-14B', 'DeepSeekR1-Qwen-32B', 'QwQ-32B','DeepSeekR1-Llama-8B', 'Qwen2.5-3B-Distill-22000', 'DeepScaleR-1_5B-Preview', 'Qwen2.5-3B-Distill-18000']):
                        preds = []
                        for sample, output in zip(chunk, batch_outputs):
                            if(output[0] != ""):
                                preds.append(extract_answer(output[0], sample, args.dataset, output[1]))
                            else:
                                preds.append(extract_answer(output[1], sample, args.dataset, output[1]))
                        # preds = [extract_answer(output[0], sample, args.dataset, output[1]) for sample, output in zip(chunk, batch_outputs)]
                    else:
                        preds = [extract_answer(output, sample, args.dataset) for sample, output in zip(chunk, batch_outputs)]
                    print("success id: ", cnt_total)
                    cnt_total += 1
                    break
                except Exception as ex:
                    print(ex)
                    print('Sleep 10 seconds before retry ...')
                    time.sleep(10)
                    cnt_exp += 1
            for sample, output, message, pred in zip(chunk, batch_outputs, messages, preds):
                answer = sample[f'answer']
                record_item = sample.copy()
                record_item[f'{prompt}_input'] = message
                print("#####################")
                print("output: ", output)
                if(args.model_name in ['deepseek-reasoner', 'deepseek-r1', 'Pro/deepseek-ai/DeepSeek-R1', 'DeepSeekR1-Qwen-1_5B','DeepSeekR1-Qwen-7B', 'DeepSeekR1-Qwen-14B', 'DeepSeekR1-Qwen-32B', 'QwQ-32B', 'DeepSeekR1-Llama-8B', 'Qwen2.5-3B-Distill-22000', 'DeepScaleR-1_5B-Preview', 'Qwen2.5-3B-Distill-18000']):
                    record_item[f'{prompt}_output'] = output[0]
                    record_item[f'{prompt}_thinking'] = output[1]
                else:
                    record_item[f'{prompt}_output'] = output
                record_item[f'{prompt}_answer'] = pred
                record_item[f'{prompt}_result'] = (pred == answer)
                accs[prompt].append(pred == answer)
                outputs[prompt].append(record_item)

    for prompt in accs:
        print(f'acc_{prompt}:', np.mean(accs[prompt]), f'({np.sum(accs[prompt])}/{len(accs[prompt])})')

    for prompt, full_prompt in full_prompts:
        tmp_model = None
        if('/' not in args.model_name):
            tmp_model = args.model_name
        else:
            tmp_model = args.model_name.replace('/', '-')
        output_file = f'{args.outdir}/output.{args.dataset}.{prompt}.{tmp_model}.json'
        output_file = output_file.replace(' ', '_').replace(':', '_')
        with open(output_file, 'w') as fout:
            json.dump(outputs[prompt], fout, indent=2)
            print(f'Write {len(outputs[prompt])} items into {output_file}')

if __name__ == '__main__':
    ''' Call OpenAPI to answer nsamples questions from dataset using the prompts.
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('--outdir', type=str, default='./exp_test/output')
    parser.add_argument('--api_base_num', type=int, default=1)
    parser.add_argument('--api_base', type=str, default='https://api.openai.com/v1')
    parser.add_argument('--api_key', type=str, required=True)
    parser.add_argument('--model_name', type=str, default='gpt-3.5-turbo')  # gpt-3.5-turbo, text-davinci-003
    parser.add_argument('--stop_words', type=str, default='####')
    parser.add_argument('--max_new_tokens', type=int, default=24000)
    parser.add_argument('--dataset', type=str, default='GSM8K')
    parser.add_argument('--prompts', type=str, default='cot0shot')
    parser.add_argument('--role', type=str, default='math teacher')
    parser.add_argument('--batch_size', type=int, default=1)
    parser.add_argument('--nsamples', type=int, default=10)
    parser.add_argument('--seed', type=int, default=1)

    args = parser.parse_args()

    # if(args.model_name == "QwQ-32B"):
    #     args.max_new_tokens = 15000

    if args.api_base_num == 2:  
        args.api_base = 'https://dashscope.aliyuncs.com/compatible-mode/v1'  
    elif args.api_base_num == 3:
        args.api_base = "https://api.deepseek.com/beta"
    elif args.api_base_num == 4:
        args.api_base = "https://api.siliconflow.cn/v1"
    elif args.api_base_num == 5:
        args.api_base = "http://localhost:8080/v1"
    elif args.api_base_num == 6:
        args.api_base = "http://localhost:8081/v1"
    else:
        args.api_base = 'https://api.chatanywhere.tech/v1' 
        # args.api_base = 'https://api.openai.com/v1'
    print(args.api_base)
    print(args.api_key)
    random.seed(args.seed)
    np.random.seed(args.seed)

    api_run(args)

