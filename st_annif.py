import streamlit as st
import pandas as pd
import numpy as np
from annif import rest, create_flask_app


def list_annif_projects():
    app = create_flask_app
    with app().app_context():
        projects = rest.list_projects()
    return projects


def get_annif_projects():
    projects = list_annif_projects()
    models = [i['project_id'] for i in projects[0]['projects']]
    return models


def run_annif_suggest(model_name, input_text):
    app = create_flask_app
    with app().app_context():
        results = rest._suggest(project_id=model_name, documents=[{'text': input_text}], parameters={})
    return results


models = get_annif_projects()


def main():
    if not "valid_inputs_received" in st.session_state:
        st.session_state["valid_inputs_received"] = False

    st.set_page_config(
        layout="centered", page_title="US Congress Bill's committees suggester.", page_icon=":)"
    )
    st.title("US Congress bill's text committees suggester")
    selected_model = st.selectbox(
        "Please select annif model:",
        models,
        index=2,
        disabled=True,
    )

    st.write("")
    st.markdown(
        f"""

    Classify Bill's committees using the Annif model: "{selected_model}" trained on the US Congress dataset.

    """
    )
    st.write("")
    with st.form(key="my_form"):

        text = st.text_area(
            "Enter Bill's text to classify",
            height=200,
            key="1",
        )

        text = text.strip()


        submit_button = st.form_submit_button(label="Submit")
    
    if not submit_button and not st.session_state.valid_inputs_received:
        st.stop()

    elif submit_button and not text:
        st.warning("Bill's text cannot be empty.")
        st.session_state.valid_inputs_received = False
        st.stop()
    
    elif submit_button or st.session_state.valid_inputs_received:

        if submit_button:

            st.session_state.valid_inputs_received = True

            results = run_annif_suggest(selected_model, text)

            df = pd.DataFrame(results[0]['results'])
            f = [f"{row:.2%}" for row in df["score"]]
            df["Classification scores"] = f

            df.rename(columns={"label": "Committee", "uri": "URL"}, inplace=True)

            df.drop(["notation", "score"], inplace=True, axis=1)

            df.index = np.arange(1, len(df) + 1)

            df = df[['Committee', 'Classification scores', 'URL']]

            st.success("✅ Done!")

            st.caption("")
            st.markdown("### Check the results!")
            st.caption("")

            st.data_editor(
                df,
                column_config={
                    "URL": st.column_config.LinkColumn("URL")
                },
                hide_index=True,
            )


if __name__ == "__main__":
    main()
