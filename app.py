import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="BAR PAGANO - Cassa", page_icon="💰", layout="wide")

DB_FILE = "ordini_bar_pagano.csv"

MENU = {
    "Cornetto al cioccolato": 1.50,
    "Cornetto a crema": 1.50,
    "Cornetto a miele": 1.50,
    "Treccia miele e noci": 1.80,
    "Polacca": 2.00,
    "Graffa": 1.20,
    "Monachina": 1.80,
    "Pandistelle": 1.00,
    "Flauto": 1.00
}

TAVOLI = [str(i) for i in range(1, 21)]

# --- FUNZIONI DATABASE ---
def carica_ordini():
    if not os.path.exists(DB_FILE):
        return []
    try:
        df = pd.read_csv(DB_FILE)
        if df.empty:
            return []
        # Convertiamo tutto in una lista di dizionari e forziamo 'tavolo' come stringa
        lista = df.to_dict('records')
        for d in lista:
            d['tavolo'] = str(d['tavolo'])
        return lista
    except:
        return []

def salva_ordini(lista_ordini):
    if not lista_ordini:
        # Se la lista è vuota, creiamo un file con solo le intestazioni per resettarlo
        df = pd.DataFrame(columns=["tavolo", "prodotto", "prezzo", "nota", "orario"])
    else:
        df = pd.DataFrame(lista_ordini)
    df.to_csv(DB_FILE, index=False)

# Caricamento iniziale
if 'ordini' not in st.session_state:
    st.session_state.ordini = carica_ordini()

# Navigazione
query_params = st.query_params
ruolo = query_params.get("ruolo", "tavolo")

# --- INTERFACCIA BANCONE / CASSA ---
if ruolo == "banco":
    st.title("🖥️ BANCONE & CASSA - BAR PAGANO")
    
    # Ricarichiamo gli ordini dal file per essere sicuri di vedere gli ultimi arrivati
    st.session_state.ordini = carica_ordini()

    if not st.session_state.ordini:
        st.info("Nessun ordine attivo al momento.")
        if st.button("🔄 Controlla nuovi ordini"):
            st.rerun()
    else:
        df_ordini = pd.DataFrame(st.session_state.ordini)
        # Assicuriamoci che il tavolo sia letto come stringa
        df_ordini['tavolo'] = df_ordini['tavolo'].astype(str)
        
        # Lista dei tavoli che hanno ordini
        lista_tavoli_attivi = df_ordini['tavolo'].unique()

        st.subheader("🧾 Conti aperti per tavolo")
        
        cols = st.columns(2) # Due colonne di tavoli
        for idx, num_tavolo in enumerate(lista_tavoli_attivi):
            with cols[idx % 2]:
                with st.container(border=True):
                    # Filtriamo i prodotti di questo tavolo
                    prodotti_tavolo = df_ordini[df_ordini['tavolo'] == num_tavolo]
                    totale_tavolo = prodotti_tavolo['prezzo'].sum()
                    
                    st.error(f"🪑 TAVOLO {num_tavolo}")
                    
                    # ELENCO DETTAGLIATO (Sempre visibile)
                    st.write("**Dettaglio prodotti:**")
                    for _, row in prodotti_tavolo.iterrows():
                        nota_testo = f" ({row['nota']})" if str(row['nota']) != 'nan' and row['nota'] else ""
                        st.write(f"- {row['prodotto']}{nota_testo}: **€{row['prezzo']:.2f}**")
                    
                    st.markdown(f"### TOTALE: € {totale_tavolo:.2f}")
                    
                    # TASTO PAGATO / RESET
                    if st.button(f"CHIUDI CONTO T{num_tavolo}", key=f"btn_{num_tavolo}", type="primary", use_container_width=True):
                        # RIMUOVIAMO TUTTI GLI ORDINI DI QUESTO TAVOLO
                        nuova_lista = [o for o in st.session_state.ordini if str(o['tavolo']) != str(num_tavolo)]
                        st.session_state.ordini = nuova_lista
                        salva_ordini(nuova_lista)
                        st.success(f"Tavolo {num_tavolo} resettato!")
                        time.sleep(1)
                        st.rerun()
    
    # Auto-aggiornamento ogni 20 secondi
    time.sleep(20)
    st.rerun()

# --- INTERFACCIA CLIENTE ---
else:
    st.title("☕ BAR PAGANO - ORDINA")
    
    tavolo = st.selectbox("Il tuo Tavolo", TAVOLI)
    prodotto = st.selectbox("Cosa desideri?", list(MENU.keys()))
    prezzo = MENU[prodotto]
    
    st.markdown(f"## Prezzo: € {prezzo:.2f}")
    nota = st.text_input("Note (es: macchiato freddo, tazza grande...)")
    
    if st.button("INVIA ORDINE", use_container_width=True, type="primary"):
        nuovo = {
            "tavolo": str(tavolo),
            "prodotto": prodotto,
            "prezzo": prezzo,
            "nota": nota,
            "orario": datetime.now().strftime("%H:%M")
        }
        # Carica quelli esistenti, aggiungi il nuovo e salva
        correnti = carica_ordini()
        correnti.append(nuovo)
        salva_ordini(correnti)
        st.session_state.ordini = correnti
        
        st.success(f"Ordine inviato con successo al bancone!")
        st.balloons()
