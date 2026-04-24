import streamlit as st
import polars as pl

# Configuration de la page
st.set_page_config(page_title="Smart Data Auditor", layout="wide")

st.title("🛡️ Smart Data Auditor 2026")
st.markdown("---")

# --- 1. CHARGEMENT DES DONNÉES ---
uploaded_file = st.file_uploader("Étape 1 : Dépose ton fichier CSV", type="csv")

if uploaded_file:
    # Lecture des données
    df = pl.read_csv(uploaded_file)
    
    # Affichage du tableau
    st.write("### 📊 Aperçu des données brutes")
    st.dataframe(df.head(10))

    # --- 2. AUDIT & STATS ---
    st.sidebar.header("🛠️ Outils d'Audit")
    
    # Calcul des doublons
    num_duplicates = df.height - df.unique().height
    
    st.sidebar.metric("Lignes totales", df.height)
    st.sidebar.metric("Doublons détectés", num_duplicates)

    # --- 3. LOGIQUE DE NETTOYAGE (Ton expertise) ---
    st.write("### 🧹 Actions de Nettoyage")
    
    col_btn1, col_btn2 = st.columns(2)

    with col_btn1:
        if st.button("Supprimer les doublons"):
            df = df.unique()
            st.success("✅ Doublons supprimés !")

    with col_btn2:
        if st.button("Nettoyer les colonnes (Minuscules/Espaces)"):
            # Exemple de Python pur appliqué à Polars : on nettoie les noms de colonnes
            new_columns = [col.strip().lower() for col in df.columns]
            df.columns = new_columns
            st.success("✅ Colonnes formatées !")

    # Affichage du résultat après nettoyage
    st.write("### ✨ Données nettoyées")
    st.dataframe(df)

    # --- 4. EXPORT ---
    # Permettre au client de télécharger son fichier propre
    csv_data = df.write_csv()
    st.download_button(
        label="📥 Télécharger le fichier propre",
        data=csv_data,
        file_name="data_clean_2026.csv",
        mime="text/csv"
    )

else:
    st.info("👋 Bonjour ! Pour commencer, importe un fichier CSV dans le module ci-dessus.")


# --- 4. VISUALISATION AUTOMATIQUE ---
st.write("### 📈 Visualisation des données")

if st.checkbox("Afficher les graphiques"):
    # On sépare les colonnes par type
    num_cols = [col for col in df.columns if df[col].dtype in [pl.Int64, pl.Float64]]
    cat_cols = [col for col in df.columns if df[col].dtype == pl.String]

    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        if num_cols:
            st.write("#### Distribution des âges (ou autres nombres)")
            # Graphique simple avec Streamlit
            st.bar_chart(df.select(num_cols[0])) 
        else:
            st.info("Aucune donnée numérique pour un graphique.")

    with col_chart2:
        if cat_cols:
            st.write("#### Répartition par Ville (ou catégories)")
            # On compte les occurrences et on affiche
            counts = df[cat_cols[0]].value_counts()
            st.bar_chart(data=counts, x=cat_cols[0], y="count")

from langchain_experimental.agents import create_csv_agent
from langchain_openai import ChatOpenAI

# --- 5. MODULE IA ---
st.write("### 🤖 Interroger les données avec l'IA")

api_key = st.text_input("Entre ta clé API OpenAI pour discuter avec les données", type="password")

if api_key:
    user_question = st.text_input("Pose une question (ex: 'Quel est l'âge moyen ?' ou 'Affiche les lignes de Lyon')")
    
    if user_question:
        # Initialisation de l'IA
        llm = ChatOpenAI(api_key=api_key, model="gpt-4o", temperature=0)
        
        # Création de l'agent qui lit le CSV
        # Note: On repasse par le fichier temporaire pour l'agent
        agent = create_csv_agent(llm, uploaded_file, verbose=True, allow_dangerous_code=True)
        
        with st.spinner("L'IA réfléchit..."):
            response = agent.run(user_question)
            st.success("Réponse de l'IA :")
            st.write(response)
