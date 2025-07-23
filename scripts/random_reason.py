import json
import random
from utils_api import OpenAIModel, chat_completions_with_backoff, dispatch_openai_chat_requests
from tqdm import tqdm
import nltk
nltk.download('punkt')
import re
import time
import asyncio
import argparse

SYSTEM_PROMPT = """Inverse Wordsmith specializes in creatively inverting the meaning of sentences while preserving their structure. The GPT will operate with inputs and outputs enclosed in triple double quotes. Specifically, it will:
1. Subtly alter a sentence to make its meaning the exact opposite of the original.
2. Add or remove words as needed, but without significantly changing the sentence structure.
3. Keep all original punctuation intact!!!
4. Ensure the new sentence closely mirrors the original in form but completely differs in meaning.
5. Provide the inverted sentence as a single, coherent statement, enclosed in triple double quotes.
6. If the sentence contains answer identifiers like "The answer is C", change the answer to a different option.
output example: \"\"\"Your output\"\"\""""

def batch_chat_generate(self, messages_list, temperature = 0.0, interfere_mode=0):
        open_ai_messages_list = []
        for message in messages_list:
            open_ai_messages_list.append(
                [   {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": message}]
            )
        predictions = asyncio.run(
            dispatch_openai_chat_requests(
                    open_ai_messages_list, self.model_name, temperature, self.max_new_tokens, 1.0, self.stop_words
            )
        )
        return [x['choices'][0]['message']['content'].strip() for x in predictions]

def chat_generate(self, input_string, temperature = 0.0, interfere_mode=0):
        response = chat_completions_with_backoff(
                model = self.model_name,
                messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": input_string}
                    ],
                max_tokens = self.max_new_tokens,
                temperature = temperature,
                top_p = 1.0,
                stop = self.stop_words
        )
        # print("input_string", input_string)
        generated_text = response['choices'][0]['message']['content'].strip()
        # print("generated_text", generated_text)
        return generated_text

def tokenize_preserving_newlines(text):
    lines = text.split('\n')
    sentences = [nltk.sent_tokenize(line) for line in lines]
    sentences_with_newlines = []
    for line in sentences:
        for sentence in line:
            sentences_with_newlines.append(sentence)
        sentences_with_newlines.append('\n')
    return sentences_with_newlines

def select_random_segment(sentences, min_length=3):
    part_size = len(sentences) // 3
    start = max(2*part_size-1,0)
    end = len(sentences)
    return (start, end)

    # rand_span = [max(2*part_size-1,0),len(sentences)]

    # try_times = 0
    # while True:
    #     try_times+=1
    #     pos_1 = random.randint(rand_span[0],rand_span[-1])
    #     pos_2 = random.randint(rand_span[0],rand_span[-1])
    #     start = min(pos_1, pos_2)
    #     end = max(pos_1, pos_2)
    #     segment = sentences[start:end]
    #     if try_times == 6:
    #         if part_size<=2:
    #             return (0,len(sentences))
    #         return (rand_span[0],rand_span[-1])
    #     if len(segment) >= 1 and len(segment)<=8:
    #         if sentences[start] == '\n' or sentences[end-1] == '\n':
    #             continue
    #         for s in segment:
    #             if len(s)>min_length:
    #                 return (start,end)

def extract_reason(output):
    seps = ['The correct option','\nAnswer:\n', '\n\n', 'Now,']
    reason = output
    # print("reason: ", reason)
    if(isinstance(reason, list)):
        return ""
    for sep in seps:
        if reason.find(sep) > 0:
            reason = reason.split(sep)[:-1]
            reason = sep.join(reason).strip()
            break
    return reason


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', type=str,choices=['FOLIO','ProofWriter','LOGIQA'])
    parser.add_argument('--prompt', type=str)
    parser.add_argument('--role', type=str,default='math teacher')
    parser.add_argument('--model_name', type=str)
    parser.add_argument('--api_base', type=str, default='https://api.chatanywhere.tech/v1')
    parser.add_argument('--api_key', type=str,default='math teacher')
    parser.add_argument('--batch_size', type=int,default=1)

    args = parser.parse_args()
    # Change chat generate function
    OpenAIModel.chat_generate = chat_generate
    OpenAIModel.batch_chat_generate = batch_chat_generate
    # Load default reason data
    suffix = '.thinking' if args.model_name in ['deepseek-reasoner', 'deepseek-r1', 'Pro/deepseek-ai/DeepSeek-R1', 
                                              'DeepSeekR1-Qwen-1_5B', 'DeepSeekR1-Qwen-7B', 'DeepSeekR1-Qwen-14B', 
                                              'DeepSeekR1-Qwen-32B', 'QwQ-32B', 'DeepSeekR1-Llama-8B', 'Qwen2.5-32B-Instruct', 'Qwen2.5-3B-Instruct', 'Qwen2.5-3B-Base', 'Qwen2.5-3B-GRPO-16000', 'Qwen2.5-3B-GRPO-4000', 'Qwen2.5-3B-GRPO-8000', 'Qwen2.5-3B-SFT-GRPO-4000'] else ''
    default_output_path = f'exp_cot/output/output.{args.dataset}.{args.prompt}.{args.role}.{args.model_name}{suffix}.json'.replace(' ', '_')
    print("load_path: ", default_output_path)
    default_data = json.load(open(default_output_path))
    gpt_model_name = 'gpt-3.5-turbo'
    stop_words = None
    max_new_tokens = 4096
    openai_api = OpenAIModel(args.api_base, args.api_key, gpt_model_name, stop_words, max_new_tokens)

    batch_size = args.batch_size
    dataset_chunks = [default_data[i:i + batch_size] for i in range(0, len(default_data), batch_size)]

    processed_data = []
    for chunk in tqdm(dataset_chunks):
        try_time = 0
        while True:
            input_segments = []
            other_part = []
            for d in chunk:
                # Process _output field
                default_reason = d[f'{args.prompt}.{args.role}_output']
                if("Base" in args.model_name and len(default_reason) > 10000):
                    default_reason = default_reason[0:10000]
                default_reason = extract_reason(default_reason)
                default_reason_sentences = tokenize_preserving_newlines(default_reason)
                start,end = select_random_segment(default_reason_sentences,3)
                segment_content = default_reason_sentences[start:end]
                segment_content = ''.join(segment_content)
                segment_content = f'"""{segment_content}"""'
                other_part.append((''.join(default_reason_sentences[:start]),''.join(default_reason_sentences[end:])))
                input_segments.append(segment_content)
            try:
                if len(input_segments) >= 2:
                    batch_outputs = openai_api.batch_generate(input_segments,temperature=0.7)
                else:
                    batch_outputs = [openai_api.generate(message) for message in input_segments]
                # extract the answer and regenerate if the output format is out of expectation
                pattern = r'"""(.*?)"""'
                for b_o_index in range(len(batch_outputs)):
                    matches = re.findall(pattern, batch_outputs[b_o_index], re.DOTALL)
                    if not matches or len(matches)>1:
                        print(input_segments[b_o_index])
                        print(batch_outputs[b_o_index])
                        raise ValueError("No quoted sentences found in the text.")
                    else:
                        batch_outputs[b_o_index] = matches[0]
                break
            except Exception as ex:
                print(ex)
                print('Sleep 3 seconds before retry ...')
                time.sleep(3)
                if try_time >= 5:
                    batch_outputs = ['FAILED']*len(input_segments)
                    break
                try_time+=1
        for sample, output, other in zip(chunk, batch_outputs, other_part):
            # Store random reason for _output
            sample['random_reason'] = ''.join([other[0],output,other[1]])
            
            # Process _thinking_CoT if it exists
            # if f'{args.prompt}.{args.role}_thinking_CoT' in sample:
            #     thinking_cot = sample[f'{args.prompt}.{args.role}_thinking_CoT']
            #     thinking_cot_sentences = tokenize_preserving_newlines(thinking_cot)
            #     start,end = select_random_segment(thinking_cot_sentences,3)
            #     segment_content = thinking_cot_sentences[start:end]
            #     segment_content = ''.join(segment_content)
            #     segment_content = f'"""{segment_content}"""'
            #     try:
            #         # print("thinking_cot!!!!!!!!!!!!!!!!!!!!!!")
            #         cot_output = openai_api.generate(segment_content, temperature=0.7)
            #         matches = re.findall(pattern, cot_output, re.DOTALL)
            #         # print("thinking_cot matches", matches)
            #         if matches and len(matches) == 1:
            #             cot_output = matches[0]
            #             sample['random_reason_thinking_CoT'] = ''.join([
            #                 ''.join(thinking_cot_sentences[:start]),
            #                 cot_output,
            #                 ''.join(thinking_cot_sentences[end:])
            #             ])
            #         # print(" end thinking_cot!!!!!!!!!!!!!!!!!!!!!!")
            #         # print("")
            #     except Exception as ex:
            #         print(f"Error processing thinking_CoT: {ex}")
            #         sample['random_reason_thinking_CoT'] = 'FAILED'

            # if 'reason' in sample:
            #     goldreason = sample[f'reason']
            #     goldreason_sentences = tokenize_preserving_newlines(goldreason)
            #     start,end = select_random_segment(goldreason_sentences,3)
            #     segment_content = goldreason_sentences[start:end]
            #     segment_content = ''.join(segment_content)
            #     segment_content = f'"""{segment_content}"""'
            #     try:
            #         print("goldreason!!!!!!!!!!!!!!!!!!!!!!")
            #         cot_output = openai_api.generate(segment_content, temperature=0.7)
            #         matches = re.findall(pattern, cot_output, re.DOTALL)
            #         # print("thinking_cot matches", matches)
            #         if matches and len(matches) == 1:
            #             cot_output = matches[0]
            #             sample['random_reason_goldreason'] = ''.join([
            #                 ''.join(goldreason_sentences[:start]),
            #                 cot_output,
            #                 ''.join(goldreason_sentences[end:])
            #             ])
            #         # print(" end thinking_cot!!!!!!!!!!!!!!!!!!!!!!")
            #         # print("")
            #     except Exception as ex:
            #         print(f"Error processing thinking_CoT: {ex}")
            #         sample['random_reason_goldreason'] = 'FAILED'
            
            # Process _thinking if it exists
            if f'{args.prompt}.{args.role}_thinking' in sample:
                thinking = sample[f'{args.prompt}.{args.role}_thinking']
                thinking_sentences = tokenize_preserving_newlines(thinking)
                start,end = select_random_segment(thinking_sentences,3)
                segment_content = thinking_sentences[start:end]
                segment_content = ''.join(segment_content)
                segment_content = f'"""{segment_content}"""'
                try:
                    # print("thinking!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                    thinking_output = openai_api.generate(segment_content, temperature=0.7)
                    matches = re.findall(pattern, thinking_output, re.DOTALL)
                    # print("thinking matches", matches)
                    if matches and len(matches) == 1:
                        thinking_output = matches[0]
                        sample['random_reason_thinking'] = ''.join([
                            ''.join(thinking_sentences[:start]),
                            thinking_output,
                            ''.join(thinking_sentences[end:])
                        ])
                    # print(" end thinking!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                except Exception as ex:
                    print(f"Error processing thinking: {ex}")
                    sample['random_reason_thinking'] = 'FAILED'
            
            # Process _output_CoT if it exists
            if f'{args.prompt}.{args.role}_output_CoT' in sample:
                output_cot = sample[f'{args.prompt}.{args.role}_output_CoT']
                # print("orig output_cot: ", output_cot)
                # if(len(output_cot.strip()) < 8):
                #     output_cot = sample['reason']
                # print("new output_cot: ", output_cot)
                output_cot_sentences = tokenize_preserving_newlines(output_cot)
                start,end = select_random_segment(output_cot_sentences,3)
                segment_content = output_cot_sentences[start:end]
                segment_content = ''.join(segment_content)
                segment_content = f'"""{segment_content}"""'
                # print("segment_content: \n", segment_content)
                # print("orig_content: \n", output_cot_sentences)
                try:
                    cot_output = openai_api.generate(segment_content, temperature=0.7)
                    matches = re.findall(pattern, cot_output, re.DOTALL)
                    # print("cot_output: ", cot_output)
                    if matches and len(matches) == 1:
                        cot_output = matches[0]
                        sample['random_reason_output_CoT'] = ''.join([
                            ''.join(output_cot_sentences[:start]),
                            cot_output,
                            ''.join(output_cot_sentences[end:])
                        ])
                        # print("output_cot_1: ", ''.join(output_cot_sentences[:start]))
                        # print("output_cot_2: ", cot_output)
                        # print("output_cot_3: ", ''.join(output_cot_sentences[end:]))
                except Exception as ex:
                    print(f"Error processing output_CoT: {ex}")
                    sample['random_reason_output_CoT'] = 'FAILED'

            if f'{args.prompt}.{args.role}_thinking_CoT' in sample:
                output_cot = sample[f'{args.prompt}.{args.role}_thinking_CoT']
                # print("orig output_cot: ", output_cot)
                # if(len(output_cot.strip()) < 8):
                #     output_cot = sample['reason']
                # print("new output_cot: ", output_cot)
                output_cot_sentences = tokenize_preserving_newlines(output_cot)
                start,end = select_random_segment(output_cot_sentences,3)
                segment_content = output_cot_sentences[start:end]
                segment_content = ''.join(segment_content)
                segment_content = f'"""{segment_content}"""'
                try:
                    cot_output = openai_api.generate(segment_content, temperature=0.7)
                    matches = re.findall(pattern, cot_output, re.DOTALL)
                    if matches and len(matches) == 1:
                        cot_output = matches[0]
                        sample['random_reason_thinking_CoT'] = ''.join([
                            ''.join(output_cot_sentences[:start]),
                            cot_output,
                            ''.join(output_cot_sentences[end:])
                        ])
                except Exception as ex:
                    print(f"Error processing output_CoT: {ex}")
                    sample['random_reason_output_CoT'] = 'FAILED'
            
            processed_data.append(sample)

    output_random_reason_path = f'exp_cot/random_reason/random_reason.{args.dataset}.{args.prompt}.{args.role}.{args.model_name}.json'.replace(' ','_')
    with open(output_random_reason_path, 'w', encoding='utf-8') as fout:
        print(output_random_reason_path)
        json.dump(processed_data, fout, ensure_ascii=False, indent=2)