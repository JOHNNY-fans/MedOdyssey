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

TASK_NAME_LIST = ['zh_norm', 'en_norm', 'zh_kg', 'en_kg', 'zh_table', 'zh_medcase', 'zh_counting', 'en_counting']
BASE_DIR = '/ailab/user/sunhongli/workspace/MedLongContextEval/query_result'
result_files = glob.glob(BASE_DIR + '/*')

result_file_list = [result_file.split('/')[-1] for result_file in result_files]

task_model_score = {task: {model: -1 for model in model2maxlen} for task in TASK_NAME_LIST}
task_model_ssm_socre = {task: {model: [] for model in model2maxlen} for task in TASK_NAME_LIST}

task_model_result = {task: {model: [] for model in model2maxlen} for task in TASK_NAME_LIST}

for task in TASK_NAME_LIST:
    for result_file in result_files:
        if task in result_file.split('/')[-1]:
            with open(result_file, 'r', encoding='utf-8') as f:
                for line in f.readlines():
                    result = json.loads(line)
                    task_model_result[task][result['model']].append({
                        'id': result['id'],
                        'type': result['type'],
                        'true_answer': result['true_answer'],
                        'pred_answer': result['pred_answer'],
                        'pred_origin_answer': result['pred_origin'],
                        'sample_size': result['sample_size'],
                    })

# Norm Acc
for task in ['zh_norm', 'en_norm']:
    for model in task_model_result[task]:
        correct = 0
        total = 0
        ssm_correct = 0
        for result in task_model_result[task][model]:
            total += 1
            true_answer = result['true_answer']
            pred_answer = result['pred_answer']
            pred_origin_answer = result['pred_origin_answer']
            if pred_answer == []:
                pred_answer = ''

            if true_answer.lower() == pred_answer.lower():
                correct += 1
            if true_answer.lower() in pred_answer.lower():
                ssm_correct += 1
        task_model_score[task][model] = (float(correct) / float(total)) if total > 0 else -1
        task_model_ssm_socre[task][model] = (float(ssm_correct) / float(total)) if total > 0 else -1

# KG Precision/Recall/F1
for task in ['zh_kg', 'en_kg']:
    for model in task_model_result[task]:
        TP = 0
        FP = 0
        FN = 0
        for result in task_model_result[task][model]:
            true_answer = [t.lower() for t in result['true_answer']]
            pred_answer = [p.lower() for p in result['pred_answer']]
            true_answer = set(true_answer)
            pred_answer = set(pred_answer)
            for t in true_answer:
                if t in pred_answer:
                    TP += 1
                else:
                    FN += 1
            for p in pred_answer:
                if p not in true_answer:
                    FP += 1
        precision = TP / (TP + FP) if TP + FP > 0 else -1
        recall = TP / (TP + FN) if TP + FN > 0 else -1
        f1 = 2 * precision * recall / (precision + recall) if precision + recall > 0 else -1
        task_model_score[task][model] = (precision, recall, f1)

        total = 0
        ssm_correct = 0
        for result in task_model_result[task][model]:
            total += 1
            true_answer = [t.lower() for t in result['true_answer']]
            true_answer = set(true_answer)
            pred_origin_answer = result['pred_origin_answer'].lower()
            right_answer = True
            for t in true_answer:
                if t not in pred_origin_answer:
                    right_answer = False
                    break
            if right_answer:
                ssm_correct += 1

        task_model_ssm_socre[task][model] = (float(ssm_correct) / float(total)) if total > 0 else -1

