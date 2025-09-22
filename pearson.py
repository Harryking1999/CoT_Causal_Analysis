import numpy as np
from scipy.stats import pearsonr

# Base模型+GRPO数据
base_spurious = [10.2, 9.6, 14.5, 8.5]  # 伪特征程度 (%)
base_causal = [0, 1, 0, 2]  # 好的因果图数量
# base_spurious = [0, -0.6, 4.3, -1.7, 0, -23.4, -24.3, -22.1]  # 伪特征程度 (%)
# base_causal = [0, 1, 0, 2, 0,1,2,3]  # 好的因果图数量

# SFT模型+GRPO数据
sft_spurious = [39.0, 15.6, 14.7, 16.9]  # 伪特征程度 (%)
sft_causal = [1, 2, 3, 4]  # 好的因果图数量

# 计算Base组的皮尔森相关系数
base_corr, base_p_value = pearsonr(base_spurious, base_causal)

# 计算SFT组的皮尔森相关系数
sft_corr, sft_p_value = pearsonr(sft_spurious, sft_causal)

# 输出结果
print("Base模型+GRPO组:")
print(f"皮尔森相关系数: {base_corr:.3f}")
print(f"p值: {base_p_value:.3f}")

print("\nSFT模型+GRPO组:")
print(f"皮尔森相关系数: {sft_corr:.3f}")
print(f"p值: {sft_p_value:.3f}")

# 如果需要手动计算（不使用scipy）
def manual_pearson(x, y):
    n = len(x)
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    
    numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    sum_sq_x = sum((x[i] - mean_x) ** 2 for i in range(n))
    sum_sq_y = sum((y[i] - mean_y) ** 2 for i in range(n))
    
    denominator = (sum_sq_x * sum_sq_y) ** 0.5
    
    return numerator / denominator if denominator != 0 else 0

# 手动计算验证
print("\n手动计算验证:")
print(f"Base组手动计算: {manual_pearson(base_spurious, base_causal):.3f}")
print(f"SFT组手动计算: {manual_pearson(sft_spurious, sft_causal):.3f}")