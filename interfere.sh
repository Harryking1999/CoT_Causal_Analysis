#!/usr/bin/env bash
# Copyright (c) Guangsheng Bao and Hongbo Zhang.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#
# command help
if [ $# == '0' ]; then
    echo "Please follow the usage:"
    echo "    bash $0 gpt-3.5-turbo Addition:6 cot0shot goldreason"
    echo "    bash $0 gpt-3.5-turbo Product:3 cot0shot randomreason"
    echo "    bash $0 gpt-3.5-turbo Addition:6 cot0shot defaultreason strongbias"
    echo "    bash $0 gpt-3.5-turbo Addition:6 cot0shot goldreason strongbias randomrole"
    echo "    bash $0 gpt-3.5-turbo Addition:6 cot0shot goldreason strongbias randomrole 1"
    echo "    bash $0 gpt-3.5-turbo Addition:6 cot0shot goldreason strongbias randomrole 1 0"
    exit
fi

# run command
model_name=$1 # gpt-3.5-turbo, gpt-4, etc.
dataset=$2  # Addition, Product, ProofWriter, etc.
prompts=$3  # cot0shot, direct
do_reason=$4 # defaultreason, goldreason, randomreason
do_bias=$5  # nobias, weakbias, strongbias
do_role=$6  # defaultrole, randomrole
interfere_mode=$7  # 0=default, 1=test Y1 internal causality, 2=test Y1 and Z(Y2) causality, 3=test instruction-Y2-Z causality
api_base_num=$8  # 0=https://api.deepseek.com/beta, 1=http://localhost:8080/v1

if [ $# == '4' ]; then
    do_bias="nobias"
    do_role="defaultrole"  # default role
    interfere_mode=0
    api_base_num=0
fi

if [ $# == '5' ]; then
    do_role="defaultrole"  # default role
    interfere_mode=0
    api_base_num=0
fi

if [ $# == '6' ]; then
    interfere_mode=0
    api_base_num=0
fi

if [ $# == '7' ]; then
    api_base_num=0
fi

outdir=exp_cot/output

mkdir -p $outdir

echo `date`, Evaluating samples from ${dataset} using prompts ${prompts} with ${do_reason} and ${do_role} and ${do_bias} and mode ${interfere_mode} and api_base_num ${api_base_num} and seed ${SEED}...
python scripts/interfere.py  --dataset $dataset --prompt $prompts --outdir $outdir \
                             --do_reason $do_reason  --do_role $do_role --do_bias $do_bias \
                             --interfere_mode $interfere_mode --api_base_num $api_base_num \
                             --api_key $api_key --model_name $model_name