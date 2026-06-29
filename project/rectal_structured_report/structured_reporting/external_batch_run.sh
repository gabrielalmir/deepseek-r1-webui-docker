#!/usr/bin/bash
# export OPENAI_BASE_URL=http://localhost:11434/v1
# structured-report extract excel examples/rectal_mri_esmo.yaml \
#   --prompt  examples/rectal_mri_esmo.optimized.prompt.yaml \
#   --input 副本直肠癌多中心文本.xlsx \
#   --output outputs/副本直肠癌多中心文本_esmo_qwen3-8b_direction.xlsx \
#   --checkpoint outputs/副本直肠癌多中心文本_esmo_qwen3-8b_direction.ckpt.json \
#   --error-log outputs/result.qwen3-8b.errors.jsonl \
#   --sheet-name Sheet1 \
#   --id-column patient_id \
#   --report-column Report \
#   --provider ollama \
#   --model qwen3:8b 


# structured-report extract excel examples/rectal_mri_esmo.yaml \
#   --prompt examples/rectal_mri_esmo.optimized.prompt.yaml \
#   --input 副本直肠癌多中心文本.xlsx \
#   --output outputs/副本直肠癌多中心文本_esmo_deepseek-r1-8b_direction.xlsx \
#   --checkpoint outputs/副本直肠癌多中心文本_esmo_deepseek-r1-8b_direction.ckpt.json \
#   --error-log outputs/result.deepseek-r1-8b.errors.jsonl \
#   --sheet-name Sheet1 \
#   --id-column patient_id \
#   --report-column Report \
#   --provider ollama \
#   --model deepseek-r1:8b 

export OPENAI_BASE_URL=https://api.deepseek.com
: "${OPENAI_API_KEY:?Set OPENAI_API_KEY before running this script}"
structured-report extract excel examples/rectal_mri_esmo.yaml \
  --prompt examples/rectal_mri_esmo.optimized.prompt.yaml \
  --input /home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/external_data/deepseek-reasoner_FE_report.xlsx \
  --output /home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/external_data/deepseek-reasoner_deepseek-reasoner_ESMO.xlsx \
  --checkpoint /home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/external_data/log/deepseek-reasoner_deepseek-reasoner_ESMO.ckpt.json \
  --error-log /home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/external_data/log/deepseek-reasoner_deepseek-reasoner_ESMO.errors.jsonl \
  --sheet-name Sheet1 \
  --id-column patient_id \
  --report-column Report \
  --provider openai \
  --model deepseek-reasoner

structured-report extract excel examples/rectal_mri_esmo.yaml \
  --prompt examples/rectal_mri_esmo.optimized.prompt.yaml \
  --input /home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/external_data/ollama-deepseek-r1-8b_FE_report.xlsx \
  --output /home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/external_data/deepseek-r1-8b_deepseek-reasoner_ESMO.xlsx \
  --checkpoint /home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/external_data/log/deepseek-r1-8b_deepseek-reasoner_ESMO.ckpt.json \
  --error-log /home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/external_data/log/deepseek-r1-8b_deepseek-reasoner_ESMO.errors.jsonl \
  --sheet-name Sheet1 \
  --id-column patient_id \
  --report-column Report \
  --provider openai \
  --model deepseek-reasoner

structured-report extract excel examples/rectal_mri_esmo.yaml \
  --prompt examples/rectal_mri_esmo.optimized.prompt.yaml \
  --input /home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/external_data/ollama-qwen3-8b_FE_report.xlsx \
  --output /home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/external_data/qwen3-8b_deepseek-reasoner_ESMO.xlsx \
  --checkpoint /home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/external_data/log/qwen3-8b_deepseek-reasoner_ESMO.ckpt.json \
  --error-log /home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/external_data/log/qwen3-8b_deepseek-reasoner_ESMO.errors.jsonl \
  --sheet-name Sheet1 \
  --id-column patient_id \
  --report-column Report \
  --provider openai \
  --model deepseek-reasoner

