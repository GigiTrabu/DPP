import networkx as nx
import random
import pickle
import os

class NodeAnonymizer:
    def __init__(self, G):
        self.G = G

    def anonymize_nodes(self, k=6, method='random'):
        """
        method='random' shuffle dei nodi casuale
        method='greedy' ordiniamo per grrpo di ricerca
        """
        nodes_list = list(self.G.nodes(data=True))
        
        # ordinamento dei nodi
        if method == 'greedy':
            # Greedy è deterministico (sempre uguale)
            nodes_list.sort(key=lambda x: str(x[1].get('group', 'zzzz')))
        else:
            random.shuffle(nodes_list)
        
        #chunking in cluster di dimensione k (come riportato nel paper)
        clusters = {}
        cluster_id = 0
        current_batch = []
        
        for i, (node, data) in enumerate(nodes_list):
            current_batch.append(node)
            if len(current_batch) == k:
                clusters[cluster_id] = current_batch
                cluster_id += 1
                current_batch = []
        
        # Gestione residui per la k-anonymization (evitiamo di avcere gruppi k anonimizzati più piccolii di k)
        if current_batch:
            for node in current_batch:
                target_c = random.randint(0, cluster_id - 1)
                clusters[target_c].append(node)

        # rinomina dei nodi (C0_0, C0_1, ... per cluster 0; C1_0, C1_1,... per cluster 1 eccetera)
        mapping = {} 
        G_anon = nx.MultiGraph() 
        
        for cid, nodes in clusters.items():
            for idx, original_node in enumerate(nodes):
                new_name = f"C{cid}_{idx}"
                mapping[original_node] = new_name
                
                original_data = self.G.nodes[original_node]
                G_anon.add_node(new_name, cluster=f"C{cid}", **original_data)

        # ricostruzione degli archi con il mapping
        for u, v, key, data in self.G.edges(keys=True, data=True):
            if u in mapping and v in mapping:
                G_anon.add_edge(mapping[u], mapping[v], **data)

        #Salviamo mapping in cache per poterlo riutilizzare in anonymizerEdges
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        map_path = os.path.join(base_dir, "data", "node_mapping.pickle")
        with open(map_path, 'wb') as f:
            pickle.dump(mapping, f)

        return G_anon