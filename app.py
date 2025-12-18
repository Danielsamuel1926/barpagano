import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime
import streamlit.components.v1 as components

# --- CONFIGURAZIONE E STILE ---
st.set_page_config(page_title="BAR PAGANO - POS", page_icon="☕", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    .servito { color: #555555 !important; text-decoration: line-through; opacity: 0.6; font-style: italic; }
    .da-servire { color: #FFFFFF !important; font-weight: bold; font-size: 18px; }
    .selected-tavolo { background-color: #FF4B4B; color: white; padding: 15px; border-radius: 15px; text-align: center; font-size: 24px; font-weight: bold; margin-bottom: 20px; }
    /* Stile per il tasto AGGIORNA verde come prima */
    .stButton>button[kind="secondary"] { background-color: #2E7D32 !important; color: white !important; border: none !important; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

# --- FILE E COSTANTI ---
DB_FILE = "ordini_bar_pagano.csv"
MENU_FILE = "menu_personalizzato.csv"
STOCK_FILE = "stock_bar_pagano.csv"
COLONNE_ORDINI = ["id_univoco", "tavolo", "prodotto", "prezzo", "orario", "stato"]

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
    except:
        return []

def salva_ordini(lista):
    df = pd.DataFrame(lista) if lista else pd.DataFrame(columns=COLONNE_ORDINI)
    df.to_csv(DB_FILE, index=False)

def carica_stock():
    menu = carica_menu()
    mask = menu['categoria'].str.contains('Brioche|Cornetti|Cornetto', case=False, na=False)
    prod_stock = menu[mask].copy()
    if not os.path.exists(STOCK_FILE) or os.stat(STOCK_FILE).st_size <= 2:
        prod_stock['quantita'] = 0
        prod_stock.to_csv(STOCK_FILE, index=False)
        return prod_stock
    stock_df = pd.read_csv(STOCK_FILE)
    return stock_df

# --- FUNZIONE STAMPA ---
def stampa_scontrino(tavolo, prodotti, totale):
    ora = datetime.now().strftime("%d/%m/%Y %H:%M")
    righe = "".join([f"<tr><td>{p['prodotto']}</td><td style='text-align:right'>€{float(p['prezzo']):.2f}</td></tr>" for p in prodotti])
    html = f"""
    <div id="s" style="font-family:monospace; width:75mm; color:black; background:white; padding:5px;">
        <h2 style="text-align:center;">BAR PAGANO</h2><hr>
        <p>Tavolo {tavolo} - {ora}</p>
        <table style="width:100%;">{righe}</table><hr>
        <h3 style="text-align:right;">TOTALE: €{totale:.2f}</h3>
    </div>
    <script>
        var w = window.open('', '_blank');
        w.document.write('<html><body>' + document.getElementById('s').outerHTML + '</body></html>');
        w.document.close();
        setTimeout(function(){{ w.print(); w.close(); }}, 500);
    </script>
    """
    components.html(html, height=0)

# --- LOGICA APP ---
ruolo = st.query_params.get("ruolo", "tavolo")
menu_df = carica_menu()

if ruolo == "banco":
    st.title("🖥️ CONSOLE BANCONE")
    
    # TASTO AGGIORNA POSIZIONATO IN ALTO
    if st.button("🔄 AGGIORNA", type="secondary"):
        st.rerun()

    tab1, tab2, tab3 = st.tabs(["📋 ORDINI", "🥐 VENDITA RAPIDA & STOCK", "⚙️ GESTIONE LISTINO"])
    
    with tab1:
        ordini = carica_ordini()
        if not ordini: st.info("Nessun ordine attivo.")
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
                            cl = "servito" if r['stato'] == "SI" else "da-servire"
                            c_t, c_b = st.columns([3, 1])
                            c_t.markdown(f"<div class='{cl}'>{r['prodotto']}</div>", unsafe_allow_html=True)
                            if r['stato'] == "NO" and c_b.button("Ok", key=f"ok_{r['id_univoco']}"):
                                for o in ordini: 
                                    if o['id_univoco'] == r['id_univoco']: o['stato'] = "SI"
                                salva_ordini(ordini)
                                st.rerun()
                        if st.button(f"PAGA €{tot:.2f}", key=f"p_{t}", type="primary", use_container_width=True):
                            stampa_scontrino(t, items, tot)
                            salva_ordini([o for o in ordini if str(o['tavolo']) != t])
                            st.rerun()

    with tab2:
        st.subheader("⚡ Vendita Rapida Brioche")
        stock_df = carica_stock()
        brioche_view = stock_df[stock_df['categoria'].str.contains('Brioche|Cornetti', case=False, na=False)]
        for i, (idx, r) in enumerate(brioche_view.iterrows()):
            c1, c2, c3 = st.columns([3, 2, 2])
            c1.write(f"**{r['prodotto']}** (Stock: {r['quantita']})")
            if c2.button("➕ +1", key=f"a_{idx}"):
                stock_df.at[idx, 'quantita'] += 1
                stock_df.to_csv(STOCK_FILE, index=False); st.rerun()
            if c3.button(f"VENDI €{r['prezzo']}", key=f"v_{idx}", disabled=r['quantita'] <= 0):
                stock_df.at[idx, 'quantita'] = max(0, r['quantita'] - 1)
                stock_df.to_csv(STOCK_FILE, index=False); st.rerun()

    with tab3:
        st.subheader("🛠️ Modifica Listino")
        for i, row in menu_df.iterrows():
            with st.expander(f"{row['categoria']} - {row['prodotto']}"):
                with st.form(f"m_{i}"):
                    n_c = st.text_input("Categoria", row['categoria'])
                    n_p = st.text_input("Nome", row['prodotto'])
                    n_r = st.number_input("Prezzo €", value=float(row['prezzo']), step=0.1)
                    c1, c2 = st.columns(2)
                    if c1.form_submit_button("SALVA"):
                        menu_df.at[i, 'categoria'], menu_df.at[i, 'prodotto'], menu_df.at[i, 'prezzo'] = n_c, n_p, n_r
                        menu_df.to_csv(MENU_FILE, index=False); st.rerun()
                    if c2.form_submit_button("ELIMINA", type="primary"):
                        menu_df.drop(i).to_csv(MENU_FILE, index=False); st.rerun()

        st.divider()
        with st.form("nuovo"):
            st.write("### Aggiungi Nuovo")
            nc = st.text_input("Categoria")
            np = st.text_input("Prodotto")
            nr = st.number_input("Prezzo €", step=0.1)
            if st.form_submit_button("AGGIUNGI"):
                if np and nc:
                    nuovo = pd.DataFrame([{"categoria": nc, "prodotto": np, "prezzo": nr}])
                    pd.concat([menu_df, nuovo], ignore_index=True).to_csv(MENU_FILE, index=False)
                    st.rerun()

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
        scelta = st.radio("Sezioni:", cats, horizontal=True)
        prods = menu_df[menu_df['categoria'] == scelta]
        
        for i, (idx, r) in enumerate(prods.iterrows()):
            if st.button(f"➕ {r['prodotto']} - €{r['prezzo']:.2f}", key=f"c_{idx}", use_container_width=True):
                st.session_state.carrello.append(r.to_dict())
                st.toast("Aggiunto!")

        if st.session_state.carrello:
            st.divider()
            if st.button(f"🚀 INVIA ORDINE (€{sum(c['prezzo'] for c in st.session_state.carrello):.2f})", type="primary", use_container_width=True):
                ord_db = carica_ordini()
                for c in st.session_state.carrello:
                    ord_db.append({"id_univoco": f"{time.time()}_{c['prodotto']}", "tavolo": st.session_state.tavolo, "prodotto": c['prodotto'], "prezzo": c['prezzo'], "orario": datetime.now().strftime("%H:%M"), "stato": "NO"})
                salva_ordini(ord_db); st.session_state.carrello = []; st.success("Inviato!"); time.sleep(1); st.rerun()


