# --------------------------------------------------#
#                                                   #
#           porzione di codice sui grafici          #
#           creata con l'aiuto di Gemini AI         #
#                                                   #
#---------------------------------------------------#

import os
import pickle
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
import csv

def load_graph(filename):
    """
    Caricamento dei grafi gpickle
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base_dir, "data", filename)
    if not os.path.exists(path): return None
    try:
        with open(path, 'rb') as f: return pickle.load(f)
    except Exception as e:
        print(f"Errore caricamento {filename}: {e}")
        return None

def count_edges_by_type(G):
    """
    contiamo gli edge a seconda del tipo
    """
    counts = {'classmate': 0, 'groupmate': 0, 'friend': 0, 'total': 0}
    for u, v, k, d in G.edges(keys=True, data=True):
        st = d.get('subtype', 'other')
        if st in counts: counts[st] += 1
        counts['total'] += 1
    return counts

def calculate_utility(G_original, G_anonymized):
    """
    Calcola le metriche base di utilità:
    - Differenza nel numero totale di archi.
    - Percentuale di preservazione
    studio basato sul paper (Utility Analysis, Sezione 8.1)
    """
    edges_orig = count_edges_by_type(G_original)
    edges_anon = count_edges_by_type(G_anonymized)
    
    edges_removed_total = edges_orig['total'] - edges_anon['total']
    edge_preservation_rate = 100 * (1 - edges_removed_total / edges_orig['total']) if edges_orig['total'] > 0 else 0
    
    edge_stats = {
        'total_removed': edges_removed_total,
        'preservation_rate': edge_preservation_rate,
        'classmate': edges_anon['classmate'],
        'groupmate': edges_anon['groupmate']
    }
    return edge_stats

def run_utility_analysis():
    """
    Confrontiamo il Ground truth con i vari grafi anonimizzati
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(base_dir, "output")
    if not os.path.exists(output_dir): os.makedirs(output_dir)

    G_original = load_graph("grafo_cache.gpickle")
    if G_original is None: return

    # Elenco delle strategie da processare con i relativi nomi file
    strategies = [
        ("Baseline (Intact)",           "anon_1_baseline.gpickle"),
        ("Partial (50% removal)",       "anon_2_partial.gpickle"),
        ("Cluster Random Unc (k=6)",    "anon_3_unconstrained.gpickle"),
        ("Cluster Random Cons (k=6)",   "anon_4_constrained.gpickle"),
        ("Cluster Greedy Unc (k=6)",    "anon_6_greedy_unc.gpickle"),
        ("Cluster Greedy Cons (k=6)",   "anon_7_greedy_cons.gpickle"),
        ("Total Removal",               "anon_5_empty.gpickle")
    ]
    
    results_summary = {}
    for label, filename in strategies:
        G_anon = load_graph(filename)
        if G_anon is not None:
            results_summary[label] = [calculate_utility(G_original, G_anon)]

    # Generazione dei tre asset grafici principali
    plot_edge_preservation(results_summary, output_dir)
    plot_collapse_distribution(G_original, output_dir)
    plot_edge_type_breakdown(G_original, strategies, output_dir)
    print(f"Grafici salvati correttamente in: {output_dir}")

def plot_edge_preservation(results_summary, output_dir):
    labels = list(results_summary.keys())
    preservation_rates = [results_summary[l][0]['preservation_rate'] for l in labels]
    
    fig, ax = plt.subplots(figsize=(12, 6))
    colors = ['green' if rate > 80 else 'orange' if rate > 50 else 'red' for rate in preservation_rates]
    bars = ax.barh(range(len(labels)), preservation_rates, color=colors, edgecolor='black')
    
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels)
    ax.set_xlabel("Edge Preservation Rate (%)", fontweight='bold')
    ax.set_title("Utility: Edge Preservation by Technique", fontweight='bold', fontsize=12)
    ax.set_xlim(0, 105)
    
    # Aggiunta di etichette percentuali a fine barra per leggibilità immediata
    for i, rate in enumerate(preservation_rates):
        ax.text(rate + 1, i, f'{rate:.1f}%', va='center', fontweight='bold')
    
    ax.xaxis.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "utility_edge_preservation.png"), dpi=300)
    plt.close()

