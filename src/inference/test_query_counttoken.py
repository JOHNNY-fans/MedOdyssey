import os
os.environ['HTTP_PROXY']='https://sunhongli:Tiankong1234@blsc-proxy.pjlab.org.cn:13128'
os.environ['HTTPS_PROXY']='https://sunhongli:Tiankong1234@blsc-proxy.pjlab.org.cn:13128'
os.environ['http_proxy']='https://sunhongli:Tiankong1234@blsc-proxy.pjlab.org.cn:13128'
os.environ['https_proxy']='https://sunhongli:Tiankong1234@blsc-proxy.pjlab.org.cn:13128'

import re
import json
import random
import asyncio

from tqdm import tqdm

# from utils import *

# 测试一部分还是全部
# 针对某一模型在某一数据上的结果
# 如果是full，那么清空原来结果，重新开始
# 如果是supply，那么只跑原来没跑过的id
# PART = 'supply'

# # 重试次数是0的时候不重试
# FORMAT_RETRY = 0
# API_RETRY = 20

# # 并发数
# ALL_CONCURRENT_LIMIT = 32
# # API_CONCURRENT_LIMIT = 1


# # MODEL_NAME = 'claude-3-haiku-20240307'
# # MODEL_NAME = 'gpt-4-turbo-2024-04-09'
# MODEL_NAME = 'claude-3-sonnet-20240229'
# # MODEL_NAME = 'gpt-3.5-turbo-0125'
# # MODEL_NAME = 'gpt-4o'
# # MODEL_NAME = 'moonshot-v1-128k'

# # MODEL_NAME = 'chatglm3-6b-128k'
# # MODEL_NAME = 'Yarn-Mistral-7b-128k'
MODEL_NAME = 'internlm2-chat-7b'

TASK_NAME_LIST = ['zh_norm', 'en_norm', 'zh_kg', 'en_kg', 'zh_table', 'zh_medcase', 'zh_counting', 'en_counting']
TASK_NAME = 'zh_medcase'

BASE_DIR = '/ailab/user/sunhongli/workspace/MedLongContextEval/dataset/task_data'
# # MODEL_DIR_BASE = '/ailab/user/sunhongli/weights/'

# OPENAI_BASE_URL = 'https://api.dstargpt.com/v1'
# OPENAI_API_KEY = 'sk-nyKp75atOaPKzCLBCaBa8cAc3cB9496fB8B95b563eB02aCf'

# OPENAI_BASE_URL = 'https://api.gpt.ge/v1'
# OPENAI_API_KEY = 'sk-zjDjS7pWcBf0Lo3U50B56885080c4353A9272fAf89A1D734'

# OPENAI_BASE_URL = 'https://api.moonshot.cn/v1'
# OPENAI_API_KEY = 'sk-J6Qp2qwhez7joRxhFva6tPHQioBVCBMv6H7HuTp5qmMxQAaU'

# openai_client = AsyncOpenAI(
#     base_url='https://api.moonshot.cn/v1',
#     api_key='sk-J6Qp2qwhez7joRxhFva6tPHQioBVCBMv6H7HuTp5qmMxQAaU',
# )

# openai_client = AsyncOpenAI(
#     base_url='http://10.254.30.46:39250/v1',
#     api_key='sshhhll',
# )


# tokenizer = TokenzierForLength(MODEL_NAME)

# def find_dicts(markdown):
#     dicts = []
#     if markdown == None:
#         return dicts
#     pattern = r"\{[^{}]*\}"
#     matches = re.findall(pattern, markdown)
#     for match in matches:
#         try:
#             d = json.loads(match)
#             if isinstance(d, dict):
#                 dicts.append(d)
#         except:
#             pass
#     return dicts

# def format_check(markdown: str):
#     markdown = markdown.replace('```json','').replace('```','')
#     dicts = find_dicts(markdown)
#     if dicts == []:
#         check_dicts = []
#     else:
#         check_dicts = [i for i in dicts if set(['result']).issubset(list(i)) or set(['小星星']).issubset(list(i)) or set(['little_star']).issubset(list(i))]

#     return True if len(check_dicts)==1 else False


