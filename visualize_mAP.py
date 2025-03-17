import json
import matplotlib.pyplot as plt
import os

def visualize_map_results(results_file="checkpoint_evaluation.json"):
    """Visualizes mAP@50 and mAP@50:95 results from a JSON file."""

    if not os.path.exists(results_file):
        print(f"Error: Results file '{results_file}' not found.")
        return

    try:
        with open(results_file, "r") as f:
            results = json.load(f)
    except FileNotFoundError:
        print(f"Error: Results file '{results_file}' not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in '{results_file}'.")
        return

    iterations = sorted(map(int, results.keys()))
    mAP_50_values = [results[str(iter_num)]["mAP@50"] for iter_num in iterations]
    mAP_50_95_values = [results[str(iter_num)]["mAP@50:95"] for iter_num in iterations]

    plt.figure(figsize=(10, 6))
    plt.plot(iterations, mAP_50_values, label="mAP@50", marker='o')
    plt.plot(iterations, mAP_50_95_values, label="mAP@50:95", marker='o')

    # Add node labels
    for i, iter_num in enumerate(iterations):
        plt.annotate(f"{mAP_50_values[i]:.2f}", (iter_num, mAP_50_values[i]), textcoords="offset points", xytext=(0, -15), ha='center', fontsize=8) # mAP@50 below
        plt.annotate(f"{mAP_50_95_values[i]:.2f}", (iter_num, mAP_50_95_values[i]), textcoords="offset points", xytext=(0, 5), ha='center', fontsize=8) # mAP@50:95 above

    plt.xlabel("Checkpoint Iterations")
    plt.ylabel("mAP Value")
    plt.title("mAP@50 and mAP@50:95 vs. Checkpoint Iterations")
    plt.legend()
    plt.grid(True, alpha=0.3)

    # Hide specific x-axis labels, but keep gridlines
    hidden_labels = [3000, 5000, 7000]
    all_ticks = [iter_num for iter_num in iterations]
    plt.xticks(all_ticks)
    ax = plt.gca()
    for label in ax.get_xticklabels():
        if int(label.get_text()) in hidden_labels:
            label.set_visible(False)

    plt.show()

if __name__ == "__main__":
    visualize_map_results()