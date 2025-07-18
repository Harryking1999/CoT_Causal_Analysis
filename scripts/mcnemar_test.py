# Copyright (c) Guangsheng Bao and Hongbo Zhang.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#
import os.path as path
import json
import argparse
import numpy as np
import statsmodels.stats.contingency_tables as ssc


def load_output(output_file):
    with open(output_file, 'r', encoding="utf-8") as fin:
        data = json.load(fin)  # data from default role to new role
        print(f'Loaded {len(data)} items from {output_file}')
    return data


def get_accuracy(output_file):
    outputs = load_output(output_file)
    
    # Check if file has .extracted suffix
    is_extracted = '.extracted' in output_file
    
    if is_extracted:
        # For extracted files, use key_prefix format
        file_name = path.basename(output_file).replace('.extracted', '')
        prompt = file_name.split(".")[3].replace("math_teacher", "math teacher")
        key = "newdirect." + prompt
    else:
        # Original format
        key = path.basename(output_file).split('.')
        key = '.'.join(key[2:4]).replace('math_teacher', 'math teacher')
    
    aa = []
    for item in outputs:
        result = item[f'{key}_result']
        aa.append(1 if result else 0)
    return np.mean(aa)


def get_paired_results(group_a_file, group_b_file):
    group_a = load_output(group_a_file.replace(':', '_'))
    group_b = load_output(group_b_file.replace(':', '_'))
    assert len(group_a) == len(group_b)
    
    # Check if files have .extracted suffix
    is_extracted_a = '.extracted' in group_a_file
    is_extracted_b = '.extracted' in group_b_file
    
    if is_extracted_a:
        # For extracted files, use key_prefix format
        file_name_a = path.basename(group_a_file).replace('.extracted', '')
        prompt_a = file_name_a.split(".")[3].replace("math_teacher", "math teacher")
        key_a = "newdirect." + prompt_a
        if('newdirectbase' in file_name_a):
            key_a = "newdirectbase." + prompt_a
    else:
        # Original format
        key_a = path.basename(group_a_file).split('.')
        key_a = '.'.join(key_a[2:4]).replace('math_teacher', 'math teacher')
    
    if is_extracted_b:
        # For extracted files, use key_prefix format
        file_name_b = path.basename(group_b_file).replace('.extracted', '')
        prompt_b = file_name_b.split(".")[3].replace("math_teacher", "math teacher")
        print("file_name_b: ", file_name_b)
        key_b = "newdirect." + prompt_b
        if('newdirectbase' in file_name_b):
            key_b = "newdirectbase." + prompt_b
        print("promtp_b: ", prompt_b)
    else:
        # Original format
        key_b = path.basename(group_b_file).split('.')
        key_b = '.'.join(key_b[2:4]).replace('math_teacher', 'math teacher')

    aa = []
    bb = []
    for a, b in zip(group_a, group_b):
        assert a['id'] == b['id']
        
        # Use appropriate key format based on file type
        if is_extracted_a:
            result_a = a[f'{key_a}_result']
            # print(f"{key_a}_result")
        else:
            result_a = a[f'{key_a}_result']
            
        if is_extracted_b:
            result_b = b[f'{key_b}_result']
            # print(f"{key_b}_result")
        else:
            result_b = b[f'{key_b}_result']

        # Check if result_a is True or contains "true" string
        if isinstance(result_a, bool):
            aa.append(1 if result_a else 0)
        elif isinstance(result_a, str):
            aa.append(1 if 'true' in result_a.lower() else 0)
        else:
            aa.append(1 if result_a else 0)

        # Check if result_b is True or contains "true" string
        if isinstance(result_b, bool):
            bb.append(1 if result_b else 0)
        elif isinstance(result_b, str):
            bb.append(1 if 'true' in result_b.lower() else 0)
        else:
            bb.append(1 if result_b else 0)
    return aa, bb


def mcnemar_test(aa, bb):
    aa = np.array(aa)
    bb = np.array(bb)
    table = np.array([[0., 0.], [0., 0.]])
    table[0, 0] = ((1 - aa) * (1 - bb)).sum()
    table[0, 1] = ((1 - aa) * bb).sum()
    table[1, 0] = (aa * (1 - bb)).sum()
    table[1, 1] = (aa * bb).sum()
    result = ssc.mcnemar(table, exact=True, correction=True)
    return result.statistic, result.pvalue

def cohens_d_paired(aa, bb):
    aa = np.array(aa)
    bb = np.array(bb)
    diff = bb - aa
    mean_diff = np.mean(diff)
    std_diff = np.std(diff, ddof=1)
    return mean_diff / std_diff


def get_average_treatment_effect(group_a_file, group_b_file):
    aa, bb = get_paired_results(group_a_file, group_b_file)
    base = np.mean(aa)
    ate = np.mean(bb) - np.mean(aa)
    _, pvalue = mcnemar_test(aa, bb)
    return base, ate, pvalue


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--group_a', type=str, default='exp_cot/output/output.Addition_6.cot0shot.defaultreason.gpt-3.5-turbo.json')
    parser.add_argument('--group_b', type=str, default='exp_cot/output/output.Addition_6.cot0shot.randomreason.gpt-3.5-turbo.json')
    args = parser.parse_args()

    aa, bb = get_paired_results(args.group_a.replace(':', '_'),args.group_b.replace(':', '_'))
    print(f'Group A: {np.mean(aa):.3f} ({np.sum(aa)}/{len(aa)})')
    print(f'Group B: {np.mean(bb):.3f} ({np.sum(bb)}/{len(bb)})')
    print(f'B - A: {np.mean(bb) - np.mean(aa):.3f} ({np.sum(bb) - np.sum(aa)}/{len(bb)})')

    statistic, pvalue = mcnemar_test(aa, bb)
    cohens_d = cohens_d_paired(aa, bb)
    print(f'Statistic: {statistic:.2f}, p-value: {pvalue:.2g}, cohens_d: {cohens_d:.2g}')
