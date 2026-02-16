#!/usr/bin/env python3
import os
import pickle
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict
from anonymizerNodes import NodeAnonymizer

CONFIG = {
    "N_SAMPLES": 20,           # Numero di ripetizioni per ogni taglia di dataset
    "K_VALUES": [6, 2],        # Valori di k-anonimità da confrontare
    "PERCENTAGES": [10, 20, 30, 40, 50, 75, 100],
    "COLORS": {"greedy": "green", "random": "red", "gain": "blue"}
}

def get_paths():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return {
        "graph": os.path.join(base_dir, "data", "grafo_cache.gpickle"),
        "mapping": os.path.join(base_dir, "data", "node_mapping.pickle"),
        "output": os.path.join(base_dir, "output", "structural_analysis.png")
    }

def get_natural_ties(G, nodes_subset):
    """
    Identifichiamo i legami pre-esistenti nel Ground Truth. (grafo originale)
    Un tie esiste se u e v sono connessi E appartengono allo stesso gruppo.
    """
    subset_set = set(nodes_subset)
    ties = []
    for u, v in G.edges():
        if u in subset_set and v in subset_set:
            if G.nodes[u].get('group') == G.nodes[v].get('group'):
                ties.append((u, v))
    return ties

def evaluate_preservation(G_sub, natural_ties, method, k):
    #valutazione del numero di nodi preservati rispetto al numero totale di legami natural
    if not natural_ties:
        return 0.0
    
    #anonimizzazione del grafo campionato a seconda del metodo e del val di k
    anon = NodeAnonymizer(G_sub)
    anon.anonymize_nodes(k=k, method=method)
    
    #caricamento del mapping
    with open(get_paths()["mapping"], 'rb') as f:
        mapping = pickle.load(f)
    
    #mappatura dei nodi per cluster
    node_to_c = {n: str(name).split('_')[0] for n, name in mapping.items()}
    
    #due nodi sono preservati se appartengono allo stesso cluster dopo l'anonimizzazione
    preserved = sum(1 for u, v in natural_ties if node_to_c.get(u) == node_to_c.get(v))
    return (preserved / len(natural_ties)) * 100

def print_results_table(results):
    header = (f"{'NODI':<8} | {'k=6 Grd %':<10} | {'k=6 Rnd %':<10} | {'k=6 Gain':<8} || "
              f"{'k=2 Grd %':<10} | {'k=2 Rnd %':<10} | {'k=2 Gain':<8}")
    sep = "=" * 110
    
    print(f"\n\n{sep}\n{header}\n{'-' * 110}")
    
    for i in range(len(CONFIG["PERCENTAGES"])):
        n = results[6]['nodes'][i]
        r6, r2 = results[6], results[2]
        print(f"{n:<8} | {r6['g'][i]:<10.1f} | {r6['r'][i]:<10.1f} | {r6['gain'][i]:<8.2f} || "
              f"{r2['g'][i]:<10.1f} | {r2['r'][i]:<10.1f} | {r2['gain'][i]:<8.2f}")
    print(f"{sep}\n")

def run_analysis():
    with open(get_paths()["graph"], 'rb') as f:
        G_orig = pickle.load(f)
    
    all_nodes = list(G_orig.nodes())
    total_nodes_count = len(all_nodes)
    results = {k: {'nodes': [], 'g': [], 'r': [], 'gain': []} for k in CONFIG["K_VALUES"]}

    for perc in CONFIG["PERCENTAGES"]:
        node_count = int(total_nodes_count * perc / 100)
        temp_stats = {k: {'g': [], 'r': []} for k in CONFIG["K_VALUES"]}
        
        for _ in range(CONFIG["N_SAMPLES"]):
            # Campionamento casuale dei nodi dal Ground Truth
            subset = list(np.random.choice(all_nodes, size=node_count, replace=False))
            G_sub = G_orig.subgraph(subset).copy()
            ties = get_natural_ties(G_orig, subset)
            
            if not ties: continue

            for k in CONFIG["K_VALUES"]:
                temp_stats[k]['g'].append(evaluate_preservation(G_sub, ties, 'greedy', k))
                temp_stats[k]['r'].append(evaluate_preservation(G_sub, ties, 'random', k))

        for k in CONFIG["K_VALUES"]:
            avg_g = np.mean(temp_stats[k]['g'])
            avg_r = np.mean(temp_stats[k]['r'])
            results[k]['nodes'].append(node_count)
            results[k]['g'].append(avg_g)
            results[k]['r'].append(avg_r)
            results[k]['gain'].append(avg_g / avg_r if avg_r > 0 else 1.0)

    print_results_table(results)
    return results

def plot_dual_results(res):
    """Genera il grafico comparativo side-by-side k=6 vs k=2."""
    fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=(18, 8), sharey=True)
    plots = [(ax_left, 6, "k=6"), (ax_right, 2, "k=2")]

    # Scala globale per i Gain per rendere i grafici confrontabili visivamente
    max_gain_val = max([max(res[k]['gain']) for k in CONFIG["K_VALUES"]])

    for ax, k, title in plots:
        x = res[k]['nodes']
        
        # Plot linee principali (Utility)
        ax.plot(x, res[k]['g'], 'go-', label='Greedy', lw=3, ms=8, zorder=5)
        ax.plot(x, res[k]['r'], 'ro-', label='Random', lw=3, ms=8, zorder=4)
        
        ax.set_title(title, fontsize=15, fontweight='bold', pad=15)
        ax.set_xlabel('Numero di Nodi nel Dataset', fontweight='bold')
        ax.grid(True, alpha=0.2, linestyle='--')
        ax.set_ylim(-5, 115)
        
        # Plot barre secondarie (Gain Factor)
        ax_gain = ax.twinx()
        ax_gain.bar(x, res[k]['gain'], alpha=0.1, color=CONFIG["COLORS"]["gain"], width=max(x)*0.03)
        ax_gain.set_ylim(0, max_gain_val * 1.3)
        ax_gain.set_ylabel('Gain Factor (x Volte)', fontweight='bold', color=CONFIG["COLORS"]["gain"], alpha=0.6)
        
        # Annotazioni Gain Factor sopra le barre
        for i, g in enumerate(res[k]['gain']):
            if x[i] > 15: # Evita sovrapposizioni a basse percentuali
                ax_gain.text(x[i], g + 0.05, f'{g:.1f}x', ha='center', va='bottom', 
                             color=CONFIG["COLORS"]["gain"], fontweight='bold', fontsize=9)

    ax_left.set_ylabel('% Legami Naturali Preservati', fontweight='bold', fontsize=12)
    ax_left.legend(loc='upper right', shadow=True)
    ax_right.legend(loc='upper right', shadow=True)

    plt.suptitle("Integrità Strutturale: Impatto di K sulla Preservazione dei Gruppi", 
                 fontsize=18, fontweight='bold', y=1.02)
    
    plt.tight_layout()
    plt.savefig(get_paths()["output"], dpi=300, bbox_inches='tight')
    print(f"Grafico salvato in: {get_paths()['output']}")

if __name__ == "__main__":
    final_results = run_analysis()
    plot_dual_results(final_results)