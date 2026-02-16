import os
import pickle
import networkx as nx
from pathlib import Path

def get_data_path(filename):
    base_dir = Path(__file__).resolve().parents[1]
    return base_dir / "data" / filename

def load_graph(filename):
    path = get_data_path(filename)
    
    if not path.exists():
        return None
    
    try:
        with open(path, 'rb') as f:
            return pickle.load(f)
    except Exception as e:
        print(f"[ERRORE] Caricamento fallito per {filename}: {e}")
        return None

def analyze_edges(G):
    #analizziamo la composizione del grafo per quanto riguareda le relazione e il numero totale di archi presenti per controllo
    counts = {'classmate': 0, 'groupmate': 0, 'friend': 0, 'total': 0}
    
    #Iteriamo sul multigraph
    for _, _, _, data in G.edges(keys=True, data=True):
        subtype = data.get('subtype', 'other')
        if subtype in counts:
            counts[subtype] += 1
        counts['total'] += 1
        
    return counts

def print_header():
    #stampa di una tabella riepilogativa per controllo valori 
    header = f"{'STRATEGIA DI ANONIMIZZAZIONE':<35} | {'NODI':<6} | {'TOT ARCHI':<10} | {'CLASS':<6} | {'GROUP':<6} | {'FRIEND':<6}"
    separator = "-" * len(header)
    print(separator)
    print(header)
    print(separator)

def main():
    #effettuiamo il controllo su tutti i gpickle generati fino ad adessso
    experiment_files = [
        ("Originale (Ground Truth)",    "grafo_cache.gpickle"),
        ("1. Baseline (No Friends)",    "anon_1_baseline.gpickle"),
        ("2. Partial (50% Noise)",      "anon_2_partial.gpickle"),
        ("3a. Random Unconstrained",    "anon_3_unconstrained.gpickle"),
        ("3b. Random Constrained",      "anon_4_constrained.gpickle"),
        ("4a. Greedy Unconstrained",    "anon_6_greedy_unc.gpickle"),
        ("4b. Greedy Constrained",      "anon_7_greedy_cons.gpickle"),
        ("5. Total Removal (Empty)",    "anon_5_empty.gpickle")
    ]

    print_header()

    for label, filename in experiment_files:
        G = load_graph(filename)
        if G is None:
            print(f"{label:<35} | {'[NON GENERATO]':<10}")
            continue

        n_nodes = G.number_of_nodes()
        stats = analyze_edges(G)
        
        # formattaione dei dati
        print(f"{label:<35} | {n_nodes:<6} | {stats['total']:<10} | "
              f"{stats['classmate']:<6} | {stats['groupmate']:<6} | {stats['friend']:<6}")

    print("-" * 85)

if __name__ == "__main__":
    main()