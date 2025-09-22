import matplotlib.pyplot as plt
import numpy as np

# 设置字体为更正式好看的字体
plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 原始数据
data = {
    'qwen2.5-3B-base': {'math500': 0.303, 'math500_noop': 0.272, 'rel_delta': 10.23},
    'qwen2.5-3B-grpo-600': {'math500': 0.478, 'math500_noop': 0.432, 'rel_delta': 9.62},
    'qwen2.5-3B-grpo-1000': {'math500': 0.53, 'math500_noop': 0.453, 'rel_delta': 14.53},
    'qwen2.5-3B-grpo-2000': {'math500': 0.47, 'math500_noop': 0.43, 'rel_delta': 8.51},
    'qwen2.5-3B-sft': {'math500': 0.633, 'math500_noop': 0.386, 'rel_delta': 39.02},
    'qwen2.5-3B-sft-grpo-200': {'math500': 0.582, 'math500_noop': 0.491, 'rel_delta': 15.64},
    'qwen2.5-3B-sft-grpo-1000': {'math500': 0.58, 'math500_noop': 0.495, 'rel_delta': 14.66},
    'qwen2.5-3B-sft-grpo-2000': {'math500': 0.614, 'math500_noop': 0.51, 'rel_delta': 16.94},
    'qwen2.5-3B-18000-distill-openr1': {'math500': 0.72, 'math500_noop': 0.404, 'rel_delta': 43.89},
    'qwen2.5-3B-grpo-16000-openr1': {'math500': 0.556, 'math500_noop': 0.451, 'rel_delta': 18.88},
    'deepseek-distill-1.5b': {'math500': 0.692, 'math500_noop': 0.357, 'rel_delta': 48.41},
    'deepscaler-1.5b-preview': {'math500': 0.819, 'math500_noop': 0.546, 'rel_delta': 33.33}
}

# 定义rel_delta的颜色（不太亮但明显）
rel_delta_color = 'darkorange'

# 第一张图：修改后的组名
groups_1 = {
    'Qwen2.5-3B-GRPO': {
        'models': ['qwen2.5-3B-base', 'qwen2.5-3B-grpo-600', 'qwen2.5-3B-grpo-1000', 'qwen2.5-3B-grpo-2000'],
        'labels': ['0', '600', '1000', '2000']
    },
    'Qwen2.5-3B-Instr.-GRPO': {
        'models': ['qwen2.5-3B-sft', 'qwen2.5-3B-sft-grpo-200', 'qwen2.5-3B-sft-grpo-1000', 'qwen2.5-3B-sft-grpo-2000'],
        'labels': ['0', '200', '1000', '2000']
    }
}

# 创建第一张图
fig1, ax1 = plt.subplots(figsize=(10, 6))

# 计算位置
x_positions = []
group_centers = []
current_x = 0
group_gap = 1.5
bar_gap = 0.25
bar_width = 0.8

all_labels = []
all_models = []

for group_name, group_info in groups_1.items():
    group_start = current_x
    for i, (model, label) in enumerate(zip(group_info['models'], group_info['labels'])):
        x_positions.append(current_x)
        all_labels.append(label)
        all_models.append(model)
        current_x += bar_width + bar_gap
    
    group_end = current_x - bar_gap
    group_centers.append((group_start + group_end - bar_width) / 2)
    current_x += group_gap

# 绘制堆叠柱状图
math500_noop_values = [data[model]['math500_noop'] for model in all_models]
math500_diff_values = [data[model]['math500'] - data[model]['math500_noop'] for model in all_models]
math500_values = [data[model]['math500'] for model in all_models]
rel_delta_values = [data[model]['rel_delta'] for model in all_models]

# 转换rel_delta为0-1范围的值
rel_delta_normalized = [abs(delta) / 100 for delta in rel_delta_values]

# 绘制柱子
bars1 = ax1.bar(x_positions, math500_noop_values, width=bar_width, 
               label='math500-Noop', color='lightgray', alpha=0.8)
bars2 = ax1.bar(x_positions, math500_diff_values, width=bar_width, 
               bottom=math500_noop_values, label='math500', 
               color='steelblue', alpha=0.8)

# 绘制rel_delta折线（分组绘制，组间不连接）
line_plotted = False
current_pos = 0
for group_name, group_info in groups_1.items():
    group_size = len(group_info['models'])
    group_x = x_positions[current_pos:current_pos + group_size]
    group_rel_delta = rel_delta_normalized[current_pos:current_pos + group_size]
    
    if not line_plotted:
        ax1.plot(group_x, group_rel_delta, 'o-', color=rel_delta_color, linewidth=2.5, 
                markersize=8, label=r'$\Delta$%', alpha=0.9)
        line_plotted = True
    else:
        ax1.plot(group_x, group_rel_delta, 'o-', color=rel_delta_color, linewidth=2.5, 
                markersize=8, alpha=0.9)
    
    current_pos += group_size

# 在柱子内部添加数值标注
for i, (x, noop, diff, math500, delta) in enumerate(zip(x_positions, math500_noop_values, math500_diff_values, math500_values, rel_delta_values)):
    if noop > 0.05:
        ax1.text(x, noop/2, f'{noop:.3f}', 
                ha='center', va='center', fontsize=12, fontweight='bold', color='black')
    
    if diff > 0.03:
        ax1.text(x, noop + diff/2, f'{diff:.3f}', 
                ha='center', va='center', fontsize=12, fontweight='bold', color='white')
    
    total_height = noop + diff
    ax1.text(x, total_height + 0.01, f'{delta:.1f}%', 
            ha='center', va='bottom', fontsize=12, fontweight='bold', color=rel_delta_color)

