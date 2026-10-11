import os

import anthropic
import polars as pl
import streamlit as st
from anthropic import beta_tool

st.set_page_config(page_title="Smart Data Auditor", page_icon="🛡️", layout="wide")

MODEL = "claude-opus-5-5"
MAX_RESULT_ROWS = 100


# --- ÉTAT DE LA SESSION ---
# Streamlit relance le script à chaque clic : on garde le tableau nettoyé
# et l'historique du chat dans st.session_state.
def init_state():
    defaults = {"df": None, "file_id": None, "file_name": "", "log": [], "chat": []}
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def read_csv(uploaded_file) -> pl.DataFrame:
    for encoding in ("utf8", "iso-8859-1"):
        try:
            uploaded_file.seek(0)
            return pl.read_csv(
                uploaded_file,
                encoding=encoding,
                infer_schema_length=10000,
                ignore_errors=True,
                try_parse_dates=True,
            )
        except Exception:
            continue
    raise ValueError("Impossible de lire le fichier (encodage ou séparateur non reconnu).")


def get_api_key() -> str | None:
    try:
        if "ANTHROPIC_API_KEY" in st.secrets:
            return st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        pass
    return os.environ.get("ANTHROPIC_API_KEY") or st.session_state.get("api_key_input") or None


def apply_cleaning(new_df: pl.DataFrame, message: str):
    st.session_state.df = new_df
    st.session_state.log.append(message)
    st.rerun()


init_state()

st.title("🛡️ Smart Data Auditor")
st.caption("Auditez, nettoyez et interrogez vos données en langage naturel.")

# --- 1. CHARGEMENT ---
SAMPLE_PATH = os.path.join(os.path.dirname(__file__), "sample_data", "ventes_exemple.csv")

uploaded_file = st.file_uploader("Déposez votre fichier CSV", type="csv")


def load_source(file, file_id: str, name: str):
    try:
        st.session_state.df = read_csv(file)
    except ValueError as e:
        st.error(str(e))
        st.stop()
    st.session_state.file_id = file_id
    st.session_state.file_name = name
    st.session_state.log = []
    st.session_state.chat = []


if uploaded_file is not None:
    if st.session_state.file_id != uploaded_file.file_id:
        load_source(uploaded_file, uploaded_file.file_id, uploaded_file.name)
elif st.session_state.file_id != "sample":
    st.info("👋 Pour commencer, importez un fichier CSV, ou testez avec notre fichier d'exemple.")
    if st.button("🧪 Essayer avec un fichier d'exemple (500 ventes)"):
        with open(SAMPLE_PATH, "rb") as f:
            load_source(f, "sample", "ventes_exemple.csv")
        st.rerun()
    st.stop()
else:
    st.caption("📄 Fichier d'exemple chargé : 500 ventes fictives, avec des doublons et des erreurs à nettoyer.")

df: pl.DataFrame = st.session_state.df

tab_audit, tab_clean, tab_viz, tab_ai = st.tabs(
    ["📋 Audit", "🧹 Nettoyage", "📈 Visualisation", "🤖 Questions à l'IA"]
)

# --- 2. AUDIT ---
with tab_audit:
    num_duplicates = df.height - df.unique().height
    total_nulls = sum(df.null_count().row(0))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Lignes", f"{df.height:,}".replace(",", " "))
    c2.metric("Colonnes", df.width)
    c3.metric("Doublons", num_duplicates)
    c4.metric("Valeurs manquantes", total_nulls)

    st.subheader("Qualité par colonne")
    quality = pl.DataFrame(
        {
            "colonne": df.columns,
            "type": [str(t) for t in df.dtypes],
            "valeurs manquantes": [df[c].null_count() for c in df.columns],
            "% manquant": [
                round(100 * df[c].null_count() / df.height, 1) if df.height else 0.0
                for c in df.columns
            ],
            "valeurs uniques": [df[c].n_unique() for c in df.columns],
        }
    )
    st.dataframe(quality, width="stretch", hide_index=True)

    st.subheader("Aperçu")
    st.dataframe(df.head(20), width="stretch")

# --- 3. NETTOYAGE ---
with tab_clean:
    st.write("Chaque action s'applique au tableau actuel et reste mémorisée.")

    col1, col2, col3, col4 = st.columns(4)

    if col1.button("Supprimer les doublons", width="stretch"):
        before = df.height
        df = df.unique(maintain_order=True)
        apply_cleaning(df, f"Doublons supprimés : {before - df.height} lignes")

    if col2.button("Normaliser les noms de colonnes", width="stretch"):
        df = df.rename({c: c.strip().lower().replace(" ", "_") for c in df.columns})
        apply_cleaning(df, "Noms de colonnes normalisés (minuscules, sans espaces)")

    if col3.button("Retirer les espaces en trop", width="stretch"):
        text_cols = [c for c, t in zip(df.columns, df.dtypes) if t == pl.String]
        df = df.with_columns(pl.col(text_cols).str.strip_chars())
        apply_cleaning(df, f"Espaces retirés dans {len(text_cols)} colonnes texte")

    if col4.button("Supprimer les lignes vides", width="stretch"):
        before = df.height
        df = df.filter(~pl.all_horizontal(pl.all().is_null()))
        apply_cleaning(df, f"Lignes entièrement vides supprimées : {before - df.height}")

    if st.session_state.log:
        st.success("\n".join(f"✅ {line}" for line in st.session_state.log))

    st.dataframe(df.head(50), width="stretch")

    st.download_button(
        label="📥 Télécharger le fichier nettoyé",
        data=df.write_csv(),
        file_name=f"{os.path.splitext(st.session_state.file_name)[0]}_clean.csv",
        mime="text/csv",
    )

