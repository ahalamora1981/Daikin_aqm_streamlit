import streamlit as st
import pandas as pd
import altair as alt
import matplotlib.pyplot as plt
import seaborn as sns
from aqm import AQM
from get_file import get_file


st.set_page_config(layout='wide')

# Set Seaborn/Matplotlib Font (disable due to not working on Streamlit cloud)
rc = {'font.sans-serif': 'Consolas',
    'axes.unicode_minus': False}
sns.set(context='notebook', style='ticks', rc=rc)

st.header("大金空调 AQM Demo")

# Layout into 2 columns with width ratio of "2:1"
col1, col2 = st.columns([7, 3])

# Layout sidebar
with st.sidebar:
    aqm_type = st.selectbox("质检点类型", ["开始语", "结束语", "语速"], index=0)
    uploaded_file = st.file_uploader("上传ZIP压缩包", type="zip")
    
    # When file is upload, do greeting scoring and show the result
    if uploaded_file is not None:

        # Save zip file to current folder and unzip it
        file_path = get_file(uploaded_file)

        aqm = AQM(file_path)

        if aqm_type == "开始语":
            start_n = st.slider("开始语适用范围（词数）", 0, 40, 20)
            n_words_to_pass = st.slider("合格所需词数", 0, 10, 3)
            greeting_scores = aqm.greeting(start_n, n_words_to_pass)
            aqm_type_en = "greeting"
        elif aqm_type == "结束语":
            last_n = st.slider("结束语适用范围（词数）", 0, 40, 20)
            n_words_to_pass = st.slider("合格所需词数", 0, 10, 3)
            greeting_scores = aqm.closing(last_n, n_words_to_pass)
            aqm_type_en = "closing"

        df = pd.DataFrame(columns=["通话ID", "是否合格", "命中词语", "命中词语数量"])

        for index, item in enumerate(greeting_scores):
            df.loc[index, "通话ID"] = item["contact_id"]
            if item["aqm"][aqm_type_en]["score"]:
                df.loc[index, "是否合格"] = "合格"
            else:
                df.loc[index, "是否合格"] = "不合格"
            df.loc[index, "命中词语"] = item["aqm"][aqm_type_en]["words_said"]
            df.loc[index, "命中词语数量"] = item["aqm"][aqm_type_en]["n_words_said"]

        n_pass = (df["是否合格"]=="合格").sum()
        n_fail = (df["是否合格"]=="不合格").sum()
        n_total = n_pass + n_fail

        # Show greeting scoring table
        col1.subheader("打分结果：" + aqm_type)
        col1.dataframe(df, 800, 600)

        # Generate pass/fail table dataframe and show it
        col2.subheader("合格率统计：" + aqm_type)
        df_pass_table = pd.DataFrame([[n_pass, n_fail, n_total]], columns=["合格", "不合格", "通话总数"], index=["合格率："])
        col2.dataframe(df_pass_table, width=300)

        col2.markdown("---")

        # Generate pass/fail chart dataframe and show it
        df_pass = pd.DataFrame({
            '合格通话统计': ["合格", "不合格"],
            '数量': [n_pass, n_fail]
        })
        df_pass_chart = alt.Chart(df_pass, width=300, height=150).mark_bar().encode(
            y='合格通话统计',
            x='数量',
            color=alt.Color("合格通话统计", scale=alt.Scale(domain=["合格", "不合格"],
                                                            range=['green', 'red']))
        )
        col2.altair_chart(df_pass_chart, use_container_width=False)

        # Generate countplot for "命中词语数量"
        fig = plt.figure(figsize=(5, 3))
        sns.countplot(x = "命中词语数量", data = df, palette="Set3")
        plt.xlabel("Count of Words Said")
        plt.ylabel("")
        col2.pyplot(fig)