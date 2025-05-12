import numpy as np
import matplotlib.pyplot as plt
from scipy.special import erf

def relu(x):
    return np.maximum(0, x)

def gelu(x):
    return 0.5 * x * (1 + erf(x / np.sqrt(2)))

def swish(x):
    return x * (1 / (1 + np.exp(-x)))

# Generate x values
x = np.linspace(-4, 4, 1000)

# Calculate y values for each activation function
y_relu = relu(x)
y_gelu = gelu(x)
y_swish = swish(x)

# Create the plot
plt.figure(figsize=(8, 5))

# Plot each activation function
plt.plot(x, y_relu, label='ReLU', linewidth=2)
plt.plot(x, y_gelu, label='GELU', linewidth=2)
plt.plot(x, y_swish, label='Swish', linewidth=2)

# Add grid and labels
plt.grid(True, linestyle='--', alpha=0.7)
plt.xlabel('Input (x)', fontsize=12)
plt.ylabel('Output', fontsize=12)
plt.title('Activation Functions Comparison', fontsize=14)
plt.legend(fontsize=12)

# Add zero lines
plt.axhline(y=0, color='k', linestyle='-', alpha=0.3)
plt.axvline(x=0, color='k', linestyle='-', alpha=0.3)

# Set axis limits
plt.xlim(-4, 4)
plt.ylim(-1, 4)

# Show the plot
plt.tight_layout()
plt.show() 