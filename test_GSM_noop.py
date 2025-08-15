from datasets import load_dataset

filepath = "/home/fuzhizhang.fzz/data/GSM-Symbolic"
ds_main = load_dataset(filepath, name="main")
ds_p1 = load_dataset(filepath, name="p1")
ds_p2 = load_dataset(filepath, name="p2")

# print(ds_main)
print("=== ds_main 前3条数据 ===")
for i in range(3):
    print(f"第{i+1}条:", ds_main['test'][i])
    print()

# 打印 p1 数据集的前3条
print("=== ds_p1 前3条数据 ===")
for i in range(3):
    print(f"第{i+1}条:", ds_p1['test'][i])
    print()

# 打印 p2 数据集的前3条
print("=== ds_p2 前3条数据 ===")
for i in range(3):
    print(f"第{i+1}条:", ds_p2['test'][i])
    print()