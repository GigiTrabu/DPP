import json
import networkx as nx
import itertools
import os
import sys
import pickle

class GraphLoader:
    #utilizzo di multigraph per poter annotare più tipi di relazioni (friend, groupmate, classmate) tra gli stessi nodi
    def __init__(self):
        self.G = nx.MultiGraph() 
        self.sensitive_pairs = [] 
        self.observed_pairs = []

    def load_graph(self, json_path):
        print(f"--- [Loader] Caricamento Grafo da JSON ---")
        
        if not os.path.exists(json_path):
            raise FileNotFoundError(f"File non trovato: {json_path}")

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Caricamento dei nodi sul multigraph
        friendship_set = set()
        student_attrs = {}

        for entry in data:
            uid = entry['id']
            group = entry['research_group']
            courses = entry['courses']
            
            self.G.add_node(uid, group=group, courses=tuple(courses))
            student_attrs[uid] = {'group': group, 'courses': set(courses)}

            for friend_id in entry.get('friends', []):
                if friend_id != uid:
                    friendship_set.add(tuple(sorted((uid, friend_id))))

        # generazione archi sul multigraph con annotazione di tipo (friend, groupmate, classmate)
        all_nodes = list(self.G.nodes())
        
        for u, v in itertools.combinations(all_nodes, 2):
            pair = tuple(sorted((u, v)))
            
            # Amizcizie sensibili
            if pair in friendship_set:
                self.sensitive_pairs.append(pair)
                self.G.add_edge(u, v, subtype='friend', weight=4)
            
            u_data = student_attrs[u]
            v_data = student_attrs[v]
            
            # edge per i gruppi
            if u_data['group'] == v_data['group'] and u_data['group'] is not None:
                self.observed_pairs.append(pair)
                self.G.add_edge(u, v, subtype='groupmate', weight=3)
            
            # edge stessa classe (1 per ogni corso)
            common_courses = u_data['courses'].intersection(v_data['courses'])
            for course in common_courses:
                self.observed_pairs.append(pair)
                self.G.add_edge(u, v, subtype='classmate', weight=1, course=course)

        return self.G

    #salvataggio del grafo in cache con gpickle (per evitare di dover ricaricare e processare il JSON ogni volta)
    def save_cache(self, output_path):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'wb') as f:
            pickle.dump(self.G, f)
        print(f"   -> Grafo salvato in cache: {os.path.basename(output_path)}")
        print()


if __name__ == "__main__":
    # Setup Paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_path = os.path.join(base_dir, "data", "studenti_paper_noiseOR.json")
    cache_path = os.path.join(base_dir, "data", "grafo_cache.gpickle")

    if not os.path.exists(json_path): 
        alt_path = os.path.join("data", "studenti_paper_noiseOR.json")
        if os.path.exists(alt_path):
            json_path = alt_path

    # Esecuzione
    loader = GraphLoader()
    
    if os.path.exists(json_path):
        loader.load_graph(json_path)
        loader.save_cache(cache_path)
    else:
        print(f"ERRORE: JSON non trovato in {json_path}")