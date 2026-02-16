# --------------------------------------------------#
#                                                   #
#      File creato con l'aiuto di Gemini AI         #
#                                                   #
#---------------------------------------------------#

import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import os

class GraphVisualizer:
    def __init__(self, G):
        self.G = G

    def plot_all_relationships(self, output_dir="output/visualizations"):
        """
        Genera tre immagini separate per il grafo originale:
        1 classi - 2 gruppi - 3 amici
        in 3 grafici diversi (troppo "rumore" altrimenti e diventavano di difficile lettura)
        """
        if self.G.number_of_nodes() == 0:
            return

        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        print(f"--- [Visualizer] Generazione immagini originali in {output_dir} ---")
        
        # Layout fissato per coerenza visiva tra i diversi plot
        pos = nx.spring_layout(self.G, k=0.15, weight='weight', seed=42)

        # Liste per categorizzare gli archi
        edges_friend = []
        edges_group = []
        edges_class = []

        for u, v, key, data in self.G.edges(keys=True, data=True):
            subtype = data.get('subtype')
            if subtype == 'friend': 
                edges_friend.append((u, v))
            elif subtype == 'groupmate': 
                edges_group.append((u, v))
            elif subtype == 'classmate': 
                edges_class.append((u, v))

        #Plot Classi
        self._save_plot(pos, edges_class, 
                        color='#2ecc71', style='dashed', width=1, 
                        label='Classmates (Corsi)', 
                        filename='grafo_classi.png', output_dir=output_dir, curved=True)

        #Plot Gruppi
        self._save_plot(pos, edges_group, 
                        color='#3498db', style='solid', width=1.2, 
                        label='Groupmates (Gruppi)', 
                        filename='grafo_gruppi.png', output_dir=output_dir, curved=True)

        #Plot Amici
        self._save_plot(pos, edges_friend, 
                        color='#e74c3c', style='solid', width=1.5, 
                        label='Friends (Sensitive)', 
                        filename='grafo_amici.png', output_dir=output_dir, curved=False)

    def _save_plot(self, pos, edge_list, color, style, width, label, filename, output_dir, curved=False):
        plt.figure(figsize=(16, 12))
        
        # Disegno dei nodi
        nx.draw_networkx_nodes(self.G, pos, node_size=150, node_color='#e6f2ff', edgecolors='#666666')
        nx.draw_networkx_labels(self.G, pos, font_size=7, font_family='sans-serif')
        
        # Disegno degli archi
        if edge_list:
            if curved:
                nx.draw_networkx_edges(self.G, pos, edgelist=edge_list, edge_color=color, 
                                       style=style, width=width,
                                       connectionstyle='arc3, rad=0.1', arrows=True)
            else:
                nx.draw_networkx_edges(self.G, pos, edgelist=edge_list, edge_color=color, 
                                       style=style, width=width)
        
        # Configurazione Legenda e Titolo
        legend_line = mlines.Line2D([], [], color=color, linestyle=style, linewidth=width, label=label)
        plt.legend(handles=[legend_line], loc='upper right', fontsize=12)
        plt.title(f"Visualizzazione Grafo: {label}", fontsize=16)
        plt.axis('off')
        
        # Salvataggio file
        filepath = os.path.join(output_dir, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"   -> Salvata immagine: {filename}")

 
    def plot_anonymized_graph(self, filename, title, output_dir="output/visualizations"):
        """
        Visualizza il grafo anonimizzato, evidenziando i cluster con colori diversi.
        Supporta sia il formato 'Intact' che quello 'Collapsed' (Cluster).
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        print(f"    -> Generazione PNG: {filename} ...")
        
        plt.figure(figsize=(16, 12))
        pos = nx.spring_layout(self.G, k=0.15, weight='weight', seed=42)

        # 1. Identificazione e raggruppamento dei Cluster per la colorazione
        clusters = set()
        for n, attr in self.G.nodes(data=True):
            c = attr.get('cluster')
            if c: 
                clusters.add(c)
            elif str(n).startswith('C') and '_' not in str(n): 
                clusters.add(n)

        # Ordinamento logico dei cluster (es: C0, C1, C2...)
        unique_clusters = sorted(list(clusters), 
                                 key=lambda x: int(x[1:]) if len(x) > 1 and x[1:].isdigit() else 999)
        
        colormap = plt.cm.get_cmap('tab20', len(unique_clusters) if unique_clusters else 1)
        
        # Disegno dei nodi cluster per cluster
        for i, cluster_label in enumerate(unique_clusters):
            nodelist = [n for n, attr in self.G.nodes(data=True) 
                        if attr.get('cluster') == cluster_label or n == cluster_label]
            if nodelist:
                nx.draw_networkx_nodes(self.G, pos, nodelist=nodelist, 
                                       node_color=[colormap(i)] * len(nodelist),
                                       node_size=150, edgecolors='#333333', label=cluster_label)

        # 2. Categorizzazione degli archi anonimizzati
        edges_class = []
        edges_group = []
        edges_fake = []
        
        for u, v, k, d in self.G.edges(keys=True, data=True):
            if u == v: continue
            subtype = d.get('subtype', '')
            
            if 'fake' in subtype: 
                edges_fake.append((u, v))
            elif 'classmate' in subtype: 
                edges_class.append((u, v))
            elif 'groupmate' in subtype: 
                edges_group.append((u, v))

        # 3. Disegno degli archi con stili specifici
        # Classmates (Verde Tratteggiato)
        if edges_class:
            nx.draw_networkx_edges(self.G, pos, edgelist=edges_class, edge_color='#2ecc71', 
                                   style='dashed', width=1.0, alpha=0.7)
        # Groupmates (Blu Continuo)
        if edges_group:
            nx.draw_networkx_edges(self.G, pos, edgelist=edges_group, edge_color='#3498db', 
                                   style='solid', width=1.2, alpha=0.7)

        nx.draw_networkx_labels(self.G, pos, font_size=6, font_color='#000000')
        
        # Creazione personalizzata della Legenda Archi
        lines = []
        if edges_class: 
            lines.append(mlines.Line2D([], [], color='#2ecc71', linestyle='--', label='Classmates'))
        if edges_group: 
            lines.append(mlines.Line2D([], [], color='#3498db', linestyle='-', label='Groupmates'))
        if edges_fake: 
            lines.append(mlines.Line2D([], [], color='#e74c3c', linestyle=':', linewidth=2, label='Fake/Anonymized'))

        plt.legend(handles=lines, loc='upper right', title="Legenda Archi", fontsize=10)
        plt.title(title, fontsize=16)
        plt.axis('off')

        # Salvataggio finale dell'immagine anonimizzata
        filepath = os.path.join(output_dir, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

if __name__ == "__main__":
    print("[Visualizer] -------------")