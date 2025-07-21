sh random_reason.sh Qwen2.5-3B-SFT-GRPO-4000 ProofWriter newdirectbase
sh random_reason.sh Qwen2.5-3B-SFT-GRPO-4000 LOGIQA newdirectbase
sh random_reason.sh Qwen2.5-3B-SFT-GRPO-4000 FOLIO newdirectbase
python ./scripts/openai_math500.py --model_name gpt-4.1-mini --file_path ./exp_cot/output/output.MATH500.newdirectbase.math_teacher.Qwen2.5-3B-SFT-GRPO-4000.json --mode 1
# python ./scripts/openai_math500.py --model_name gpt-4.1-mini --file_path exp_cot/output/output.MATH500.newdirectbase.randomreason.Qwen2.5-3B-GRPO-4000.modedefault.json --mode 0
# python ./scripts/openai_math500.py --model_name gpt-4.1-mini --file_path exp_cot/output/output.MATH500.newdirectbase.defaultreason.Qwen2.5-3B-GRPO-4000.modedefault.json --mode 0
# python ./scripts/openai_math500.py --model_name gpt-4.1-mini --file_path exp_cot/output/output.MATH500.newdirectbase.defaultreason_strongbias.Qwen2.5-3B-GRPO-4000.modedefault.json --mode 0
# python .\scripts\openai_math500.py --model_name gpt-4.1-mini --file_path ./exp_cot/output/output.MATH500.newdirect.math_teacher.deepseek-reasoner.json --mode 1
# python ./scripts/openai_math500.py --model_name gpt-4.1-mini --file_path ./exp_cot/output/output.MATH500.newdirect.math_teacher.QwQ-32B.json --mode 1
# python ./scripts/openai_math500.py --model_name gpt-4.1-mini --file_path ./exp_cot/output/output.MATH500.newdirect.math_teacher.DeepSeekR1-Qwen-7B.json --mode 1