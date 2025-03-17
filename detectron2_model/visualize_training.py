import json
import numpy as np
import matplotlib.pyplot as plt
import os


# Load data from the provided snippet
file_path = "./Training Phase/third_train_output/metrics.json"  # Update with correct path

iterations = []
total_losses = []

# Read and process the file
with open(file_path, "r") as file:
    for line in file:
        try:
            data = json.loads(line.strip())
            iterations.append(data["iteration"])
            total_losses.append(data["total_loss"])
        except json.JSONDecodeError:
            continue

# Compute Moving Average with window size 20
window_size = 50
moving_avg = np.convolve(total_losses, np.ones(window_size) / window_size, mode='valid')

# Adjust iterations to match the moving average length
iterations_ma = iterations[window_size - 1:]

# Plot total loss and moving average
plt.figure(figsize=(10, 9))
plt.plot(iterations, total_losses, linestyle='-', alpha=0.5, label="Total Loss")
plt.plot(iterations_ma, moving_avg, linestyle='-', color='red', label="Moving Average (20)")

# Add vertical lines for checkpoints
checkpoint_iters = [1999, 3999, 5999, 7999]
for ckpt in checkpoint_iters:
    plt.axvline(x=ckpt, color='blue', linestyle='--', alpha=0.7, label=f"Checkpoints" if ckpt == 1999 else None)

# Labels, title, and legend
plt.xlabel("Iteration")
plt.ylabel("Total Loss")
plt.title("Total Loss per Iteration with Moving Average (20) and Checkpoints")
plt.legend()
plt.grid(True)

# Save the image
plt.savefig("total_loss_plot.png", dpi=300, bbox_inches='tight')
plt.show()
