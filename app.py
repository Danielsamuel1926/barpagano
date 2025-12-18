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
    .servito { color: #555555 !important; text-decoration: line-through; opacity: 0.6; font-style: italic; }
    .selected-tavolo { background-color: #FF4B4B; color: white; padding: 15px; border-radius: 15px; text-align: center; font-size: 24px; font-weight: bold; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

DB_FILE = "ordini_bar_pagano.csv"
STOCK_FILE = "stock_bar_pagano.csv"
MENU_FILE = "menu_personalizzato.csv"
COLONNE_ORDINI = ["id_univoco", "tavolo", "prodotto", "prezzo", "nota", "orario", "stato"]

# --- FUNZIONE STAMPA SCONTRINO (JavaScript) ---
def stampa_scontrino(tavolo, prodotti, totale):
    data_ora = datetime.now().strftime("%d/%m/%Y %H:%M")
    linee_prodotti = "".join([f"<tr><td>{p['prodotto']}</td><td style='text-align:right'>€{p['prezzo']:.2f}</td></tr>" for p in prodotti])
    
    html_scontrino = f"""
    <html>
    <head>
        <style>
            body {{ font-family: 'Courier New', Courier, monospace; width: 80mm; padding: 5px; }}
            .header {{ text-align: center; border-bottom: 1px dashed #000; padding-bottom: 10px; }}
            table {{ width: 100%; margin-top: 10px; border-collapse: collapse; }}
            .totale {{ border-top: 2px solid #000; font-weight: bold; font-size: 1.2em; }}
            .footer {{ text-align: center; margin-top: 20px; font-size: 0.8em; border-top: 1px dashed #000; }}
            @media print {{ @page {{ margin: 0; }} }}
        </style>
    </head>
    <body onload="window.print(); window.close();">
        <div class="header">
            <h2>BAR PAGANO</h2>
            <p>SCONTRINO NON FISCALE<br>Tavolo: {tavolo}<br>{data_ora}</p>
        </div>
        <table>
            {linee_prodotti}
            <tr class="totale"><td>TOTALE</td><td style='text-align:right'>€{totale:.2f}</td></tr>
        </table>
        <div class="footer">
            <p>Grazie e a presto!</p>
        </div>
    </body>
    </html>
    """
    # Questo apre una finestra popup con lo scontrino e lancia la stampa
    components.html(f"""
        <script>
        var win = window.open('', '_blank');
        win.document.write(`{html_scontrino}`);
        win.document.close();
        </script>
    """, height=0)

# --- FUNZIONI CARICAMENTO DATI ---
def carica_menu():
    if not os.path.exists(MENU_FILE) or os.stat(MENU_FILE).st_size == 0:
        default = [{"categoria": "Brioche", "prodotto": "Cornetto", "prezzo": 1.50}]
        pd.DataFrame(default).to_csv(MENU_FILE, index=False)
        return pd.DataFrame(default)
    return pd.read_csv(MENU_FILE)

def carica_ordini():
    if not os.path.exists(DB_FILE) or os.stat(DB_FILE).st_size == 0:
        pd.DataFrame(columns=COLONNE_ORDINI).to_csv(DB_FILE, index=False)
        return []
    return pd.read_csv(DB_FILE).to_dict('records')

def salva_ordini(lista):
    pd.DataFrame(lista if lista else columns=COLONNE_ORDINI).to_csv(DB_FILE, index=False)

# --- LOGICA BANCONE ---
ruolo = st.query_params.get("ruolo", "tavolo")

if ruolo == "banco":
    st.title("🖥️ CONSOLE BANCONE")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📋 ORDINI", "⚡ VENDITA", "📦 STOCK", "⚙️ LISTINO"])
    
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
                        prod_tavolo = [o for o in ordini if str(o['tavolo']) == str(t)]
                        tot_tavolo = sum(float(p['prezzo']) for p in prod_tavolo)
                        tutto_servito = all(p['stato'] == "SI" for p in prod_tavolo)

                        for i, r in enumerate(ordini):
                            if str(r['tavolo']) == str(t):
                                c_t, c_b = st.columns([3, 1])
                                cl = "servito" if r['stato'] == "SI" else "da-servire"
                                c_t.markdown(f"<span class='{cl}'>{r['prodotto']}</span>", unsafe_allow_html=True)
                                if r['stato'] == "NO" and c_b.button("Ok", key=f"ok_{r['id_univoco']}"):
                                    r['stato'] = "SI"; salva_ordini(ordini); st.rerun()

                        st.divider()
                        if st.button(f"PAGATO €{tot_tavolo:.2f}", key=f"pay_{t}", type="primary", use_container_width=True, disabled=not tutto_servito):
                            # Lancio la stampa prima di cancellare
                            stampa_scontrino(t, prod_tavolo, tot_tavolo)
                            # Rimuovo gli ordini del tavolo
                            nuovi_ordini = [o for o in ordini if str(o['tavolo']) != str(t)]
                            salva_ordini(nuovi_ordini)
                            st.success("Scontrino inviato alla stampa!")
                            time.sleep(1)
                            st.rerun()

    # (Le altre tab rimangono come nelle versioni precedenti...)
    # [Codice per Tab 2, 3 e 4 omesso per brevità ma uguale all'ultima versione funzionante]

else:
    st.title("☕ BENVENUTO AL BAR PAGANO")
    # [Logica Cliente omessa per brevità...]

