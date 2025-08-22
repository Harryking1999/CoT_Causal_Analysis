import backoff  # for exponential backoff
import openai
import os
import asyncio
from typing import Any

@backoff.on_exception(backoff.expo, openai.error.RateLimitError)
def completions_with_backoff(**kwargs):
    # print(f"completions_with_backoff收到的完整参数: {kwargs}")
    # print(f"其中max_tokens: {kwargs.get('max_tokens', 'None')}")
    return openai.Completion.create(**kwargs)

@backoff.on_exception(backoff.expo, openai.error.RateLimitError)
def chat_completions_with_backoff(**kwargs):
    return openai.ChatCompletion.create(**kwargs)

async def dispatch_openai_chat_requests(
    messages_list: list, # : list[list[dict[str, Any]]],
    model: str,
    temperature: float,
    max_tokens: int,
    top_p: float,
    stop_words: list # : list[str]
) -> list: # list[str]:
    """Dispatches requests to OpenAI API asynchronously.
    
    Args:
        messages_list: List of messages to be sent to OpenAI ChatCompletion API.
        model: OpenAI model to use.
        temperature: Temperature to use for the model.
        max_tokens: Maximum number of tokens to generate.
        top_p: Top p to use for the model.
        stop_words: List of words to stop the model from generating.
    Returns:
        List of responses from OpenAI API.
    """
    if model in ['o1', 'o1-mini', 'o3', 'deepseek-r1']:
        async_responses = [
            openai.ChatCompletion.acreate(
                model=model,
                messages=x,
                max_completion_tokens=max_tokens,
                stop = stop_words
            )
            for x in messages_list
        ]
    else:
        async_responses = [
            openai.ChatCompletion.acreate(
                model=model,
                messages=x,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                stop = stop_words
            )
            for x in messages_list
        ]
    return await asyncio.gather(*async_responses)

async def dispatch_openai_prompt_requests(
    messages_list: list,
    model: str,
    temperature: float,
    max_tokens: int,
    top_p: float,
    stop_words: list
) -> list:
    async_responses = [
        openai.Completion.acreate(
            model=model,
            prompt=x,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            frequency_penalty = 0.0,
            presence_penalty = 0.0,
            stop = stop_words
        )
        for x in messages_list
    ]
    return await asyncio.gather(*async_responses)

