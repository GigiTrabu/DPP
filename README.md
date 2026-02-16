# Graph Anonymization & Link Re-identification Framework

This project implements and evaluates various privacy-preservation strategies for structured graph data, strictly based on the theoretical principles introduced in the paper: **"Preserving the Privacy of Sensitive Relationships in Graph Data" (Zheleva & Getoor)**.

The framework is designed to counter **link re-identification**—the risk of an adversary inferring sensitive relationships between individuals from anonymized datasets using predictive models based on structural network characteristics.

---

## 📖 Theoretical Foundations (from the Paper)

The software architecture reflects the **Privacy vs. Utility** trade-off analyzed in the paper, operationalizing the data sanitization strategies proposed by the authors:

1.  **Link De-identification**: Masking sensitive relationships by altering the graph structure.
2.  **Adversary Modeling**: We assume the attacker possesses an accurate predictive model based on node attributes and neighborhood density.
3.  **Anonymization Strategies**:
    * **Intact Nodes, Edges Removed**: Pruning sensitive relationships while keeping nodes visible (implemented as our `Baseline` and  `Empty`).
    * **Partial Edge Removal**: Increasing uncertainty by removing non-sensitive edges (implemented as our `Partial` method).
    * **Cluster-based Unconstrained Anonymization**: Grouping nodes into "Super-nodes" to hide individual identities and specific link existence (implemented via `Random` and `Greedy`       clustering) while maintain all the non-sensitive edges.
    * **Cluster-based Constrained Anonymization**: Grouping nodes into "Super-nodes" to hide individual identities and specific link existence (implemented via `Random` and `Greedy`       clustering) while collapsing all the non-sensitive edges between cluster into 1 edge per type.



---

## 📂 Module Architecture & Implementation

### 1. Defense: Anonymization Strategies (`src/`)

* **`anonymizerNodes.py`**: Handles the node partitioning phase.
    * **Greedy Clustering**: Following the paper's observations on **homophily**, this module groups nodes by minimizing attribute distance (Class, Group). This ensures the anonymized graph retains high utility for legitimate social network analysis (personal implementation, not present in the Paper)
    * **Random Clustering**: A control method providing structural *k-anonymity* without optimizing for attribute similarity.
* **`anonymizerEdges.py`**: Manages the edge synthesis and graph transformation.
    * **Baseline & Partial**: Implements the targeted removal of inter-group sensitive edges as defined in the paper’s primary strategies.
    * **`_collapse_graph` (Constrained vs. Unconstrained)**: Generates macro-edges between clusters. The **Constrained** mode is specifically designed to block attacks based on local density "fingerprints" by forcing uniform edge counts.

### 2. Evaluation: Adversary Modeling (`src/`)

* **`attacker.py`**: Operationalizes the adversarial logic. As per Zheleva & Getoor, we model three levels of attack complexity based on the adversary's background knowledge:

    * **Global Density Attack**: A baseline attack where the adversary assumes the probability of a link between two nodes is simply the overall density of the observed graph.
    * **Attribute-based Inference**: An attack that exploits node attributes (Class, Group) and the principle of homophily to predict links, assuming that nodes with similar attributes are more likely to be connected.
    * **Noisy-OR Probabilistic Attack**: The most sophisticated model described in the paper. It uses the **Noisy-OR** gate to combine the evidence from the anonymized cluster-graph. It estimates the probability $P(e_{u,v} = 1)$ by analyzing the density of the macro-edge connecting cluster $C_i$ and $C_j$.



* **`run_attack.py`**: The orchestration script that validates defense efficacy by measuring **Precision**, **Recall**, and **Disclosure Count** across varying probability thresholds ($\tau$). It simulates how an adversary would "threshold" their confidence to decide which links to re-identify.


### 3. Utility & Data Preservation Analysis (`src/`)

Our framework includes a dedicated utility study that mirrors the evaluation metrics reported in the paper, focusing on the impact of sanitization on data quality:

* **`utility_analysis.py`**: This module conducts an **Information Loss Study** directly inspired by the paper's experiments. It quantifies the damage to the dataset caused by the removal of both sensitive and non-sensitive edges. It measures how much "signal" is lost for legitimate data mining tasks when the graph is pruned to protect privacy.
* **`structural_integrity_analysis.py`**: A final structural evaluation focused on the cluster-based methods. It analyzes how the **Greedy** and **Random** implementations affect the global properties of the network. While the Greedy approach aims to preserve the original homophily and degree distribution, this analysis validates the integrity of the transformed "Super-node" graph compared to the original topology.

---


## 🖼️ Project Outputs (`/output`)

All graphical results generated by the analyses are stored in the `/output` directory, organized as follows:

* **Main Folder (`/output`)**: Contains performance benchmarks, computational complexity curves, and attack results (Precision, Recall, Disclosure Count).
* **`visualization/` Subfolder**: Contains visual representations of the reference graph. It includes plots of the graph topology before and after anonymization, visually demonstrating how clustering and edge collapsing affect the network structure.

---

