import os
import random
import sys
import pickle
import numpy as np
from collections import defaultdict
import matplotlib.pyplot as plt

# Seed per la riproducibilità
random.seed(12345)

# Configurazione path per importare i moduli locali
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from anonymizerEdges import _collapse_graph, remove_sensitive_edges
    from attacker import LinkAttacker
    from anonymizerNodes import NodeAnonymizer 
except ImportError as e:
    print(f"Errore Import: {e}")
    sys.exit(1)

# CONFIGURAZIONE ESPERIMENTO basat sui parametri del paper
N_ITERATIONS = 5  
THRESHOLDS = [0.2, 0.4, 0.6, 0.8]
K_VALUES = [2, 6]

def run_simulation():
    # Strutture per aggregare i risultati
    agg_precision = defaultdict(lambda: defaultdict(list))
    agg_tp = defaultdict(lambda: defaultdict(list))
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    cache_path = os.path.join(data_dir, "grafo_cache.gpickle")
    mapping_path = os.path.join(data_dir, "node_mapping.pickle")
    
    if not os.path.exists(cache_path):
        print(f"ERRORE: Grafo cache non trovato in {cache_path}")
        return
    
    with open(cache_path, "rb") as f:
        G_gt_fixed = pickle.load(f)

    print(f"=== INIZIO SIMULAZIONE SU {N_ITERATIONS} ITERAZIONI (k={K_VALUES}) ===")

    for i in range(N_ITERATIONS):
        sys.stdout.write(f"\r -> Esecuzione Run {i+1}/{N_ITERATIONS}...   ")
        sys.stdout.flush()
        
        G_gt = G_gt_fixed.copy()
        node_anon = NodeAnonymizer(G_gt)

        #Baseline e Partial (Base di confronto fissa per ogni run)
        G_nodes_tmp = node_anon.anonymize_nodes(k=2, method='random')
        with open(mapping_path, "rb") as f:
            mapping_std = pickle.load(f)
        
        G_baseline = remove_sensitive_edges(G_nodes_tmp.copy())
        _attack_and_record(G_gt, G_baseline, mapping_std, 'Baseline', agg_precision, agg_tp)
        
        G_partial = G_baseline.copy()
        edges = list(G_partial.edges(keys=True))
        random.shuffle(edges)
        for j in range(int(len(edges)*0.5)): G_partial.remove_edge(*edges[j])
        _attack_and_record(G_gt, G_partial, mapping_std, 'Partial', agg_precision, agg_tp)

        # Loop su k per le varianti Cluster
        for k in K_VALUES:
            #Random metod
            G_nodes_rand = node_anon.anonymize_nodes(k=k, method='random')
            with open(mapping_path, "rb") as f:
                mapping_rand = pickle.load(f)
            
            G_unc_rand = _collapse_graph(G_nodes_rand, constrained=False)
            G_cons_rand = _collapse_graph(G_nodes_rand, constrained=True)
            
            _attack_and_record(G_gt, G_unc_rand, mapping_rand, f'Rand Unc k={k}', agg_precision, agg_tp)
            _attack_and_record(G_gt, G_cons_rand, mapping_rand, f'Rand Cons k={k}', agg_precision, agg_tp)

            #greedy method
            G_nodes_greedy = node_anon.anonymize_nodes(k=k, method='greedy')
            with open(mapping_path, "rb") as f:
                mapping_greedy = pickle.load(f)
            
            G_unc_greedy = _collapse_graph(G_nodes_greedy, constrained=False)
            G_cons_greedy = _collapse_graph(G_nodes_greedy, constrained=True)
            
            _attack_and_record(G_gt, G_unc_greedy, mapping_greedy, f'Grd Unc k={k}', agg_precision, agg_tp)
            _attack_and_record(G_gt, G_cons_greedy, mapping_greedy, f'Grd Cons k={k}', agg_precision, agg_tp)

    print("\n\nGenerazione dei 4 grafici comparativi...")

    # Gruppi per i plot
    strategies_rand = ['Baseline', 'Partial'] + [f'Rand Unc k={k}' for k in K_VALUES] + [f'Rand Cons k={k}' for k in K_VALUES]
    strategies_greedy = ['Baseline', 'Partial'] + [f'Grd Unc k={k}' for k in K_VALUES] + [f'Grd Cons k={k}' for k in K_VALUES]

    #RANDOM - DISCLOSURE
    _plot_custom(agg_tp, strategies_rand, "Disclosure (Count)", "Random Techniques - Fig. 7", "random_disclosure_k2_k6.png")
    #RANDOM - PRECISION
    _plot_custom(agg_precision, strategies_rand, "Precision", "Random Techniques - Fig. 8", "random_precision_k2_k6.png")
    #GREEDY - DISCLOSURE
    _plot_custom(agg_tp, strategies_greedy, "Disclosure (Count)", "Greedy Techniques - Fig. 7", "greedy_disclosure_k2_k6.png")
    #GREEDY - PRECISION
    _plot_custom(agg_precision, strategies_greedy, "Precision", "Greedy Techniques - Fig. 8", "greedy_precision_k2_k6.png")

