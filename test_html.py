import streamlit as st

st.set_page_config(page_title="HTML Test")

st.html("""
<style>
.test-card {
    background: #111827;
    color: white;
    padding: 40px;
    border-radius: 20px;
    text-align: center;
    font-family: Arial, sans-serif;
}

.test-title {
    font-size: 40px;
    font-weight: bold;
}

.test-text {
    margin-top: 10px;
    font-size: 18px;
}
</style>

<div class="test-card">
    <div class="test-title">🚆 SplitSnap</div>
    <div class="test-text">HTML IS WORKING ✓</div>
</div>
""")

st.write("Normal Streamlit content")