# async def api_and_formatcheck(question_str, model_name, retry=30):
#     pred_origin = await openai_api(question_str, model_name, OPENAI_BASE_URL, OPENAI_API_KEY, API_RETRY, STREAM)
#     # pred_origin = openai_api_sync(question_str, model_name, OPENAI_BASE_URL, OPENAI_API_KEY, API_RETRY, STREAM)
#     if format_check(pred_origin):
#         pred_answer = []
#         for x in find_dicts(pred_origin):
#             if 'result' in x:
#                 pred_answer.append(x['result'])
#             elif '小星星' in x:
#                 pred_answer.append(x['小星星'])
#             elif 'little_star' in x:
#                 pred_answer.append(x['little_star'])
#         right_format = True
#     else:
#         if retry > 0:
#             print('origin output:', pred_origin)
#             print('format wrong, tring the {} time'.format(FORMAT_RETRY - retry))
#             await asyncio.sleep(random.normalvariate(3, 1))
#             return await api_and_formatcheck(question_str, model_name, retry-1)
#         else:
#             pred_answer = []
#             right_format = False
#     if len(pred_answer) == 1:
#         pred_answer = pred_answer[0]
#     else:
#         pred_answer = []
#         right_format = False
#     return pred_origin, pred_answer, right_format


# prompt
prompt_dir = os.path.join(BASE_DIR, '..', 'prompt.json')
with open(prompt_dir, 'r', encoding='utf-8') as f:
    prompt = json.loads(f.read())


def get_ans(que, task_name, base_dir, model_name, result_file_name):
    que_input = que['input']
    que_type = que['type']
    que_id = que['id']
    que_answer = que['ground_truth']
    que_context = que['context']
    que_sample_size = que['sample_size']

    output_format = json.dumps({'result': ['xxx', 'xxx', '…']}, ensure_ascii=False)

    match task_name:
        case 'zh_norm':
            context_str = '\n'.join(que_context)
            output_format = json.dumps(
                {'result': 'xxx'},
                ensure_ascii=False,
            )
            question_str = prompt[task_name].format(output_format=output_format, mention=que_input, concept_set=context_str)
            que_answer = que_answer[0]
        case 'en_norm':
            id2name_file_dir = os.path.join(base_dir, 'en_norm', 'umls_2023ab_SMM4H-17_cid2name.json')
            with open(id2name_file_dir, 'r', encoding='utf-8') as f:
                id2name = json.loads(f.read())
            que_answer = [id2name[a] for a in que_answer]
            context = [id2name[c] for c in que_context]
            context_str = '\n'.join(context)
            output_format = json.dumps(
                {'result': 'xxx'},
                ensure_ascii=False,
            )
            question_str = prompt[task_name].format(output_format=output_format, mention=que_input, concept_set=context_str)
            que_answer = que_answer[0]
        case 'zh_kg':
            context_str = '\n'.join(que_context)
            question_str = prompt[task_name].format(output_format=output_format, triplets=context_str, question=que_input)
        case 'en_kg':
            id2name_file_dir = os.path.join(base_dir, 'en_kg', 'umls_2023ab_MedDRA_cid2name.json')
            with open(id2name_file_dir, 'r', encoding='utf-8') as f:
                id2name = json.loads(f.read())
            triplets_with_name = []
            for triplet in que_context:
                spo = triplet.split('|')
                spo[0] = id2name[spo[0]]
                spo[2] = id2name[spo[2]]
                triplets_with_name.append('|'.join(spo))
            que_answer_new = []
            for answer in que_answer:
                answer_spo = answer.split('|')
                answer_spo[0] = id2name[answer_spo[0]]
                answer_spo[2] = id2name[answer_spo[2]]
                que_answer_new.append('|'.join(answer_spo))
            que_answer = que_answer_new
            que_answer = ' '.join(que_answer)
            triplets_with_name_str = '\n'.join(triplets_with_name)
            question_str = prompt[task_name].format(output_format=output_format, triplets=triplets_with_name_str, question=que_input)
        case 'zh_table':
            context_str = '\n'.join(que_context)
            table_name = que['ground_truth_coarse'][3:]
            full_input_str = '在表格“{}”中，{}'.format(table_name, que_input)
            question_str = prompt[task_name].format(output_format=output_format, tables=context_str, question=full_input_str)
        case 'zh_medcase':
            context_str = '\n'.join(que_context)
            medcase_name = que['ground_truth_coarse'][3:]
            full_input_str = '在病例“{}”中，{}'.format(medcase_name, que_input)
            question_str = prompt[task_name].format(output_format=output_format, medcases=context_str, question=full_input_str)
        case 'zh_counting':
            question_str = que_input
            que_answer = json.loads(que_answer)
        case 'en_counting':
            question_str = que_input
            que_answer = json.loads(que_answer)
        case _:
            raise ValueError('Unknown task name')
    
    # token_length = await tokenizer.token_len(question_str)
    # # print(token_length)
    # # print(que_input)
    # # print(token_length)

    # if token_length > model2maxlen[model_name]:
    #     pred_origin = ''
    #     pred_answer = '' if 'norm' in task_name else []
    #     note = 'too long'
    # else:
    #     pred_origin, pred_answer, right_format = await api_and_formatcheck(question_str, model_name, FORMAT_RETRY)
    #     note = '' if right_format else 'wrong format'
    
    # # write2jsonl_sync(
    # await write2jsonl(
    #     {
    #         'id': que_id,
    #         'type': que_type,
    #         'input': que_input,
    #         'true_answer': que_answer,
    #         'pred_answer': pred_answer,
    #         'pred_origin': pred_origin,
    #         'model': model_name,
    #         'token_len': token_length,
    #         'sample_size': que_sample_size,
    #         'note': note
    #     },
    #     result_file_name
    # )
    return len(question_str), len(que_answer)


