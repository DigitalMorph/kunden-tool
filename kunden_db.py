import streamlit as st
import pandas as pd
from datetime import datetime
import os
import yaml
import streamlit_authenticator as stauth

# Login-Konfiguration
with open("config.yaml") as file:
    config = yaml.safe_load(file)

authenticator = stauth.Authenticate(
    config["credentials"],
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"]
)

name, authentication_status, username = authenticator.login("Login", location="main")

if authentication_status is False:
    st.error("Benutzername oder Passwort ist falsch.")
if authentication_status is None:
    st.warning("Bitte einloggen.")
if authentication_status:

    authenticator.logout("Logout", "sidebar")
    st.sidebar.success(f"Eingeloggt als {name}")

    # Datei-Pfade
    KUNDEN_DATEI = "data/kunden.csv"
    KOMMENTAR_DATEI = "data/kommentare.csv"

    ALLE_TAGS = ["LIT2Trade", "LIT-EA", "LIT-Signal", "Interessent", "gekauft"]
    ALLE_PRODUKTE = ["Kein Produkt", "Telegram-Signale", "Expert Advisor", "Komplettpaket"]

    def lade_daten():
        if not os.path.exists("data"):
            os.makedirs("data")
        if not os.path.isfile(KUNDEN_DATEI):
            pd.DataFrame(columns=["ID", "Vorname", "Nachname", "E-Mail", "Adresse", "Produkt", "Tags"]).to_csv(KUNDEN_DATEI, index=False)
        if not os.path.isfile(KOMMENTAR_DATEI):
            pd.DataFrame(columns=["Kunden-ID", "Datum", "Kommentar"]).to_csv(KOMMENTAR_DATEI, index=False)
        return pd.read_csv(KUNDEN_DATEI), pd.read_csv(KOMMENTAR_DATEI)

    def speichere_kunde(kunde):
        df = pd.read_csv(KUNDEN_DATEI)
        neue_id = df["ID"].max() + 1 if not df.empty else 1
        kunde["ID"] = neue_id
        df = pd.concat([df, pd.DataFrame([kunde])])
        df.to_csv(KUNDEN_DATEI, index=False)
        return neue_id

    def speichere_kommentar(kunden_id, kommentar_text):
        df = pd.read_csv(KOMMENTAR_DATEI)
        neuer_kommentar = {
            "Kunden-ID": kunden_id,
            "Datum": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Kommentar": kommentar_text
        }
        df = pd.concat([df, pd.DataFrame([neuer_kommentar])])
        df.to_csv(KOMMENTAR_DATEI, index=False)

    st.title("👤 Kundenmanagement Tool")

    kunden_df, kommentar_df = lade_daten()

    st.sidebar.header("📥 Neuen Kunden anlegen")
    with st.sidebar.form("neuer_kunde"):
        vorname = st.text_input("Vorname")
        nachname = st.text_input("Nachname")
        email = st.text_input("E-Mail")
        adresse = st.text_area("Adresse")
        produkt = st.selectbox("Produkt", ALLE_PRODUKTE)
        tags = st.multiselect("Tags", ALLE_TAGS)
        kommentar = st.text_area("Kommentar (optional)")
        submitted = st.form_submit_button("Speichern")

        if submitted and vorname and nachname and email:
            kunden_id = speichere_kunde({
                "Vorname": vorname,
                "Nachname": nachname,
                "E-Mail": email,
                "Adresse": adresse,
                "Produkt": produkt,
                "Tags": ";".join(tags)
            })
            if kommentar.strip():
                speichere_kommentar(kunden_id, kommentar.strip())
            st.success(f"Kunde {vorname} {nachname} wurde erfolgreich angelegt.")

    st.subheader("📋 Kundenübersicht")
    tag_filter = st.multiselect("🔎 Filter nach Tags", ALLE_TAGS)
    produkt_filter = st.multiselect("🔎 Filter nach Produkt", ALLE_PRODUKTE)

    gefiltert = kunden_df.copy()
    if tag_filter:
        gefiltert = gefiltert[gefiltert["Tags"].fillna("").str.contains("|".join(tag_filter))]
    if produkt_filter:
        gefiltert = gefiltert[gefiltert["Produkt"].isin(produkt_filter)]

    st.dataframe(gefiltert)

    st.subheader("💬 Kommentarhistorie")
    if not kunden_df.empty:
        kunden_auswahl = st.selectbox(
            "Kunde auswählen",
            kunden_df["ID"].astype(str) + " – " + kunden_df["Vorname"] + " " + kunden_df["Nachname"]
        )

        if kunden_auswahl:
            try:
                ausgewählte_id = int(kunden_auswahl.split("–")[0].strip())
                kommentare_kunde = kommentar_df[kommentar_df["Kunden-ID"] == ausgewählte_id]
                st.write(kommentare_kunde.sort_values("Datum", ascending=False).reset_index(drop=True))
            except Exception as e:
                st.error(f"Fehler bei der Auswahl des Kunden: {e}")
    else:
        st.info("❕ Noch keine Kunden vorhanden.")

