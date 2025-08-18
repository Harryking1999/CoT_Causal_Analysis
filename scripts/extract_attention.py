import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import pandas as pd
import re
import h5py
from typing import List, Tuple
import numpy as np

Attn = Tuple[Tuple[torch.Tensor, ...], ...]  # (layers) -> (tensors per layer)

def pack_cpu_fp16(attn: Attn) -> Attn:
    """Move to CPU and cast to float16 for smaller storage."""
    return tuple(tuple(t.detach().to('cpu', dtype=torch.float16).contiguous()
                    for t in layer) for layer in attn)

# allowed thousands separators inside numbers: comma, spaces (incl. NBSP/thin), underscore, apostrophe, middle dot
_SEP_CLASS = r"[,\s\u00A0\u202F\u2009\u200A\u2007_'·]"
# matches numbers like "1,225,519", "1 225 519", "1225519", and optional decimals like "1,234.56"
_NUM_WITH_SEPS = re.compile(
    rf"(?x)"                                  # verbose
    rf"(?<!\w)"                               # no letter/number just before
    rf"("                                     
    rf"\d{{1,3}}(?:{_SEP_CLASS}\d{{3}})+(?:[.,]\d+)?"
    rf"|"
    rf"\d+(?:[.,]\d+)?"                       # plain digits w/ optional decimal
    rf")"
    rf"(?!\w)"                                # no letter/number just after
)

def new_extract_answer_location(gen_text, gold, tokenizer):
    """
    Find a numeric answer that may contain grouping separators (commas/spaces/etc.),
    return its token span [start_tok, end_tok) in `gen_text` tokenization,
    and return both the raw matched string (with separators) and the normalized digits.

    Returns:
        start_tok (int), end_tok (int), answer_raw (str), answer_norm (str), (char_s, char_e)
    """
    matches = list(_NUM_WITH_SEPS.finditer(gen_text))
    if not matches:
        raise ValueError("No numeric-like text found.")

    gold_norm = None
    if gold is not None:
        gold_norm = re.sub(r"\D", "", str(gold))

    # Prefer a match whose digits equal gold's digits; else take the last match
    def norm_digits(m): return re.sub(r"\D", "", m.group(1))
    candidates = [m for m in matches if gold_norm and norm_digits(m) == gold_norm]
    m = candidates[-1] if candidates else matches[-1]

    answer_raw = m.group(1)                 # e.g., "1,225,519"
    answer_norm = re.sub(r"\D", "", answer_raw)  # e.g., "1225519"
    char_s, char_e = m.span(1)              # includes separators inside the number

    # --- Map char span -> token span ---
    try:
        enc = tokenizer(
            gen_text,
            add_special_tokens=False,
            return_offsets_mapping=True,
            return_special_tokens_mask=True,
        )
        offsets = enc["offset_mapping"]
        # print(offsets)

        # token covering first char of the match
        start_tok = next(i for i, (a, b) in enumerate(offsets) if a <= char_s < b)
        # token covering last char of the match (char_e is exclusive)
        end_tok = next(i for i, (a, b) in reversed(list(enumerate(offsets))) if a < char_e <= b) + 1

    except Exception:
        # Fallback without offsets: count tokens in prefixes
        start_tok = len(tokenizer(gen_text[:char_s], add_special_tokens=False)["input_ids"])
        end_tok   = len(tokenizer(gen_text[:char_e], add_special_tokens=False)["input_ids"])

    return start_tok, end_tok, answer_raw, answer_norm, (char_s, char_e)


# Brute force algorithm for string matching
def bruteForce(S, P):
    start_indexes = []
    for i in range(len(S) - len(P) + 1):
        if S[i : i + len(P)] == P:
            start_indexes.append(i)
    return start_indexes

