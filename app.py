import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="BAR PAGANO", page_icon="☕", layout="wide")

# CSS PER TASTI TAVOLI AFFIANCATI E QUADRATI
st.markdown("""
    <style>
    /* Forza i contenitori delle colonne a stare vicini */
    [data-testid="column"] {
        width: calc(20% - 10px) !important;
        flex: 1 1 calc(20% - 10px) !important;
        min-width: 60px !important;
    }
    
    /* Rende i tasti dei tavoli quadrati e grandi */
    div[data-testid="column"] button {
        aspect-ratio: 1 / 1 !important;
        width: 100% !important;
        font-weight: bold !important;
        font-size: 22px !important;
        margin-bottom: 10px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    .product-text { font-size: 22px !important; font-weight: bold; }
    .stButton>button { border-radius: 12px; }
    </style>
    """, unsafe_allow_html=True)

DB_FILE = "ordini_bar_pagano.csv"
STOCK_FILE = "stock_bar_pagano.csv"

# --- LISTINO PRODOTTI ---
MENU_DATA = {
    "Brioche e Cornetti": {
        "Cornetto cioccolato": 1.50, "Cornetto crema": 1.50, "Cornetto miele": 1.50,
        "Treccia noci": 1.80, "Polacca": 2.00, "Graffa": 1.20,
        "Monachina": 1.80, "Pandistelle": 1.00, "Flauto": 1.00
    },
    "Bevande Calde": {
        "Caffè": 1.00, "Caffè Macchiato": 1.10, "Cappuccino": 1.50, 
        "Latte Macchiato": 2.00, "Tè caldo": 1.50, "Cioccolata": 2.50
    },
    "Bevande Fredde": {
        "Acqua 0.5L": 1.00, "Coca Cola": 2.50, "Aranciata": 2.50, 
        "The Limone/Pesca": 2.50, "Succo Frutta": 2.00, "Birra": 3.00
    }
}

# --- FUNZIONI DATABASE ---
def inizializza_stock():
    if not os.path.exists(STOCK_FILE):
        data = [{"prodotto": n, "quantita": 50} for c in MENU_DATA for n in MENU_DATA[c]]
        pd.DataFrame(data).to_csv(STOCK_FILE, index=False)

def carica_stock():
    inizializza_stock()
    return pd.read_csv(STOCK_FILE).set_index('prodotto')['quantita'].to_dict()

def aggiorna_stock(nome, var):
    s = carica_stock()
    if nome in s:
        s[nome] = max(0, s[nome] + var)
        pd.DataFrame(list(s.items()), columns=['prodotto', 'quantita']).to_csv(STOCK_FILE, index=False)

def carica_ordini():
    if not os.path.exists(DB_FILE): return []
    try:
        df = pd.read_csv(DB_FILE)
        return df.to_dict('records') if not df.empty else []
    except: return []

# Inizializzazione Sessione
if 'carrello' not in st.session_state: st.session_state.carrello = []
if 'tavolo_scelto' not in st.session_state: st.session_state.tavolo_scelto = None
if 'categoria_scelta' not in st.session_state: st.session_state.categoria_scelta = "Brioche e Cornetti"

ruolo = st.query_params.get("ruolo", "tavolo")

# --- INTERFACCIA BANCONE ---
if ruolo == "banco":
    st.title("🖥️ BANCONE")
    ordini = carica_ordini()
    if not ordini:
        st.info("Nessun ordine.")
    else:
        df_o = pd.DataFrame(ordini)
        tavoli = sorted(df_o['tavolo'].unique())
        cols = st.columns(4)
        for idx, t in enumerate(tavoli):
            with cols[idx % 4]:
                with st.container(border=True):
                    st.subheader(f"🪑 T{t}")
                    p_t = df_o[df_o['tavolo'] == t]
                    for _, r in p_t.iterrows():
                        st.write(f"• {r['prodotto']} (€{r['prezzo']:.2f})")
                    if st.button(f"CHIUDI", key=f"c_{t}"):
                        nuovi = [o for o in ordini if str(o['tavolo']) != str(t)]
                        pd.DataFrame(nuovi if nuovi else columns=["tavolo", "prodotto", "prezzo", "nota", "orario"]).to_csv(DB_FILE, index=False)
                        st.rerun()
    time.sleep(10)
    st.rerun()

# --- INTERFACCIA CLIENTE ---
else:
    st.title("☕ BAR PAGANO")
    
    # SELEZIONE TAVOLI AFFIANCATI (5 colonne)
    st.write("### 1. Seleziona Tavolo:")
    t_cols = st.columns(5)
    for i in range(1, 21):
        t_str = str(i)
        with t_cols[(i-1) % 5]:
            # Se il tavolo è scelto, il tasto diventa rosso (primary)
            stile = "primary" if st.session_state.tavolo_scelto == t_str else "secondary"
            if st.button(f"{i}", key=f"t_{i}", type=stile):
                st.session_state.tavolo_scelto = t_str
                st.rerun()

    if st.session_state.tavolo_scelto:
        st.divider()
        st.write(f"### 2. Menu Tavolo {st.session_state.tavolo_scelto}")
        
        # Categorie
        c_cols = st.columns(3)
        for i, cat in enumerate(MENU_DATA.keys()):
            if c_cols[i].button(cat, use_container_width=True, type="primary" if st.session_state.categoria_scelta==cat else "secondary"):
                st.session_state.categoria_scelta = cat
                st.rerun()
        
        # Prodotti e Carrello
        col_prod, col_cart = st.columns([2, 1])
        dispo = carica_stock()
        
        with col_prod:
            p_cols = st.columns(2)
            prods = MENU_DATA[st.session_state.categoria_scelta]
            for idx, (nome, prezzo) in enumerate(prods.items()):
                qta = dispo.get(nome, 0)
                off = qta <= 0
                with p_cols[idx % 2]:
                    label = f"➕ {nome}\n€{prezzo:.2f}" if not off else f"❌ {nome}\nFINITO"
                    if st.button(label, key=f"p_{idx}", disabled=off, use_container_width=True):
                        st.session_state.carrello.append({"prodotto": nome, "prezzo": prezzo, "tavolo": st.session_state.tavolo_scelto})
                        st.rerun()

        with col_cart:
            st.write("🛒 Carrello")
            totale = 0
            for i, item in enumerate(st.session_state.carrello):
                st.write(f"{item['prodotto']} €{item['prezzo']:.2f}")
                totale += item['prezzo']
            
            st.write(f"**Tot: €{totale:.2f}**")
            if st.button("🚀 INVIA", use_container_width=True, type="primary") and st.session_state.carrello:
                esistenti = carica_ordini()
                for item in st.session_state.carrello:
                    item['orario'] = datetime.now().strftime("%H:%M")
                    esistenti.append(item)
                    aggiorna_stock(item['prodotto'], -1)
                pd.DataFrame(esistenti).to_csv(DB_FILE, index=False)
                st.session_state.carrello = []
                st.success("Inviato! ☕")
                time.sleep(1)
                st.rerun()
