import re
import json
from tqdm import tqdm
import random
import os
import argparse

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


def human_check(sample):
    # Print the sample
    print(f"Found wrong data, please check the reasoning and extract the answer.")
    predicted_reasoning = sample.pop("predicted_reasoning")

    # Add 'predicted_reasoning' back to the dictionary, but it will be placed at the end
    sample["predicted_reasoning"] = predicted_reasoning
    print(sample)
    
    
    # Get user input
    mark = input("Extract the option(A/B/C): ")
    return mark


