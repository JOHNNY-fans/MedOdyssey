import json
import glob

model2maxlen = {
    'gpt-4-turbo-2024-04-09': 128000,
    'gpt-4o': 128000,
    'claude-3-haiku-20240307': 200000,
    'claude-3-sonnet-20240229': 200000,
    'chatglm3-6b-128k': 128000,
    'Yarn-Mistral-7b-128k': 128000,
    'internlm2-chat-7b': 200000,
    'internlm2-chat-20b': 200000,
    'moonshot-v1-128k': 128000,
    'Yi-6B-200K': 200000,
}

token_len_list = [4000, 8000, 16000, 32000, 64000, 128000, 200000]
position_list = [0, 25, 50, 75, 100]
NIAH_BASE_DIR = '/ailab/user/sunhongli/workspace/MedLongContextEval/niah_result'
niah_result_files = glob.glob(NIAH_BASE_DIR + '/*')

# EN
with open('/ailab/user/sunhongli/workspace/MedLongContextEval/dataset/task_data/needles/en_pure_needles.json', 'r', encoding='utf-8') as f:
    en_needles = json.loads(f.read())
en_needles_new = {}
for needle in en_needles:
    en_needles_new[needle['id']] = needle
en_needles = en_needles_new

niah_result_model_length_depth_en = {k:{length: {position: [] for position in position_list} for length in token_len_list} for k in model2maxlen}
niah_score_model_length_depth_en = {k:{length: {position: {} for position in position_list} for length in token_len_list} for k in model2maxlen}
for niah_result in niah_result_files:
    if 'en' in niah_result.split('/')[-1]:
        with open(niah_result, 'r', encoding='utf-8') as f:
            for line in f.readlines():
                result = json.loads(line)
                idx = result['idx']
                length = result['length(origin)']
                position = result['position(%)']
                model_name = result['model']
                true_answer = [str(r).lower() for r in en_needles[idx]['ground_truth']]
                pred_answer = str(result['pred_answer']).lower()
                pred_origin_answer = str(result['pred_origin']).lower()

                niah_result_model_length_depth_en[model_name][length][position].append({
                    'id': idx,
                    'true_answer': true_answer,
                    'pred_answer': pred_answer,
                    'pred_origin_answer': pred_origin_answer,
                })

for model in niah_result_model_length_depth_en:
    for length in niah_result_model_length_depth_en[model]:
        all_pos_total = 0
        all_pos_correct = 0
        all_pos_ssm_correct = 0
        for position in niah_result_model_length_depth_en[model][length]:
            total = 0
            correct = 0
            ssm_correct = 0
            wrong_id_list = []
            for r in niah_result_model_length_depth_en[model][length][position]:
                total += 1
                right_answer = False
                for ta in r['true_answer']:
                    if ta == r['pred_answer']:
                        correct += 1
                        right_answer = True
                        break
                for ta in r['true_answer']:
                    if ta in r['pred_origin_answer']:
                        ssm_correct += 1
                        break
                if not right_answer:
                    wrong_id_list.append(int(r['id']))

            niah_score_model_length_depth_en[model][length][position] = {
                'total': total,
                'correct': correct,
                'acc': (float(correct) / float(total)) * 100 if total > 0 else -1,
                'ssm_correct': ssm_correct,
                'ssm_acc': (float(ssm_correct) / float(total)) * 100 if total > 0 else -1,
                # 'wrong_id_list': wrong_id_list,
            }
            all_pos_total += total
            all_pos_correct += correct
            all_pos_ssm_correct += ssm_correct
        niah_score_model_length_depth_en[model][length]['all'] = {
            'total': all_pos_total,
            'correct': all_pos_correct,
            'acc': (float(all_pos_correct) / float(all_pos_total)) * 100 if all_pos_total > 0 else -1,
            'ssm_correct': all_pos_ssm_correct,
            'ssm_acc': (float(all_pos_ssm_correct) / float(all_pos_total)) * 100 if all_pos_total > 0 else -1
        }


# ZH
with open('/ailab/user/sunhongli/workspace/MedLongContextEval/dataset/task_data/needles/zh_pure_needles.json', 'r', encoding='utf-8') as f:
    zh_needles = json.loads(f.read())
zh_needles_new = {}
for needle in zh_needles:
    zh_needles_new[needle['id']] = needle
zh_needles = zh_needles_new

niah_result_model_length_depth_zh = {k:{length: {position: [] for position in position_list} for length in token_len_list} for k in model2maxlen}
niah_score_model_length_depth_zh = {k:{length: {position: {} for position in position_list} for length in token_len_list} for k in model2maxlen}
for niah_result in niah_result_files:
    if 'zh' in niah_result.split('/')[-1]:
        with open(niah_result, 'r', encoding='utf-8') as f:
            for line in f.readlines():
                result = json.loads(line)
                idx = result['idx']
                length = result['length(origin)']
                position = result['position(%)']
                model_name = result['model']
                true_answer = [str(r).replace(' ', '') for r in zh_needles[idx]['ground_truth']]
                pred_answer = str(result['pred_answer']).replace(' ', '')
                pred_origin_answer = str(result['pred_origin']).replace(' ', '')
                
                niah_result_model_length_depth_zh[model_name][length][position].append({
                    'id': idx,
                    'true_answer': true_answer,
                    'pred_answer': pred_answer,
                    'pred_origin_answer': pred_origin_answer,
                })