# Table
SPLITS = [',','，',';','；','、','+',' ']
for task in ['zh_table']:
    for model in task_model_result[task]:
        TP = 0
        FP = 0
        FN = 0
        for result in task_model_result[task][model]:
            total += 1
            true_answer = result['true_answer']
            pred_answer = list(set(result['pred_answer']))
            if len(pred_answer) == 1 and len(true_answer) > 1:
                for split in SPLITS:
                    if split in true_answer[0]:
                        true_answer = [split.join(true_answer)]
                        break
            true_answer = [t.replace(' ', '') for t in true_answer]
            pred_answer = [p.replace(' ', '') for p in pred_answer]
            true_answer = set(true_answer)
            pred_answer = set(pred_answer)
            
            for t in true_answer:
                if t in pred_answer:
                    TP += 1
                else:
                    FN += 1
            for p in pred_answer:
                if p not in true_answer:
                    FP += 1
        precision = TP / (TP + FP) if TP + FP > 0 else -1
        recall = TP / (TP + FN) if TP + FN > 0 else -1
        f1 = 2 * precision * recall / (precision + recall) if precision + recall > 0 else -1
        task_model_score[task][model] = (precision, recall, f1)

        total = 0
        ssm_correct = 0
        for result in task_model_result[task][model]:
            total += 1
            true_answer = result['true_answer']
            pred_origin_answer = result['pred_origin_answer']
            right_answer = True
            for t in true_answer:
                if t not in pred_origin_answer:
                    right_answer = False
                    break
            if right_answer:
                ssm_correct += 1
        task_model_ssm_socre[task][model] = (float(ssm_correct) / float(total)) if total > 0 else -1


# Medcase Acc
with open('/ailab/user/sunhongli/workspace/MedLongContextEval/dataset/raw_data/zh_medcase/answer_correct.json', 'r', encoding='utf-8') as f:
    supplement_answers = json.loads(f.read())
supplement_answers = {int(k): v for k, v in supplement_answers.items()}
SPLITS = [',','，',';','；','、','+',' ']
for task in ['zh_medcase']:
    for model in task_model_result[task]:
        correct = 0
        total = 0
        ssm_correct = 0
        for result in task_model_result[task][model]:
            total += 1
            if result['id'] in supplement_answers:
                true_answers = supplement_answers[result['id']]
            else:
                true_answers = [result['true_answer']]

            for true_answer in true_answers:
                true_answer = true_answer[0]
                pred_answer = result['pred_answer']
                if pred_answer == []:
                    pred_answer = ''
                elif len(pred_answer) == 1:
                    pred_answer = pred_answer[0]
                elif len(pred_answer) > 1:
                    for split in SPLITS:
                        if split in true_answer:
                            pred_answer = split.join(pred_answer)
                            break
                    if type(pred_answer) == list:
                        pred_answer = pred_answer[0]
                true_answer = true_answer.replace(' ', '')
                pred_answer = pred_answer.replace(' ', '')
                if true_answer == pred_answer:
                    correct += 1
                    break
            right_ssm_answer = False
            for true_answer in true_answers:
                true_answer = true_answer[0]
                pred_origin_answer = result['pred_origin_answer']
                if true_answer in pred_origin_answer:
                    right_ssm_answer = True
                    break
            if right_ssm_answer:
                ssm_correct += 1
        task_model_score[task][model] = (float(correct) / float(total)) if total > 0 else -1
        task_model_ssm_socre[task][model] = (float(ssm_correct) / float(total)) if total > 0 else -1


# Counting Acc
for task in ['zh_counting', 'en_counting']:
    for model in task_model_result[task]:
        all_correct = 0
        all_total = 0
        sub_tasks = ['acquisition_1', 'acquisition_inc', 'acquisition_shuffle', 'reasoning']
        sub_task_scores = {k: {'total': 0, 'correct': 0, 'acc': 0.0} for k in sub_tasks}
        
        all_ssm_correct = 0
        sub_task_ssm_scores = {k: {'total': 0, 'ssm_correct': 0, 'acc': 0.0} for k in sub_tasks}

        for result in task_model_result[task][model]:
            all_total += 1
            sub_task_scores[result['type']]['total'] += 1
            sub_task_ssm_scores[result['type']]['total'] += 1
            
            true_answer = result['true_answer']
            pred_answer = result['pred_answer']
            pred_origin_answer = result['pred_origin_answer']
            
            if pred_answer == []:
                pred_answer = ''
            right_answer = False
            if true_answer == pred_answer:
                all_correct += 1
                right_answer = True
                sub_task_scores[result['type']]['correct'] += 1
            
            if str(true_answer).replace(' ', '').replace('\n', '') in pred_origin_answer.replace(' ', '').replace('\n', '') or right_answer:
                all_ssm_correct += 1
                sub_task_ssm_scores[result['type']]['ssm_correct'] += 1

        for k, v in sub_task_scores.items():
            sub_task_scores[k]['acc'] = (float(v['correct']) / float(v['total'])) if v['total'] > 0 else -1
        for k, v in sub_task_ssm_scores.items():
            sub_task_ssm_scores[k]['acc'] = (float(v['ssm_correct']) / float(v['total'])) if v['total'] > 0 else -1

        task_model_score[task][model] = {k: v for k, v in sub_task_scores.items()}
        task_model_score[task][model]['all'] = {'total': all_total, 'correct': all_correct, 'acc': (float(all_correct) / float(all_total)) if all_total > 0 else -1}
        
        task_model_ssm_socre[task][model] = {k: v for k, v in sub_task_ssm_scores.items()}
        task_model_ssm_socre[task][model]['all'] = {'total': all_total, 'ssm_correct': all_ssm_correct, 'acc': (float(all_ssm_correct) / float(all_total)) if all_total > 0 else -1}


