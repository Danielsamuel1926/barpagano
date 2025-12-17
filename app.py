import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="BAR PAGANO", page_icon="💰", layout="wide")

DB_FILE = "ordini_bar_pagano.csv"

# --- LISTINO PREZZI ---
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
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            if df.empty: return []
            return df.to_dict('records')
        except: return []
    return []

def salva_ordini(ordini):
    df = pd.DataFrame(ordini) if ordini else pd.DataFrame(columns=["tavolo", "prodotto", "prezzo", "nota", "orario"])
    df.to_csv(DB_FILE, index=False)

# Inizializzazione dati
if 'ordini' not in st.session_state:
    st.session_state.ordini = carica_ordini()

# --- NAVIGAZIONE ---
query_params = st.query_params
ruolo = query_params.get("ruolo", "tavolo")

# --- INTERFACCIA BANCONE / CASSA ---
if ruolo == "banco":
    st.title("🖥️ GESTIONE CASSA E TAVOLI - BAR PAGANO")
    
    if not st.session_state.ordini:
        st.info("Nessun ordine attivo.")
    else:
        # Trasformiamo in DataFrame per fare i calcoli facilmente
        df_ordini = pd.DataFrame(st.session_state.ordini)
        
        # 1. VISUALIZZAZIONE PER TAVOLO (IL CONTO)
        st.header("🧾 Conti Tavoli")
        conti = df_ordini.groupby("tavolo")["prezzo"].sum().reset_index()
        
        col_conti = st.columns(3) # Dividiamo in 3 colonne per risparmiare spazio
        for index, row in conti.iterrows():
            with col_conti[index % 3]:
                with st.container(border=True):
                    st.error(f"TAVOLO {row['tavolo']}")
                    st.subheader(f"Totale: € {row['prezzo']:.2f}")
                    if st.button(f"CHIUDI CONTO T{row['tavolo']}", key=f"chiudi_{row['tavolo']}"):
                        # Rimuoviamo tutti gli ordini di quel tavolo
                        st.session_state.ordini = [o for o in st.session_state.ordini if str(o['tavolo']) != str(row['tavolo'])]
                        salva_ordini(st.session_state.ordini)
                        st.success(f"Conto Tavolo {row['tavolo']} pagato!")
                        time.sleep(1)
                        st.rerun()

        st.divider()

        # 2. LISTA SINGOLI ORDINI (PER PREPARAZIONE)
        st.header("📋 Dettaglio Comande")
        for i, ordine in enumerate(st.session_state.ordini):
            with st.expander(f"T{ordine['tavolo']} - {ordine['prodotto']} ({ordine['orario']})"):
                st.write(f"**Nota:** {ordine['nota'] if ordine['nota'] else 'Nessuna'}")
                st.write(f"**Prezzo:** € {ordine['prezzo']:.2f}")
                if st.button("Rimuovi solo questo prodotto", key=f"del_{i}"):
                    st.session_state.ordini.pop(i)
                    salva_ordini(st.session_state.ordini)
                    st.rerun()

    # Auto-refresh
    time.sleep(15)
    st.rerun()

# --- INTERFACCIA CLIENTE ---
else:
    st.title("☕ BAR PAGANO")
    st.subheader("Ordina dal tuo tavolo")

    # RIMOSSO IL FORM PER PERMETTERE L'AGGIORNAMENTO DINAMICO DEL PREZZO
    tavolo_scelto = st.selectbox("Seleziona il tuo Tavolo", TAVOLI)
    prodotto_scelto = st.selectbox("Cosa desideri?", list(MENU.keys()))
    
    # Adesso il prezzo cambia istantaneamente quando cambi prodotto!
    prezzo_corrente = MENU[prodotto_scelto]
    st.markdown(f"### Prezzo: € {prezzo_corrente:.2f}")
    
    nota = st.text_input("Note (es: macchiato freddo, tazza grande...)")
    
    if st.button("INVIA ORDINE AL BANCONE", use_container_width=True, type="primary"):
        nuovo = {
            "tavolo": tavolo_scelto,
            "prodotto": prodotto_scelto,
            "prezzo": prezzo_corrente,
            "nota": nota,
            "orario": datetime.now().strftime("%H:%M")
        }
        ordini_attuali = carica_ordini()
        ordini_attuali.append(nuovo)
        salva_ordini(ordini_attuali)
        st.session_state.ordini = ordini_attuali
        st.success(f"Ordine inviato! Totale attuale per il tavolo: € {prezzo_corrente:.2f}")
        st.balloons()