# 设置x轴标签
ax1.set_xticks(x_positions)
ax1.set_xticklabels(all_labels, rotation=0, ha='center', fontsize=14)

# 添加组标签 - 增加距离
for i, (group_name, center) in enumerate(zip(groups_1.keys(), group_centers)):
    ax1.text(center, -0.1, group_name, ha='center', va='top', 
            fontweight='bold', fontsize=16, transform=ax1.get_xaxis_transform())

# 设置标签
ax1.set_ylabel('Score', fontsize=16, fontweight='bold')

# 调整图例位置
ax1.legend(loc='upper left', fontsize=14, frameon=True, fancybox=True, shadow=True)

# 设置网格
ax1.grid(True, alpha=0.3, axis='y')
max_height = max([data[model]['math500'] for model in all_models])
ax1.set_ylim(0, max_height * 1.2)
ax1.set_xlim(-0.5, max(x_positions) + 0.5)

# 设置y轴刻度标签字体大小
ax1.tick_params(axis='y', labelsize=14)

plt.tight_layout()
plt.show()

# 第二张图：修改后的组名
groups_2 = {
    'Qwen2.5-3B': {
        'models': ['qwen2.5-3B-18000-distill-openr1', 'qwen2.5-3B-grpo-16000-openr1'],
        'labels': ['Distill', 'RLVR']
    },
    'Qwen2.5-Math-1.5B': {
        'models': ['deepseek-distill-1.5b', 'deepscaler-1.5b-preview'],
        'labels': ['Distill', 'Distill+RLVR']
    }
}

# 创建第二张图
fig2, ax2 = plt.subplots(figsize=(10, 6))

# 计算位置 - 从更靠中间的位置开始
x_positions = []
group_centers = []
current_x = 1.5  # 从更靠中间的位置开始
group_gap = 2.5  # 增大组间间隔

all_labels = []
all_models = []

for group_name, group_info in groups_2.items():
    group_start = current_x
    for i, (model, label) in enumerate(zip(group_info['models'], group_info['labels'])):
        x_positions.append(current_x)
        all_labels.append(label)
        all_models.append(model)
        current_x += bar_width + bar_gap
    
    group_end = current_x - bar_gap
    group_centers.append((group_start + group_end - bar_width) / 2)
    current_x += group_gap

# 绘制堆叠柱状图
math500_noop_values = [data[model]['math500_noop'] for model in all_models]
math500_diff_values = [data[model]['math500'] - data[model]['math500_noop'] for model in all_models]
math500_values = [data[model]['math500'] for model in all_models]
rel_delta_values = [data[model]['rel_delta'] for model in all_models]

# 转换rel_delta为0-1范围的值
rel_delta_normalized = [abs(delta) / 100 for delta in rel_delta_values]

# 绘制柱子
bars1 = ax2.bar(x_positions, math500_noop_values, width=bar_width, 
               label='math500-Noop', color='lightgray', alpha=0.8)
bars2 = ax2.bar(x_positions, math500_diff_values, width=bar_width, 
               bottom=math500_noop_values, label='math500', 
               color='steelblue', alpha=0.8)

# 绘制rel_delta折线（分组绘制，组间不连接）
line_plotted = False
current_pos = 0
for group_name, group_info in groups_2.items():
    group_size = len(group_info['models'])
    group_x = x_positions[current_pos:current_pos + group_size]
    group_rel_delta = rel_delta_normalized[current_pos:current_pos + group_size]
    
    if not line_plotted:
        ax2.plot(group_x, group_rel_delta, 'o-', color=rel_delta_color, linewidth=2.5, 
                markersize=8, label=r'$\Delta$%', alpha=0.9)
        line_plotted = True
    else:
        ax2.plot(group_x, group_rel_delta, 'o-', color=rel_delta_color, linewidth=2.5, 
                markersize=8, alpha=0.9)
    
    current_pos += group_size

# 在柱子内部添加数值标注
for i, (x, noop, diff, math500, delta) in enumerate(zip(x_positions, math500_noop_values, math500_diff_values, math500_values, rel_delta_values)):
    if noop > 0.05:
        ax2.text(x, noop/2, f'{noop:.3f}', 
                ha='center', va='center', fontsize=12, fontweight='bold', color='black')
    
    if diff > 0.03:
        ax2.text(x, noop + diff/2, f'{diff:.3f}', 
                ha='center', va='center', fontsize=12, fontweight='bold', color='white')
    
    total_height = noop + diff
    ax2.text(x, total_height + 0.01, f'{delta:.1f}%', 
            ha='center', va='bottom', fontsize=12, fontweight='bold', color=rel_delta_color)

# 设置x轴标签
ax2.set_xticks(x_positions)
ax2.set_xticklabels(all_labels, rotation=0, ha='center', fontsize=14)

# 添加组标签 - 增加距离
for i, (group_name, center) in enumerate(zip(groups_2.keys(), group_centers)):
    ax2.text(center, -0.1, group_name, ha='center', va='top', 
            fontweight='bold', fontsize=16, transform=ax2.get_xaxis_transform())

# 设置标签
ax2.set_ylabel('Score', fontsize=16, fontweight='bold')

# 调整图例位置
ax2.legend(loc='upper left', fontsize=14, frameon=True, fancybox=True, shadow=True)

# 设置网格
ax2.grid(True, alpha=0.3, axis='y')
max_height = max([data[model]['math500'] for model in all_models])
ax2.set_ylim(0, max_height * 1.2)
ax2.set_xlim(0, max(x_positions) + 1.5)  # 调整边界让柱子更居中

# 设置y轴刻度标签字体大小
ax2.tick_params(axis='y', labelsize=14)

plt.tight_layout()
plt.show()