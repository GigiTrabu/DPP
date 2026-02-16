import networkx as nx
import pickle
import os
import random
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try:
    from anonymizerNodes import NodeAnonymizer
    from visualizerGraph import GraphVisualizer
except ImportError as e:
    print(f"Errore critico: Impossibile importare moduli dipendenti ({e}).")
    sys.exit(1)

def remove_sensitive_edges(G):
    """
    Rimozione degli archi sensibili (amico) così da avere il nostro grafo clean
    (algoritmo per tecnica Baseline del paper)
    """
    G_clean = G.copy()
    to_rem = [(u,v,k) for u,v,k,d in G_clean.edges(keys=True, data=True) 
              if d.get('subtype') == 'friend']
    G_clean.remove_edges_from(to_rem)
    return G_clean

def _collapse_graph(G_input, constrained=False):
    """
    funzione per far collassare i nodi in un macro-nodo (CLUSTER)
    se constrained = false -> unconstrained -> manteniamo tutti gli edges tra i macro nodi
    se constrained = true -> constrained -> un solo arco per tipo tra i macronodi
    """
    G_collapsed = nx.MultiGraph()
    #estraiamo l'ID del cluster dal nome del nodo (assegnato nel nodeanonimyzer)
    node_to_cluster = {n: n.split('_')[0] for n in G_input.nodes()}
    
    #creeazione cluster
    for cluster_id in set(node_to_cluster.values()):
        G_collapsed.add_node(cluster_id, cluster=cluster_id)
    
    seen_types = set()
    for u, v, k, d in G_input.edges(keys=True, data=True):
        if d.get('subtype') == 'friend': continue # non dovrebbero essserci amici presenti, ma se ci sono non li facciamo collassare
        
        c1, c2 = node_to_cluster[u], node_to_cluster[v]
        if c1 == c2: continue # Rimozione dei loop interni
        
        if constrained:
            # identifichiamounivocamente la connessione per tipo tra i due cluster visionati
            connection_id = tuple(sorted((c1, c2))) + (d.get('subtype'),)
            if connection_id in seen_types: continue
            seen_types.add(connection_id)
            G_collapsed.add_edge(c1, c2, **d)
        else:
            G_collapsed.add_edge(c1, c2, **d)
            
    return G_collapsed

def anonymize_and_save(G_raw, k_val=6):
    """
    Generiamo le 5 varianti di anonimizzazione proposte dal paper (nel mio caso 7 contando la clusterizzazione greedy)
    Restituisce un dizionario di grafi pronti per il salvataggio.
    """
    results = {}
    node_anon = NodeAnonymizer(G_raw)

    # (1) Baseline -> rimozione degli archi sensibili
    G_anon_rand = node_anon.anonymize_nodes(k=k_val, method='random')
    G_public = remove_sensitive_edges(G_anon_rand)

    results['baseline'] = G_public.copy()
    
    # (2) Partial -> rimozione del 50% delle relazioni 
    G_part = G_public.copy() #partiamo sempre dalla baseline (senza archi sensibili)
    edges = list(G_part.edges(keys=True))
    random.shuffle(edges)
    G_part.remove_edges_from(edges[:int(len(edges)*0.5)])
    results['partial'] = G_part

    # (5) Empty -> rimozione di tutte le relazioni
    G_empty = G_public.copy()
    G_empty.remove_edges_from(list(G_empty.edges(keys=True)))
    results['empty'] = G_empty

    # (3/4) Cluster Strategies (RANDOM)
    results['cluster_random_unc_k6'] = _collapse_graph(G_anon_rand, constrained=False)
    results['cluster_random_cons_k6'] = _collapse_graph(G_anon_rand, constrained=True)

    # (3/4) Cluster Strategies (GREEDY)
    G_anon_greedy = node_anon.anonymize_nodes(k=k_val, method='greedy')
    results['cluster_greedy_unc'] = _collapse_graph(G_anon_greedy, constrained=False)
    results['cluster_greedy_cons'] = _collapse_graph(G_anon_greedy, constrained=True)

    return results

def main():
    # Setup percorsi
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    viz_dir = os.path.join(base_dir, "output", "visualizations")
    cache_path = os.path.join(data_dir, "grafo_cache.gpickle")

    # Mappatura chiavi interne -> nomi file fisici per salvataggio file .gpickle per successivi simulazioni di attacco sui grafi
    FILE_MAP = {
        'baseline':               'anon_1_baseline.gpickle',
        'partial':                'anon_2_partial.gpickle',
        'cluster_random_unc_k6':  'anon_3_unconstrained.gpickle',
        'cluster_random_cons_k6': 'anon_4_constrained.gpickle',
        'empty':                  'anon_5_empty.gpickle',
        'cluster_greedy_unc':     'anon_6_greedy_unc.gpickle',
        'cluster_greedy_cons':    'anon_7_greedy_cons.gpickle'
    }

    if not os.path.exists(cache_path):
        print("Errore: Cache del grafo non trovata. Eseguire prima il loader.")
        return

    print("[EdgeAnon] Avvio elaborazione varianti...")
    with open(cache_path, 'rb') as f:
        G_raw = pickle.load(f)

    #Visualizzazione grafo originale
    GraphVisualizer(G_raw).plot_all_relationships(output_dir=viz_dir)

    # Elaborazione
    anonymized_results = anonymize_and_save(G_raw)

    #salviamo e visualiziamo (grazie a GraphVisualizer) i vari grafi anonimizzati
    for key, G_variant in anonymized_results.items():
        if key in FILE_MAP:
            fname = FILE_MAP[key]
            save_path = os.path.join(data_dir, fname)
            
            with open(save_path, 'wb') as f:
                pickle.dump(G_variant, f)
            
            print(f" -> Salvataggio: {fname}")

            # generazione grafica
            viz = GraphVisualizer(G_variant)
            title = key.replace('_', ' ').replace('k6', '').capitalize()
            viz.plot_anonymized_graph(f"graph_{key}.png", f"Configurazione: {title}", viz_dir)

if __name__ == "__main__":
    main()