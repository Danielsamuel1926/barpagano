import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="BAR PAGANO", page_icon="☕", layout="wide")

st.markdown("""
    <style>
    [data-testid="column"] { flex: 1 1 calc(25% - 10px) !important; min-width: 70px !important; }
    div[data-testid="column"] button { width: 100% !important; font-weight: bold !important; border-radius: 12px !important; }
    .servito { color: #888888; text-decoration: line-through; opacity: 0.6; }
    .da-servire { color: #000000; font-weight: bold; }
    .product-info { font-size: 13px; color: #666; text-align: center; margin-bottom: 10px; }
    .selected-tavolo { background-color: #FF4B4B; color: white; padding: 15px; border-radius: 15px; text-align: center; font-size: 24px; font-weight: bold; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

DB_FILE = "ordini_bar_pagano.csv"
STOCK_FILE = "stock_bar_pagano.csv"
COLONNE = ["id_univoco", "tavolo", "prodotto", "prezzo", "nota", "orario", "stato"]

MENU_DATA = {
    "Brioche e Cornetti": {"Cornetto cioccolato": 1.50, "Cornetto crema": 1.50, "Cornetto miele": 1.50, "Graffa": 1.20, "Polacca": 2.00},
    "Bevande Calde": {"Caffè": 1.00, "Caffè Macchiato": 1.10, "Cappuccino": 1.50, "Tè caldo": 1.50},
    "Bevande Fredde": {"Acqua 0.5L": 1.00, "Coca Cola": 2.50, "Aranciata": 2.50, "Birra": 3.00}
}

# --- FUNZIONI DATI ---
def carica_ordini():
    if not os.path.exists(DB_FILE):
        pd.DataFrame(columns=COLONNE).to_csv(DB_FILE, index=False)
        return []
    return pd.read_csv(DB_FILE).to_dict('records')

def salva_ordini(lista):
    pd.DataFrame(lista if lista else columns=COLONNE).to_csv(DB_FILE, index=False)

def carica_stock():
    if not os.path.exists(STOCK_FILE):
        data = [{"prodotto": n, "quantita": 100} for c in MENU_DATA for n in MENU_DATA[c]]
        pd.DataFrame(data).to_csv(STOCK_FILE, index=False)
    return pd.read_csv(STOCK_FILE).set_index('prodotto')['quantita'].to_dict()

def aggiorna_stock(nome, nuova_qta):
    df = pd.read_csv(STOCK_FILE)
    df.loc[df['prodotto'] == nome, 'quantita'] = nuova_qta
    df.to_csv(STOCK_FILE, index=False)

# --- LOGICA RUOLI ---
ruolo = st.query_params.get("ruolo", "tavolo")

if ruolo == "banco":
    st.title("🖥️ CONSOLE BANCONE")
    tab1, tab2 = st.tabs(["📋 Ordini Tavoli", "📦 Gestione Stock/Quantità"])
    
    with tab1:
        ordini = carica_ordini()
        if not ordini:
            st.info("Nessun ordine attivo.")
        else:
            df_o = pd.DataFrame(ordini)
            tavoli = sorted(df_o['tavolo'].unique(), key=lambda x: int(x))
            cols = st.columns(3)
            for idx, t in enumerate(tavoli):
                with cols[idx % 3]:
                    with st.container(border=True):
                        st.subheader(f"🪑 Tavolo {t}")
                        p_t = df_o[df_o['tavolo'] == t]
                        for i, r in p_t.iterrows():
                            # Logica Visualizzazione Servito/Non Servito
                            classe = "servito" if r['stato'] == "SI" else "da-servire"
                            col_text, col_btn = st.columns([3, 1])
                            
                            col_text.markdown(f"<span class='{classe}'>{r['prodotto']}</span>", unsafe_allow_html=True)
                            if r['stato'] == "NO":
                                if col_btn.button("Servi", key=f"sv_{t}_{i}"):
                                    ordini[i]['stato'] = "SI"
                                    salva_ordini(ordini)
                                    st.rerun()
                            else:
                                col_btn.write("✅")
                        
                        st.divider()
                        if st.button(f"PAGATO (€{p_t['prezzo'].sum():.2f})", key=f"pay_{t}", type="primary"):
                            salva_ordini([o for o in ordini if str(o['tavolo']) != str(t)])
                            st.rerun()
        time.sleep(10)
        st.rerun()

    with tab2:
        st.write("### Aggiorna Disponibilità Prodotti")
        stk = carica_stock()
        for prod, qta in stk.items():
            c1, c2 = st.columns([3, 1])
            nuova = c2.number_input(f"{prod}", value=int(qta), key=f"edit_{prod}")
            if nuova != qta:
                aggiorna_stock(prod, nuova)
                st.toast(f"Aggiornato {prod}")

else:
    # --- LATO CLIENTE ---
    st.title("☕ BAR PAGANO")
    if st.session_state.get('tavolo_scelto') is None:
        st.write("### Seleziona il tuo tavolo:")
        t_cols = st.columns(4)
        for i in range(1, 21):
            if t_cols[(i-1) % 4].button(f"{i}", key=f"t_{i}"):
                st.session_state.tavolo_scelto = str(i)
                st.rerun()
    else:
        st.markdown(f"<div class='selected-tavolo'>TAVOLO {st.session_state.tavolo_scelto}</div>", unsafe_allow_html=True)
        if st.button("🔄 Cambia Tavolo"):
            st.session_state.tavolo_scelto = None
            st.rerun()

        cat = st.radio("Categoria", list(MENU_DATA.keys()), horizontal=True)
        dispo = carica_stock()
        p_cols = st.columns(2)
        
        for idx, (nome, prezzo) in enumerate(MENU_DATA[cat].items()):
            qta = dispo.get(nome, 0)
            off = qta <= 0
            with p_cols[idx % 2]:
                if st.button(f"➕ {nome}\n€{prezzo:.2f}", disabled=off, key=f"btn_{nome}", use_container_width=True):
                    if 'carrello' not in st.session_state: st.session_state.carrello = []
                    st.session_state.carrello.append({"tavolo": st.session_state.tavolo_scelto, "prodotto": nome, "prezzo": prezzo})
                    st.rerun()
                st.markdown(f"<div class='product-info'>Disponibili: {qta}</div>", unsafe_allow_html=True)

        if st.session_state.get('carrello'):
            with st.sidebar:
                st.write("🛒 **CARRELLO**")
                tot = 0
                for i, item in enumerate(st.session_state.carrello):
                    st.write(f"{item['prodotto']} - €{item['prezzo']:.2f}")
                    tot += item['prezzo']
                nota = st.text_input("Note")
                if st.button("🚀 INVIA ORDINE"):
                    ordini_at = carica_ordini()
                    for item in st.session_state.carrello:
                        item.update({"nota": nota, "orario": datetime.now().strftime("%H:%M"), "stato": "NO", "id_univoco": time.time()})
                        ordini_at.append(item)
                        # Sottrai dallo stock
                        stk_attuale = carica_stock()
                        aggiorna_stock(item['prodotto'], stk_attuale[item['prodotto']] - 1)
                    salva_ordini(ordini_at)
                    st.session_state.carrello = []
                    st.success("Ordine Inviato!")
                    time.sleep(2)
                    st.rerun()