class OpenAIModel:
    def __init__(self, API_BASE, API_KEY, model_name, stop_words, max_new_tokens) -> None:
        openai.api_base = API_BASE
        openai.api_key = API_KEY
        self.model_name = model_name
        self.max_new_tokens = max_new_tokens
        self.stop_words = stop_words
        print(f'OpenAI API with {API_BASE}, {model_name}, {stop_words}, {max_new_tokens}')

    # used for chat-gpt and gpt-4 and o1
    def chat_generate(self, input_string, temperature = 0.6, interfere_mode=0):
        #interfere_mode influences the output format.
        #interfere_mode = 0: default setting
            #input: <|User|>{question}<|Assistant|>
            #output: reasoning: xxxxxx
        #interfere_mode = 1: for reasoning models, SCM to be evaluated: <think>thinking_CoT -> thinking_answer</think>
            #input: <|User|>{question}<|Assistant|><think>xxxx
            #output: yyyyy</think>zzzzzz
        #interfere_mode = 2: for reasoning models, SCM to be evaluated: <think>thinking_CoT</think> -> answer
            #input: <|User|>{question}<|Assistant|><think>xxxx</think>
            #output: yyyyy
        #interfere_mode = 3: for reasoning models, SCM to be evaluated: thinking_CoT -> answer
            #input: <|User|>{question}<|Assistant|>xxxx
            #output: yyyyy
        # print("interfere_mode", interfere_mode)
        # if(interfere_mode == 3):
        #     self.stop_words = [self.stop_words, "</think>"]
        response = None
        system_prompt = "You are a helpful AI Assistant that provides well-reasoned and detailed responses. You first think about the reasoning process as an internal monologue and then provide the user with the answer. Respond in the following format: <think>\n...\n</think>\n<answer>\n...\n</answer>"
        system_prompt_distill = "You are Open-R1, a language model trained by Hugging Face to help users. Your role as an assistant involves thoroughly exploring questions through a systematic thinking process before providing the final precise and accurate solutions. This requires engaging in a comprehensive cycle of analysis, summarizing, exploration, reassessment, reflection, backtracing, and iteration to develop well-considered thinking process. Please structure your response into two main sections: Thought and Solution using the specified format: <think> Thought section </think> Solution section. In the Thought section, detail your reasoning process in steps. Each step should include detailed considerations such as analysing questions, summarizing relevant findings, brainstorming new ideas, verifying the accuracy of the current steps, refining any errors, and revisiting previous steps. In the Solution section, based on various attempts, explorations, and reflections from the Thought section, systematically present the final solution that you deem correct. The Solution section should be logical, accurate, and concise and detail necessary steps needed to reach the conclusion. Now, try to solve the following question through the above guidelines."
        if(self.model_name in ['deepseek-reasoner']):
            # Handle list messages for deepseek-reasoner
            if isinstance(input_string, list) and self.model_name in ['deepseek-reasoner', 'deepseek-r1', 'Pro/deepseek-ai/DeepSeek-R1']:
                messages = [
                    {"role": "user", "content": input_string[0]},
                    {"role": "assistant", "content": input_string[1], "prefix": True}
                ]
            else:
                messages = [{"role": "user", "content": input_string}]
                
            response = chat_completions_with_backoff(
                    model = self.model_name,
                    messages=messages,
                    max_completion_tokens = self.max_new_tokens,
                    stop = self.stop_words,
                    temperature=temperature
            )
            print('response: ', response)
            # print('messages: ', messages)
        elif self.model_name in ['DeepSeekR1-Qwen-1_5B','DeepSeekR1-Qwen-7B', 'DeepSeekR1-Qwen-14B', 'DeepSeekR1-Qwen-32B', 'QwQ-32B', 'Qwen2.5-7B-Instruct', 'DeepSeekR1-Llama-8B', 'Qwen2.5-32B-Instruct', 'Qwen2.5-3B-Instruct', 'Qwen2.5-3B-GRPO-16000', 'Qwen2.5-3B-GRPO', 'Qwen2.5-3B-Base', 'Qwen2.5-3B-Distill-22000', 'Qwen2.5-3B-GRPO-2000', 'Qwen2.5-3B-GRPO-4000', 'Qwen2.5-3B-GRPO-8000', 'Qwen2.5-3B-SFT-GRPO-4000', 'Qwen2.5-3B-SFT-GRPO-200', 'Qwen2.5-3B-SFT-GRPO-400', 'Qwen2.5-3B-SFT-GRPO-1000', 'Qwen2.5-3B-SFT-GRPO-2000', 'Qwen2.5-3B-GRPO-600', 'Qwen2.5-3B-GRPO-800', 'Qwen2.5-3B-GRPO-1400', 'Qwen2.5-3B-GRPO-1000', 'Qwen2.5-3B-Distill', 'Qwen2.5-1.5B-Open-R1-GRPO', 'Qwen2.5-1.5B-Open-R1-Distill', 'Qwen2.5-1.5B-Open-R1-Distill-v2', 'DeepScaleR-1_5B-Preview', 'Qwen2.5-3B-Distill-18000']:
            # Special handling for local API
            if isinstance(input_string, list):
                question = input_string[0]
                answer_prefix = input_string[1]
                prompt = f"<｜User｜>{question}<｜Assistant｜>{answer_prefix}"
                if (self.model_name in ['Qwen2.5-32B-Instruct', 'Qwen2.5-7B-Instruct', 'Qwen2.5-3B-Instruct', 'Qwen2.5-3B-Base', 'Qwen2.5-3B-Distill-22000', 'Qwen2.5-1.5B-Open-R1-GRPO', 'Qwen2.5-1.5B-Open-R1-Distill', 'Qwen2.5-1.5B-Open-R1-Distill-v2', 'Qwen2.5-3B-Distill', 'Qwen2.5-3B-Distill-18000']):
                    prompt = f'<|im_start|>user\n{question}<|im_end|>\n<|im_start|>assistant\n{answer_prefix}'
                elif (self.model_name in ['Qwen2.5-3B-GRPO-16000', 'Qwen2.5-3B-GRPO', 'Qwen2.5-3B-GRPO-2000', 'Qwen2.5-3B-GRPO-4000', 'Qwen2.5-3B-GRPO-8000', 'Qwen2.5-3B-SFT-GRPO-4000', 'Qwen2.5-3B-SFT-GRPO-200', 'Qwen2.5-3B-SFT-GRPO-400', 'Qwen2.5-3B-SFT-GRPO-1000', 'Qwen2.5-3B-SFT-GRPO-2000', 'Qwen2.5-3B-GRPO-600', 'Qwen2.5-3B-GRPO-800', 'Qwen2.5-3B-GRPO-1400', 'Qwen2.5-3B-GRPO-1000']):
                    # For Qwen2.5-3B-GRPO models, use chat_template format
                    prompt = f"{system_prompt}<|User|>{question}<｜Assistant｜>{answer_prefix}"
            else:
                question = input_string
                prompt = f"<｜User｜>{question}<｜Assistant｜>"
                if self.model_name in ['QwQ-32B']:
                    prompt = f"<｜User｜>{question}<｜Assistant｜>\n<think>"
                elif (self.model_name in ['Qwen2.5-3B-GRPO-16000', 'Qwen2.5-3B-GRPO', 'Qwen2.5-3B-GRPO-2000', 'Qwen2.5-3B-GRPO-4000', 'Qwen2.5-3B-GRPO-8000', 'Qwen2.5-3B-SFT-GRPO-4000', 'Qwen2.5-3B-SFT-GRPO-200', 'Qwen2.5-3B-SFT-GRPO-400', 'Qwen2.5-3B-SFT-GRPO-1000', 'Qwen2.5-3B-SFT-GRPO-2000', 'Qwen2.5-3B-GRPO-600', 'Qwen2.5-3B-GRPO-800', 'Qwen2.5-3B-GRPO-1400', 'Qwen2.5-3B-GRPO-1000']):
                    # For Qwen2.5-3B-GRPO models, use chat_template format
                    prompt = f"{system_prompt}<|User|>{question}<｜Assistant｜>"
                elif (self.model_name in ['Qwen2.5-1.5B-Open-R1-GRPO']):
                    # For Qwen2.5-3B-distill, use <|im_start|> format with system prompt
                    prompt = f'<|im_start|>user\n{question}<|im_end|>\n<|im_start|>assistant\n'
                elif (self.model_name in ['Qwen2.5-3B-Distill-22000', 'Qwen2.5-1.5B-Open-R1-Distill', 'Qwen2.5-1.5B-Open-R1-Distill-v2', 'Qwen2.5-3B-Distill', 'Qwen2.5-3B-Distill-18000']):
                    prompt = f'<|im_start|>system\n{system_prompt_distill}<|im_end|>\n<|im_start|>user\n{question}<|im_end|>\n<|im_start|>assistant\n'
            response = completions_with_backoff(
                model=self.model_name,
                prompt=prompt,
                max_tokens=self.max_new_tokens,
                temperature=temperature,
                stop=self.stop_words
            )
            if self.model_name in ['QwQ-32B']:
                response = completions_with_backoff(
                    model=self.model_name,
                    prompt=prompt,
                    max_tokens=self.max_new_tokens,
                    temperature=0.6,
                    stop=self.stop_words
                    # top_p = 0.95
                )
            # request_params = {
            #     "model": self.model_name,
            #     "max_completion_tokens": self.max_new_tokens,
            #     "stop": self.stop_words,
            #     "temperature": temperature
            # }
            print('response: ', response)
            # print('request_params', request_params)
        else:
            response = chat_completions_with_backoff(
                    model = self.model_name,
                    messages=[
                            {"role": "user", "content": input_string}
                        ],
                    max_tokens = self.max_new_tokens,
                    temperature = temperature,
                    top_p = 1.0,
                    stop = self.stop_words
            )

        if(self.model_name not in ['deepseek-reasoner', 'deepseek-r1', 'Pro/deepseek-ai/DeepSeek-R1', 'DeepSeekR1-Qwen-1_5B','DeepSeekR1-Qwen-7B', 'DeepSeekR1-Qwen-14B', 'DeepSeekR1-Qwen-32B', 'QwQ-32B','Qwen2.5-7B-Instruct', 'DeepSeekR1-Llama-8B', 'Qwen2.5-32B-Instruct', 'Qwen2.5-3B-Instruct', 'Qwen2.5-3B-GRPO-16000', 'Qwen2.5-3B-GRPO', 'Qwen2.5-3B-Distill-22000', 'Qwen2.5-3B-Base', 'Qwen2.5-3B-GRPO-2000', 'Qwen2.5-3B-GRPO-4000', 'Qwen2.5-3B-GRPO-8000', 'Qwen2.5-3B-SFT-GRPO-4000', 'Qwen2.5-3B-SFT-GRPO-200', 'Qwen2.5-3B-SFT-GRPO-400', 'Qwen2.5-3B-SFT-GRPO-1000', 'Qwen2.5-3B-SFT-GRPO-2000', 'Qwen2.5-3B-GRPO-600', 'Qwen2.5-3B-GRPO-800', 'Qwen2.5-3B-GRPO-1400', 'Qwen2.5-3B-GRPO-1000', 'Qwen2.5-3B-Distill', 'Qwen2.5-1.5B-Open-R1-GRPO', 'Qwen2.5-1.5B-Open-R1-Distill', 'Qwen2.5-1.5B-Open-R1-Distill-v2', 'DeepScaleR-1_5B-Preview', 'Qwen2.5-3B-Distill-18000']):
            #non-reasoning models
            generated_text = response['choices'][0]['message']['content'].strip()
            return generated_text
        else:#reasoning models
            if(self.model_name in ['DeepSeekR1-Qwen-1_5B','DeepSeekR1-Qwen-7B', 'DeepSeekR1-Qwen-14B', 'DeepSeekR1-Qwen-32B', 'QwQ-32B', 'DeepSeekR1-Llama-8B', 'Qwen2.5-3B-Distill-22000', 'DeepScaleR-1_5B-Preview', 'Qwen2.5-1.5B-Open-R1-Distill', 'Qwen2.5-1.5B-Open-R1-Distill-v2', 'Qwen2.5-3B-Distill', 'Qwen2.5-3B-Distill-18000']):#vllm reasoning models: parsing by hand
                generated_content = response['choices'][0]['text'].strip()
                # generated_content = 3000 * "1" + 3000 * "2"
                # generated_thinking = generated_content.split("</think>")[0]
                generated_thinking = ""
                generated_text = ""
                # print('generated_content: ', generated_content)
                if(interfere_mode not in [1, 2, 3, 4, 5, 6, 7]):## <think>thinking</think> -> answer
                    #only 1 situation
                    if("</think>" in generated_content and "<think>" in generated_content):
                        generated_text = generated_content.split("</think>")[1]
                        generated_thinking = generated_content.split("</think>")[0].split("<think>")[1]
                    elif("</think>" not in generated_content and "<think>" in generated_content):
                        generated_thinking = generated_text
                        generated_text = ""
                    elif("</think>" in generated_content and "<think>" not in generated_content):
                        generated_text = generated_content.split("</think>")[1]
                        generated_thinking = generated_content.split("</think>")[0]
                    else:
                        generated_text = generated_content
                        generated_thinking = ""
                        if(self.model_name in ['QwQ-32B']):
                            generated_text = ""
                            generated_thinking = generated_content
                elif(interfere_mode == 1):## <think>thinking_CoT -> thinking_answer</think>
                    if("</think>" in generated_content):
                        generated_text = generated_content.split("</think>")[1]
                        generated_thinking = generated_content.split("</think>")[0]
                    else:
                        generated_text = ""
                        generated_thinking = generated_content
                elif(interfere_mode in [2, 3, 4, 5, 6, 7]):## <think>thinking_CoT</think> -> answer
                    generated_text = generated_content
                    generated_thinking = ""
                # elif(interfere_mode == 3):## thinking_CoT -> answer
                #     generated_text = generated_content
                #     generated_thinking = ""
                # elif(interfere_mode == 4):
                #     generated_text = generated_content
                #     generated_thinking = ""
            elif (self.model_name in ['Qwen2.5-7B-Instruct', 'Qwen2.5-32B-Instruct', 'Qwen2.5-3B-Instruct', 'Qwen2.5-3B-GRPO-16000', 'Qwen2.5-3B-GRPO', 'Qwen2.5-3B-Base', 'Qwen2.5-3B-GRPO-2000', 'Qwen2.5-3B-GRPO-4000', 'Qwen2.5-3B-GRPO-8000', 'Qwen2.5-3B-SFT-GRPO-4000', 'Qwen2.5-3B-SFT-GRPO-200', 'Qwen2.5-3B-SFT-GRPO-400', 'Qwen2.5-3B-SFT-GRPO-1000', 'Qwen2.5-3B-SFT-GRPO-2000', 'Qwen2.5-3B-GRPO-600', 'Qwen2.5-3B-GRPO-800', 'Qwen2.5-3B-GRPO-1400', 'Qwen2.5-3B-GRPO-1000', 'Qwen2.5-1.5B-Open-R1-GRPO']):
                return response['choices'][0]['text'].strip()
            else:##commercial api: parsing with content&reasoning_content
                if(response['choices'][0]['message']['content'] is not None):
                    generated_text = response['choices'][0]['message']['content'].strip()
                else:
                    generated_text = ""
                if(response['choices'][0]['message']['reasoning_content'] is not None):
                    generated_thinking = response['choices'][0]['message']['reasoning_content'].strip()
                else:
                    generated_thinking = ""
            # print("final_output: ", str([generated_text, generated_thinking]).encode('utf-8', errors='ignore').decode('utf-8'))
            # print("final_output: ", [generated_text, generated_thinking])
            return [generated_text, generated_thinking]
    
    # used for text/code-davinci
    def prompt_generate(self, input_string, temperature = 0.6):
        response = completions_with_backoff(
            model = self.model_name,
            prompt = input_string,
            max_tokens = self.max_new_tokens,
            temperature = temperature,
            top_p = 1.0,
            frequency_penalty = 0.0,
            presence_penalty = 0.0,
            stop = self.stop_words
        )
        generated_text = response['choices'][0]['text'].strip()
        return generated_text

    def generate(self, input_string, temperature = 0.0, interfere_mode=0):
        if self.model_name in ['text-davinci-002', 'code-davinci-002', 'text-davinci-003', 'gpt-3.5-turbo-instruct']:
            return self.prompt_generate(input_string, temperature)
        elif self.model_name in ['gpt-4', 'gpt-3.5-turbo','gpt-4-turbo-preview','gpt-4-0125-preview','gpt-4-1106-preview',
                                 'llama2-70b-chat', 'llama2-7b-chat', 'mistral-base', 'mistral-sft', 'mistral-dpo', 'o1-mini', 
                                 'o1', 'deepseek-reasoner', 'deepseek-r1', 'Pro/deepseek-ai/DeepSeek-R1', 'DeepSeekR1-Qwen-1_5B',
                                 'DeepSeekR1-Qwen-7B', 'DeepSeekR1-Qwen-14B', 'DeepSeekR1-Qwen-32B', 'QwQ-32B', 'DeepSeekR1-Llama-8B', 'Qwen2.5-3B-GRPO-16000', 'Qwen2.5-3B-GRPO', 'Qwen2.5-3B-GRPO-2000', 'Qwen2.5-3B-GRPO-4000', 'Qwen2.5-3B-GRPO-8000', 'Qwen2.5-3B-SFT-GRPO-4000', 'Qwen2.5-3B-SFT-GRPO-200', 'Qwen2.5-3B-SFT-GRPO-400', 'Qwen2.5-3B-SFT-GRPO-1000', 'Qwen2.5-3B-SFT-GRPO-2000', 'Qwen2.5-3B-GRPO-600', 'Qwen2.5-3B-GRPO-800', 'Qwen2.5-3B-GRPO-1400', 'Qwen2.5-3B-GRPO-1000', 'Qwen2.5-3B-Distill-22000', 'Qwen2.5-1.5B-Open-R1-GRPO', 'Qwen2.5-1.5B-Open-R1-Distill', 'Qwen2.5-1.5B-Open-R1-Distill-v2', 'DeepScaleR-1_5B-Preview', 'Qwen2.5-3B-Distill', 'Qwen2.5-3B-Distill-18000']:
            
            return self.chat_generate(input_string, temperature, interfere_mode)
        else:
            return self.chat_generate(input_string, temperature)
    
    def batch_chat_generate(self, messages_list, temperature = 0.0):
        open_ai_messages_list = []
        for message in messages_list:
            open_ai_messages_list.append(
                [{"role": "user", "content": message}]
            )
        predictions = asyncio.run(
            dispatch_openai_chat_requests(
                    open_ai_messages_list, self.model_name, temperature, self.max_new_tokens, 1.0, self.stop_words
            )
        )
        return [x['choices'][0]['message']['content'].strip() for x in predictions]
    
    def batch_prompt_generate(self, prompt_list, temperature = 0.0):
        predictions = asyncio.run(
            dispatch_openai_prompt_requests(
                    prompt_list, self.model_name, temperature, self.max_new_tokens, 1.0, self.stop_words
            )
        )
        return [x['choices'][0]['text'].strip() for x in predictions]

    def batch_generate(self, messages_list, temperature = 0.0):
        if self.model_name in ['text-davinci-002', 'code-davinci-002', 'text-davinci-003']:
            return self.batch_prompt_generate(messages_list, temperature)
        elif self.model_name in ['gpt-4', 'gpt-3.5-turbo','gpt-4-turbo-preview','gpt-4-0125-preview','gpt-4-1106-preview',
                                 'llama2-70b-chat', 'llama2-7b-chat', 'mistral-base', 'mistral-sft', 'mistral-dpo']:
            return self.batch_chat_generate(messages_list, temperature)
        else:
            return self.batch_chat_generate(messages_list, temperature)

    def generate_insertion(self, input_string, suffix, temperature = 0.0):
        response = completions_with_backoff(
            model = self.model_name,
            prompt = input_string,
            suffix= suffix,
            temperature = temperature,
            max_tokens = self.max_new_tokens,
            top_p = 1.0,
            frequency_penalty = 0.0,
            presence_penalty = 0.0
        )
        generated_text = response['choices'][0]['text'].strip()
        return generated_text