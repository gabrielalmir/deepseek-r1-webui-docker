import pandas as pd
# feature_extract_file = '/home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/external_data/deepseek-reasoner_FE.xlsx'
# fe_df = pd.read_excel(feature_extract_file)
# feature_cols = ['肿瘤的位置', '肿瘤累及长度', '肿瘤浸润深度', '直肠系膜内淋巴结评估', '直肠系膜外淋巴结评估', 'CRM受累情况', 'EMVI受累情况']
# # print(pd.isna(fe_df.loc[0, '直肠系膜外淋巴结评估']))
# for index in fe_df.index:
#     fe_df.loc[index, 'Report'] = ""
#     for col in feature_cols:
#         value = fe_df.loc[index, col]
#         if col in ['直肠系膜内淋巴结评估', '直肠系膜外淋巴结评估', 'CRM受累情况', 'EMVI受累情况']:
#             if pd.isna(value) or value == 'None':
#                 value = '无'
#         fe_df.loc[index, 'Report'] += f"{col}：{value}；"
# fe_df.drop(columns=feature_cols, inplace=True)
# fe_df.to_excel('/home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/external_data/deepseek-reasoner_FE_report.xlsx', index=False)    

# feature_extract_file = '/home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/external_data/ollama-deepseek-r1-8b_FE.xlsx'
# fe_df = pd.read_excel(feature_extract_file)
# feature_cols = ['肿瘤的位置', '肿瘤累及长度', '肿瘤浸润深度', '直肠系膜内淋巴结评估', '直肠系膜外淋巴结评估', 'CRM受累情况', 'EMVI受累情况']
# # print(pd.isna(fe_df.loc[0, '直肠系膜外淋巴结评估']))
# for index in fe_df.index:
#     fe_df.loc[index, 'Report'] = ""
#     for col in feature_cols:
#         value = fe_df.loc[index, col]
#         if col in ['直肠系膜内淋巴结评估', '直肠系膜外淋巴结评估', 'CRM受累情况', 'EMVI受累情况']:
#             if pd.isna(value) or value == 'None':
#                 value = '无'
#         fe_df.loc[index, 'Report'] += f"{col}：{value}；"
# fe_df.drop(columns=feature_cols, inplace=True)
# fe_df.to_excel('/home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/external_data/ollama-deepseek-r1-8b_FE_report.xlsx', index=False)  

feature_extract_file = '/home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/external_data/ollama-qwen3-8b_FE.xlsx'
fe_df = pd.read_excel(feature_extract_file)
feature_cols = ['肿瘤的位置', '肿瘤累及长度', '肿瘤浸润深度', '直肠系膜内淋巴结评估', '直肠系膜外淋巴结评估', 'CRM受累情况', 'EMVI受累情况']
# print(pd.isna(fe_df.loc[0, '直肠系膜外淋巴结评估']))
for index in fe_df.index:
    fe_df.loc[index, 'Report'] = ""
    for col in feature_cols:
        value = fe_df.loc[index, col]
        if col in ['直肠系膜内淋巴结评估', '直肠系膜外淋巴结评估', 'CRM受累情况', 'EMVI受累情况']:
            if pd.isna(value) or value == 'None':
                value = '无'
        fe_df.loc[index, 'Report'] += f"{col}：{value}；"
fe_df.drop(columns=feature_cols, inplace=True)
fe_df.to_excel('/home/fsk/deepseek-r1-webui-docker/project/rectal_structured_report/structured_reporting/data/external_data/ollama-qwen3-8b_FE_report.xlsx', index=False) 