export OPENAI_BASE_URL=http://localhost:11434/v1
structured-report extract excel examples/rectal_mri_esmo.yaml \
  --prompt examples/rectal_mri_esmo.optimized.prompt.yaml \
  --input /home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/external_data/ollama-qwen3-8b_FE_report.xlsx \
  --output /home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/external_data/qwen3-8b_deepseek-r1-8b_ESMO.xlsx \
  --checkpoint /home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/external_data/log/qwen3-8b_deepseek-r1-8b_ESMO.ckpt.json \
  --error-log /home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/external_data/log/qwen3-8b_deepseek-r1-8b_ESMO.errors.jsonl \
  --sheet-name Sheet1 \
  --id-column patient_id \
  --report-column Report \
  --provider openai \
  --model deepseek-r1:8b

structured-report extract excel examples/rectal_mri_esmo.yaml \
  --prompt examples/rectal_mri_esmo.optimized.prompt.yaml \
  --input /home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/external_data/ollama-deepseek-r1-8b_FE_report.xlsx \
  --output /home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/external_data/deepseek-r1-8b_deepseek-r1-8b_ESMO.xlsx \
  --checkpoint /home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/external_data/log/deepseek-r1-8b_deepseek-r1-8b_ESMO.ckpt.json \
  --error-log /home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/external_data/log/deepseek-r1-8b_deepseek-r1-8b_ESMO.errors.jsonl \
  --sheet-name Sheet1 \
  --id-column patient_id \
  --report-column Report \
  --provider openai \
  --model deepseek-r1:8b

structured-report extract excel examples/rectal_mri_esmo.yaml \
  --prompt examples/rectal_mri_esmo.optimized.prompt.yaml \
  --input /home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/external_data/deepseek-reasoner_FE_report.xlsx \
  --output /home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/external_data/deepseek-reasoner_deepseek-r1-8b_ESMO.xlsx \
  --checkpoint /home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/external_data/log/deepseek-reasoner_deepseek-r1-8b_ESMO.ckpt.json \
  --error-log /home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/external_data/log/deepseek-reasoner_deepseek-r1-8b_ESMO.errors.jsonl \
  --sheet-name Sheet1 \
  --id-column patient_id \
  --report-column Report \
  --provider openai \
  --model deepseek-r1:8b


  structured-report extract excel examples/rectal_mri_esmo.yaml \
  --prompt examples/rectal_mri_esmo.optimized.prompt.yaml \
  --input /home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/external_data/ollama-qwen3-8b_FE_report.xlsx \
  --output /home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/external_data/qwen3-8b_qwen3-8b_ESMO.xlsx \
  --checkpoint /home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/external_data/log/qwen3-8b_qwen3-8b_ESMO.ckpt.json \
  --error-log /home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/external_data/log/qwen3-8b_qwen3-8b_ESMO.errors.jsonl \
  --sheet-name Sheet1 \
  --id-column patient_id \
  --report-column Report \
  --provider openai \
  --model qwen3:8b

structured-report extract excel examples/rectal_mri_esmo.yaml \
  --prompt examples/rectal_mri_esmo.optimized.prompt.yaml \
  --input /home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/external_data/ollama-deepseek-r1-8b_FE_report.xlsx \
  --output /home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/external_data/deepseek-r1-8b_qwen3-8b_ESMO.xlsx \
  --checkpoint /home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/external_data/log/deepseek-r1-8b_qwen3-8b_ESMO.ckpt.json \
  --error-log /home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/external_data/log/deepseek-r1-8b_qwen3-8b_ESMO.errors.jsonl \
  --sheet-name Sheet1 \
  --id-column patient_id \
  --report-column Report \
  --provider openai \
  --model qwen3:8b

structured-report extract excel examples/rectal_mri_esmo.yaml \
  --prompt examples/rectal_mri_esmo.optimized.prompt.yaml \
  --input /home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/external_data/deepseek-reasoner_FE_report.xlsx \
  --output /home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/external_data/deepseek-reasoner_qwen3-8b_ESMO.xlsx \
  --checkpoint /home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/external_data/log/deepseek-reasoner_qwen3-8b_ESMO.ckpt.json \
  --error-log /home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/external_data/log/deepseek-reasoner_qwen3-8b_ESMO.errors.jsonl \
  --sheet-name Sheet1 \
  --id-column patient_id \
  --report-column Report \
  --provider openai \
  --model qwen3:8b
