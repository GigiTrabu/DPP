#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "=============================================="
echo "   AVVIO PROGETTO PRIVACY EDGES SENSIBILI"
echo "=============================================="

# 1. CLEANING
echo "[0/7] Pulizia dati e immagini precedenti..."
rm -f data/*.gpickle data/*.pickle
rm -f output/*.png
rm -f output/visualizations/*.png
rm -f data/bench_*.json
rm -f data/temp_*.json
rm -f data/*.csv
rm -f data/studenti_paper*.json
python3 -c "import networkx, matplotlib, sklearn, numpy" || pip3 install networkx matplotlib scikit-learn numpy

# 3. Pipeline
echo -e "\n[1/7] Generazione Dati Sintetici (Noisy-OR)..."
python3 data/transform_data_noiseOR.py

echo -e "\n[2/7] Loader (Caching)..."
python3 src/loader.py

echo -e "\n[3/7] Anonimizzazione & Visualizzazione..."
# Genera i grafi standard (k=6) e le immagini visuali
python3 src/anonymizerEdges.py

echo -e "\n[4/7] Simulazione Attacchi (Privacy Attack Fig 7-8)..."
# Analisi della PRIVACY (Precision/Recall)
python3 src/experiment_runner.py

echo -e "\n[5/7] Utility analysis..."
# Analisi dell'UTILITÀ (Clustering/Nodes/Edges)
python3 src/utility_analysis.py

echo -e "\n[6/7] Structural Integrity analysis..."
# Analisi dell'integrità strutturale (Preservation Gain)
python3 src/structural_integrity_analysis.py

echo -e "\n[7/7] Complexity analysis..."
# Analisi della complessità algoritmica (Costi di Difesa vs Attacco)
python3 src/complexity_analysis.py

echo -e "\n[Chech_stats] Verifica statistiche finali..."
python3 src/check_stats.py


echo -e "\n========================================"
echo " ESECUZIONE COMPLETATA CON SUCCESSO"
echo "========================================"