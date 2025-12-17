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
    div[data-testid="column"] button {
        aspect-ratio: 1 / 1 !important;
        width: 100% !important;
        font-weight: bold !important;
        font-size: 20px !important;
    }
    .product-text { font-size: 24px !important; font-weight: bold; margin-bottom: 0px; }
    .price-text { font-size: 18px !important; font-weight: normal; opacity: 0.9; }
    .note-text { font-size: 18px !important; font-style: italic; opacity: 0.8; color: #ff4b4b; }
    .stock-text { font-size: 14px; color: #666; }
    .stButton>button { border-radius: 10px; }
    .cart-item { 
        background-color: rgba(255, 75, 75, 0.1); 
        padding: 10px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #FF4B4B;
    }
    </style>
    """, unsafe_allow_html=True)

DB_FILE = "ordini_bar_pagano.csv"
STOCK_FILE = "stock_bar_pagano.csv"

# --- LISTINO FISSO ---
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

# --- FUNZIONI STOCK (DISPONIBILITÀ) ---
def inizializza_stock():
    if not os.path.exists(STOCK_FILE):
        data = []
        for cat, prods in MENU_DATA.items():
            for nome in prods:
                data.append({"prodotto": nome, "quantita": 50}) # Default 50 pezzi
        pd.DataFrame(data).to_csv(STOCK_FILE, index=False)

def carica_stock():
    inizializza_stock()
    df = pd.read_csv(STOCK_FILE)
    return df.set_index('prodotto')['quantita'].to_dict()

def aggiorna_stock(nome_prodotto, variazione):
    stock = carica_stock()
    if nome_prodotto in stock:
        stock[nome_prodotto] = max(0, stock[nome_prodotto] + variazione)
        df = pd.DataFrame(list(stock.items()), columns=['prodotto', 'quantita'])
        df.to_csv(STOCK_FILE, index=False)

# --- FUNZIONI ORDINI ---
def carica_ordini():
    if not os.path.exists(DB_FILE): return []
    try:
        df = pd.read_csv(DB_FILE)
        return df.to_dict('records') if not df.empty else []
    except: return []

def salva_lista_ordini(lista):
    df = pd.DataFrame(lista) if lista else pd.DataFrame(columns=["tavolo", "prodotto", "prezzo", "nota", "orario"])
    df.to_csv(DB_FILE, index=False)

# --- ANIMAZIONE ---
def animazione_caffe():
    st.components.v1.html("""
        <div id="coffee-rain" style="position:fixed; top:0; left:0; width:100vw; height:100vh; pointer-events:none; z-index:9999;"></div>
        <script>
        const container = document.getElementById('coffee-rain');
        const emojis = ['☕', '🍵', '🍩'];
        for (let i = 0; i < 30; i++) {
            const el = document.createElement('div');
            el.innerHTML = emojis[Math.floor(Math.random() * emojis.length)];
            el.style.position = 'fixed'; el.style.bottom = '-50px';
            el.style.left = Math.random() * 100 + 'vw';
            el.style.fontSize = (Math.random() * 20 + 20) + 'px';
            el.style.transition = 'transform ' + (Math.random() * 2 + 2) + 's linear, opacity 2s';
            container.appendChild(el);
            setTimeout(() => {
                el.style.transform = 'translateY(-110vh) rotate(360deg)';
                el.style.opacity = '0';
            }, 100);
        }
        </script>
    """, height=0)

# Inizializzazione Sessione
if 'carrello' not in st.session_state: st.session_state.carrello = []
if 'tavolo_scelto' not in st.session_state: st.session_state.tavolo_scelto = None
if 'categoria_scelta' not in st.session_state: st.session_state.categoria_scelta = "Brioche e Cornetti"
if 'mostra_animazione' not in st.session_state: st.session_state.mostra_animazione = False

query_params = st.query_params
ruolo = query_params.get("ruolo", "tavolo")

# --- INTERFACCIA BANCONE ---
if ruolo == "banco":
    st.title("🖥️ GESTIONE BANCONE")
    
    tab1, tab2 = st.tabs(["Ordini Attivi", "Gestione Disponibilità (Sottoscorta)"])
    
    with tab1:
        ordini = carica_ordini()
        if not ordini: st.info("Nessun ordine.")
        else:
            df_o = pd.DataFrame(ordini)
            tavoli = sorted(df_o['tavolo'].unique())
            cols = st.columns(4)
            for idx, t in enumerate(tavoli):
                with cols[idx % 4]:
                    with st.container(border=True):
                        st.subheader(f"🪑 Tavolo {t}")
                        p_t = df_o[df_o['tavolo'] == t]
                        for _, r in p_t.iterrows():
                            st.write(f"• {r['prodotto']} (€{r['prezzo']:.2f})")
                        st.divider()
                        st.write(f"**Totale: €{p_t['prezzo'].sum():.2f}**")
                        if st.button(f"CHIUDI T{t}", key=f"c_{t}"):
                            salva_lista_ordini([o for o in ordini if str(o['tavolo']) != str(t)])
                            st.rerun()
                            
    with tab2:
        st.write("### Imposta quantità disponibili")
        attual_stock = carica_stock()
        for p_nome, qta in attual_stock.items():
            col_p, col_q = st.columns([3, 1])
            new_q = col_q.number_input(f"{p_nome}", value=int(qta), min_value=0, key=f"stk_{p_nome}")
            if new_q != qta:
                aggiorna_stock(p_nome, new_q - qta)
                st.rerun()

# --- INTERFACCIA CLIENTE ---
else:
    if st.session_state.mostra_animazione:
        animazione_caffe()
        st.session_state.mostra_animazione = False

    st.title("☕ BAR PAGANO")
    
    # 1. TAVOLO
    st.write("### 1. Il tuo Tavolo:")
    t_cols = st.columns(5)
    for i in range(1, 21):
        with t_cols[(i-1)%5]:
            if st.button(f"{i}", key=f"t_{i}", type="primary" if st.session_state.tavolo_scelto==str(i) else "secondary"):
                st.session_state.tavolo_scelto = str(i)
                st.rerun()

    if st.session_state.tavolo_scelto:
        st.divider()
        col_menu, col_cart = st.columns([2, 1])
        disponibilita = carica_stock()
        
        with col_menu:
            st.write("### 2. Scegli cosa ordinare:")
            cat_cols = st.columns(3)
            for i, c in enumerate(MENU_DATA.keys()):
                if cat_cols[i].button(c, type="primary" if st.session_state.categoria_scelta==c else "secondary"):
                    st.session_state.categoria_scelta = c
                    st.rerun()
            
            p_cols = st.columns(2)
            prodotti = MENU_DATA[st.session_state.categoria_scelta]
            for idx, (nome, prezzo) in enumerate(prodotti.items()):
                qta_residua = disponibilita.get(nome, 0)
                disabilitato = qta_residua <= 0
                label = f"➕ {nome}\n€{prezzo:.2f}" if not disabilitato else f"❌ {nome}\nESAURITO"
                
                with p_cols[idx % 2]:
                    if st.button(label, key=f"p_{idx}", disabled=disabilitato, use_container_width=True):
                        st.session_state.carrello.append({"prodotto": nome, "prezzo": prezzo, "tavolo": st.session_state.tavolo_scelto})
                        st.rerun()
                    st.markdown(f"<p class='stock-text'>Disponibili: {qta_residua}</p>", unsafe_allow_html=True)

        with col_cart:
            st.write("### 🛒 Carrello")
            tot = 0
            for i, item in enumerate(st.session_state.carrello):
                c1, c2 = st.columns([4, 1])
                c1.markdown(f"<div class='cart-item'>{item['prodotto']}</div>", unsafe_allow_html=True)
                if c2.button("❌", key=f"del_{i}"):
                    st.session_state.carrello.pop(i)
                    st.rerun()
                tot += item['prezzo']
            
            st.write(f"## Totale: €{tot:.2f}")
            nota = st.text_input("Note")
            if st.button("🚀 INVIA", type="primary", use_container_width=True) and st.session_state.carrello:
                esistenti = carica_ordini()
                for item in st.session_state.carrello:
                    item['nota'] = nota
                    item['orario'] = datetime.now().strftime("%H:%M")
                    esistenti.append(item)
                    aggiorna_stock(item['prodotto'], -1) # SOTTRAE 1 DALLO STOCK
                salva_lista_ordini(esistenti)
                st.session_state.carrello = []
                st.session_state.mostra_animazione = True
                st.rerun()
