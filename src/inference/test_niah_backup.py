import os
os.environ['HTTP_PROXY']='https://sunhongli:Tiankong1234@blsc-proxy.pjlab.org.cn:13128'
os.environ['HTTPS_PROXY']='https://sunhongli:Tiankong1234@blsc-proxy.pjlab.org.cn:13128'
os.environ['http_proxy']='https://sunhongli:Tiankong1234@blsc-proxy.pjlab.org.cn:13128'
os.environ['https_proxy']='https://sunhongli:Tiankong1234@blsc-proxy.pjlab.org.cn:13128'

import re
import copy
import json
import random
import asyncio


from tqdm import tqdm
import glob

from utils import *

# 长度
token_len_list = [4000, 8000, 16000, 32000, 64000, 128000, 200000] # token length
zh_len_scale = 1.41
en_len_scale = 0.36
zh_string_len = [int(i // zh_len_scale) for i in token_len_list] # string length
en_string_len = [int(i // en_len_scale) for i in token_len_list] # string length

# 深度(%)
position_list = [0, 25, 50, 75, 100]

# 为答案预留的string_length长度
LENGTH_FOR_ANSWER = 200

LANGUAGE = 'zh'

# 测试一部分还是全部
# 针对某一模型在某一数据上的结果
# 如果是full，那么清空原来结果，重新开始
# 如果是supply，那么只跑原来没跑过的id
PART = 'supply'

API_RETRY = 20
FORMAT_RETRY = 0

ALL_CONCURRENT_LIMIT = 32


# 请求openai接口时是否流式
STREAM = False

# MODEL_NAME = 'claude-3-haiku-20240307'
# MODEL_NAME = 'gpt-4-turbo-2024-04-09'
MODEL_NAME = 'claude-3-sonnet-20240229'
# MODEL_NAME = 'gpt-4o'
# MODEL_NAME = 'gpt-3.5-turbo-0125'
# MODEL_NAME = 'gpt-4o-2024-05-13'
# MODEL_NAME = 'moonshot-v1-200k'

# MODEL_NAME = 'chatglm3-6b-128k'

BASE_DIR = '/ailab/user/sunhongli/workspace/MedLongContextEval'

VERSION = 'v1'
RESULT_FILE_NAME = os.path.join(BASE_DIR, 'niah_result', LANGUAGE + '_' + MODEL_NAME + '_' + VERSION + '.jsonl')

OPENAI_BASE_URL = 'https://api.dstargpt.com/v1'
OPENAI_API_KEY = 'sk-nyKp75atOaPKzCLBCaBa8cAc3cB9496fB8B95b563eB02aCf'

# OPENAI_BASE_URL = 'https://api.moonshot.cn/v1'
# OPENAI_API_KEY = 'sk-J6Qp2qwhez7joRxhFva6tPHQioBVCBMv6H7HuTp5qmMxQAaU'

# OPENAI_BASE_URL = 'http://139.196.50.48:50051/v1'
# OPENAI_API_KEY = 'sshhhll'


tokenizer = TokenzierForLength(MODEL_NAME)


heystack_dir = os.path.join(BASE_DIR, 'dataset', 'raw_data', 'en_guidelines') if LANGUAGE == 'en' else os.path.join(BASE_DIR, 'dataset', 'raw_data', 'zh_book')

heystack_str = ''
heystack_files = glob.glob(heystack_dir + '/*.md')
for heystack_file in heystack_files:
    with open(heystack_file, 'r', encoding='utf-8') as f:
        heystack_str = f.read()
        heystack_str = re.sub(r'\n+', '\n', heystack_str)
        heystack_str = heystack_str.replace('\\x','\n')
        heystack_str += heystack_str

# TASK_PROMPT = "请根据接下来的内容回答后续的问题。请直接给出简短的答案短语。严禁给出所提供内容之外的信息，严禁给出答案之外的多余内容。\n内容：\n" if LANGUAGE == 'zh' else "Please answer the question based on the context. Please give a short answer directly. It is strictly forbidden to give information other than what is provided, and it is strictly forbidden to give extra content other than the answer.\nContext:\n"
TASK_PROMPT = '请根据接下来的内容回答后续的问题。请按照JSON格式要求直接输出答案，格式要求：{"答案": "xxx"}。要求答案来自所给内容，严禁要给出无关文本。\n内容：\n' if LANGUAGE == 'zh' else 'Please answer the question based on the context. Please output the answer directly according to the JSON format requirements. The format requirements is: {"answer": "xxx"}. The answer is required to come from the given content, and irrelevant text is strictly prohibited.\nContext:\n'

if LANGUAGE == 'zh':
    needles_file_name = os.path.join(BASE_DIR, 'dataset', 'task_data', 'needles', 'zh_pure_needles.json')
else:
    needles_file_name = os.path.join(BASE_DIR, 'dataset', 'task_data', 'needles', 'en_pure_needles.json')

with open(needles_file_name, 'r', encoding='utf-8') as f:
    needles = json.loads(f.read())

tested_list = []
if PART == 'full' or not os.path.exists(RESULT_FILE_NAME):
    with open(RESULT_FILE_NAME, 'w', encoding='utf-8') as f:
        f.seek(0)
        f.truncate()
elif PART == 'supply':
    with open(RESULT_FILE_NAME, 'r', encoding='utf-8') as f:
        for line in f.readlines():
            tested_list.append(json.loads(line))
else:
    raise ValueError('Unknown part')


def find_dicts(markdown):
    dicts = []
    if markdown == None:
        return dicts
    pattern = r"\{[^{}]*\}"
    matches = re.findall(pattern, markdown)
    for match in matches:
        try:
            d = eval(match)
            if isinstance(d, dict):
                dicts.append(d)
        except:
            pass
    return dicts

def format_check(markdown: str):
    markdown = markdown.replace('```json','').replace('```','')
    dicts = find_dicts(markdown)
    if dicts == []:
        check_dicts = []
    else:
        check_dicts = [i for i in dicts if set(['answer']).issubset(list(i)) or set(['答案']).issubset(list(i))]

    return True if len(check_dicts)==1 else False


async def api_and_formatcheck(input_str, model_name, retry=30):
    pred_origin = await openai_api(input_str, model_name, OPENAI_BASE_URL, OPENAI_API_KEY, API_RETRY, STREAM)
    if format_check(pred_origin):
        pred_answer = []
        for x in find_dicts(pred_origin):
            if 'answer' in x:
                pred_answer.append(x['answer'])
            elif '答案' in x:
                pred_answer.append(x['答案'])
        right_format = True
    else:
        if retry > 0:
            print('origin output:', pred_origin)
            print('format wrong, tring the {} time'.format(FORMAT_RETRY - retry))
            await asyncio.sleep(random.normalvariate(3, 1))
            return await api_and_formatcheck(input_str, model_name, retry-1)
        else:
            pred_answer = []
            right_format = False
    if len(pred_answer) == 1:
        pred_answer = pred_answer[0]
    else:
        pred_answer = []
        right_format = False
    return pred_origin, pred_answer, right_format


async def get_ans(heystack, needle, position, context_length, context_token_length_origin, model_name, tokenizer, result_dir):
    needle_str = needle['needle']
    if position == 0:
        needle_str += '\n'
    elif position == 100:
        needle_str = '\n' + needle_str
    else:
        needle_str = '\n' + needle_str + '\n'

    needle_type = needle['type']
    question_str = ('\n问题：' if LANGUAGE == 'zh' else '\nQuestion: ') + needle['input'] + ('\n答案：' if LANGUAGE == 'zh' else '\nAnswer: ')
    answer_str = needle['ground_truth']
    needle_idx = needle['id']

    needls_tokens = tokenizer.encode(needle_str)
    question_tokens = tokenizer.encode(question_str)
    task_prompt_tokens = tokenizer.encode(TASK_PROMPT)

    # context_length_origin = copy.deepcopy(context_length)
    context_length -= len(needle_str)
    context_length -= len(question_str)
    context_length -= len(TASK_PROMPT)
    context_length -= LENGTH_FOR_ANSWER
    
    # print(heystack[:100])
    # print(context_length)
    context_heystack = heystack[:context_length]
    context_heystack_tokens = tokenizer.encode(context_heystack)
    context_heystack_tokens_length = len(context_heystack_tokens)
    
    
    if position == 0:
        # context_tokens = full_context_tokens[:context_length]
        context_tokens = context_heystack_tokens
        input_tokens = task_prompt_tokens + needls_tokens + context_tokens + question_tokens
    else:
        context_prefix_tokens = context_heystack_tokens[:int(context_heystack_tokens_length * position / 100)]
        context_suffix_tokens = context_heystack_tokens[int(context_heystack_tokens_length * position / 100):]
        input_tokens = task_prompt_tokens + context_prefix_tokens + needls_tokens + context_suffix_tokens + question_tokens
    input_str = tokenizer.decode(input_tokens)

    # print('处理前：', context_length_origin, '\n', '处理后：', len(input_str), '\n---------\n')

    if len(input_tokens) > model2maxlen[model_name]:
        pred_origin = ''
        pred_answer = ''
        note = 'too long'
    else:
        pred_origin, pred_answer, right_format = await api_and_formatcheck(input_str, model_name, FORMAT_RETRY)
        note = '' if right_format else 'wrong format'

    result = {
        'idx': needle_idx,
        'needle': needle['needle'],
        'question': needle['input'],
        'type': needle_type,
        'true_answer': answer_str,
        'pred_answer': pred_answer,
        'pred_origin': pred_origin,
        'position(%)': position,
        'length(string)': len(input_str),
        'length(tokens)': len(input_tokens),
        'length(origin)': context_token_length_origin,
        'model': model_name,
        'note': note
    }

    history_file_dir = os.path.join(BASE_DIR, 'niah_result', 'history', LANGUAGE + '_' + MODEL_NAME + '_' + str(position) + '_' + str(context_token_length_origin) + '_' + str(needle_idx) + VERSION + '.txt')
    with open(history_file_dir, 'w', encoding='utf-8') as f:
        f.write(input_str)

    await write2jsonl(result, result_dir)


async def main():
    print('depth: ', position_list)
    print('length: ', token_len_list)

    semaphore = asyncio.Semaphore(ALL_CONCURRENT_LIMIT)
    
    tasks = []

    string_len_list = zh_string_len if LANGUAGE == 'zh' else en_string_len
    for string_len, token_len in zip(string_len_list, token_len_list):
        # print('string_len:', string_len, 'token_len:', token_len)
        for position in position_list:
            for needle_dict in needles:
                have_tested = False
                for tested in tested_list:
                    if tested['idx'] == needle_dict['id'] and tested['position(%)'] == position and tested['length(origin)'] == token_len:
                        have_tested = True
                        break
                if not have_tested:
                    tasks.append(asyncio.create_task(get_ans(heystack_str, needle_dict, position, string_len, token_len, MODEL_NAME, tokenizer, RESULT_FILE_NAME)))

    async def limited_task(task):
        async with semaphore:
            result = await task
            progress_bar.update(1)
            return result

    progress_bar = tqdm(total=len(tasks))

    await asyncio.gather(*(limited_task(task) for task in tasks))
    progress_bar.close()


if __name__ == '__main__':
    asyncio.run(main())
