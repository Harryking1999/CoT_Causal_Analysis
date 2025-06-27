#!/bin/bash

# recal_extract_answer.sh - Script to re-extract answers from existing output files

# Default values
API_BASE_NUM=1
API_KEY="your_api_key_here"
MODEL_NAME="gpt-3.5-turbo"
DATASET="GSM8K"
INPUT_FILE=""
INTERFERE_MODE=0

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --api_base_num)
            API_BASE_NUM="$2"
            shift 2
            ;;
        --api_key)
            API_KEY="$2"
            shift 2
            ;;
        --model_name)
            MODEL_NAME="$2"
            shift 2
            ;;
        --dataset)
            DATASET="$2"
            shift 2
            ;;
        --input_file)
            INPUT_FILE="$2"
            shift 2
            ;;
        --interfere_mode)
            INTERFERE_MODE="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 --input_file <file> [--api_base_num <num>] [--api_key <key>] [--model_name <name>] [--dataset <dataset>] [--interfere_mode <mode>]"
            exit 1
            ;;
    esac
done

# Check if input file is provided
if [ -z "$INPUT_FILE" ]; then
    echo "Error: --input_file is required"
    echo "Usage: $0 --input_file <file> [--api_base_num <num>] [--api_key <key>] [--model_name <name>] [--dataset <dataset>] [--interfere_mode <mode>]"
    exit 1
fi

# Check if input file exists
if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: Input file '$INPUT_FILE' does not exist"
    exit 1
fi

echo "Running recal_extract_answer.py with the following parameters:"
echo "  Input file: $INPUT_FILE"
echo "  API base num: $API_BASE_NUM"
echo "  Model name: $MODEL_NAME"
echo "  Dataset: $DATASET"
echo "  Interfere mode: $INTERFERE_MODE"

# Run the Python script
python scripts/recal_extract_answer.py \
    --api_base_num "$API_BASE_NUM" \
    --api_key "$API_KEY" \
    --model_name "$MODEL_NAME" \
    --dataset "$DATASET" \
    --input_file "$INPUT_FILE" \
    --interfere_mode "$INTERFERE_MODE" 