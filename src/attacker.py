import networkx as nx
import numpy as np
from sklearn.metrics import precision_score, recall_score
from collections import defaultdict
import itertools

class LinkAttacker:
    def __init__(self, ground_truth_G, anonymized_G, mapping):
        """
        Inizializiamo l'attaccante basato sul modello Noisy-OR riportato nel aper
        Implementiamo le Sezioni 6.1, 7.1 e 7.2 del paper orriginale
        """
        self.GT = ground_truth_G
        self.AnonG = anonymized_G
        self.mapping = mapping
        
        # -Parametri noisy-OR (come per creazione amicizie)
        self.lambda_leak = 0.2    
        self.lambda_class = 0.4   
        self.lambda_group = 0.6 
        
        # Determiniamo inizialmente se l'attaccante si trova d'avanti ad un gafo anonimizzato non clusterizzato o clusterizzato
        sample_node = next(iter(self.AnonG.nodes())) if self.AnonG.number_of_nodes() > 0 else ""
        self.is_collapsed = "_" not in str(sample_node) and str(sample_node).startswith("C")

        # Inizializzazione mappature cluster
        self.cluster_sizes = defaultdict(int)
        self.node_to_cluster = {}
        for orig, anon in self.mapping.items():
            cluster_id = anon.split('_')[0]
            self.cluster_sizes[cluster_id] += 1
            self.node_to_cluster[orig] = cluster_id
        
        # parametri per la stima uniforme globale (sez 7.2 del papper)
        self._init_global_stats()

    def _init_global_stats(self):
        #calcoliamo la densità globale di classmate e groupmate nel grafo originale per la stima uniforme globale
        self.total_nodes = self.GT.number_of_nodes()
        self.possible_pairs = (self.total_nodes * (self.total_nodes - 1)) / 2
        self.global_counts = defaultdict(int)
        
        for _, _, d in self.GT.edges(data=True):
            st = d.get('subtype')
            if st in ['classmate', 'groupmate']:
                self.global_counts[st] += 1

    def _noisy_or(self, p_class, p_group):
        #calcolo della probabilità noisyOR
        term_leak = 1.0 - self.lambda_leak
        term_class = 1.0 - (self.lambda_class * p_class)
        term_group = 1.0 - (self.lambda_group * p_group)
        return 1.0 - (term_leak * term_class * term_group)

    def _is_strategy_constrained(self):
        #vediamo se il grafo anonimizzato è constrained
        for u, v in self.AnonG.edges():
            subtypes = [d.get('subtype') for d in self.AnonG[u][v].values()]
            if len(subtypes) != len(set(subtypes)):
                return False
        return True

    def _get_cluster_density(self, c_u, c_v, edge_type):
        #cacoliamo la densità di classmate/groupmate tra i cluster c_u e c_v (sez 7.1 e 7.2)
        if not (self.AnonG.has_node(c_u) and self.AnonG.has_node(c_v)):
            return 0.0
        
        # Contiamo gli archi osservati tra i due cluster analizzati
        count_observed = 0
        if self.AnonG.has_edge(c_u, c_v):
            count_observed = sum(1 for d in self.AnonG[c_u][c_v].values() 
                                 if d.get('subtype') == edge_type)
        
        if count_observed == 0: 
            return 0.0

        # Selezione della modalità di stima
        if self._is_strategy_constrained():
            # Stima Uniforme Globale (Sezione 7.2)
            return self.global_counts[edge_type] / self.possible_pairs
        else:
            # Stima basata sui Cluster (Sezione 7.1)
            size_u, size_v = self.cluster_sizes[c_u], self.cluster_sizes[c_v]
            possible = (size_u * (size_u - 1) / 2) if c_u == c_v else (size_u * size_v)
            return min(1.0, count_observed / possible) if possible > 0 else 0.0

    def run_attack(self):
        predictions = [] 
        nodes = list(self.GT.nodes())
        
        for u, v in itertools.combinations(nodes, 2):
            # recupero del ground truht
            is_friend_real = 1 if self.GT.has_edge(u, v) and any(
                d.get('subtype') == 'friend' for d in self.GT[u][v].values()
            ) else 0
            
            #prediction probabilistica basata su osservazione diretta o stima tramite cluster
            u_anon, v_anon = self.mapping.get(u), self.mapping.get(v)
            
            if u_anon and v_anon:
                if not self.is_collapsed:
                    # Caso Baseline/Partial: Osservazione diretta
                    p_class = 1.0 if self.AnonG.has_edge(u_anon, v_anon) and any(
                        d.get('subtype') == 'classmate' for d in self.AnonG[u_anon][v_anon].values()
                    ) else 0.0
                    p_group = 1.0 if self.AnonG.has_edge(u_anon, v_anon) and any(
                        d.get('subtype') == 'groupmate' for d in self.AnonG[u_anon][v_anon].values()
                    ) else 0.0
                else:
                    # Caso Cluster: Stima tramite densità (globale o cluster-based come riportato nel aper)
                    p_class = self._get_cluster_density(self.node_to_cluster[u], self.node_to_cluster[v], 'classmate')
                    p_group = self._get_cluster_density(self.node_to_cluster[u], self.node_to_cluster[v], 'groupmate')
                
                prob = self._noisy_or(p_class, p_group)
            else:
                prob = self._noisy_or(0.0, 0.0) # Caso di nodi isolati/mancanti

            predictions.append((prob, is_friend_real))
        return predictions

    def evaluate(self, predictions, threshold=0.5):
        #valutazione precision e recall per creazione grafici come quelli del paper
        y_true = [p[1] for p in predictions]
        y_scores = [p[0] for p in predictions]
        y_pred = [1 if s >= threshold else 0 for s in y_scores]
        
        prec = precision_score(y_true, y_pred, zero_division=0)
        rec = recall_score(y_true, y_pred, zero_division=0)
        tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 1 and yp == 1)
        
        return prec, rec, 0.0, tp