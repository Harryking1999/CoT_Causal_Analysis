import backoff  # for exponential backoff
import openai
import os
import asyncio
from typing import Any

@backoff.on_exception(backoff.expo, openai.error.RateLimitError)
def completions_with_backoff(**kwargs):
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
    def chat_generate(self, input_string, temperature = 1.0, interfere_mode=0):
        #interfere_mode influences the output format.
        #interfere_mode = 0: default setting
            #input: <|User|>{question}<|Assistant|>
            #output: for reasoning models: <think>xxxxx</think>yyyy; for non-reasoning models: xxxxxx
        #interfere_mode = 1: for reasoning models, SCM to be evaluated: <think>thinking_CoT -> thinking_answer</think>
            #input: <|User|>{question}<|Assistant|><think>xxxx
            #output: yyyyy</think>zzzzzz
        #interfere_mode = 2: for reasoning models, SCM to be evaluated: <think>thinking_CoT</think> -> answer
            #input: <|User|>{question}<|Assistant|><think>xxxx</think>
            #output: yyyyy
        #interfere_mode = 3: for reasoning models, SCM to be evaluated: thinking_CoT -> answer
            #input: <|User|>{question}<|Assistant|>xxxx
            #output: yyyyy
        if(interfere_mode == 3):
            self.stop_word = [self.stop_word, "</think>"]
        response = None
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
        elif self.model_name in ['DeepSeekR1-Qwen-1_5B','DeepSeekR1-Qwen-7B', 'DeepSeekR1-Qwen-14B', 'DeepSeekR1-Qwen-32B']:
            # Special handling for local API
            if isinstance(input_string, list):
                question = input_string[0]
                answer_prefix = input_string[1]
                prompt = f"<｜User｜>{question}<｜Assistant｜>{answer_prefix}"
            else:
                question = input_string
                prompt = f"<｜User｜>{question}<｜Assistant｜>"
            
            response = completions_with_backoff(
                model=self.model_name,
                prompt=prompt,
                max_tokens=self.max_new_tokens,
                temperature=temperature,
                stop=self.stop_words
            )
            print('response: ', response)
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

        if(self.model_name not in ['deepseek-reasoner', 'deepseek-r1', 'Pro/deepseek-ai/DeepSeek-R1', 'DeepSeekR1-Qwen-1_5B','DeepSeekR1-Qwen-7B', 'DeepSeekR1-Qwen-14B', 'DeepSeekR1-Qwen-32B']):
            #non-reasoning models
            generated_text = response['choices'][0]['message']['content'].strip()
            return generated_text
        else:#reasoning models
            if(self.model_name in ['DeepSeekR1-Qwen-1_5B','DeepSeekR1-Qwen-7B', 'DeepSeekR1-Qwen-14B', 'DeepSeekR1-Qwen-32B']):#vllm reasoning models: parsing by hand
                generated_content = response['choices'][0]['text'].strip()
                # generated_thinking = generated_content.split("</think>")[0]
                generated_thinking = ""
                generated_text = ""
                if(interfere_mode not in [1, 2, 3]):## <think>thinking</think> -> answer
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
                elif(interfere_mode == 1):## <think>thinking_CoT -> thinking_answer</think>
                    if("</think>" in generated_content):
                        generated_text = generated_content.split("</think>")[1]
                        generated_thinking = generated_content.split("</think>")[0]
                    else:
                        generated_text = ""
                        generated_thinking = generated_content
                elif(interfere_mode == 2):## <think>thinking_CoT</think> -> answer
                    generated_text = generated_content
                    generated_thinking = ""
                elif(interfere_mode == 3):## thinking_CoT -> answer
                    generated_text = generated_content
                    generated_thinking = ""
            else:##commercial api: parsing with content&reasoning_content
                if(response['choices'][0]['message']['content'] is not None):
                    generated_text = response['choices'][0]['message']['content'].strip()
                else:
                    generated_text = ""

                if(response['choices'][0]['message']['reasoning_content'] is not None):
                    generated_thinking = response['choices'][0]['message']['reasoning_content'].strip()
                else:
                    generated_thinking = ""
            return [generated_text, generated_thinking]
    
    # used for text/code-davinci
    def prompt_generate(self, input_string, temperature = 0.0):
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
                                 'llama2-70b-chat', 'llama2-7b-chat', 'mistral-base', 'mistral-sft', 'mistral-dpo', 'o1-mini', 'o1']:
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