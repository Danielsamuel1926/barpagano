import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="CASSA BAR PAGANO", page_icon="💰", layout="wide")

DB_FILE = "ordini_bar_pagano.csv"

# --- LISTINO PREZZI FISSO ---
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

# --- FUNZIONI PER IL DATABASE (CSV) ---
def carica_ordini():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            if df.empty: return []
            return df.to_dict('records')
        except: return []
    return []

def salva_ordini(ordini):
    # Se la lista è vuota, salviamo un file con solo le intestazioni
    df = pd.DataFrame(ordini) if ordini else pd.DataFrame(columns=["tavolo", "prodotto", "prezzo", "nota", "orario"])
    df.to_csv(DB_FILE, index=False)

# Inizializzazione dello stato degli ordini
if 'ordini' not in st.session_state:
    st.session_state.ordini = carica_ordini()

# --- GESTIONE RUOLI TRAMITE URL ---
query_params = st.query_params
ruolo = query_params.get("ruolo", "tavolo")

# --- 1. INTERFACCIA BANCONE E CASSA ---
if ruolo == "banco":
    st.title("🖥️ PANNELLO CASSA - BAR PAGANO")
    st.write("Qui puoi vedere i conti totali per ogni tavolo e resettarli dopo il pagamento.")

    if not st.session_state.ordini:
        st.info("Nessun tavolo ha ordini aperti al momento.")
    else:
        # Convertiamo in DataFrame per calcolare i totali per tavolo
        df_ordini = pd.DataFrame(st.session_state.ordini)
        
        # Raggruppiamo per tavolo e sommiamo i prezzi
        conti_per_tavolo = df_ordini.groupby("tavolo")["prezzo"].sum().reset_index()

        st.subheader("💰 Conti da Incassare")
        
        # Creiamo una griglia per i tavoli
        col_tavoli = st.columns(3)
        for i, row in conti_per_tavolo.iterrows():
            numero_tavolo = str(row['tavolo'])
            totale_tavolo = row['prezzo']
            
            with col_tavoli[i % 3]:
                with st.container(border=True):
                    st.markdown(f"### 🪑 Tavolo {numero_tavolo}")
                    st.markdown(f"## **€ {totale_tavolo:.2f}**")
                    
                    # DETTAGLIO PRODOTTI PER IL BARISTA
                    prodotti_tavolo = df_ordini[df_ordini['tavolo'].astype(str) == numero_tavolo]
                    with st.expander("Vedi dettaglio prodotti"):
                        for _, p in prodotti_tavolo.iterrows():
                            st.write(f"- {p['prodotto']} (€{p['prezzo']:.2f})")
                            if str(p['nota']) != 'nan' and p['nota']:
                                st.caption(f"  Note: {p['nota']}")

                    # TASTO RESET (CHIUDI CONTO)
                    if st.button(f"PAGATO E RESET T{numero_tavolo}", key=f"reset_{numero_tavolo}", type="primary"):
                        # LOGICA RESET: Teniamo tutti gli ordini TRANNE quelli di questo tavolo
                        st.session_state.ordini = [o for o in st.session_state.ordini if str(o['tavolo']) != numero_tavolo]
                        salva_ordini(st.session_state.ordini)
                        st.success(f"Tavolo {numero_tavolo} resettato!")
                        time.sleep(1)
                        st.rerun()

    # Aggiornamento automatico ogni 15 secondi per vedere nuovi ordini
    time.sleep(15)
    st.rerun()

# --- 2. INTERFACCIA CLIENTE (IL MENU) ---
else:
    st.title("☕ BAR PAGANO")
    st.subheader("Benvenuto! Ordina qui i tuoi prodotti:")

    # Selezione tavolo e prodotto (Aggiornamento istantaneo)
    tavolo_selezionato = st.selectbox("Seleziona il tuo Tavolo", TAVOLI)
    prodotto_selezionato = st.selectbox("Cosa desideri ordinare?", list(MENU.keys()))
    
    # Visualizzazione prezzo istantanea
    prezzo_attuale = MENU[prodotto_selezionato]
    st.markdown(f"### Prezzo: **€ {prezzo_attuale:.2f}**")
    
    nota = st.text_input("Aggiungi una nota (es. macchiato caldo, senza zucchero)")

    if st.button("INVIA ORDINE", use_container_width=True, type="primary"):
        # Creazione nuovo ordine
        nuovo_ordine = {
            "tavolo": tavolo_selezionato,
            "prodotto": prodotto_selezionato,
            "prezzo": prezzo_attuale,
            "nota": nota,
            "orario": datetime.now().strftime("%H:%M")
        }
        
        # Carica, aggiungi e salva
        ordini_correnti = carica_ordini()
        ordini_correnti.append(nuovo_ordine)
        salva_ordini(ordini_correnti)
        st.session_state.ordini = ordini_correnti
        
        st.success(f"Ordine inviato! Aggiunto €{prezzo_attuale:.2f} al conto del Tavolo {tavolo_selezionato}.")
        st.balloons()