def extract_answer_location(seq, text, gold, tokenizer):
    # TODO： use new output format to extract answer location (see wechat info)

    # Given the generated text and the gold answer, extract the start and end indices of the answer in the text.
    # gold = output['answer'][1]
    gen_out = text.split('\n')
    gen_out = [line for line in gen_out if len(re.findall('\d+', line)) > 0]
    # print(gen_out)
    # print(len(gen_out))
    if(len(gen_out) == 0):
        raise ValueError("No valid output found in the generated text.")
    else:
        gen_out = gen_out[-1]
    
    answer = gen_out #.replace(',', '').replace('\\!', '').replace('\\', '').replace(" ", "")  # do not remove any character
    answer = re.findall('\d+', answer)
    # print(answer)
    answer = gold if gold in answer else answer[-1]
    answer = answer.strip()
    answer = str(int(answer))  # expect integer only

    try:
        m = re.search(str(int(answer)), text)
        if m:
            ans_range = m.span()
            ans_str = text[ans_range[0]:ans_range[1]]
            encoded_ans = tokenizer.encode(ans_str, add_special_tokens=False)
            # print(encoded_ans)
            
            result = []
            token_list = seq[0].tolist()
            start = 0
            for i in range(len(token_list)):
                if token_list[i] == 198:  # 198 is the token for '\n'
                    result.append(token_list[start:i+1])
                    start = i + 1
            result.append(token_list[start:])
 
            start_indexes = bruteForce(result[-1], encoded_ans)
            if len(start_indexes) > 1:
                print(f"Warning: Multiple occurrences of the answer found. Using the last occurrence.")

            return start_indexes[-1] + start, start_indexes[-1] + start + len(encoded_ans), answer         
    except Exception as e:
        print(f"Error finding answer in text: {e}")
        return None

def extract_token_attention(instruct, cot, seq, attns, tokenizer, inputs, inspect_token_index, token_index):
    """
    inspect_token_index : 1-based index in the generated sequence

    return instruct_attention, cot_attention, token_attn
    - instruct_attention: cumulated attention of the inspect token over the instruction tokens
    - cot_attention: cumulated attention of the inspect token over CoT tokens
    - token_attn: tensor storing attention from the inspect token to all previous tokens in the sequence
    """

    # Calculate token lengths
    instruct_tokens = tokenizer(instruct, return_tensors="pt")["input_ids"].shape[1]
    cot_tokens = tokenizer(cot, return_tensors="pt")["input_ids"].shape[1]

    assert inspect_token_index < seq.shape[1]-inputs["input_ids"].shape[1], "Inspect token index out of bounds"
    assert token_index < seq.shape[1], "Token index out of bounds"

    tokens = tokenizer.convert_ids_to_tokens(seq[0], skip_special_tokens=False)[:token_index+1] # select correct subsequence
    # Token cleanup
    token_labels = [t.replace("Ġ", "") for t in tokens]  # remove BPE artifacts

    # Extract attention from last layer
    layer_index = -1
    selected_layer = attns[inspect_token_index][layer_index] # (heads, seq, seq)
    # print(f"Selected layer shape: {selected_layer.shape}")
    attn_from_i = selected_layer.squeeze()  # (heads, seq)
    # print(f"Selected layer shape: {attn_from_i.shape}") 
    avg_attn_from_i = attn_from_i.mean(dim=0).cpu().detach().numpy()

    instruct_attention = avg_attn_from_i[:instruct_tokens].sum()
    cot_attention = avg_attn_from_i[instruct_tokens:instruct_tokens+cot_tokens].sum()

    return instruct_attention, cot_attention, avg_attn_from_i

def get_total_attention(instruct, cot, attns, seq, inputs, start, end, tokenizer):
    """
    total_attn:[attn] list of attention values for each token in the range [start, end)
    """
    total_instruct_attention = 0
    total_cot_attention = 0
    total_attn = []
    for i in range(start, end):
        instruct_attention, cot_attention, token_attn = extract_token_attention(instruct, cot, seq, attns, tokenizer, inputs, i-inputs["input_ids"].shape[1], i)
        total_instruct_attention += instruct_attention
        total_cot_attention += cot_attention
        total_attn.append(token_attn)
    
    return total_instruct_attention, total_cot_attention, total_attn

