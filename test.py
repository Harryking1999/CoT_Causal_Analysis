import numpy as np
import matplotlib.pyplot as plt

# 参数
a = 1
p = 0.1
x = np.linspace(1, 100, 200)

# acc 图
plt.figure()
plt.plot(x, a * x**p, color='blue')
plt.xticks([])
plt.yticks([])
plt.box(True)  # 显示边框
plt.show()

# loss 图
plt.figure()
plt.plot(x, a * (1/x)**p, color='red')
plt.xticks([])
plt.yticks([])
plt.box(True)  # 显示边框
plt.show()