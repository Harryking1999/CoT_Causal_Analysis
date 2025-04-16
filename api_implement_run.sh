#!/usr/bin/env bash
# Copyright (c) Guangsheng Bao and Hongbo Zhang.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#
# command help
if [ $# == '0' ]; then
    echo "Please follow the usage:"
    echo "    bash $0 output.GSM8K.cot0shot.math_teacher.json gpt-3.5-turbo 1 GSMK"
    echo "    bash $0 output.Addition:6.direct.math_teacher.json gpt-4 1 Addition:6"
    echo "    bash $0 output.Product:3.cot0shot.math_teacher.json deepseek-reasoner 3 Product:3"
    exit
fi

# run command
input_file=$1  # Input file name in exp_cot/output/
model_name=$2  # Model name: gpt-3.5-turbo, gpt-4, deepseek-reasoner, etc.
api_base_num=$3  # 1=openai api，2=bailian api
dataset=$4  # Dataset name: GSM8K, Addition:6, Product:3, etc.

if [ $# -lt 4 ]; then
    echo "Error: Please provide input file, model name, api_base_num and dataset"
    echo "Usage: bash $0 <input_file> <model_name> <api_base_num> <dataset>"
    exit 1
fi

# Set directory
outdir=./exp_cot/output
input_path="$outdir/$input_file"

# Check if file exists
if [ ! -f "$input_path" ]; then
    echo "Error: File not found: $input_path"
    exit 1
fi

echo `date`, Retrying failed items from ${input_path} using ${model_name} ...
python scripts/api_implement_run.py --input_file $input_path --outdir $outdir \
                          --api_key $api_key --model_name $model_name --api_base_num $api_base_num \
                          --dataset $dataset 