def plot_collapse_distribution(G_original, output_dir):
    from anonymizerNodes import NodeAnonymizer
    
    # Rigenerazione locale del clustering per calcolare i rapporti originali
    node_anon_rand = NodeAnonymizer(G_original)
    G_nodes_rand = node_anon_rand.anonymize_nodes(k=6, method='random')
    node_anon_grd = NodeAnonymizer(G_original)
    G_nodes_grd = node_anon_grd.anonymize_nodes(k=6, method='greedy')

    G_rand_cons = load_graph('anon_4_constrained.gpickle')
    G_grd_cons = load_graph('anon_7_greedy_cons.gpickle')

    def pair_stats(G_nodes, G_collapsed):
        #mappatura dei nodi
        node_to_cluster = {n: str(n).split('_')[0] for n in G_nodes.nodes()}
        orig_counts = defaultdict(int)
        for u, v, k, d in G_nodes.edges(keys=True, data=True):
            if d.get('subtype') == 'friend' or u not in node_to_cluster or v not in node_to_cluster: continue
            c1, c2 = node_to_cluster[u], node_to_cluster[v]
            if c1 != c2: orig_counts[tuple(sorted((c1, c2)))] += 1

        coll_counts = defaultdict(int)
        if G_collapsed is not None:
            for u, v, k, d in G_collapsed.edges(keys=True, data=True):
                coll_counts[tuple(sorted((str(u), str(v))))] += 1
        
        # rapporto tra archi originali e archi collassati
        ratios = [orig / coll_counts[p] if coll_counts.get(p, 0) > 0 else float('inf') for p, orig in orig_counts.items()]
        return ratios

    ratios_rand = pair_stats(G_nodes_rand, G_rand_cons)
    ratios_grd = pair_stats(G_nodes_grd, G_grd_cons)
    
    data_rand_plot = [r for r in ratios_rand if np.isfinite(r)]
    data_grd_plot = [r for r in ratios_grd if np.isfinite(r)]
    max_range = max(max(data_rand_plot), max(data_grd_plot)) + 1

    # Visualizzazione distribuzione: Istogrammi sopra, Boxplot sotto
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    axes[0, 0].hist(data_rand_plot, bins=40, color='#3498db', edgecolor='black')
    axes[0, 0].set_title('Compression Ratio Distribution (Random Constrained)', fontweight='bold')
    axes[0, 0].set_xlim(0, max_range)

    axes[0, 1].hist(data_grd_plot, bins=40, color='#9b59b6', edgecolor='black')
    axes[0, 1].set_title('Compression Ratio Distribution (Greedy Constrained)', fontweight='bold')
    axes[0, 1].set_xlim(0, max_range)

    # Boxplot per visualizzare mediana, quartili e outlier (indicano i cluster 'pesanti')
    for ax, data, color, label in zip([axes[1, 0], axes[1, 1]], [data_rand_plot, data_grd_plot], ['#3498db', '#9b59b6'], ['Random', 'Greedy']):
        bp = ax.boxplot(data, vert=True, patch_artist=True, widths=0.5)
        plt.setp(bp['boxes'], facecolor=color, alpha=0.7)
        ax.set_title(f'Percentiles & Outliers ({label})', fontweight='bold')
        ax.set_ylim(0, max_range)
        ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "utility_collapse_ratio_hist.png"), dpi=300)
    plt.close()

def plot_edge_type_breakdown(G_original, strategies, output_dir):
    edges_orig = count_edges_by_type(G_original)
    labels, classmate_counts, groupmate_counts = [], [], []

    for label, filename in strategies:
        G = load_graph(filename)
        if G is None: continue
        labels.append(label)
        edges = count_edges_by_type(G)
        classmate_counts.append(edges['classmate'])
        groupmate_counts.append(edges['groupmate'])

    x = np.arange(len(labels))
    width = 0.35
    fig, ax = plt.subplots(figsize=(12, 6))

    ax.bar(x - width/2, classmate_counts, width, label='Classmate', color='#1f77b4', edgecolor='black')
    ax.bar(x + width/2, groupmate_counts, width, label='Groupmate', color='#ff7f0e', edgecolor='black')
    
    # Linee tratteggiate di riferimento (Baseline originale)
    ax.axhline(y=edges_orig['classmate'], color='#1f77b4', linestyle='--', linewidth=2, label='Orig Classmate')
    ax.axhline(y=edges_orig['groupmate'], color='#ff7f0e', linestyle='--', linewidth=2, label='Orig Groupmate')

    # Valore numerico sopra ogni barra
    for i, (c, g) in enumerate(zip(classmate_counts, groupmate_counts)):
        ax.text(i - width/2, c, str(int(c)), ha='center', va='bottom', fontweight='bold', fontsize=9)
        ax.text(i + width/2, g, str(int(g)), ha='center', va='bottom', fontweight='bold', fontsize=9)

    ax.set_ylabel("Edge Count", fontweight='bold')
    ax.set_title("Edge Type Preservation (Absolute)", fontweight='bold', fontsize=12)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=30, ha='right')
    ax.legend(loc='upper right')
    ax.yaxis.grid(True, linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "utility_edge_type_breakdown.png"), dpi=300)
    plt.close()

if __name__ == "__main__":
    run_utility_analysis()