for model in niah_result_model_length_depth_zh:
    for length in niah_result_model_length_depth_zh[model]:
        all_pos_total = 0
        all_pos_correct = 0
        all_pos_ssm_correct = 0
        for position in niah_result_model_length_depth_zh[model][length]:
            total = 0
            correct = 0
            ssm_correct = 0
            wrong_id_list = []
            for r in niah_result_model_length_depth_zh[model][length][position]:
                total += 1
                right_answer = False
                for ta in r['true_answer']:
                    if ta == r['pred_answer']:
                        correct += 1
                        right_answer = True
                        break
                for ta in r['true_answer']:
                    if ta in r['pred_origin_answer']:
                        ssm_correct += 1
                        break
                if not right_answer:
                    wrong_id_list.append(int(r['id']))
            niah_score_model_length_depth_zh[model][length][position] = {
                'total': total,
                'correct': correct,
                'acc': (float(correct) / float(total)) * 100 if total > 0 else -1,
                'ssm_correct': ssm_correct,
                'ssm_acc': (float(ssm_correct) / float(total)) * 100 if total > 0 else -1,
                # 'wrong_id_list': wrong_id_list,
            }
            all_pos_total += total
            all_pos_correct += correct
            all_pos_ssm_correct += ssm_correct
        niah_score_model_length_depth_zh[model][length]['all'] = {
            'total': all_pos_total,
            'correct': all_pos_correct,
            'acc': (float(all_pos_correct) / float(all_pos_total)) * 100 if all_pos_total > 0 else -1,
            'ssm_correct': all_pos_ssm_correct,
            'ssm_acc': (float(all_pos_ssm_correct) / float(all_pos_total)) * 100 if all_pos_total > 0 else -1
        }

with open('niah_en_result_score.json', 'w', encoding='utf-8') as f:
    f.write(json.dumps(niah_score_model_length_depth_en, ensure_ascii=False, indent=4))

with open('niah_zh_result_score.json', 'w', encoding='utf-8') as f:
    f.write(json.dumps(niah_score_model_length_depth_zh, ensure_ascii=False, indent=4))


for model in model2maxlen:
    print(model)
    zh_results, en_results = niah_score_model_length_depth_zh[model], niah_score_model_length_depth_en[model]
    for position in position_list:
        total = 0
        correct = 0
        for length in token_len_list:
            print('& ', end='')
            if en_results[length][position]["total"] == 0:
                print('$-$', end='')
            else:
                print(en_results[length][position]["correct"], end='')
            print(' ', end='')
            total += en_results[length][position]["total"]
            correct += en_results[length][position]["correct"]
        print('& ', end='')
        print(str(correct) + '$/$' + str(total), end='')
        print(' ', end='')

        total = 0
        correct = 0
        for length in token_len_list:
            print('& ', end='')
            if zh_results[length][position]["total"] == 0:
                print('$-$', end='')
            else:
                print(zh_results[length][position]["correct"], end='')
            print(' ', end='')
            total += zh_results[length][position]["total"]
            correct += zh_results[length][position]["correct"]
        print('& ', end='')
        print(str(correct) + '$/$' + str(total), end='')
        print(' ', end='')
        
        print('\\\\')


    for length in token_len_list:
        print('& ', end='')
        print(str(en_results[length]["all"]["correct"]) + '$/$100', end='')
        print(' ', end='')
    print('& ', end='')
    for length in token_len_list:
        print('& ', end='')
        print(str(zh_results[length]["all"]["correct"]) + '$/$100', end='')
        print(' ', end='')
    print('& ', end='')
    print('\\\\')

print('\n\n')
# SSM Acc.
for model in model2maxlen:
    print(model)
    zh_results, en_results = niah_score_model_length_depth_zh[model], niah_score_model_length_depth_en[model]
    for position in position_list:
        total = 0
        correct = 0
        for length in token_len_list:
            print('& ', end='')
            if en_results[length][position]["total"] == 0:
                print('$-$', end='')
            else:
                print(en_results[length][position]["ssm_correct"], end='')
            print(' ', end='')
            total += en_results[length][position]["total"]
            correct += en_results[length][position]["ssm_correct"]
        print('& ', end='')
        print(str(correct) + '$/$' + str(total), end='')
        print(' ', end='')

        total = 0
        correct = 0
        for length in token_len_list:
            print('& ', end='')
            if zh_results[length][position]["total"] == 0:
                print('$-$', end='')
            else:
                print(zh_results[length][position]["ssm_correct"], end='')
            print(' ', end='')
            total += zh_results[length][position]["total"]
            correct += zh_results[length][position]["ssm_correct"]
        print('& ', end='')
        print(str(correct) + '$/$' + str(total), end='')
        print(' ', end='')
        
        print('\\\\')


    for length in token_len_list:
        print('& ', end='')
        print(str(en_results[length]["all"]["ssm_correct"]) + '$/$100', end='')
        print(' ', end='')
    print('& ', end='')
    for length in token_len_list:
        print('& ', end='')
        print(str(zh_results[length]["all"]["ssm_correct"]) + '$/$100', end='')
        print(' ', end='')
    print('& ', end='')
    print('\\\\')
