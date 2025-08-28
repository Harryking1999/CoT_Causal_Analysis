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

# 定义分组和代号
groups = {
    'Base-RL': {
        'models': ['qwen2.5-3B-base', 'qwen2.5-3B-grpo-600', 'qwen2.5-3B-grpo-1000', 'qwen2.5-3B-grpo-2000'],
        'labels': ['0', '600', '1000', '2000']
    },
    'SFT-RL': {
        'models': ['qwen2.5-3B-sft', 'qwen2.5-3B-sft-grpo-200', 'qwen2.5-3B-sft-grpo-1000', 'qwen2.5-3B-sft-grpo-2000'],
        'labels': ['0', '200', '1000', '2000']
    },
    'Base-RL/Distill': {
        'models': ['qwen2.5-3B-18000-distill-openr1', 'qwen2.5-3B-grpo-16000-openr1'],
        'labels': ['Distill', 'RL']
    },
    'Distill-RL': {
        'models': ['deepseek-distill-1.5b', 'deepscaler-1.5b-preview'],
        'labels': ['Distill', 'Distill+RL']
    }
}

# 创建图表 - 调整图表尺寸
fig, ax = plt.subplots(figsize=(18, 9))

# 计算位置
x_positions = []
group_centers = []
current_x = 0
group_gap = 1.5  # 组间距
bar_gap = 0.2    # 柱间距

all_labels = []
all_models = []

for group_name, group_info in groups.items():
    group_start = current_x
    for i, (model, label) in enumerate(zip(group_info['models'], group_info['labels'])):
        x_positions.append(current_x)
        all_labels.append(label)
        all_models.append(model)
        current_x += 1 + bar_gap
    
    group_end = current_x - bar_gap
    group_centers.append((group_start + group_end - 1) / 2)
    current_x += group_gap

# 绘制堆叠柱状图
math500_noop_values = [data[model]['math500_noop'] for model in all_models]
math500_diff_values = [data[model]['math500'] - data[model]['math500_noop'] for model in all_models]
math500_values = [data[model]['math500'] for model in all_models]
rel_delta_values = [data[model]['rel_delta'] for model in all_models]

# 转换rel_delta为0-1范围的值
rel_delta_normalized = [abs(delta) / 100 for delta in rel_delta_values]

# 绘制柱子
bars1 = ax.bar(x_positions, math500_noop_values, width=0.8, 
               label='math500-Noop', color='lightgray', alpha=0.8)
bars2 = ax.bar(x_positions, math500_diff_values, width=0.8, 
               bottom=math500_noop_values, label='math500', 
               color='steelblue', alpha=0.8)

# 绘制rel_delta折线（分组绘制，组间不连接）
line_plotted = False  # 用于控制图例只显示一次
current_pos = 0
for group_name, group_info in groups.items():
    group_size = len(group_info['models'])
    group_x = x_positions[current_pos:current_pos + group_size]
    group_rel_delta = rel_delta_normalized[current_pos:current_pos + group_size]
    
    if not line_plotted:
        ax.plot(group_x, group_rel_delta, 'o-', color='steelblue', linewidth=2.5, 
                markersize=7, label='rel_delta', alpha=0.9)
        line_plotted = True
    else:
        ax.plot(group_x, group_rel_delta, 'o-', color='steelblue', linewidth=2.5, 
                markersize=7, alpha=0.9)
    
    current_pos += group_size

# 在柱子内部添加数值标注
for i, (x, noop, diff, math500, delta) in enumerate(zip(x_positions, math500_noop_values, math500_diff_values, math500_values, rel_delta_values)):
    # 在灰色部分中间显示math500_noop值
    if noop > 0.05:  # 只有当柱子足够高时才显示
        ax.text(x, noop/2, f'{noop:.3f}', 
                ha='center', va='center', fontsize=9, fontweight='bold', color='black')
    
    # 在蓝色部分中间显示math500值
    if diff > 0.03:  # 只有当差值部分足够高时才显示
        ax.text(x, noop + diff/2, f'{math500:.3f}', 
                ha='center', va='center', fontsize=9, fontweight='bold', color='white')
    
    # 在柱子顶部显示rel_delta
    total_height = noop + diff
    ax.text(x, total_height + 0.01, f'{delta:.1f}%', 
            ha='center', va='bottom', fontsize=9, fontweight='bold')

# 设置x轴标签
ax.set_xticks(x_positions)
ax.set_xticklabels(all_labels, rotation=0, ha='center', fontsize=11)

# 添加组标签
for i, (group_name, center) in enumerate(zip(groups.keys(), group_centers)):
    ax.text(center, -0.05, group_name, ha='center', va='top', 
            fontweight='bold', fontsize=12, transform=ax.get_xaxis_transform())

# 设置标题和标签
ax.set_ylabel('Score', fontsize=13, fontweight='bold')
ax.set_title('Math500 vs Math500-Noop', fontsize=16, fontweight='bold', pad=20)

# 调整图例位置避免重合 - 移到左上角
ax.legend(loc='upper left', fontsize=11, frameon=True, fancybox=True, shadow=True)

# 设置网格
ax.grid(True, alpha=0.3, axis='y')
# 调整y轴上限，给最高的柱子留出更多空间
max_height = max([data[model]['math500'] for model in all_models])
ax.set_ylim(0, max_height * 1.25)

# 调整x轴范围，给右侧说明留出空间
ax.set_xlim(-1, max(x_positions) + 2)

# 分别绘制说明文字，实现组标题加粗效果
legend_groups = [
    ('Base-RL:', [
        '  0: Qwen2.5-3B-Base',
        '  600: Qwen2.5-3B-Base-GRPO-600', 
        '  1000: Qwen2.5-3B-Base-GRPO-1000',
        '  2000: Qwen2.5-3B-Base-GRPO-2000'
    ]),
    ('SFT-RL:', [
        '  0: Qwen2.5-3B-Instruct',
        '  200: Qwen2.5-3B-Instruct-GRPO-200',
        '  1000: Qwen2.5-3B-Instruct-GRPO-1000', 
        '  2000: Qwen2.5-3B-Instruct-GRPO-2000'
    ]),
    ('Base-RL/Distill:', [
        '  Distill: Qwen2.5-3B-Base-Distill-openr1',
        '  RL: Qwen2.5-3B-Base-GRPO-openr1'
    ]),
    ('Distill-RL:', [
        '  Distill: Deepseek-Distill-Qwen-1.5b',
        '  Distill+RL: Deepscaler-1.5b-Preview'
    ])
]

# 计算文字位置
start_y = 0.85
current_y = start_y
line_height = 0.04

for group_title, group_items in legend_groups:
    # 绘制组标题（加粗）
    ax.text(1.02, current_y, group_title, transform=ax.transAxes, fontsize=10, 
            fontweight='bold', verticalalignment='top')
    current_y -= line_height
    
    # 绘制组内容（普通字体）
    for item in group_items:
        ax.text(1.02, current_y, item, transform=ax.transAxes, fontsize=10, 
                fontweight='normal', verticalalignment='top')
        current_y -= line_height
    
    # 组间空行
    current_y -= line_height * 0.5

# 添加背景框
from matplotlib.patches import Rectangle
bbox_height = start_y - current_y + 0.05
bbox = Rectangle((1.01, current_y - 0.02), 0.25, bbox_height, 
                 transform=ax.transAxes, facecolor='lightgray', alpha=0.8, 
                 edgecolor='gray', linewidth=1)
ax.add_patch(bbox)

plt.tight_layout()
plt.show()