def main():
    # Load model
    model_name = "Qwen/Qwen2.5-3B-Instruct"
    model = AutoModelForCausalLM.from_pretrained(model_name, output_attentions=True, device_map="auto")
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    # Load output data
    # output = pd.read_json("../exp_cot/output/output.Addition_6.cot0shot.math_teacher.Qwen2.5-3B-Base.thinking.json")
    output = pd.read_json("../exp_cot/output/output.Addition_6.newdirectbase.defaultreason_strongbias.Qwen2.5-3B-GRPO-600.modedefault.json")
    # Variables to store extracted accumulated attention values
    extracted_df = pd.DataFrame(columns=["text","extracted_ans","start","end","instruct_attention", "cot_attention"])
    all_answer_attn = []
    all_generated_attn = []

    for i in range(495, output.shape[0]):
        # instruct = output["cot0shot.math teacher_input"][i]
        instruct = output["newdirectbase.defaultreason_strongbias_input_user"][i]
        # cot = output["cot0shot.math teacher_output_CoT"][i]
        cot = output["newdirectbase.defaultreason_strongbias_input_assistant"][i]
        # ans = output["newdirectbase.defaultreason_strongbias_output"][i]
        if output["newdirectbase.defaultreason_strongbias_output"][i] == "":
            continue

        messages = [
            {"role": "user", "content": instruct},
            {"role": "assistant", "content": cot}
        ]
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=False # token(s) that indicate the start of an assistant message will be appended to the formatted output
        )

        inputs = tokenizer(text[:-11], return_tensors="pt").to(model.device) # Input ids
        gen_out = model.generate(
            **inputs,
            max_new_tokens=8192,            # generate up to 8192 new tokens
            output_attentions=True,       # tell the forward pass to keep attentions
            return_dict_in_generate=True  # return a GenerationOutput instead of just the tokens
        )

        seq      = gen_out.sequences                 # (batch, src + new) token ids
        attns    = gen_out.attentions                # attns[generated_token][layer][batch_size, num_heads, generated_length, sequence_length]
        # https://huggingface.co/docs/transformers/en/internal/generation_utils#transformers.generation.GenerateDecoderOnlyOutput.attentions

        generated_text = tokenizer.batch_decode(seq, skip_special_tokens=False)[0]

        # start, end, extracted_answer = extract_answer_location(seq, generated_text, output['answer'][i], tokenizer)
        start, end, answer_raw, extracted_answer, _ = new_extract_answer_location(generated_text, output['answer'][i], tokenizer)
        print(start, end, extracted_answer)

        instruct_attention, cot_attention, total_attn = get_total_attention(instruct, cot, attns, seq, inputs, start, end, tokenizer)

        extracted_df.loc[i] = [generated_text, extracted_answer, start, end, instruct_attention, cot_attention]
        all_answer_attn.append(total_attn)
        all_generated_attn.append(attns)

        print(f"Sample {i+1}/{output.shape[0]}: Instruct Attention: {instruct_attention:.4f}, CoT Attention: {cot_attention:.4f}")

    # Locally save the data
    # extracted_df.to_csv(f"extracted_attn.Addition_6.cot0shot.math_teacher.Qwen2.5-3B-Base.thinking.csv", index=False)
    extracted_df.to_csv(f"extracted_attn.output.Addition_6.newdirectbase.defaultreason_strongbias.Qwen2.5-3B-GRPO-600.modedefault.csv", index=False)
    
    # Store attention vectors in HDF5 format
    dt = h5py.vlen_dtype(np.float32)     # vlen vectors of int64

    with h5py.File("extracted_token_attn_new.h5", "w") as f:
        rows = len(all_answer_attn)
        cols = max(len(r) for r in all_answer_attn)  # handle uneven row lengths
        dset = f.create_dataset(f"ragged", shape=(rows, cols),dtype=dt)
        
        empty = np.asarray([], dtype=np.float32)
        for i, row in enumerate(all_answer_attn):
            for j in range(cols):
                if j < len(row):
                    vec = np.asarray(row[j], dtype=np.float32).ravel()
                else:
                    vec = empty
                dset[i, j] = vec 
        # for i, row in enumerate(all_answer_attn):
        #     for j, arr in enumerate(row):
        #         dset[i, j] = arr       # each cell gets a 1-D array
    # load back
    # with h5py.File("extracted_token_attn.h5") as f:
    # out = f["ragged"][...]         # object array of arrays
    # print(out[0, 1], type(out[0, 1]), out[0, 1].shape)

    # Store entire generation seq & attn
    payload = [pack_cpu_fp16(e) for e in all_generated_attn]
    torch.save(payload, "all_attn_new.pt")
    # loaded_entries: List[Attn] = torch.load("all_attn.pt", map_location="cpu")


if __name__ == "__main__":
    main()