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
    .selected-tavolo { background-color: #FF4B4B; color: white; padding: 15px; border-radius: 15px; text-align: center; font-size: 24px; font-weight: bold; margin-bottom: 20px; }
    .stButton>button[kind="secondary"] { background-color: #2E7D32 !important; color: white !important; border: none !important; }
    .carrello-item { background-color: #262730; padding: 5px 15px; border-radius: 10px; margin-bottom: 5px; border-left: 5px solid #FF4B4B; display: flex; justify-content: space-between; align-items: center; }
    </style>
    """, unsafe_allow_html=True)

# --- FILE DATABASE ---
DB_FILE = "ordini_bar_pagano.csv"
STOCK_FILE = "stock_bar_pagano.csv"
MENU_FILE = "menu_personalizzato.csv"
COLONNE_ORDINI = ["id_univoco", "tavolo", "prodotto", "prezzo", "nota", "orario", "stato"]

# --- FUNZIONI AUDIO E STAMPA ---
def suona_notifica():
    audio_url = "https://www.soundjay.com/buttons/sounds/button-3.mp3"
    components.html(f"<audio autoplay><source src='{audio_url}' type='audio/mp3'></audio>", height=0)

def stampa_scontrino(tavolo, prodotti, totale):
    ora = datetime.now().strftime("%d/%m/%Y %H:%M")
    righe = "".join([f"<tr><td>{p['prodotto']}</td><td style='text-align:right'>€{float(p['prezzo']):.2f}</td></tr>" for p in prodotti])
    html = f"""
    <div id="s" style="font-family:monospace; width:75mm; color:black; background:white; padding:10px;">
        <h2 style="text-align:center;">BAR PAGANO</h2><hr>
        <p><b>TAVOLO {tavolo}</b><br>{ora}</p><hr>
        <table style="width:100%;">{righe}</table><hr>
        <h3 style="text-align:right;">TOTALE: €{totale:.2f}</h3>
    </div>
    <script>
        var w = window.open('', '', 'width=600,height=600');
        w.document.write('<html><body>' + document.getElementById('s').outerHTML + '</body></html>');
        w.document.close();
        setTimeout(function(){{ w.print(); w.close(); }}, 700);
    </script>
    """
    components.html(html, height=0)

# --- FUNZIONI DI CARICAMENTO ---
def carica_menu():
    if not os.path.exists(MENU_FILE) or os.stat(MENU_FILE).st_size <= 2:
        df = pd.DataFrame([{"categoria": "Brioche e Cornetti", "prodotto": "Cornetto cioccolato", "prezzo": 1.50}])
        df.to_csv(MENU_FILE, index=False)
        return df
    return pd.read_csv(MENU_FILE)

def carica_ordini():
    if not os.path.exists(DB_FILE) or os.stat(DB_FILE).st_size <= 2:
        return []
    try:
        return pd.read_csv(DB_FILE).to_dict('records')
    except: return []

def carica_stock():
    menu = carica_menu()
    cat_con_stock = [c for c in menu['categoria'].unique() if any(x in c.lower() for x in ["brioche", "cornetto", "cornetti"])]
    prod_con_stock = menu[menu['categoria'].isin(cat_con_stock)]['prodotto'].unique().tolist()
    
    if not os.path.exists(STOCK_FILE) or os.stat(STOCK_FILE).st_size <= 2:
        data = [{"prodotto": p, "quantita": 0} for p in prod_con_stock]
        pd.DataFrame(data).to_csv(STOCK_FILE, index=False)
        return {p: 0 for p in prod_con_stock}
    try:
        df = pd.read_csv(STOCK_FILE)
        return df.set_index('prodotto')['quantita'].to_dict()
    except: return {}

def salva_ordini(lista):
    df = pd.DataFrame(lista) if lista else pd.DataFrame(columns=COLONNE_ORDINI)
    df.to_csv(DB_FILE, index=False)

def aggiorna_stock_veloce(nome, var):
    if os.path.exists(STOCK_FILE):
        df = pd.read_csv(STOCK_FILE)
        if nome in df['prodotto'].values:
            idx = df[df['prodotto'] == nome].index[0]
            df.at[idx, 'quantita'] = max(0, df.at[idx, 'quantita'] + var)
            df.to_csv(STOCK_FILE, index=False)

# --- LOGICA APPLICAZIONE ---
ruolo = st.query_params.get("ruolo", "tavolo")
menu_df = carica_menu()

if ruolo == "banco":
    st.title("🖥️ CONSOLE BANCONE")
    
    # Auto-aggiornamento 3s
    if "last_refresh" not in st.session_state: st.session_state.last_refresh = time.time()
    if time.time() - st.session_state.last_refresh > 3:
        st.session_state.last_refresh = time.time()
        st.rerun()

    if st.button("🔄 AGGIORNA", use_container_width=True, type="secondary"):
        st.rerun()

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
                        tot_tavolo = sum(float(o['prezzo']) for o in items_tavolo)
                        tutto_servito = True
                        for r in items_tavolo:
                            if r['stato'] == "NO": tutto_servito = False
                            c_t, c_b = st.columns([3, 1])
                            cl = "servito" if r['stato'] == "SI" else "da-servire"
                            c_t.markdown(f"<span class='{cl}'>{r['prodotto']}</span>", unsafe_allow_html=True)
                            if r['stato'] == "NO" and c_b.button("Ok", key=f"sv_{r['id_univoco']}"):
                                for o in ordini: 
                                    if o['id_univoco'] == r['id_univoco']: o['stato'] = "SI"
                                salva_ordini(ordini); st.rerun()
                        st.divider()
                        if st.button(f"PAGATO €{tot_tavolo:.2f}", key=f"pay_{t}", type="primary", use_container_width=True):
                            stampa_scontrino(t, items_tavolo, tot_tavolo)
                            salva_ordini([o for o in ordini if str(o['tavolo']) != str(t)]); st.rerun()

    with tab2:
        st.write("### ⚡ Vendita Rapida")
        stk = carica_stock()
        # Filtriamo solo brioche e cornetti per la vendita rapida
        brioche_prods = menu_df[menu_df['categoria'].str.contains('Brioche|Cornetti', case=False, na=False)]
        cols_v = st.columns(4)
        for i, (idx_r, r) in enumerate(brioche_prods.iterrows()):
            if cols_v[i % 4].button(f"{r['prodotto']}", key=f"bs_{idx_r}"):
                if r['prodotto'] in stk: aggiorna_stock_veloce(r['prodotto'], -1)
                st.rerun()

    with tab3:
        st.write("### 📦 Carico Magazzino (+1)")
        stk = carica_stock()
        for p, q in stk.items():
            c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
            c1.write(f"**{p}**")
            if c2.button("➖", key=f"m_{p}"): aggiorna_stock_veloce(p, -1); st.rerun()
            c3.write(f"**{q}**")
            if c4.button("➕", key=f"p_{p}"): aggiorna_stock_veloce(p, 1); st.rerun()

    with tab4:
        # (Codice gestione listino originale...)
        st.subheader("🆕 Aggiungi Prodotto")
        with st.form("nuovo_p"):
            c1, c2 = st.columns(2)
            cat = c1.text_input("Categoria")
            nome = c2.text_input("Nome Prodotto")
            prezzo = st.number_input("Prezzo €", step=0.1)
            if st.form_submit_button("SALVA"):
                nuovo = pd.DataFrame([{"categoria": cat, "prodotto": nome, "prezzo": prezzo}])
                pd.concat([menu_df, nuovo], ignore_index=True).to_csv(MENU_FILE, index=False); st.rerun()

else:
    # --- CLIENTE ---
    st.title("☕ BAR PAGANO")
    if 'tavolo' not in st.session_state: st.session_state.tavolo = None
    if 'carrello' not in st.session_state: st.session_state.carrello = []

    if st.session_state.tavolo is None:
        st.write("### Seleziona Tavolo:")
        t_cols = st.columns(4)
        for i in range(1, 21):
            if t_cols[(i-1) % 4].button(f"{i}", key=f"t_{i}", use_container_width=True):
                st.session_state.tavolo = str(i); st.rerun()
    else:
        st.markdown(f"<div class='selected-tavolo'>TAVOLO {st.session_state.tavolo}</div>", unsafe_allow_html=True)
        if st.button("🔄 Cambia Tavolo"): st.session_state.tavolo = None; st.rerun()
        
        st.divider()
        scelta_cat = st.radio("Menù:", sorted(menu_df['categoria'].unique()), horizontal=True)
        prod_filtrati = menu_df[menu_df['categoria'] == scelta_cat]
        p_cols = st.columns(2)
        for idx, (idx_r, r) in enumerate(prod_filtrati.iterrows()):
            with p_cols[idx % 2]:
                if st.button(f"➕ {r['prodotto']}\n€{r['prezzo']:.2f}", key=f"cl_{idx_r}", use_container_width=True):
                    item = r.to_dict()
                    item['temp_id'] = time.time() + idx
                    st.session_state.carrello.append(item)
                    st.toast("Aggiunto!")
        
        if st.session_state.carrello:
            st.divider()
            st.write("### 🛒 Il tuo Ordine:")
            for i, item in enumerate(st.session_state.carrello):
                c1, c2, c3 = st.columns([4, 2, 1])
                c1.write(item['prodotto'])
                c2.write(f"€{item['prezzo']:.2f}")
                if c3.button("❌", key=f"del_{item['temp_id']}"):
                    st.session_state.carrello.pop(i); st.rerun()
            
            if st.button(f"🚀 ORDINA €{sum(c['prezzo'] for c in st.session_state.carrello):.2f}", type="primary", use_container_width=True):
                suona_notifica()
                ord_db = carica_ordini()
                for c in st.session_state.carrello:
                    ord_db.append({"id_univoco": str(time.time())+c['prodotto'], "tavolo": st.session_state.tavolo, "prodotto": c['prodotto'], "prezzo": c['prezzo'], "nota": "", "orario": datetime.now().strftime("%H:%M"), "stato": "NO"})
                salva_ordini(ord_db)
                st.session_state.carrello = []
                st.success("Inviato!"); time.sleep(1); st.rerun()

