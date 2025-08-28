sh random_reason.sh X-R1-3B-4-FLAN-COT-ZS-KL001 ProofWriter newdirect
sh random_reason.sh X-R1-3B-4-FLAN-COT-ZS-KL001 LOGIQA newdirect
sh random_reason.sh X-R1-3B-4-FLAN-COT-ZS-KL001 FOLIO newdirect
sh random_reason.sh X-R1-3B-4-FLAN-COT-FS-KL001 ProofWriter newdirect
sh random_reason.sh X-R1-3B-4-FLAN-COT-FS-KL001 LOGIQA newdirect
sh random_reason.sh X-R1-3B-4-FLAN-COT-FS-KL001 FOLIO newdirect
# python ./scripts/openai_math500.py --model_name gpt-4.1-mini --file_path ./exp_cot/output/output.MATH500.newdirectbase.math_teacher.Qwen2.5-3B-GRPO-2000.json --mode 1
# python ./scripts/openai_math500.py --model_name gpt-4.1-mini --file_path exp_cot/output/output.MATH500.newdirectbase.randomreason.Qwen2.5-3B-GRPO-2000.modedefault.json --mode 0
# python ./scripts/openai_math500.py --model_name gpt-4.1-mini --file_path exp_cot/output/output.MATH500.newdirectbase.defaultreason.Qwen2.5-3B-GRPO-1000.modedefault.json --mode 0
# python ./scripts/openai_math500.py --model_name gpt-4.1-mini --file_path exp_cot/output/output.MATH500.newdirectbase.defaultreason_strongbias.Qwen2.5-3B-GRPO-1000.modedefault.json --mode 0
# python .\scripts\openai_math500.py --model_name gpt-4.1-mini --file_path ./exp_cot/output/output.MATH500.newdirect.math_teacher.deepseek-reasoner.json --mode 1
# python ./scripts/openai_math500.py --model_name gpt-4.1-mini --file_path ./exp_cot/output/output.MATH500.newdirect.math_teacher.QwQ-32B.json --mode 1
# python ./scripts/openai_math500.py --model_name gpt-4.1-mini --file_path ./exp_cot/output/output.MATH500.newdirect.math_teacher.DeepSeekR1-Qwen-7B.json --mode 1