def main():

    # semaphore = asyncio.Semaphore(ALL_CONCURRENT_LIMIT)
    # for task_name in TASK_NAME_LIST:
    
    VERSION = 'v1'
    RESULT_FILE_NAME = 'query_result/' + TASK_NAME + '_' + MODEL_NAME + '_' + VERSION + '.jsonl'
    
    # qa
    qa_list = []
    qa_dir = os.path.join(BASE_DIR, TASK_NAME, 'input_data.jsonl')
    with open(qa_dir, 'r', encoding='utf-8') as f:
        for item in f.readlines():
            item = json.loads(item)
            qa_list.append(item)
    
    results = []
    for qa in tqdm(qa_list):
        results.append(get_ans(qa, TASK_NAME, BASE_DIR, MODEL_NAME, RESULT_FILE_NAME))
    
    print(results)
    print(len(results))
    
    total_que_len = 0
    total_ans_len = 0
    for res in results:
        total_que_len += res[0]
        total_ans_len += res[1]
    print(total_que_len, total_ans_len)
    print('avg:')
    print(total_que_len/len(results), total_ans_len/len(results))

    # if PART == 'full' or not os.path.exists(RESULT_FILE_NAME):
    #     with open(RESULT_FILE_NAME, 'w', encoding='utf-8') as f:
    #         f.seek(0)
    #         f.truncate()
    # elif PART == 'supply':
    #     idx_tested = []
    #     with open(RESULT_FILE_NAME, 'r', encoding='utf-8') as f:
    #         for line in f.readlines():
    #             idx_tested.append(json.loads(line)['id'])
    #     qa_list = [x for x in qa_list if x['id'] not in idx_tested]
    # else:
    #     raise ValueError('Unknown part')
    

    # tasks = [asyncio.create_task(get_ans(que, TASK_NAME, base_dir=BASE_DIR, model_name=MODEL_NAME, result_file_name=RESULT_FILE_NAME)) for que in qa_list]
    # print(len(tasks))

    # async def limited_task(task):
    #     async with semaphore:
    #         result = await task
    #         progress_bar.update(1)
    #         return result

    # progress_bar = tqdm(total=len(tasks))

    # results = await asyncio.gather(*(limited_task(task) for task in tasks))
    # progress_bar.close()
    # print(results)


if __name__ == '__main__':
    # asyncio.run(main())
    main()
