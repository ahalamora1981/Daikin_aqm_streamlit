import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from package.aqm import AQM
from package.get_file import get_file


st.set_page_config(layout='wide')

# Set Seaborn/Matplotlib Font (disable due to not working on Streamlit cloud)
rc = {'font.sans-serif': 'Consolas',
    'axes.unicode_minus': False}
sns.set(context='notebook', style='ticks', rc=rc)
sns.set_theme(style="darkgrid", font_scale=1.1)

@st.cache
def create_df_pace(scores):
    df = pd.DataFrame(columns=["通话ID", "是否合格", "最大语速", "句子", "句子长度", "时间戳"])

    for index, item in enumerate(scores):
        df.loc[index, "通话ID"] = item["contact_id"]

        if item["aqm"][aqm_type_en]["score"]:
            df.loc[index, "是否合格"] = "合格"
        else:
            df.loc[index, "是否合格"] = "不合格"

        df.loc[index, "最大语速"] = item["aqm"][aqm_type_en]["pace_max"]
        df.loc[index, "句子"] = item["aqm"][aqm_type_en]["words"]
        df.loc[index, "句子长度"] = item["aqm"][aqm_type_en]["n_words"]
        df.loc[index, "时间戳"] = item["aqm"][aqm_type_en]["start"]//1000

    return df

@st.cache
def create_df_greeting_closing(scores):
    df = pd.DataFrame(columns=["通话ID", "是否合格", "命中词语", "命中词语数量"])

    for index, item in enumerate(scores):
        df.loc[index, "通话ID"] = item["contact_id"]

        if item["aqm"][aqm_type_en]["score"]:
            df.loc[index, "是否合格"] = "合格"
        else:
            df.loc[index, "是否合格"] = "不合格"

        df.loc[index, "命中词语"] = item["aqm"][aqm_type_en]["words_said"]
        df.loc[index, "命中词语数量"] = item["aqm"][aqm_type_en]["n_words_said"]

    return df

@st.cache
def create_df_sentiment(scores):
    df = pd.DataFrame(columns=["通话ID", "分机号", "情感分", "文本"])

    for index, (key, value) in enumerate(scores["all_calls"].items()):
        df.loc[index, "通话ID"] = key
        df.loc[index, "分机号"] = value["metadata"]["extension"]
        df.loc[index, "情感分"] = value["score"]
        df.loc[index, "文本"] = value["text"]

    return df

@st.cache
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode("gbk")


st.header("大金空调 AQM Demo")

# Layout into 2 columns with width ratio of "7:3"
col1, col2 = st.columns([3, 2])

# Layout sidebar
with st.sidebar:
    st.image("./img/daikin_logo.png")
    st.write("**Version 0.1.0**  -- Developed by Johnny Tao")
    aqm_type = st.selectbox("质检点类型", ["开始语", "结束语", "语速", "情感分析"], index=0)
    uploaded_file = st.file_uploader("上传ZIP压缩包", type="zip")
    
# When file is upload, do greeting scoring and show the result
if uploaded_file is not None:

    # Save zip file to current folder and unzip it
    file_path = get_file(uploaded_file)

    aqm = AQM(file_path)

    if aqm_type in ["开始语", "结束语", "语速"]:

        if aqm_type == "开始语":

            with st.sidebar:
                start_n = st.slider("开始语适用范围（词数）", 0, 40, 20)
                n_words_to_pass = st.slider("合格所需词数", 0, 10, 3)
                greeting_words = st.multiselect(
                    "开始语词汇",
                    aqm.greeting_words,
                    aqm.greeting_words)

            aqm.greeting_words = greeting_words
            scores = aqm.greeting(start_n, n_words_to_pass)
            aqm_type_en = "greeting"

            df = create_df_greeting_closing(scores)

        elif aqm_type == "结束语":

            with st.sidebar:
                last_n = st.slider("结束语适用范围（词数）", 0, 40, 20)
                n_words_to_pass = st.slider("合格所需词数", 0, 10, 3)
                closing_words = st.multiselect(
                    "结束语词汇",
                    aqm.closing_words,
                    aqm.closing_words)

            aqm.closing_words = closing_words
            scores = aqm.closing(last_n, n_words_to_pass)
            aqm_type_en = "closing"

            df = create_df_greeting_closing(scores)

        elif aqm_type == "语速":
            
            with st.sidebar:
                min_words = st.slider("单句词数下限", 1, 20, 10)
                pace_to_pass = st.slider("合格语速", 1.0, 10.0, 5.0, 0.5)
                
            scores = aqm.pace(min_words, pace_to_pass)
            aqm_type_en = "pace"

            df = create_df_pace(scores)

        n_pass = (df["是否合格"]=="合格").sum()
        n_fail = (df["是否合格"]=="不合格").sum()
        n_total = n_pass + n_fail

        # Show scoring table
        col1.subheader("打分结果：" + aqm_type)
        col1.dataframe(df, 800, 600)

        csv = convert_df(df)
        col1.download_button(
            label="Download data as CSV",
            data=csv,
            file_name= aqm_type_en + ".csv",
            mime='text/csv',
        )

        # Generate pass/fail table dataframe and show it
        col2.subheader("合格率统计：" + aqm_type)
        df_pass_table = pd.DataFrame([[n_pass, n_fail, n_total]], columns=["合格", "不合格", "通话总数"], index=["合格率："])
        col2.dataframe(df_pass_table, width=300)

        col2.markdown("---")

        # Generate countplot for "命中词语数量"
        fig = plt.figure(figsize=(5, 3))

        if aqm_type == "语速":
            sns.histplot(x = "最大语速", data = df, palette="Set3")
            plt.xlabel("Count of Speaking Pace")
            plt.ylabel("")
            col2.pyplot(fig)
        else:
            sns.countplot(x = "命中词语数量", data = df, palette="Set3")
            plt.xlabel("Count of Words Said")
            plt.ylabel("")
            col2.pyplot(fig)

    elif aqm_type == "情感分析":

        score = aqm.sentiment()
        df = create_df_sentiment(score)

        score_mean = df.groupby("分机号")["情感分"].mean().astype(int).rename("Sentiment")
        score_count = df.groupby("分机号")["情感分"].count().rename("Counts")

        df_mean = pd.concat([score_mean, score_count], axis=1)
        df_mean.index = df_mean.index.rename("Extension")
        df_mean = df_mean.reset_index()

        col1.subheader("打分结果：" + aqm_type)
        col1.dataframe(df, 800, 600)

        csv = convert_df(df)

        col1.download_button(
            label="Download data as CSV",
            data=csv,
            file_name='Sentiment.csv',
            mime='text/csv',
        )

        col2.subheader("情感得分末10名：")

        fig, (ax1, ax2) = plt.subplots(nrows=2, figsize=(9,10))
        sns.barplot(data=df_mean.sort_values("Sentiment")[:10], ax=ax1, x="Sentiment", y="Extension", palette="rocket")
        sns.barplot(data=df_mean.sort_values("Sentiment")[:10], ax=ax2, x="Counts", y="Extension", palette="mako")
        ax1.set_title("Average Sentiment per Employee (Bottom 10)")
        ax2.set_title("Call Counts per Employee (Sentiment Bottom 10)")
        col2.pyplot(fig)
