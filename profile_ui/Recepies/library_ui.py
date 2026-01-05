# profile/library_ui.py
import streamlit as st
from .library_css import inject_library_css

# --- Recipes and Shopping lists page ---


def render_library_page():
    """Render the recipes and shopping lists library page."""
    # Inject custom CSS for this page
    inject_library_css()
    st.header("Recipes & shopping lists")

    recipes = st.session_state.get("saved_recipes", [])
    weekly_list = st.session_state.get("weekly_shopping_list")
    last_list = st.session_state.get("last_shopping_list")

    # --- Recipes ---
    st.subheader("My recipes")
    if not recipes:
        st.info("No recipes saved yet. You can save recipes from the chatbot.")
    else:
        for i, recipe_md in enumerate(recipes, start=1):
            with st.expander(f"Recipe {i}", expanded=False):
                st.markdown(recipe_md)

    st.write("---")

    # --- Shopping lists ---
    st.subheader("Shopping lists")

    if not weekly_list and not last_list:
        st.info(
            "No shopping lists generated yet. "
            "You can create them from the Plan or Chatbot pages."
        )
    else:
        if weekly_list:
            with st.expander("Weekly shopping list", expanded=True):
                st.markdown(weekly_list)

        if last_list:
            title = st.session_state.get(
                "last_recipe_shopping_title",
                "Shopping list from last recipe/answer",
            )
            with st.expander(title, expanded=False):
                st.markdown(last_list)

