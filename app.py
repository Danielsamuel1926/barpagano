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
    [data-testid="column"] {
        flex: 1 1 calc(20% - 10px) !important;
        min-width: 60px !important;
    }
    div[data-testid="column"] button {
        aspect-ratio: 1 / 1 !important;
        width: 100% !important;
        font-weight: bold !important;
        font-size: 22px !important;
        margin-bottom: 8px !important;
    }
    .product-text { font-size: 22px !important; font-weight: bold; }
    .stButton>button { border-radius: 12px; }
    .cart-item { 
        background-color: rgba(255, 75, 75, 0.1); 
        padding: 8px; border-radius: 8px; margin-bottom: 5px; border-left: 4px solid #FF4B4B;
    }
    </style>
    """, unsafe_allow_html=True)

DB_FILE = "ordini_bar_pagano.csv"
STOCK_FILE = "stock_bar_pagano.csv"
COLONNE = ["tavolo", "prodotto", "prezzo", "nota", "orario"]

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

# --- FUNZIONI DI GESTIONE FILE (RIPARATE) ---
def carica_ordini():
    if not os.path.exists(DB_FILE):
        pd.DataFrame(columns=COLONNE).to_csv(DB_FILE, index=False)
        return []
    try:
        df = pd.read_csv(DB_FILE)
        return df.to_dict('records')
    except pd.errors.EmptyDataError:
        # Se il file è vuoto, lo rigeneriamo con le colonne
        pd.DataFrame(columns=COLONNE).to_csv(DB_FILE, index=False)
        return []

def salva_ordini(lista_ordini):
    df = pd.DataFrame(lista_ordini) if lista_ordini else pd.DataFrame(columns=COLONNE)
    df.to_csv(DB_FILE, index=False)

def carica_stock():
    if not os.path.exists(STOCK_FILE):
        data = [{"prodotto": n, "quantita": 100} for c in MENU_DATA for n in MENU_DATA[c]]
        pd.DataFrame(data).to_csv(STOCK_FILE, index=False)
    try:
        return pd.read_csv(STOCK_FILE).set_index('prodotto')['quantita'].to_dict()
    except:
        return {n: 100 for c in MENU_DATA for n in MENU_DATA[c]}

def aggiorna_stock(nome, var):
    s = carica_stock()
    if nome in s:
        s[nome] = max(0, s[nome] + var)
        pd.DataFrame(list(s.items()), columns=['prodotto', 'quantita']).to_csv(STOCK_FILE, index=False)

# --- ANIMAZIONE ---
def animazione_caffe():
    st.components.v1.html("""
        <div id="coffee-rain" style="position:fixed; top:0; left:0; width:100vw; height:100vh; pointer-events:none; z-index:9999;"></div>
        <script>
        const container = document.getElementById('coffee-rain');
        const emojis = ['☕', '🍵', '🥐'];
        for (let i = 0; i < 30; i++) {
            const el = document.createElement('div');
            el.innerHTML = emojis[Math.floor(Math.random() * emojis.length)];
            el.style.position = 'fixed'; el.style.bottom = '-50px';
            el.style.left = Math.random() * 100 + 'vw';
            el.style.fontSize = (Math.random() * 20 + 25) + 'px';
            el.style.transition = 'transform ' + (Math.random() * 2 + 1.5) + 's linear, opacity 1.5s';
            container.appendChild(el);
            setTimeout(() => {
                el.style.transform = 'translateY(-115vh) rotate(360deg)';
                el.style.opacity = '0';
            }, 100);
        }
        </script>
    """, height=0)

# Session State
if 'carrello' not in st.session_state: st.session_state.carrello = []
if 'tavolo_scelto' not in st.session_state: st.session_state.tavolo_scelto = None
if 'categoria_scelta' not in st.session_state: st.session_state.categoria_scelta = "Brioche e Cornetti"
if 'mostra_animazione' not in st.session_state: st.session_state.mostra_animazione = False

ruolo = st.query_params.get("ruolo", "tavolo")

# --- BANCONE ---
if ruolo == "banco":
    st.title("🖥️ BANCONE")
    ordini = carica_ordini()
    if not ordini:
        st.info("In attesa di ordini...")
    else:
        df_o = pd.DataFrame(ordini)
        tavoli = sorted(df_o['tavolo'].unique(), key=lambda x: int(x) if str(x).isdigit() else 0)
        cols = st.columns(4)
        for idx, t in enumerate(tavoli):
            with cols[idx % 4]:
                with st.container(border=True):
                    st.subheader(f"🪑 Tavolo {t}")
                    p_t = df_o[df_o['tavolo'] == t]
                    for _, r in p_t.iterrows():
                        st.write(f"• {r['prodotto']} (€{r['prezzo']:.2f})")
                    st.divider()
                    st.write(f"**TOTALE: €{p_t['prezzo'].sum():.2f}**")
                    if st.button(f"CHIUDI CONTO", key=f"c_{t}", type="primary", use_container_width=True):
                        nuovi = [o for o in ordini if str(o['tavolo']) != str(t)]
                        salva_ordini(nuovi)
                        st.rerun()
    time.sleep(15)
    st.rerun()

# --- CLIENTE ---
else:
    if st.session_state.mostra_animazione:
        animazione_caffe()
        st.session_state.mostra_animazione = False

    st.title("☕ BAR PAGANO")
    st.write("### 1. Seleziona il tuo Tavolo:")
    t_cols = st.columns(5)
    for i in range(1, 21):
        t_str = str(i)
        with t_cols[(i-1) % 5]:
            stile = "primary" if st.session_state.tavolo_scelto == t_str else "secondary"
            if st.button(f"{i}", key=f"t_{i}", type=stile):
                st.session_state.tavolo_scelto = t_str
                st.rerun()

    if st.session_state.tavolo_scelto:
        st.divider()
        st.write(f"### 2. Menu Tavolo {st.session_state.tavolo_scelto}")
        c_cols = st.columns(3)
        for i, cat in enumerate(MENU_DATA.keys()):
            if c_cols[i].button(cat, use_container_width=True, type="primary" if st.session_state.categoria_scelta==cat else "secondary"):
                st.session_state.categoria_scelta = cat
                st.rerun()
        
        col_prod, col_cart = st.columns([2, 1])
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

        with col_cart:
            st.write("### 🛒 Carrello")
            if not st.session_state.carrello:
                st.write("Vuoto")
            else:
                totale = 0
                for i, item in enumerate(st.session_state.carrello):
                    col_i, col_d = st.columns([4, 1])
                    col_i.markdown(f"<div class='cart-item'>{item['prodotto']}</div>", unsafe_allow_html=True)
                    if col_d.button("❌", key=f"del_{i}"):
                        st.session_state.carrello.pop(i)
                        st.rerun()
                    totale += item['prezzo']
                
                st.markdown(f"**Totale: € {totale:.2f}**")
                nota = st.text_input("Note (opzionale)")
                if st.button("🚀 INVIA ORDINE", use_container_width=True, type="primary"):
                    esistenti = carica_ordini()
                    for item in st.session_state.carrello:
                        item['nota'] = nota
                        item['orario'] = datetime.now().strftime("%H:%M")
                        esistenti.append(item)
                        aggiorna_stock(item['prodotto'], -1)
                    salva_ordini(esistenti)
                    st.session_state.carrello = []
                    st.session_state.mostra_animazione = True
                    st.rerun()
