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
    .servito { color: #888888; text-decoration: line-through; opacity: 0.6; font-style: italic; }
    .da-servire { color: #000000; font-weight: bold; font-size: 18px; }
    .product-info { font-size: 13px; color: #666; text-align: center; margin-bottom: 10px; }
    .selected-tavolo { background-color: #FF4B4B; color: white; padding: 15px; border-radius: 15px; text-align: center; font-size: 24px; font-weight: bold; margin-bottom: 20px; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #f0f2f6; border-radius: 10px; padding: 10px 20px; }
    </style>
    """, unsafe_allow_html=True)

DB_FILE = "ordini_bar_pagano.csv"
STOCK_FILE = "stock_bar_pagano.csv"
COLONNE = ["id_univoco", "tavolo", "prodotto", "prezzo", "nota", "orario", "stato"]

MENU_DATA = {
    "Brioche e Cornetti": {"Cornetto cioccolato": 1.50, "Cornetto crema": 1.50, "Cornetto miele": 1.50, "Graffa": 1.20, "Polacca": 2.00, "Treccia noci": 1.80},
    "Bevande Calde": {"Caffè": 1.00, "Caffè Macchiato": 1.10, "Cappuccino": 1.50, "Tè caldo": 1.50},
    "Bevande Fredde": {"Acqua 0.5L": 1.00, "Coca Cola": 2.50, "Aranciata": 2.50, "Birra": 3.00}
}

# --- FUNZIONI DATI MIGLIORATE ---
def carica_ordini():
    if not os.path.exists(DB_FILE) or os.stat(DB_FILE).st_size == 0:
        pd.DataFrame(columns=COLONNE).to_csv(DB_FILE, index=False)
        return []
    return pd.read_csv(DB_FILE).to_dict('records')

def salva_ordini(lista):
    if not lista:
        df = pd.DataFrame(columns=COLONNE)
    else:
        df = pd.DataFrame(lista)
    df.to_csv(DB_FILE, index=False)

def carica_stock():
    if not os.path.exists(STOCK_FILE):
        data = [{"prodotto": n, "quantita": 100} for c in MENU_DATA for n in MENU_DATA[c]]
        pd.DataFrame(data).to_csv(STOCK_FILE, index=False)
    return pd.read_csv(STOCK_FILE).set_index('prodotto')['quantita'].to_dict()

def aggiorna_stock(nome, nuova_qta):
    df = pd.read_csv(STOCK_FILE)
    df.loc[df['prodotto'] == nome, 'quantita'] = nuova_qta
    df.to_csv(STOCK_FILE, index=False)

# --- LOGICA ---
ruolo = st.query_params.get("ruolo", "tavolo")

if ruolo == "banco":
    st.title("🖥️ CONSOLE BANCONE")
    tab1, tab2 = st.tabs(["📋 ORDINI TAVOLI", "📦 MAGAZZINO / STOCK"])
    
    with tab1:
        ordini = carica_ordini()
        if not ordini:
            st.info("In attesa di nuovi ordini...")
        else:
            df_o = pd.DataFrame(ordini)
            tavoli = sorted(df_o['tavolo'].unique(), key=lambda x: int(x))
            cols = st.columns(3)
            for idx, t in enumerate(tavoli):
                with cols[idx % 3]:
                    with st.container(border=True):
                        st.subheader(f"🪑 Tavolo {t}")
                        # Mostriamo i prodotti di questo tavolo
                        for i, r in enumerate(ordini):
                            if str(r['tavolo']) == str(t):
                                classe = "servito" if r['stato'] == "SI" else "da-servire"
                                col_text, col_btn = st.columns([3, 1])
                                
                                label_prodotto = f"{r['prodotto']} (€{r['prezzo']:.2f})"
                                col_text.markdown(f"<span class='{classe}'>{label_prodotto}</span>", unsafe_allow_html=True)
                                
                                if r['stato'] == "NO":
                                    if col_btn.button("Servi", key=f"sv_{t}_{i}"):
                                        ordini[i]['stato'] = "SI"
                                        salva_ordini(ordini)
                                        st.rerun()
                                else:
                                    col_btn.write("✅")
                        
                        st.divider()
                        tot_tavolo = sum(float(o['prezzo']) for o in ordini if str(o['tavolo']) == str(t))
                        if st.button(f"PAGATO - TOT: €{tot_tavolo:.2f}", key=f"pay_{t}", type="primary"):
                            nuovi_ordini = [o for o in ordini if str(o['tavolo']) != str(t)]
                            salva_ordini(nuovi_ordini)
                            st.rerun()
        time.sleep(10)
        st.rerun()

    with tab2:
        st.write("### 📦 Gestione Disponibilità")
        stk = carica_stock()
        for prod, qta in stk.items():
            c1, c2 = st.columns([3, 1])
            nuova = c2.number_input(f"{prod}", value=int(qta), key=f"stk_{prod}", step=1)
            if nuova != qta:
                aggiorna_stock(prod, nuova)
                st.toast(f"Stock aggiornato: {prod}")

else:
    # --- INTERFACCIA CLIENTE ---
    st.title("☕ BAR PAGANO")
    if st.session_state.get('tavolo_scelto') is None:
        st.write("### 🪑 Per favore, seleziona il tuo tavolo:")
        t_cols = st.columns(4)
        for i in range(1, 21):
            if t_cols[(i-1) % 4].button(f"{i}", key=f"t_{i}", use_container_width=True):
                st.session_state.tavolo_scelto = str(i)
                st.rerun()
    else:
        col_t, col_b = st.columns([3, 1])
        col_t.markdown(f"<div class='selected-tavolo'>TAVOLO {st.session_state.tavolo_scelto}</div>", unsafe_allow_html=True)
        if col_b.button("🔄 Cambia Tavolo"):
            st.session_state.tavolo_scelto = None
            st.rerun()

        st.divider()
        cat_scelta = st.radio("Scegli Categoria", list(MENU_DATA.keys()), horizontal=True)
        
        dispo = carica_stock()
        p_cols = st.columns(2)
        prod_items = list(MENU_DATA[cat_scelta].items())
        
        for idx, (nome, prezzo) in enumerate(prod_items):
            qta = dispo.get(nome, 0)
            off = qta <= 0
            with p_cols[idx % 2]:
                label = f"➕ {nome}\n€{prezzo:.2f}" if not off else f"❌ {nome}\nFINITO"
                if st.button(label, key=f"btn_{nome}", disabled=off, use_container_width=True):
                    if 'carrello' not in st.session_state: st.session_state.carrello = []
                    st.session_state.carrello.append({"tavolo": st.session_state.tavolo_scelto, "prodotto": nome, "prezzo": prezzo})
                    st.toast(f"Aggiunto: {nome}")
                st.markdown(f"<div class='product-info'>Disponibili: {qta}</div>", unsafe_allow_html=True)

        if st.session_state.get('carrello'):
            st.divider()
            st.write("🛒 **IL TUO CARRELLO**")
            tot = 0
            for i, item in enumerate(st.session_state.carrello):
                col_c1, col_c2 = st.columns([4, 1])
                col_c1.write(f"{item['prodotto']} - €{item['prezzo']:.2f}")
                if col_c2.button("Canc", key=f"del_{i}"):
                    st.session_state.carrello.pop(i)
                    st.rerun()
                tot += item['prezzo']
            
            st.write(f"### TOTALE: €{tot:.2f}")
            nota = st.text_input("Note (es: caffè decaffeinato)")
            if st.button("🚀 INVIA ORDINE AL BANCONE", type="primary", use_container_width=True):
                ordini_at = carica_ordini()
                for item in st.session_state.carrello:
                    item.update({
                        "nota": nota, 
                        "orario": datetime.now().strftime("%H:%M"), 
                        "stato": "NO", 
                        "id_univoco": str(time.time()) + item['prodotto']
                    })
                    ordini_at.append(item)
                    # Aggiorna Stock
                    stk_at = carica_stock()
                    aggiorna_stock(item['prodotto'], stk_at[item['prodotto']] - 1)
                
                salva_ordini(ordini_at)
                st.session_state.carrello = []
                st.success("Ordine inviato con successo! ☕")
                time.sleep(2)
                st.rerun()
