import streamlit as st
import pandas as pd
import re

# --------------------------
# Load preprocessed data
# --------------------------
@st.cache_data
def load_data():
    df_cleaned = pd.read_csv("C:/Users/dell/python_coding/cleaned_data.csv", dtype={'id': 'int32', 'city_main': 'category'})
    df_encoded = pd.read_csv("C:/Users/dell/python_coding/encoded_with_clusters.csv", dtype={'id': 'int32'})
    return df_cleaned, df_encoded

df_cleaned, df_encoded = load_data()

# --------------------------
# Streamlit UI
# --------------------------
st.title("🍴 Restaurant Recommendation System")

# Dropdowns
cities = df_cleaned["city_main"].dropna().unique()

# Dropdown should use unique single cuisines
all_cuisines = sorted(
    set(
        cuisine.strip()
        for entry in df_cleaned["cuisine"].dropna()
        for cuisine in re.split(r',\s*', entry)
    )
)

selected_city = st.selectbox("Select City", cities)

#  Multi-select for cuisines (single values)
selected_cuisines = st.multiselect("Select Cuisine(s)", all_cuisines, default=[])

min_rating = st.slider("Minimum Rating", 0.0, 5.0, 3.5, 0.1)
max_cost = st.number_input("Maximum Cost", min_value=0, value=500)

top_n = st.slider("Number of Recommendations", 1, 20, 5)

# --------------------------
# Recommendation Logic
# --------------------------
def recommend_restaurants(city, cuisines, min_rating, max_cost, top_n):
    # Step 1: filter by city first
    city_restaurants = df_cleaned[df_cleaned["city_main"] == city]

    # Step 2: filter by cuisines (optional) -> check full cuisine column
    if cuisines:
        mask = city_restaurants["cuisine"].apply(lambda x: any(c.lower() in x.lower() for c in cuisines))
        city_restaurants = city_restaurants[mask]

    if city_restaurants.empty:
        return pd.DataFrame()

    # Step 3: get clusters for restaurants in this city
    cluster_ids = df_encoded[df_encoded["id"].isin(city_restaurants["id"])]["cluster"].unique()

    # Step 4: get restaurants in the same clusters
    cluster_restaurants = df_encoded[df_encoded["cluster"].isin(cluster_ids)]

    # Step 5: map back to df_cleaned AND restrict again to selected city 
    recommendations = df_cleaned[
        (df_cleaned["id"].isin(cluster_restaurants["id"])) &
        (df_cleaned["city_main"] == city)  # enforce city restriction
    ]

    # Step 6: apply filters
    recommendations = recommendations[
        (recommendations["rating"] >= min_rating) &
        (recommendations["cost"] <= max_cost)
    ]

    # Step 7: filter cuisines again if selected
    if cuisines:
        recommendations = recommendations[
            recommendations["cuisine"].apply(lambda x: any(c.lower() in x.lower() for c in cuisines))
        ]

    # Step 8: sort and return
    return recommendations.sort_values(by="rating", ascending=False).head(top_n)


# --------------------------
# Show Recommendations
# --------------------------
if st.button("Get Recommendations"):
    results = recommend_restaurants(selected_city, selected_cuisines, min_rating, max_cost, top_n)

    if results.empty:
        st.warning(" No matching restaurants found.")
    else:
        st.success(f"Top {len(results)} Recommendations")
        st.dataframe(
            results[["id", "name", "rating", "rating_count", "cost", "cuisine", "address", "city_main"]]
        )
