import json
import random
import itertools
import os

def trasformazione_paper_probabilistica(input_file, output_file, mode="10", num_courses_per_student=2):
    #base numeri paper
    CORSI_10 = ["Basi di Data", "Seti", "ALAN", "IP", "ICDD", "ADC", "ASD", "Calculus", "TDI", "SAW"]
    GRUPPI_10 = ["GruppoA", "GruppoB", "GruppoC", "GruppoD", "GruppoE", "GruppoF", "GruppoG", "GruppoH", "GruppoI", "GruppoJ"]

    #Lista da 30 Corsi
    CORSI_30 = CORSI_10 + ["AI", "Machine Learning", "Cybersecurity", "VCC", "Sistemi Operativi", 
                           "Calculus 2", "SSDM", "FCG", "Distr Comp", "DPP",
                           "ALI", "IoT", "Mobile Dev", "Game Dev", "Quantum Computing",
                           "Data Mining", "Big Data", "VR/AR", "Software Eng", "Fis"]
    #Lista da 30 Gruppi
    GRUPPI_30 = GRUPPI_10 + ["GruppoK", "GruppoL", "GruppoM", "GruppoN", "GruppoO", "GruppoP", "GruppoQ", "GruppoR", "GruppoS", "GruppoT",
                             "GruppoU", "GruppoV", "GruppoW", "GruppoX", "GruppoY", "GruppoZ", "GruppoAA", "GruppoBB", "GruppoCC", "GruppoDD"]

    #switch modalità per numero di corsi e gruppi (densità grafo)
    if mode == "30":
        LISTA_CORSI, LISTA_GRUPPI = CORSI_30, GRUPPI_30
    else:
        LISTA_CORSI, LISTA_GRUPPI = CORSI_10, GRUPPI_10

    print(f"--- [Transformer] Esecuzione modo: {mode} ({len(LISTA_CORSI)} Corsi, {len(LISTA_GRUPPI)} Gruppi) ---")

    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    #constraint per dimensioni classi e gruppi (paper)
    MAX_CLASS_SIZE = 25
    MAX_GROUP_SIZE = 15
    
    # Probabilità Noisy-OR originali
    P_FRIEND_RANDOM = 0.2
    P_FRIEND_GIVEN_GROUP = 0.6
    P_FRIEND_GIVEN_CLASS = 0.4 

    class_counts = {c: 0 for c in LISTA_CORSI}
    group_counts = {g: 0 for g in LISTA_GRUPPI}
    processed_students = {}
    
    random.seed(17) 
    random.shuffle(data)

    for entry in data:
        cognome = entry.get('cognome', '').strip()
        if not cognome: continue

        # Assegnazione Gruppi a riempimento
        available_groups = [g for g, c in group_counts.items() if c < MAX_GROUP_SIZE]
        grp = random.choice(available_groups) if available_groups else random.choice(LISTA_GRUPPI)
        group_counts[grp] += 1

        # Assegnazione Corsi a riempimento
        my_courses = []
        for _ in range(num_courses_per_student):
            available_classes = [c for c, count in class_counts.items() 
                                 if count < MAX_CLASS_SIZE and c not in my_courses]
            if available_classes:
                crs = random.choice(available_classes)
                class_counts[crs] += 1
                my_courses.append(crs)
            else:
                my_courses.append(random.choice(LISTA_CORSI))
        
        processed_students[cognome] = {
            "id": cognome, "group": grp, "courses": my_courses
        }

    # Generazione Amicizie con modello paper Noisy-OR
    student_ids = list(processed_students.keys())
    all_friendships = set()
    for u, v in itertools.combinations(student_ids, 2):
        u_d, v_d = processed_students[u], processed_students[v]
        prob_not = (1.0 - P_FRIEND_RANDOM)

        if u_d['group'] == v_d['group']:
            prob_not *= (1.0 - P_FRIEND_GIVEN_GROUP)
        common = set(u_d['courses']).intersection(v_d['courses'])

        for _ in range(len(common)):
            prob_not *= (1.0 - P_FRIEND_GIVEN_CLASS)
        
        if random.random() < (1.0 - prob_not):
            all_friendships.add(tuple(sorted((u, v))))

    # Preparazione JSON finale (da cui creiamo il grafo base)
    adjacency = {sid: [] for sid in student_ids}
    for u, v in all_friendships:
        adjacency[u].append(v); adjacency[v].append(u)
        
    final_data = [{"id": sid, "research_group": processed_students[sid]["group"], 
                   "courses": processed_students[sid]["courses"], "friends": adjacency[sid]} 
                  for sid in student_ids]

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, indent=4)
    print(f" -> Salvato: {output_file}")

if __name__ == "__main__":
    trasformazione_paper_probabilistica("data/studenti.json", "data/studenti_paper_noiseOR.json", mode="10")