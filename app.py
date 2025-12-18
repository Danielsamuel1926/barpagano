import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime
import streamlit.components.v1 as components

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="BAR PAGANO - POS", page_icon="☕", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    .servito { color: #555555 !important; text-decoration: line-through; opacity: 0.6; font-style: italic; }
    .da-servire { color: #FFFFFF !important; font-weight: bold; font-size: 18px; color: #FF4B4B !important; }
    .selected-tavolo { background-color: #FF4B4B; color: white; padding: 15px; border-radius: 15px; text-align: center; font-size: 24px; font-weight: bold; margin-bottom: 20px; }
    .stButton>button[kind="secondary"] { background-color: #2E7D32 !important; color: white !important; border: none !important; width: 100%; }
    .carrello-item { background-color: #1E1E1E; padding: 10px; border-radius: 8px; margin-bottom: 5px; border: 1px solid #333; }
    </style>
    """, unsafe_allow_html=True)

# --- FILE ---
DB_FILE = "ordini_bar_pagano.csv"
MENU_FILE = "menu_personalizzato.csv"
STOCK_FILE = "stock_bar_pagano.csv"
COLONNE_ORDINI = ["id_univoco", "tavolo", "prodotto", "prezzo", "orario", "stato"]

# --- FUNZIONI AUDIO E STAMPA ---
def suona_notifica():
    audio_url = "https://www.soundjay.com/buttons/sounds/button-3.mp3"
    components.html(f"""
        <audio autoplay><source src="{audio_url}" type="audio/mp3"></audio>
    """, height=0)

def stampa_scontrino(tavolo, prodotti, totale):
    ora = datetime.now().strftime("%d/%m/%Y %H:%M")
    righe = "".join([f"<tr><td>{p['prodotto']}</td><td style='text-align:right'>€{float(p['prezzo']):.2f}</td></tr>" for p in prodotti])
    html = f"""
    <div id="s" style="font-family:monospace; width:75mm; color:black; background:white; padding:10px;">
        <h2 style="text-align:center;">BAR PAGANO</h2><hr>
        <p><b>TAVOLO {tavolo}</b><br>{ora}</p><hr>
        <table style="width:100%; font-size:14px;">{righe}</table><hr>
        <h3 style="text-align:right;">TOTALE: €{totale:.2f}</h3>
    </div>
    <script>
        var w = window.open('', '', 'width=600,height=600');
        w.document.write('<html><body style="margin:0;">' + document.getElementById('s').outerHTML + '</body></html>');
        w.document.close();
        setTimeout(function(){{ w.print(); w.close(); }}, 700);
    </script>
    """
    components.html(html, height=0)

# --- FUNZIONI DATI ---
def carica_menu():
    if not os.path.exists(MENU_FILE) or os.stat(MENU_FILE).st_size <= 2:
        df = pd.DataFrame([{"categoria": "Brioche e Cornetti", "prodotto": "Cornetto", "prezzo": 1.50}])
        df.to_csv(MENU_FILE, index=False)
        return df
    return pd.read_csv(MENU_FILE)

def carica_ordini():
    if not os.path.exists(DB_FILE) or os.stat(DB_FILE).st_size <= 2:
        return []
    try:
        return pd.read_csv(DB_FILE).to_dict('records')
    except: return []

def salva_ordini(lista):
    if lista:
        df = pd.DataFrame(lista)
    else:
        df = pd.DataFrame(columns=COLONNE_ORDINI)
    df.to_csv(DB_FILE, index=False)

def carica_stock():
    menu = carica_menu()
    mask = menu['categoria'].str.contains('Brioche|Cornetti', case=False, na=False)
    prod_stock = menu[mask].copy()
    if not os.path.exists(STOCK_FILE) or os.stat(STOCK_FILE).st_size <= 2:
        prod_stock['quantita'] = 0
        prod_stock.to_csv(STOCK_FILE, index=False)
        return prod_stock
    return pd.read_csv(STOCK_FILE)

# --- LOGICA APPLICAZIONE ---
ruolo = st.query_params.get("ruolo", "tavolo")
menu_df = carica_menu()

if ruolo == "banco":
    st.title("🖥️ CONSOLE BANCONE")
    
    # AGGIORNAMENTO AUTOMATICO OGNI 3 SECONDI
    if "last_refresh" not in st.session_state: st.session_state.last_refresh = time.time()
    if time.time() - st.session_state.last_refresh > 3:
        st.session_state.last_refresh = time.time()
        st.rerun()

    tab1, tab2, tab3 = st.tabs(["📋 ORDINI", "🥐 STOCK", "⚙️ LISTINO"])
    
    with tab1:
        ordini = carica_ordini()
        nuovi = [o for o in ordini if o['stato'] == "NO"]
        if nuovi: st.error(f"🔔 {len(nuovi)} NUOVI PRODOTTI IN ARRIVO!")
        
        if not ordini: st.info("In attesa di ordini...")
        else:
            tavoli = sorted(list(set(str(o['tavolo']) for o in ordini)))
            cols = st.columns(3)
            for idx, t in enumerate(tavoli):
                with cols[idx % 3]:
                    with st.container(border=True):
                        items = [o for o in ordini if str(o['tavolo']) == t]
                        tot = sum(float(i['prezzo']) for i in items)
                        st.subheader(f"Tavolo {t}")
                        for r in items:
                            c_t, c_b = st.columns([3, 1])
                            cl = "servito" if r['stato'] == "SI" else "da-servire"
                            c_t.markdown(f"<div class='{cl}'>{r['prodotto']}</div>", unsafe_allow_html=True)
                            if r['stato'] == "NO" and c_b.button("Ok", key=f"ok_{r['id_univoco']}"):
                                for o in ordini: 
                                    if o['id_univoco'] == r['id_univoco']: o['stato'] = "SI"
                                salva_ordini(ordini)
                                st.rerun()
                        
                        if st.button(f"PAGA E STAMPA €{tot:.2f}", key=f"p_{t}", type="primary", use_container_width=True):
                            stampa_scontrino(t, items, tot)
                            salva_ordini([o for o in ordini if str(o['tavolo']) != t])
                            st.rerun()

    with tab2:
        st.subheader("⚡ Carico Stock (+1)")
        stock_df = carica_stock()
        for i, (idx, r) in enumerate(stock_df.iterrows()):
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.write(f"**{r['prodotto']}** ({r['quantita']})")
            if c2.button("➕", key=f"a_{idx}"):
                stock_df.at[idx, 'quantita'] += 1
                stock_df.to_csv(STOCK_FILE, index=False); st.rerun()
            if c3.button("➖", key=f"v_{idx}"):
                stock_df.at[idx, 'quantita'] = max(0, r['quantita'] - 1)
                stock_df.to_csv(STOCK_FILE, index=False); st.rerun()

    with tab3:
        for i, row in menu_df.iterrows():
            with st.expander(f"Modifica {row['prodotto']}"):
                with st.form(f"f_{i}"):
                    nc = st.text_input("Categoria", row['categoria'])
                    np = st.text_input("Nome", row['prodotto'])
                    nr = st.number_input("Prezzo", value=float(row['prezzo']))
                    if st.form_submit_button("SALVA"):
                        menu_df.at[i, 'categoria'], menu_df.at[i, 'prodotto'], menu_df.at[i, 'prezzo'] = nc, np, nr
                        menu_df.to_csv(MENU_FILE, index=False); st.rerun()

else:
    # --- CLIENTE ---
    st.title("☕ BAR PAGANO")
    if 'tavolo' not in st.session_state: st.session_state.tavolo = None
    if 'carrello' not in st.session_state: st.session_state.carrello = []

    if st.session_state.tavolo is None:
        t_cols = st.columns(4)
        for i in range(1, 21):
            if t_cols[(i-1)%4].button(f"Tavolo {i}", use_container_width=True):
                st.session_state.tavolo = str(i); st.rerun()
    else:
        st.markdown(f"<div class='selected-tavolo'>TAVOLO {st.session_state.tavolo}</div>", unsafe_allow_html=True)
        if st.button("⬅️ Cambia Tavolo"): st.session_state.tavolo = None; st.rerun()
        
        cats = sorted(menu_df['categoria'].unique())
        scelta = st.radio("Menù:", cats, horizontal=True)
        prods = menu_df[menu_df['categoria'] == scelta]
        
        p_cols = st.columns(2)
        for i, (idx, r) in enumerate(prods.iterrows()):
            with p_cols[i % 2]:
                if st.button(f"➕ {r['prodotto']}\n€{r['prezzo']:.2f}", key=f"c_{idx}", use_container_width=True):
                    item = r.to_dict()
                    item['temp_id'] = time.time() + i
                    st.session_state.carrello.append(item)
                    st.toast("Aggiunto!")

        if st.session_state.carrello:
            st.divider()
            st.subheader("🛒 Il tuo Ordine:")
            for i, item in enumerate(st.session_state.carrello):
                with st.container():
                    c1, c2, c3 = st.columns([3, 1, 1])
                    c1.write(item['prodotto'])
                    c2.write(f"€{item['prezzo']:.2f}")
                    if c3.button("❌", key=f"del_{item['temp_id']}"):
                        st.session_state.carrello.pop(i)
                        st.rerun()
            
            if st.button("🚀 INVIA ORDINE", type="primary", use_container_width=True):
                suona_notifica()
                ord_db = carica_ordini()
                for c in st.session_state.carrello:
                    ord_db.append({"id_univoco": str(time.time())+c['prodotto'], "tavolo": st.session_state.tavolo, "prodotto": c['prodotto'], "prezzo": c['prezzo'], "orario": datetime.now().strftime("%H:%M"), "stato": "NO"})
                salva_ordini(ord_db)
                st.session_state.carrello = []
                st.success("Inviato!"); time.sleep(1); st.rerun()

