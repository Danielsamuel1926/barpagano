import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime
import streamlit.components.v1 as components

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="BAR PAGANO", page_icon="☕", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    [data-testid="column"] { flex: 1 1 calc(25% - 10px) !important; min-width: 70px !important; }
    div[data-testid="column"] button { width: 100% !important; font-weight: bold !important; border-radius: 12px !important; }
    .servito { color: #555555 !important; text-decoration: line-through; opacity: 0.6; font-style: italic; }
    .da-servire { color: #FFFFFF !important; font-weight: bold; font-size: 18px; }
    .selected-tavolo { background-color: #FF4B4B; color: white; padding: 15px; border-radius: 15px; text-align: center; font-size: 24px; font-weight: bold; margin-bottom: 10px; }
    .stButton>button[kind="secondary"] { background-color: #2E7D32 !important; color: white !important; font-size: 18px !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

# --- FILE DATABASE ---
DB_FILE = "ordini_bar_pagano.csv"
STOCK_FILE = "stock_bar_pagano.csv"
MENU_FILE = "menu_personalizzato.csv"
COLONNE_ORDINI = ["id_univoco", "tavolo", "prodotto", "prezzo", "nota", "orario", "stato"]

# --- FUNZIONI DI SUPPORTO ---
def suona_notifica():
    audio_url = "https://www.soundjay.com/buttons/sounds/button-3.mp3"
    components.html(f"<audio autoplay><source src='{audio_url}' type='audio/mp3'></audio>", height=0)

def carica_menu():
    if not os.path.exists(MENU_FILE) or os.stat(MENU_FILE).st_size <= 2:
        df = pd.DataFrame([{"categoria": "Caffetteria", "prodotto": "Caffè", "prezzo": 1.00}])
        df.to_csv(MENU_FILE, index=False)
        return df
    return pd.read_csv(MENU_FILE)

def carica_ordini():
    if not os.path.exists(DB_FILE) or os.stat(DB_FILE).st_size <= 2: return []
    try: return pd.read_csv(DB_FILE).to_dict('records')
    except: return []

def salva_ordini(lista):
    df = pd.DataFrame(lista) if lista else pd.DataFrame(columns=COLONNE_ORDINI)
    df.to_csv(DB_FILE, index=False)

def carica_stock():
    if not os.path.exists(STOCK_FILE) or os.stat(STOCK_FILE).st_size <= 2: return {}
    df = pd.read_csv(STOCK_FILE)
    return df.set_index('prodotto')['quantita'].to_dict()

def aggiorna_stock_veloce(nome, var):
    if os.path.exists(STOCK_FILE):
        df = pd.read_csv(STOCK_FILE)
        if nome in df['prodotto'].values:
            idx = df[df['prodotto'] == nome].index[0]
            df.at[idx, 'quantita'] = max(0, df.at[idx, 'quantita'] + var)
            df.to_csv(STOCK_FILE, index=False)

# --- LOGICA APP ---
ruolo = st.query_params.get("ruolo", "tavolo")
menu_df = carica_menu()

if ruolo == "banco":
    st.title("🖥️ CONSOLE BANCONE")
    
    if st.button("🔄 AGGIORNA ORDINI", use_container_width=True, type="secondary"):
        st.rerun()

    if "last_refresh" not in st.session_state: st.session_state.last_refresh = time.time()
    if time.time() - st.session_state.last_refresh > 3:
        st.session_state.last_refresh = time.time(); st.rerun()

    tab1, tab2, tab3, tab4 = st.tabs(["📋 ORDINI", "⚡ VENDITA RAPIDA", "📦 STOCK", "⚙️ GESTIONE LISTINO"])
    
    with tab1:
        ordini = carica_ordini()
        if not ordini: st.info("Nessun ordine attivo.")
        else:
            tavoli = sorted(set(str(o['tavolo']) for o in ordini), key=lambda x: int(x) if x.isdigit() else 0)
            cols = st.columns(3)
            for idx, t in enumerate(tavoli):
                with cols[idx % 3]:
                    with st.container(border=True):
                        st.subheader(f"🪑 Tavolo {t}")
                        items_tavolo = [o for o in ordini if str(o['tavolo']) == str(t)]
                        tutti_serviti = all(o['stato'] == "SI" for o in items_tavolo)
                        tot_tavolo = sum(float(o['prezzo']) for o in items_tavolo)
                        
                        for r in items_tavolo:
                            c_del, c_t, c_b = st.columns([0.5, 3, 1])
                            if c_del.button("❌", key=f"del_prod_{r['id_univoco']}"):
                                ordini = [o for o in ordini if o['id_univoco'] != r['id_univoco']]
                                salva_ordini(ordini); st.rerun()
                            cl = "servito" if r['stato'] == "SI" else "da-servire"
                            c_t.markdown(f"<span class='{cl}'>{r['prodotto']}</span>", unsafe_allow_html=True)
                            if r['stato'] == "NO" and c_b.button("Ok", key=f"sv_{r['id_univoco']}"):
                                for o in ordini: 
                                    if o['id_univoco'] == r['id_univoco']: o['stato'] = "SI"
                                salva_ordini(ordini); st.rerun()
                        st.divider()
                        if st.button(f"PAGATO €{tot_tavolo:.2f}", key=f"pay_{t}", type="primary", use_container_width=True, disabled=not tutti_serviti):
                            salva_ordini([o for o in ordini if str(o['tavolo']) != str(t)]); st.rerun()

    with tab2:
        st.write("### ⚡ Vendita Rapida")
        stk = carica_stock()
        brioche_prods = menu_df[menu_df['categoria'].str.contains('Brioche|Cornetti', case=False, na=False)]
        cols_v = st.columns(4)
        for i, (idx_r, r) in enumerate(brioche_prods.iterrows()):
            q = stk.get(r['prodotto'], 0)
            if cols_v[i % 4].button(f"{r['prodotto']} ({q})", key=f"bs_{idx_r}", disabled=(q <= 0)):
                aggiorna_stock_veloce(r['prodotto'], -1); st.rerun()

    with tab3:
        st.write("### 📦 Carico Magazzino")
        stk = carica_stock()
        for p, q in stk.items():
            c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
            c1.write(f"**{p}**")
            if c2.button("➖", key=f"m_{p}"): aggiorna_stock_veloce(p, -1); st.rerun()
            c3.write(f"**{q}**")
            if c4.button("➕", key=f"p_{p}"): aggiorna_stock_veloce(p, 1); st.rerun()

    with tab4:
        st.subheader("🗑️ Cancella Categoria")
        lista_cats = sorted(menu_df['categoria'].unique())
        cat_del = st.selectbox("Scegli categoria", ["---"] + lista_cats)
        if cat_del != "---" and st.button("ELIMINA"):
            menu_df = menu_df[menu_df['categoria'] != cat_del]
            menu_df.to_csv(MENU_FILE, index=False); st.rerun()
        st.divider()
        with st.form("nuovo_p"):
            c1, c2 = st.columns(2)
            ce, cn = c1.selectbox("Esistente", ["---"] + lista_cats), c2.text_input("Nuova")
            nome, prezzo = st.text_input("Nome"), st.number_input("€", step=0.1)
            if st.form_submit_button("AGGIUNGI"):
                cat_f = cn if cn.strip() != "" else ce
                if cat_f != "---" and nome:
                    nuovo = pd.DataFrame([{"categoria": cat_f, "prodotto": nome, "prezzo": prezzo}])
                    pd.concat([menu_df, nuovo], ignore_index=True).to_csv(MENU_FILE, index=False); st.rerun()

else:
    # --- CLIENTE ---
    st.title("☕ BAR PAGANO")
    if 'tavolo' not in st.session_state: st.session_state.tavolo = None
    if 'carrello' not in st.session_state: st.session_state.carrello = []
    
    if st.session_state.tavolo is None:
        t_cols = st.columns(4)
        for i in range(1, 21):
            if t_cols[(i-1) % 4].button(f"{i}", key=f"t_{i}", use_container_width=True):
                st.session_state.tavolo = str(i); st.rerun()
    else:
        # TASTO CAMBIA TAVOLO (RIPRISTINATO)
        st.markdown(f"<div class='selected-tavolo'>TAVOLO {st.session_state.tavolo}</div>", unsafe_allow_html=True)
        if st.button("⬅️ CAMBIA TAVOLO", use_container_width=True):
            st.session_state.tavolo = None
            st.rerun()
            
        st.divider()
        stk = carica_stock()
        scelta_cat = st.radio("Scegli Sezione:", sorted(menu_df['categoria'].unique()), horizontal=True)
        prods = menu_df[menu_df['categoria'] == scelta_cat]
        
        for idx, (idx_r, r) in enumerate(prods.iterrows()):
            q = stk.get(r['prodotto'], None)
            disp = f" (Disp: {q})" if q is not None else ""
            if st.button(f"➕ {r['prodotto']}{disp} | €{r['prezzo']:.2f}", key=f"cl_{idx_r}", use_container_width=True, disabled=(q is not None and q <= 0)):
                item = r.to_dict()
                item['temp_id'] = time.time() + idx
                st.session_state.carrello.append(item); st.toast("Aggiunto!")
        
        if st.session_state.carrello:
            st.divider(); st.write("### 🛒 Carrello:")
            for i, item in enumerate(st.session_state.carrello):
                c1, c2, c3 = st.columns([4, 2, 1])
                c1.write(item['prodotto'])
                c2.write(f"€{item['prezzo']:.2f}")
                if c3.button("❌", key=f"del_car_{item['temp_id']}"): st.session_state.carrello.pop(i); st.rerun()
            
            if st.button(f"🚀 INVIA ORDINE €{sum(c['prezzo'] for c in st.session_state.carrello):.2f}", type="primary", use_container_width=True):
                suona_notifica()
                ord_db = carica_ordini()
                for c in st.session_state.carrello:
                    if c['prodotto'] in stk: aggiorna_stock_veloce(c['prodotto'], -1)
                    ord_db.append({"id_univoco": str(time.time())+c['prodotto'], "tavolo": st.session_state.tavolo, "prodotto": c['prodotto'], "prezzo": c['prezzo'], "nota": "", "orario": datetime.now().strftime("%H:%M"), "stato": "NO"})
                salva_ordini(ord_db); st.session_state.carrello = []; st.success("Inviato!"); time.sleep(1); st.rerun()