print(json.dumps(task_model_score, ensure_ascii=False, indent=4))
with open('task_result_score.json', 'w', encoding='utf-8') as f:
    f.write(json.dumps(task_model_score, ensure_ascii=False, indent=4))

print('\n')
print(json.dumps(task_model_ssm_socre, ensure_ascii=False, indent=4))
with open('task_result_ssm_score.json', 'w', encoding='utf-8') as f:
    f.write(json.dumps(task_model_ssm_socre, ensure_ascii=False, indent=4))


# EN.KG ZH.KG EN.Term ZH.Term ZH.Case ZH.Table
for model in model2maxlen:
    print(model)
    print('&', end=' ')
    print('%.2f' % (task_model_score['en_kg'][model][0] * 100), end=' ')
    print('&', end=' ')
    print('%.2f' % (task_model_score['en_kg'][model][1] * 100), end=' ')
    print('&', end=' ')
    print('%.2f' % (task_model_score['en_kg'][model][2] * 100), end=' ')
    
    print('&', end=' ')
    print('%.2f' % (task_model_score['zh_kg'][model][0] * 100), end=' ')
    print('&', end=' ')
    print('%.2f' % (task_model_score['zh_kg'][model][1] * 100), end=' ')
    print('&', end=' ')
    print('%.2f' % (task_model_score['zh_kg'][model][2] * 100), end=' ')
    
    print('&', end=' ')
    print('%.2f' % (task_model_score['en_norm'][model] * 100), end=' ')
    
    print('&', end=' ')
    print('%.2f' % (task_model_score['zh_norm'][model] * 100), end=' ')
    
    print('&', end=' ')
    print('%.2f' % (task_model_score['zh_medcase'][model] * 100), end=' ')
    
    print('&', end=' ')
    print('%.2f' % (task_model_score['zh_table'][model][0] * 100), end=' ')
    print('&', end=' ')
    print('%.2f' % (task_model_score['zh_table'][model][1] * 100), end=' ')
    print('&', end=' ')
    print('%.2f' % (task_model_score['zh_table'][model][2] * 100), end=' ')
    print('\\\\')
print('\n')

for model in model2maxlen:
    print(model)
    print('&', end=' ')
    print('%.2f' % (task_model_ssm_socre['en_kg'][model] * 100), end=' ')
    
    print('&', end=' ')
    print('%.2f' % (task_model_ssm_socre['zh_kg'][model] * 100), end=' ')
    
    print('&', end=' ')
    print('%.2f' % (task_model_ssm_socre['en_norm'][model] * 100), end=' ')
    
    print('&', end=' ')
    print('%.2f' % (task_model_ssm_socre['zh_norm'][model] * 100), end=' ')
    
    print('&', end=' ')
    print('%.2f' % (task_model_ssm_socre['zh_medcase'][model] * 100), end=' ')
    
    print('&', end=' ')
    print('%.2f' % (task_model_ssm_socre['zh_table'][model] * 100), end=' ')
    print('\\\\')
