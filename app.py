import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="BAR PAGANO", page_icon="☕", layout="wide")

# CSS PERSONALIZZATO
st.markdown("""
    <style>
    [data-testid="column"] { flex: 1 1 calc(25% - 10px) !important; min-width: 70px !important; }
    div[data-testid="column"] button { width: 100% !important; font-weight: bold !important; border-radius: 12px !important; }
    .product-info { font-size: 14px; color: #666; margin-top: -10px; margin-bottom: 10px; text-align: center; }
    .cart-item { background-color: rgba(255, 75, 75, 0.05); padding: 10px; border-radius: 10px; margin-bottom: 5px; border-left: 5px solid #FF4B4B; }
    .selected-tavolo { background-color: #FF4B4B; color: white; padding: 15px; border-radius: 15px; text-align: center; font-size: 24px; font-weight: bold; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

DB_FILE = "ordini_bar_pagano.csv"
STOCK_FILE = "stock_bar_pagano.csv"
COLONNE = ["id_ordine", "tavolo", "prodotto", "prezzo", "nota", "orario"]

# --- LISTINO ---
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
def carica_ordini():
    if not os.path.exists(DB_FILE):
        pd.DataFrame(columns=COLONNE).to_csv(DB_FILE, index=False)
        return []
    try:
        df = pd.read_csv(DB_FILE)
        return df.to_dict('records')
    except:
        return []

def salva_ordini(lista_ordini):
    df = pd.DataFrame(lista_ordini) if lista_ordini else pd.DataFrame(columns=COLONNE)
    df.to_csv(DB_FILE, index=False)

def carica_stock():
    if not os.path.exists(STOCK_FILE):
        data = [{"prodotto": n, "quantita": 100} for c in MENU_DATA for n in MENU_DATA[c]]
        pd.DataFrame(data).to_csv(STOCK_FILE, index=False)
    return pd.read_csv(STOCK_FILE).set_index('prodotto')['quantita'].to_dict()

def aggiorna_stock(nome, var):
    s = carica_stock()
    if nome in s:
        s[nome] = max(0, s[nome] + var)
        pd.DataFrame(list(s.items()), columns=['prodotto', 'quantita']).to_csv(STOCK_FILE, index=False)

# Session State
if 'carrello' not in st.session_state: st.session_state.carrello = []
if 'tavolo_scelto' not in st.session_state: st.session_state.tavolo_scelto = None
if 'categoria_scelta' not in st.session_state: st.session_state.categoria_scelta = "Brioche e Cornetti"
if 'mostra_animazione' not in st.session_state: st.session_state.mostra_animazione = False

ruolo = st.query_params.get("ruolo", "tavolo")

# --- BANCONE ---
if ruolo == "banco":
    st.title("🖥️ GESTIONE BANCONE")
    ordini = carica_ordini()
    if not ordini:
        st.info("Nessun ordine da preparare.")
    else:
        df_o = pd.DataFrame(ordini)
        tavoli_attivi = sorted(df_o['tavolo'].unique(), key=lambda x: int(x) if str(x).isdigit() else 0)
        
        cols = st.columns(3)
        for idx, t in enumerate(tavoli_attivi):
            with cols[idx % 3]:
                with st.container(border=True):
                    st.subheader(f"🪑 Tavolo {t}")
                    p_t = df_o[df_o['tavolo'] == t]
                    
                    for i, r in p_t.iterrows():
                        col_p, col_v = st.columns([3, 1])
                        col_p.write(f"**{r['prodotto']}**\n({r['nota'] if pd.notna(r['nota']) else ''})")
                        # TASTO PER SERVIRE IL SINGOLO PRODOTTO
                        if col_v.button("Fatto ✅", key=f"done_{r['prodotto']}_{i}_{t}"):
                            # Rimuove solo questo specifico prodotto dal CSV
                            nuovi_ordini = [o for j, o in enumerate(ordini) if not (o['tavolo'] == t and j == i)]
                            salva_ordini(nuovi_ordini)
                            st.rerun()
                    
                    st.divider()
                    if st.button(f"CHIUDI CONTO (€{p_t['prezzo'].sum():.2f})", key=f"tot_{t}", type="primary"):
                        salva_ordini([o for o in ordini if str(o['tavolo']) != str(t)])
                        st.rerun()
    time.sleep(10)
    st.rerun()

# --- CLIENTE ---
else:
    st.title("☕ BAR PAGANO")

    if st.session_state.tavolo_scelto is None:
        st.write("### 🪑 Seleziona il tuo tavolo:")
        t_cols = st.columns(4)
        for i in range(1, 21):
            if t_cols[(i-1) % 4].button(f"{i}", key=f"t_{i}", use_container_width=True):
                st.session_state.tavolo_scelto = str(i)
                st.rerun()
    
    else:
        col_tav, col_back = st.columns([3, 1])
        col_tav.markdown(f"<div class='selected-tavolo'>TAVOLO {st.session_state.tavolo_scelto}</div>", unsafe_allow_html=True)
        if col_back.button("🔄 Cambia", use_container_width=True):
            st.session_state.tavolo_scelto = None
            st.rerun()

        st.divider()
        c_cols = st.columns(3)
        for i, cat in enumerate(MENU_DATA.keys()):
            if c_cols[i].button(cat, use_container_width=True, type="primary" if st.session_state.categoria_scelta==cat else "secondary"):
                st.session_state.categoria_scelta = cat
                st.rerun()
        
        col_prod, col_cart = st.columns([1.8, 1.2])
        dispo = carica_stock()
        
        with col_prod:
            p_cols = st.columns(2)
            prods = MENU_DATA[st.session_state.categoria_scelta]
            for idx, (nome, prezzo) in enumerate(prods.items()):
                qta = dispo.get(nome, 0)
                off = qta <= 0
                with p_cols[idx % 2]:
                    label = f"➕ {nome}\n€{prezzo:.2f}" if not off else f"❌ {nome}\nESAURITO"
                    if st.button(label, key=f"p_{idx}", disabled=off, use_container_width=True):
                        st.session_state.carrello.append({"prodotto": nome, "prezzo": prezzo, "tavolo": st.session_state.tavolo_scelto})
                        st.rerun()
                    # VISUALIZZAZIONE QUANTITÀ RESIDUA
                    st.markdown(f"<div class='product-info'>Disponibili: {qta}</div>", unsafe_allow_html=True)

        with col_cart:
            st.write("🛒 **CARRELLO**")
            if not st.session_state.carrello:
                st.info("Vuoto")
            else:
                totale = 0
                for i, item in enumerate(st.session_state.carrello):
                    c_i, c_d = st.columns([4, 1.2])
                    c_i.markdown(f"<div class='cart-item'>{item['prodotto']}</div>", unsafe_allow_html=True)
                    if c_d.button("Canc", key=f"del_{i}"):
                        st.session_state.carrello.pop(i)
                        st.rerun()
                    totale += item['prezzo']
                
                nota = st.text_input("Note")
                if st.button("🚀 INVIA", use_container_width=True, type="primary"):
                    esistenti = carica_ordini()
                    for item in st.session_state.carrello:
                        item['nota'] = nota
                        item['orario'] = datetime.now().strftime("%H:%M")
                        esistenti.append(item)
                        aggiorna_stock(item['prodotto'], -1)
                    salva_ordini(esistenti)
                    st.session_state.carrello = []
                    st.success("Ordine inviato!")
                    time.sleep(1)
                    st.rerun()
