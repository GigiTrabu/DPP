import numpy as np
import matplotlib.pyplot as plt
import os

if not os.path.exists("output"):
    os.makedirs("output")

#numero nodi 
N = np.linspace(1, 10000, 500)

def plot_defense_vs_attack_shared_scale():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8), sharey=True)

    cost_baseline = 0.002 * N 
    cost_partial = cost_baseline + (0.001 * N)
    cost_random = cost_baseline + (0.0015 * N)
    cost_greedy_unc = cost_baseline + (0.0005 * N * np.log2(N + 1))
    cost_greedy_con = cost_baseline + (0.0000008 * N**2)

    ax1.plot(N, cost_baseline, label='1. Baseline (O(n))', color='blue', lw=2)
    ax1.plot(N, cost_partial, label='2. Partial (O(n))', color='orange', linestyle='--')
    ax1.plot(N, cost_random, label='3. Random (O(n))', color='red', alpha=0.7)
    ax1.plot(N, cost_greedy_unc, label='4. Greedy Unconstrained (O(n log n))', color='green', lw=2)
    ax1.plot(N, cost_greedy_con, label='5. Greedy Constrained (O(n²))', color='darkgreen', lw=2.5)

    ax1.set_title("A. Theoretical Complexity: Defense", fontsize=14, fontweight='bold')
    ax1.set_xlabel("Graph Size (Nodes)")
    ax1.set_ylabel("Computational Cost Units")
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='upper left', shadow=True)
    ax1.ticklabel_format(style='plain')

    # Global Density: O(n)
    cost_global = 0.0012 * N
    # Noisy-OR: O(n²) - Calcolato su tutte le coppie possibili
    cost_noisy_or = 0.0000018 * N**2
    # Blind Mapping: O(n³) - Rappresentazione dello sforzo combinatorio
    cost_blind = 0.0000000004 * N**3

    ax2.plot(N, cost_global, label='Global Density Attack (O(n))', color='cyan', lw=2)
    ax2.plot(N, cost_noisy_or, label='Noisy-OR Attack (O(n²))', color='purple', lw=2.5)
    ax2.plot(N, cost_blind, label='Blind Mapping Attack (O(n³))', color='magenta', linestyle='--')

    ax2.set_title("B. Theoretical Complexity: Attack", fontsize=14, fontweight='bold')
    ax2.set_xlabel("Graph Size (Nodes)")
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='upper left', shadow=True)
    ax2.ticklabel_format(style='plain')

    plt.suptitle("Algorithmic Complexity Analysis: Defense vs Attack (Uniform Scale)", fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig("output/complexity_defense_attack.png", dpi=300)
    print("Grafico generato in output/complexity_defense_attack.png")

if __name__ == "__main__":
    plot_defense_vs_attack_shared_scale()