import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Circle
import numpy as np

# 分数（示例）
score_z_y = 0.6
score_x1_y = 0.9
score_x2_y = 0.3

def score_to_color(score):
    # 0分全透明，1分全黑
    alpha = score
    return (0, 0, 0, alpha)

# 节点坐标
x_gap = 2.3 # 节点距离
y0 = 0
nodes = {
    'Z':  (0, y0),
    'X1': (x_gap, y0),
    'X2': (x_gap*2, y0),
    'Y':  (x_gap*3, y0)
}

node_colors = {
    'Z':  '#b39ddb', # 浅紫
    'X1': '#fff59d', # 浅黄
    'X2': '#fff59d',
    'Y':  '#a5d6a7'  # 浅绿
}

node_size = 1100

fig, ax = plt.subplots(figsize=(8,5))
plt.axis("off")

# 画节点
for name, (x,y) in nodes.items():
    circ = Circle((x,y), 0.2, color=node_colors[name], zorder=10, ec='k', lw=1.2)
    ax.add_patch(circ)
    plt.text(x, y, name, ha='center', va='center', fontsize=18, zorder=11, fontweight="bold")

# 连线函数
def draw_arrow(ax, start, end, label='', color=(0,0,0,1), curve_height=0):
    x0, y0 = start
    x1, y1 = end
    # 曲线
    if curve_height != 0:
        con = FancyArrowPatch(
            posA=(x0, y0),
            posB=(x1, y1),
            connectionstyle=f"arc3,rad={curve_height}",
            arrowstyle='-|>',
            mutation_scale=28,
            lw=3,
            color=color
        )
    else:
        con = FancyArrowPatch(
            posA=(x0, y0),
            posB=(x1, y1),
            arrowstyle='-|>',
            mutation_scale=28,
            lw=3,
            color=color
        )
    ax.add_patch(con)
    # 在线条上标注
    if label:
        xm = (x0+x1)/2
        ym = (y0+y1)/2 + (curve_height*1) # 曲线标注要偏移一点
        plt.text(xm, ym, f"{label:.2f}", color='black', fontsize=13, zorder=12, fontweight='bold', ha='center', va='center')

# 连基础直线
draw_arrow(ax, nodes['Z'], nodes['X1'], color='k')
draw_arrow(ax, nodes['X1'], nodes['X2'], color='k')

# 曲线和直线到Y
draw_arrow(ax, nodes['Z'], nodes['Y'], label=score_z_y, color=score_to_color(score_z_y), curve_height=-0.43)
draw_arrow(ax, nodes['X1'], nodes['Y'], label=score_x1_y, color=score_to_color(score_x1_y), curve_height=0.35)
draw_arrow(ax, nodes['X2'], nodes['Y'], label=score_x2_y, color=score_to_color(score_x2_y), curve_height=0)

# 画布范围
plt.xlim(-0.9, x_gap*3+1)
plt.ylim(-1.5, 1.5)
plt.tight_layout()
plt.show()