# --- 4. VISUALISATION ---
with tab_viz:
    numeric_cols = [c for c, t in zip(df.columns, df.dtypes) if t.is_numeric()]
    category_cols = [c for c, t in zip(df.columns, df.dtypes) if t == pl.String]

    if not numeric_cols:
        st.info("Aucune colonne numérique à afficher.")
    else:
        v1, v2, v3 = st.columns(3)
        value_col = v1.selectbox("Valeur", numeric_cols)
        group_col = v2.selectbox("Regrouper par", ["(aucun)"] + category_cols)
        agg = v3.selectbox("Calcul", ["somme", "moyenne", "nombre"])

        if group_col == "(aucun)":
            st.bar_chart(df[value_col].drop_nulls().to_frame(), y=value_col)
        else:
            agg_expr = {
                "somme": pl.col(value_col).sum(),
                "moyenne": pl.col(value_col).mean(),
                "nombre": pl.col(value_col).count(),
            }[agg]
            chart_df = (
                df.group_by(group_col)
                .agg(agg_expr.alias(agg))
                .sort(agg, descending=True)
                .head(20)
            )
            st.bar_chart(chart_df, x=group_col, y=agg)

# --- 5. MODULE IA ---
with tab_ai:
    api_key = get_api_key()
    if not api_key:
        st.text_input(
            "Clé API Anthropic",
            type="password",
            key="api_key_input",
            help="Créez une clé sur console.anthropic.com. Elle n'est pas enregistrée.",
        )
        st.info("Ajoutez une clé API Anthropic pour poser des questions sur vos données.")
        st.stop()

    @beta_tool
    def run_sql(query: str) -> str:
        """Exécute une requête SQL en lecture seule sur le tableau `data` et renvoie le résultat.

        Args:
            query: Requête SQL (dialecte Polars SQL) portant sur la table `data`.
        """
        try:
            result = pl.SQLContext(data=st.session_state.df).execute(query, eager=True)
        except Exception as e:
            return f"Erreur SQL : {e}"
        note = ""
        if result.height > MAX_RESULT_ROWS:
            note = f"\n(résultat tronqué : {MAX_RESULT_ROWS} premières lignes sur {result.height})"
            result = result.head(MAX_RESULT_ROWS)
        with pl.Config(tbl_rows=MAX_RESULT_ROWS, tbl_cols=-1, fmt_str_lengths=80):
            return str(result) + note

    schema = "\n".join(f"- {c} ({t})" for c, t in zip(df.columns, df.dtypes))
    system_prompt = (
        "Tu es un data analyste. L'utilisateur a importé un fichier disponible dans la "
        f"table SQL `data` ({df.height} lignes). Colonnes :\n{schema}\n\n"
        "Utilise l'outil run_sql pour calculer les réponses à partir des données réelles ; "
        "n'invente jamais de chiffres. Réponds en français, de façon courte et claire, "
        "avec les chiffres clés et une phrase d'interprétation métier."
    )

    for msg in st.session_state.chat:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    question = st.chat_input("Ex. : Quels sont les 5 produits qui rapportent le plus ?")
    if question:
        st.session_state.chat.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Analyse en cours..."):
                client = anthropic.Anthropic(api_key=api_key)
                try:
                    runner = client.beta.messages.tool_runner(
                        model=MODEL,
                        max_tokens=16000,
                        system=system_prompt,
                        thinking={"type": "adaptive"},
                        output_config={"effort": "medium"},
                        betas=["server-side-fallback-2026-07-01"],
                        fallbacks="default",
                        tools=[run_sql],
                        messages=list(st.session_state.chat),
                    )
                    final = None
                    for message in runner:
                        final = message
                except anthropic.AuthenticationError:
                    st.error("Clé API invalide.")
                    st.session_state.chat.pop()
                    st.stop()
                except anthropic.RateLimitError:
                    st.error("Trop de requêtes, réessayez dans quelques secondes.")
                    st.session_state.chat.pop()
                    st.stop()
                except anthropic.APIStatusError as e:
                    st.error(f"Erreur de l'API ({e.status_code}) : {e.message}")
                    st.session_state.chat.pop()
                    st.stop()
                except anthropic.APIConnectionError:
                    st.error("Connexion à l'API impossible. Vérifiez votre connexion internet.")
                    st.session_state.chat.pop()
                    st.stop()

            if final is None or final.stop_reason == "refusal":
                answer = "Je ne peux pas répondre à cette question."
            else:
                answer = "\n".join(b.text for b in final.content if b.type == "text").strip()
                answer = answer or "Je n'ai pas trouvé de réponse."
            st.markdown(answer)
            st.session_state.chat.append({"role": "assistant", "content": answer})
