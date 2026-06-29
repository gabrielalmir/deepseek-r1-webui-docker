#!/usr/bin/bash
# export OPENAI_BASE_URL=http://localhost:11434/v1
# structured-report extract excel examples/rectal_mri_esmo.yaml \
#   --prompt  examples/rectal_mri_esmo.optimized.prompt.yaml \
#   --input /home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/intenral_data/原始报告.xlsx \
#   --output /home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/intenral_data/原始报告_esmo_qwen3-8b_direction.xlsx \
#   --checkpoint /home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/intenral_data/log/原始报告_esmo_qwen3-8b_direction.ckpt.json \
#   --error-log /home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/intenral_data/log/result.qwen3-8b.errors.jsonl \
#   --sheet-name Sheet1 \
#   --id-column patient_id \
#   --report-column Report \
#   --provider ollama \
#   --model qwen3:8b 


# structured-report extract excel examples/rectal_mri_esmo.yaml \
#   --prompt examples/rectal_mri_esmo.optimized.prompt.yaml \
#   --input /home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/intenral_data/原始报告.xlsx \
#   --output /home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/intenral_data/原始报告_esmo_deepseek-r1-8b_direction.xlsx \
#   --checkpoint /home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/intenral_data/log/原始报告_esmo_deepseek-r1-8b_direction.ckpt.json \
#   --error-log /home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/intenral_data/log/result.deepseek-r1-8b.errors.jsonl \
#   --sheet-name Sheet1 \
#   --id-column patient_id \
#   --report-column Report \
#   --provider ollama \
#   --model deepseek-r1:8b 

# export OPENAI_BASE_URL=https://api.deepseek.com
# export OPENAI_API_KEY=...
# structured-report extract excel examples/rectal_mri_esmo.yaml \
#   --prompt examples/rectal_mri_esmo.optimized.prompt.yaml \
#   --input /home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/intenral_data/原始报告.xlsx \
#   --output /home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/intenral_data/原始报告_esmo_deepseek-reasoner_direction.xlsx \
#   --checkpoint /home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/intenral_data/log/原始报告_esmo_deepseek-reasoner_direction.ckpt.json \
#   --error-log /home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/intenral_data/log/result.deepseek-reasoner.errors.jsonl \
#   --sheet-name Sheet1 \
#   --id-column patient_id \
#   --report-column Report \
#   --provider deepseek \
#   --model deepseek-reasoner

export OPENAI_BASE_URL=https://api.deepseek.com
: "${OPENAI_API_KEY:?Set OPENAI_API_KEY before running this script}"
structured-report prompt optimize examples/rectal_mri.yaml \
  --output examples/rectal_mri.optimized.prompt.yaml \
  --provider deepseek \
  --model deepseek-reasoner


export OPENAI_BASE_URL=http://localhost:11434/v1
structured-report extract excel examples/rectal_mri.yaml \
  --prompt  examples/rectal_mri.optimized.prompt.yaml \
  --input /home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/intenral_data/原始报告.xlsx \
  --output /home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/intenral_data/原始报z告_qwen3-8b_fe.xlsx \
  --checkpoint /home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/intenral_data/log/原始报告_qwen3-8b_fe.ckpt.json \
  --error-log /home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/intenral_data/log/result_qwen3-8b_fe.qwen3-8b.errors.jsonl \
  --sheet-name Sheet1 \
  --id-column patient_id \
  --report-column Report \
  --provider ollama \
  --model qwen3:8b 
