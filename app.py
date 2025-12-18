import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="BAR PAGANO - Sistema Integrato", page_icon="☕", layout="wide")

# --- CSS PERSONALIZZATO (Stile, Colori e Forme dei Tasti) ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    
    /* Forza i bottoni dei tavoli a essere quadrati e grandi */
    div[data-testid="column"] button {
        width: 100% !important;
        height: 120px !important; /* Altezza fissa per farli grandi e quadrati */
        font-weight: bold !important;
        font-size: 28px !important;
        border-radius: 15px !important;
        margin-bottom: 10px !important;
        color: white !important;
    }

    /* TAVOLO LIBERO (Verde Pagano) - type="secondary" */
    div[data-testid="column"] button[kind="secondary"] {
        background-color: #2E7D32 !important; 
        border: 2px solid #4CAF50 !important;
    }

    /* TAVOLO OCCUPATO (Rosso Notifica) - type="primary" */
    div[data-testid="column"] button[kind="primary"] {
        background-color: #D32F2F !important;
        border: 2px solid #FF5252 !important;
    }

    /* Testi e stati */
    .servito { color: #555555 !important; text-decoration: line-through; opacity: 0.6; font-style: italic; }
    .da-servire { color: #FFFFFF !important; font-weight: bold; font-size: 18px; }
    
    .selected-tavolo { 
        background-color: #D32F2F; color: white; padding: 15px; 
        border-radius: 15px; text-align: center; font-size: 24px; 
        font-weight: bold; margin-bottom: 15px; 
    }

    /* Nascondi elementi in stampa */
    @media print {
        .no-print { display: none !important; }
        .stButton, .stSidebar, header { display: none !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNZIONI DI SERVIZIO ---
def suona_notifica():
    audio_html = '<audio autoplay style="display:none;"><source src="https://raw.githubusercontent.com/rafaelreis-hotmart/Audio-Files/main/notification.mp3" type="audio/mp3"></audio>'
    components.html(audio_html, height=0)

def mostra_logo():
    if os.path.exists("logo.png"):
        st.image("logo.png", width=120)
    else:
        st.title("☕ BAR PAGANO")

# --- GESTIONE DATABASE (CSV) ---
DB_FILE = "ordini_bar_pagano.csv"
STOCK_FILE = "stock_bar_pagano.csv"
MENU_FILE = "menu_personalizzato.csv"
COLONNE_ORDINI = ["id_univoco", "tavolo", "prodotto", "prezzo", "stato", "orario"]

def inizializza_file(file, colonne):
    if not os.path.exists(file) or os.stat(file).st_size <= 2:
        pd.DataFrame(columns=colonne).to_csv(file, index=False)

inizializza_file(DB_FILE, COLONNE_ORDINI)
inizializza_file(MENU_FILE, ["categoria", "prodotto", "prezzo"])
inizializza_file(STOCK_FILE, ["prodotto", "quantita"])

def carica_menu(): return pd.read_csv(MENU_FILE)
def carica_ordini(): 
    try: return pd.read_csv(DB_FILE).to_dict('records')
    except: return []
def salva_ordini(lista): pd.DataFrame(lista if lista else [], columns=COLONNE_ORDINI).to_csv(DB_FILE, index=False)
def carica_stock(): 
    df = pd.read_csv(STOCK_FILE)
    return df.set_index('prodotto')['quantita'].to_dict() if not df.empty else {}
def salva_stock(d): pd.DataFrame(list(d.items()), columns=['prodotto', 'quantita']).to_csv(STOCK_FILE, index=False)

# --- LOGICA DI NAVIGAZIONE ---
ruolo = st.query_params.get("ruolo", "tavolo")
menu_df = carica_menu()
ordini_attuali = carica_ordini()

# ---------------------------------------------------------
# INTERFACCIA BANCONE (Solo Preparazione)
# ---------------------------------------------------------
if ruolo == "banco":
    st_autorefresh(interval=5000, key="banco_refresh")
    
    col_h1, col_h2 = st.columns([1, 5])
    with col_h1: mostra_logo()
    with col_h2: st.title("👨‍🍳 CONSOLE BANCONE")
    
    if "ultimo_count" not in st.session_state: st.session_state.ultimo_count = len(ordini_attuali)
    if len(ordini_attuali) > st.session_state.ultimo_count:
        suona_notifica()
    st.session_state.ultimo_count = len(ordini_attuali)

    tavoli_attivi = sorted(list(set(str(o['tavolo']) for o in ordini_attuali)))
    if not tavoli_attivi:
        st.info("In attesa di nuovi ordini...")
    else:
        cols_banco = st.columns(3)
        for idx, t in enumerate(tavoli_attivi):
            with cols_banco[idx % 3]:
                with st.container(border=True):
                    st.subheader(f"🪑 Tavolo {t}")
                    items = [o for o in ordini_attuali if str(o['tavolo']) == str(t)]
                    for r in items:
                        c_nome, c_stato = st.columns([3, 1])
                        if r['stato'] == "SI":
                            c_nome.markdown(f"<span class='servito'>{r['prodotto']}</span>", unsafe_allow_html=True)
                            c_stato.write("✅")
                        else:
                            c_nome.markdown(f"**{r['prodotto']}**")
                            if c_stato.button("Ok", key=f"b_ok_{r['id_univoco']}"):
                                for o in ordini_attuali:
                                    if o['id_univoco'] == r['id_univoco']: o['stato'] = "SI"
                                salva_ordini(ordini_attuali); st.rerun()

# ---------------------------------------------------------
# INTERFACCIA CASSA (Solo Pagamenti)
# ---------------------------------------------------------
elif ruolo == "cassa":
    st_autorefresh(interval=5000, key="cassa_refresh")
    st.title("💰 CONSOLE CASSA")
    
    tavoli_attivi = sorted(list(set(str(o['tavolo']) for o in ordini_attuali)))
    if not tavoli_attivi:
        st.info("Nessun conto aperto.")
    else:
        cols_cassa = st.columns(2)
        for idx, t in enumerate(tavoli_attivi):
            with cols_cassa[idx % 2]:
                with st.container(border=True):
                    items = [o for o in ordini_attuali if str(o['tavolo']) == str(t)]
                    totale = sum(float(x['prezzo']) for x in items)
                    st.subheader(f"Conto Tavolo {t}")
                    
                    # Lista prodotti per controllo cassa
                    for r in items:
                        st.text(f"• {r['prodotto']} - €{r['prezzo']} ({'Servito' if r['stato']=='SI' else 'In prep.'})")
                    
                    st.divider()
                    st.write(f"### Totale: €{totale:.2f}")
                    
                    if st.button(f"PAGATO E CHIUDI CONTO", key=f"c_pay_{t}", type="primary", use_container_width=True):
                        # Rimuove gli ordini dal database liberando il tavolo
                        salva_ordini([o for o in ordini_attuali if str(o['tavolo']) != str(t)])
                        st.success(f"Tavolo {t} pagato!")
                        time.sleep(1); st.rerun()

# ---------------------------------------------------------
# INTERFACCIA CLIENTE / TAVOLO
# ---------------------------------------------------------
else:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2: mostra_logo()

    if 'tavolo' not in st.session_state: st.session_state.tavolo = None
    if 'carrello' not in st.session_state: st.session_state.carrello = []

    if st.session_state.tavolo is None:
        st.write("### 🪑 Seleziona il tuo tavolo:")
        tavoli_occupati = [str(o['tavolo']) for o in ordini_attuali]
        
        for i in range(0, 15, 5):
            cols = st.columns(5)
            for j in range(5):
                n_t = i + j + 1
                if n_t <= 15:
                    t_str = str(n_t)
                    # Colore dinamico: Rosso se occupato (primary), Verde se libero (secondary)
                    tipo_btn = "primary" if t_str in tavoli_occupati else "secondary"
                    if cols[j].button(f"{n_t}", key=f"tav_{n_t}", type=tipo_btn, use_container_width=True):
                        st.session_state.tavolo = t_str
                        st.rerun()
    else:
        st.markdown(f"<div class='selected-tavolo'>TAVOLO {st.session_state.tavolo}</div>", unsafe_allow_html=True)
        if st.button("⬅️ CAMBIA TAVOLO", use_container_width=True): 
            st.session_state.tavolo = None; st.rerun()
        
        stk = carica_stock()
        if not menu_df.empty:
            cat_scelta = st.radio("Scegli Categoria:", sorted(menu_df['categoria'].unique()), horizontal=True)
            for i, r in menu_df[menu_df['categoria'] == cat_scelta].iterrows():
                q = stk.get(r['prodotto'], 99)
                if st.button(f"{r['prodotto']} | €{r['prezzo']:.2f}", key=f"p_{i}", use_container_width=True, disabled=q<=0):
                    st.session_state.carrello.append(r.to_dict())
                    st.toast(f"Aggiunto: {r['prodotto']}")

        if st.session_state.carrello:
            st.divider()
            st.write("### 🛒 Carrello")
            for idx, c in enumerate(st.session_state.carrello):
                st.write(f"- {c['prodotto']} (€{c['prezzo']})")
            
            tot_carrello = sum(x['prezzo'] for x in st.session_state.carrello)
            if st.button(f"🚀 INVIA ORDINE (€{tot_carrello:.2f})", type="primary", use_container_width=True):
                for c in st.session_state.carrello:
                    if c['prodotto'] in stk: stk[c['prodotto']] -= 1
                    ordini_attuali.append({
                        "id_univoco": f"{time.time()}_{c['prodotto']}",
                        "tavolo": st.session_state.tavolo,
                        "prodotto": c['prodotto'],
                        "prezzo": c['prezzo'],
                        "stato": "NO",
                        "orario": datetime.now().strftime("%H:%M")
                    })
                salva_stock(stk); salva_ordini(ordini_attuali)
                st.session_state.carrello = []
                st.success("Ordine Inviato!")
                time.sleep(1); st.rerun()
