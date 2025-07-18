# # import openai
# # import json

# # # 配置OpenAI客户端连接到本地vLLM服务
# # openai.api_base = "http://localhost:8080/v1"
# # openai.api_key = "EMPTY"  # vLLM不需要真实的API key

# # # 合并系统prompt和用户prompt
# # system_prompt = "You are a helpful AI Assistant that provides well-reasoned and detailed responses. You first think about the reasoning process as an internal monologue and then provide the user with the answer. Respond in the following format: <think>\n...\n</think>\n<answer>\n...\n</answer>"

# # user_prompt = "Please solve the math problem.\nQuestion: What is the sum of 534280104 and 651658122? Please reason step by step.. I think the correct answer is: 1185838226\n:"

# # # 将系统prompt和用户prompt合并成完整的prompt
# # full_prompt = f"{system_prompt}\n\n{user_prompt}"

# # try:
# #     # 发送请求
# #     response = openai.Completion.create(
# #         model="Qwen2.5-3B-GRPO-16000",
# #         prompt=full_prompt,
# #         temperature=0.7,
# #         max_tokens=2000,
# #         stop=None,
# #         stream=False
# #     )
    
# #     # 打印完整响应
# #     print("=" * 50)
# #     print("完整响应内容:")
# #     print("=" * 50)
# #     print(response.choices[0].text)
# #     print("=" * 50)
    
# #     # 打印一些额外的响应信息
# #     print(f"模型: {response.model}")
# #     print(f"完成原因: {response.choices[0].finish_reason}")
# #     print(f"Token使用情况: {response.usage}")
    
# # except Exception as e:
# #     print(f"请求失败: {e}")
# #     print("请确保vLLM服务正在运行并且端口8080可访问")


# # response['choices'][0]['text']
# import openai
# import json
# import re

# # 配置OpenAI客户端连接到本地vLLM服务
# openai.api_base = "http://localhost:8080/v1"
# openai.api_key = "EMPTY"  # vLLM不需要真实的API key

# # 系统prompt和用户prompt
# system_prompt = "You are a helpful AI Assistant that provides well-reasoned and detailed responses. You first think about the reasoning process as an internal monologue and then provide the user with the answer. Respond in the following format: <think>\n...\n</think>\n<answer>\n...\n</answer>"

# user_prompt = "Please solve the math problem.\nQuestion: What is the sum of 534280104 and 651658122? Please reason step by step.. I think the correct answer is: 1185838226\n:"

# # 根据chat_template格式化prompt
# bos_token = ""  # 模拟bos_token
# full_prompt = f"{bos_token}{system_prompt}<｜User｜>{user_prompt}<｜Assistant｜>"

# try:
#     print("=" * 60)
#     print("第一次请求 - 正常请求")
#     print("=" * 60)
#     print("使用的prompt格式:")
#     print(repr(full_prompt))
#     print("-" * 60)
    
#     # 第一次请求
#     response1 = openai.Completion.create(
#         model="Qwen2.5-3B-GRPO-16000",
#         prompt=full_prompt,
#         temperature=0.7,
#         max_tokens=2000,
#         stop=["<｜end▁of▁sentence｜>"],
#         stream=False
#     )
    
#     # 打印第一次响应
#     first_response = response1['choices'][0]['text']
#     print("第一次完整响应内容:")
#     print("-" * 40)
#     print(first_response)
#     print("-" * 40)
#     print(f"模型: {response1['model']}")
#     print(f"完成原因: {response1['choices'][0]['finish_reason']}")
#     print(f"Token使用情况: {response1['usage']}")
    
#     # 处理第一次响应，找到</think>的位置并截取
#     think_end_pattern = r'</think>'
#     match = re.search(think_end_pattern, first_response)
    
#     if match:
#         # 截取到</think>之前的部分（包含</think>）
#         truncated_response = first_response[:match.end()]
#         print("\n" + "=" * 60)
#         print("截取的assistant响应 (到</think>为止):")
#         print("=" * 60)
#         print(truncated_response)
        
#         # 构造第二次请求的prompt (按照chat_template格式)
#         second_prompt = f"{bos_token}{system_prompt}<｜User｜>{user_prompt}<｜Assistant｜>{truncated_response}"
        
#         print("\n" + "=" * 60)
#         print("第二次请求 - 基于截取的响应继续")
#         print("=" * 60)
#         print("第二次请求的prompt格式:")
#         print(repr(second_prompt))
#         print("-" * 60)
        
#         # 第二次请求
#         response2 = openai.Completion.create(
#             model="Qwen2.5-3B-GRPO-16000",
#             prompt=second_prompt,
#             temperature=0.7,
#             max_tokens=2000,
#             stop=["<｜end▁of▁sentence｜>"],
#             stream=False
#         )
        
#         # 打印第二次响应
#         second_response = response2['choices'][0]['text']
#         print("第二次响应内容:")
#         print("-" * 40)
#         print(second_response)
#         print("-" * 40)
#         print(f"模型: {response2['model']}")
#         print(f"完成原因: {response2['choices'][0]['finish_reason']}")
#         print(f"Token使用情况: {response2['usage']}")
        
#         # 合并完整响应
#         print("\n" + "=" * 60)
#         print("完整合并响应:")
#         print("=" * 60)
#         print(truncated_response + second_response)
        
