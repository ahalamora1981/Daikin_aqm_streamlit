import pysenti
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os

class AQM():

    def __init__(self, file_path):

        self.file_path = file_path
        self.greeting_words = ["您好", "大金", "客服", "请问", "先生", "女士", "空调", "为您服务", "需要", "帮助", "售后", "高兴"]
        self.closing_words = ["感谢", "您", "大金", "支持", "关注", "祝您", "生活", "愉快", "再见"]

    def greeting(self, start_n, n_words_to_pass):
        
        path = os.path.join(os.getcwd(), self.file_path)
        file_path_list = [path + "/" + file for file in os.listdir(path) if file[-4:] == "json"]

        result = []

        for file_path in file_path_list[:]:

            with open(file_path, encoding="utf-8") as file:
                data = json.load(file)

            words = data["transcript_detailed"]["words"]

            greeting_words = self.greeting_words
            greeting_words = [word.strip() for word in greeting_words]
            greeting_words = set(greeting_words)

            # 开场白的适用词数（前N个词）        
            start_n_words = [word["w"] for word in words if word["sp"]=="Agent"][:start_n]

            # 判断命中了几个开场白词语
            n_words_said = 0
            words_said = ""
            gw = greeting_words.copy()
            for word in start_n_words:
                if word in gw:
                    n_words_said += 1
                    gw.remove(word)
                    words_said += ", " + word if words_said else word

            data["aqm"] = {}
            data["aqm"]["greeting"] = {}
            data["aqm"]["greeting"]["words_said"] = words_said
            data["aqm"]["greeting"]["n_words_said"] = n_words_said

            # 开场白合格需要多少个词语
            # n_words_to_pass

            # 打分
            if n_words_said >= n_words_to_pass:
                data["aqm"]["greeting"]["score"] = 1
            else:
                data["aqm"]["greeting"]["score"] = 0

            result.append({
                "contact_id": data["metadata"]["ContactID"],
                "aqm": data["aqm"]
            })

        return result


    def closing(self, last_n, n_words_to_pass):

        path = os.path.join(os.getcwd(), self.file_path)
        file_path_list = [path + "/" + file for file in os.listdir(path) if file[-4:] == "json"]

        result = []

        for file_path in file_path_list[:]:

            with open(file_path, encoding="utf-8") as file:
                data = json.load(file)

            words = data["transcript_detailed"]["words"]

            closing_words = self.closing_words
            closing_words = [word.strip() for word in closing_words]
            closing_words = set(closing_words)

            # 开场白的适用词数（前N个词）        
            last_n_words = [word["w"] for word in words if word["sp"]=="Agent"][-last_n:]

            # 判断命中了几个开场白词语
            n_words_said = 0
            words_said = ""
            gw = closing_words.copy()
            for word in last_n_words:
                if word in gw:
                    n_words_said += 1
                    gw.remove(word)
                    words_said += ", " + word if words_said else word

            data["aqm"] = {}
            data["aqm"]["closing"] = {}
            data["aqm"]["closing"]["words_said"] = words_said
            data["aqm"]["closing"]["n_words_said"] = n_words_said

            # 开场白合格需要多少个词语
            # n_words_to_pass

            # 打分
            if n_words_said >= n_words_to_pass:
                data["aqm"]["closing"]["score"] = 1
            else:
                data["aqm"]["closing"]["score"] = 0

            result.append({
                "contact_id": data["metadata"]["ContactID"],
                "aqm": data["aqm"]
            })

        return result


    def pace(self, min_words, pace_to_pass):
        
        path = os.path.join(os.getcwd(), self.file_path)
        file_path_list = [path + "/" + file for file in os.listdir(path) if file[-4:] == "json"]

        result = []

        for file_path in file_path_list:

            with open(file_path, encoding="utf-8") as file:
                data = json.load(file)

            pace_max = 0
            n_words = 0
            w = ""
            s = 0
            e = 0

            for sentence in data["plainTextTime"]["verbatims"]:
                

                if sentence["sp"] == "Agent":
                    words = "".join(sentence["w"].split())

                    if len(words) >= min_words:
                        pace = round(len(words) * 1000 / (sentence["e"] - sentence["s"]), 2)

                        if pace > pace_max:
                            pace_max = pace
                            n_words = len(words)
                            w = sentence["w"]
                            s = sentence["s"]
                            e = sentence["e"]

            data["aqm"] = {}
            data["aqm"]["pace"] = {}
            data["aqm"]["pace"]["pace_max"] = pace_max
            data["aqm"]["pace"]["n_words"] = n_words
            data["aqm"]["pace"]["words"] = w
            data["aqm"]["pace"]["start"] = s
            data["aqm"]["pace"]["end"] = e
            
            if pace_max <= pace_to_pass:
                data["aqm"]["pace"]["score"] = 1
            else:
                data["aqm"]["pace"]["score"] = 0

            result.append({
                "contact_id": data["metadata"]["ContactID"],
                "aqm": data["aqm"]
            })

        return result
            

    def sentiment(self):

        path = os.path.join(os.getcwd(), "calls")
        files = os.listdir(path)

        result = {
        "counts": {},
        "negative_calls": {},
        "positive_calls": {},
        "short_calls": {},
        "all_calls": {}
        }

        num_total_calls = 0
        num_negative_calls = 0
        num_positive_calls = 0
        num_short_calls = 0

        for file in files:
            with open(os.path.join("calls", file), "r", encoding="utf-8") as f:
                data = json.load(f)
            text = data["plainText"]
            score = pysenti.classify(text)

            num_total_calls += 1

            text = text.replace(" ", "")
            text = text.replace("\n", " ")

            result["all_calls"][file[:-5]] = {
                "metadata": {
                    "extension": data["metadata"]["String_extension"]
                },
                "score": int(score["score"]),
                "text": text
            }
            
            if len(text) <= 10:
                num_short_calls += 1
                result["short_calls"][file[:-5]] = {
                    "metadata": {
                        "extension": data["metadata"]["String_extension"]
                    },
                    "score": int(score["score"]),
                    "text": text
                }
            elif score["score"] >= 0:
                num_positive_calls += 1
                result["positive_calls"][file[:-5]] = {
                    "metadata": {
                        "extension": data["metadata"]["String_extension"]
                    },
                    "score": int(score["score"]),
                    "text": text
                }
            else:
                num_negative_calls += 1
                result["negative_calls"][file[:-5]] = {
                    "metadata": {
                        "extension": data["metadata"]["String_extension"]
                    },
                    "score": int(score["score"]),
                    "text": text
                }

        result["counts"]["num_total_calls"] = num_total_calls
        result["counts"]["num_negative_calls"] = num_negative_calls
        result["counts"]["num_positive_calls"] = num_positive_calls
        result["counts"]["num_short_calls"] = num_short_calls

        return result


if __name__=="__main__":
    
    aqm = AQM(file_path="calls")
    greeting_scores = aqm.greeting(20, 5)
    print(greeting_scores)

    df = pd.DataFrame(columns=["通话ID", "是否合格", "命中词语", "命中词语数量"])

    for index, item in enumerate(greeting_scores[:2]):
        df.loc[index, "通话ID"] = item["contact_id"]
        if item["aqm"]["greeting"]["score"]:
            df.loc[index, "是否合格"] = "合格"
        else:
            df.loc[index, "是否合格"] = "不合格"
        df.loc[index, "命中词语"] = item["aqm"]["greeting"]["words_said"]
        df.loc[index, "命中词语数量"] = item["aqm"]["greeting"]["n_words_said"]

    print(df)