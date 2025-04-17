#!/usr/bin/env bash
# Copyright (c) Guangsheng Bao and Hongbo Zhang.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#
# command help
if [ $# == '0' ]; then
    echo "Please follow the usage:"
    echo "    bash $0 output.Addition_6.cot0shot.math_teacher.deepseek-reasoner.json"
    echo "    bash $0 output.Product_3.cot0shot.math_teacher.deepseek-reasoner.json"
    exit
fi

# run command
input_file=$1  # Input file name in exp_cot/output/

if [ $# -lt 1 ]; then
    echo "Error: Please provide input file"
    echo "Usage: bash $0 <input_file>"
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

echo `date`, Processing ${input_path} ...
python scripts/distill_thinking_CoT.py --input_file $input_path 