#     else:
#         print("\n警告: 在第一次响应中未找到</think>标记")
#         print("第一次响应可能不完整或格式不符合预期")
        
# except Exception as e:
#     print(f"请求失败: {e}")
#     print("请确保vLLM服务正在运行并且端口8080可访问")

# import openai
# import json

# # 配置OpenAI客户端连接到本地vLLM服务
# openai.api_base = "http://localhost:8080/v1"
# openai.api_key = "EMPTY"  # vLLM不需要真实的API key

# # 合并系统prompt和用户prompt
# system_prompt = "You are a helpful AI Assistant that provides well-reasoned and detailed responses. You first think about the reasoning process as an internal monologue and then provide the user with the answer. Respond in the following format: <think>\n...\n</think>\n<answer>\n...\n</answer>"

# user_prompt = "Please solve the math problem.\nQuestion: What is the sum of 534280104 and 651658122? Please reason step by step.. I think the correct answer is: 1185838226\n:"

# # 将系统prompt和用户prompt合并成完整的prompt
# full_prompt = f"{system_prompt}\n\n{user_prompt}"

# try:
#     # 发送请求
#     response = openai.Completion.create(
#         model="Qwen2.5-3B-GRPO-16000",
#         prompt=full_prompt,
#         temperature=0.7,
#         max_tokens=2000,
#         stop=None,
#         stream=False
#     )
    
#     # 打印完整响应
#     print("=" * 50)
#     print("完整响应内容:")
#     print("=" * 50)
#     print(response.choices[0].text)
#     print("=" * 50)
    
#     # 打印一些额外的响应信息
#     print(f"模型: {response.model}")
#     print(f"完成原因: {response.choices[0].finish_reason}")
#     print(f"Token使用情况: {response.usage}")
    
# except Exception as e:
#     print(f"请求失败: {e}")
#     print("请确保vLLM服务正在运行并且端口8080可访问")


# response['choices'][0]['text']
import openai
import json
import re

# 配置OpenAI客户端连接到本地vLLM服务
openai.api_base = "http://localhost:8080/v1"
openai.api_key = "EMPTY"  # vLLM不需要真实的API key

user_prompt = "Please solve the math problem.\nQuestion: What is the sum of 534280104 and 651658122? Please reason step by step.. I think the correct answer is: 1185838226\n. Let me solve the "

# 根据chat_template格式化prompt
bos_token = ""  # 模拟bos_token
full_prompt = f""

try:
    print("=" * 60)
    print("第一次请求 - 正常请求")
    print("=" * 60)
    print("使用的prompt格式:")
    print(repr(full_prompt))
    print("-" * 60)
    # 第一次请求
    response1 = openai.ChatCompletion.create(
        model="Qwen2.5-3B-Base",
        messages=[
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7,
        max_tokens=2000,
        stop=["<｜end▁of▁sentence｜>"],
        stream=False
    )
    
    # 打印第一次响应
    first_response = response1['choices'][0]['message']['content']
    print("第一次完整响应内容:")
    print("-" * 40)
    print(first_response)
    print("-" * 40)
    print(f"模型: {response1['model']}")
    print(f"完成原因: {response1['choices'][0]['finish_reason']}")
    print(f"Token使用情况: {response1['usage']}")
    
    # # 处理第一次响应，找到</think>的位置并截取
    # think_end_pattern = r'</think>'
    # match = re.search(think_end_pattern, first_response)
    
    # if match:
    #     # 截取到</think>之前的部分（包含</think>）
    #     truncated_response = first_response[:match.end()]
    #     print("\n" + "=" * 60)
    #     print("截取的assistant响应 (到</think>为止):")
    #     print("=" * 60)
    #     print(truncated_response)
        
    #     # 构造第二次请求的prompt (按照chat_template格式)
    #     second_prompt = f"{bos_token}{system_prompt}<｜User｜>{user_prompt}<｜Assistant｜>{truncated_response}"
        
    #     print("\n" + "=" * 60)
    #     print("第二次请求 - 基于截取的响应继续")
    #     print("=" * 60)
    #     print("第二次请求的prompt格式:")
    #     print(repr(second_prompt))
    #     print("-" * 60)
        
    #     # 第二次请求
    #     response2 = openai.Completion.create(
    #         model="Qwen2.5-3B-GRPO-16000",
    #         prompt=second_prompt,
    #         temperature=0.7,
    #         max_tokens=2000,
    #         stop=["<｜end▁of▁sentence｜>"],
    #         stream=False
    #     )
        
    #     # 打印第二次响应
    #     second_response = response2['choices'][0]['text']
    #     print("第二次响应内容:")
    #     print("-" * 40)
    #     print(second_response)
    #     print("-" * 40)
    #     print(f"模型: {response2['model']}")
    #     print(f"完成原因: {response2['choices'][0]['finish_reason']}")
    #     print(f"Token使用情况: {response2['usage']}")
        
    #     # 合并完整响应
    #     print("\n" + "=" * 60)
    #     print("完整合并响应:")
    #     print("=" * 60)
    #     print(truncated_response + second_response)
        
    # else:
    #     print("\n警告: 在第一次响应中未找到</think>标记")
    #     print("第一次响应可能不完整或格式不符合预期")
        
except Exception as e:
    print(f"请求失败: {e}")
    print("请确保vLLM服务正在运行并且端口8080可访问")