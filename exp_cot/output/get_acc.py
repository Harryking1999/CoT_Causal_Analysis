import json
file_name = "./exp_cot/output/output.Product_3.cot0shot.math_teacher.deepseek-reasoner.json.bak"
with open(file_name, 'r', encoding='utf-8') as f:  
    ls_data = json.load(f)
cnt_all = 0
cnt_correct = 0
# print(ls_data)
for i in ls_data:
    cnt_all += 1
    # print(i)
    # break
    if('cot0shot.math teacher_result' in i.keys() and i['cot0shot.math teacher_result']==True):
        cnt_correct += 1
f.close()
print(cnt_correct)
print(cnt_all)