def _attack_and_record(G_gt, G_anon, mapping, label, agg_prec, agg_tp):
    attacker = LinkAttacker(G_gt, G_anon, mapping)
    predictions = attacker.run_attack()
    for t in THRESHOLDS:
        prec, rec, _, tp = attacker.evaluate(predictions, threshold=t)
        agg_prec[label][t].append(prec)
        agg_tp[label][t].append(tp)


# --------------------------------------------------#
#                                                   #
#               porzione di codice                  #
#           creata con l'aiuto di Gemini AI         #
#                                                   #
#---------------------------------------------------#

def _plot_custom(agg_data, labels_to_plot, ylabel, title, filename):
    # Setup estetico per simulare lo stile del paper(fig 7 e 8)
    plt.figure(figsize=(8, 6))
    ax = plt.gca()
    
    styles = {
        'Baseline':      {'color': '#000080', 'marker': 'D', 'ms': 6, 'ls': '-',  'lw': 1.5}, # Intact
        'Partial':       {'color': '#ff00ff', 'marker': 's', 'ms': 6, 'ls': '-',  'lw': 1.5}, # 50% edges
        
        'Rand Unc k=2':  {'color': '#008000', 'marker': 'o', 'ms': 7, 'ls': '-',  'lw': 1.5},
        'Grd Unc k=2':   {'color': '#008000', 'marker': 'o', 'ms': 7, 'ls': '-',  'lw': 1.5},
        
        'Rand Unc k=6':  {'color': '#800080', 'marker': '*', 'ms': 8, 'ls': '-',  'lw': 1.5},
        'Grd Unc k=6':   {'color': '#800080', 'marker': '*', 'ms': 8, 'ls': '-',  'lw': 1.5},
        
        'Rand Cons k=2': {'color': '#ffff00', 'marker': '^', 'ms': 7, 'ls': '-',  'lw': 1.5},
        'Grd Cons k=2':  {'color': '#ffff00', 'marker': '^', 'ms': 7, 'ls': '-',  'lw': 1.5},
        
        'Rand Cons k=6': {'color': '#a52a2a', 'marker': None, 'ms': 0, 'ls': '-', 'lw': 1.5},
        'Grd Cons k=6':  {'color': '#a52a2a', 'marker': None, 'ms': 0, 'ls': '-', 'lw': 1.5}
    }

    for label in labels_to_plot:
        if label in agg_data:
            t_dict = agg_data[label]
            x = sorted(t_dict.keys())
            y = [np.mean(t_dict[t]) for t in x]
            
            s = styles.get(label, {'color': 'black', 'marker': 'o', 'ms': 4, 'ls': '-', 'lw': 1})
            
            plt.plot(x, y, label=label, color=s['color'], marker=s['marker'], 
                     markersize=s['ms'], linestyle=s['ls'], linewidth=s['lw'],
                     markeredgecolor='black', markeredgewidth=0.5)

    plt.title(title, fontsize=12, fontweight='bold', style='italic')
    plt.xlabel("Probability Threshold", fontsize=10, fontweight='bold')
    plt.ylabel(ylabel, fontsize=10, fontweight='bold')

    ax.yaxis.grid(True, linestyle='-', alpha=0.5)
    ax.xaxis.grid(False)
    
    plt.xticks(THRESHOLDS)
    if "Precision" in ylabel:
        plt.ylim(-0.05, 1.0)
    else:
        plt.ylim(bottom=0)
    
    plt.legend(loc='upper right', fontsize=8, frameon=True, edgecolor='black')

    ax.set_facecolor('white')
    for spine in ax.spines.values():
        spine.set_edgecolor('black')
        spine.set_linewidth(1)

    plt.tight_layout()
    # Salvataggio
    out_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output", filename)
    plt.savefig(out_path, dpi=300)
    plt.show()

if __name__ == "__main__":
    run_simulation()