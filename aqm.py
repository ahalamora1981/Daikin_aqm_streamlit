import os, json
import pandas as pd

class AQM():

    def __init__(self, file_path):

        self.file_path = file_path

    def greeting(self, start_n, n_words_to_pass):
        
        path = os.path.join(os.getcwd(), self.file_path)
        file_path_list = [path + "/" + file for file in os.listdir(path) if file[-4:] == "json"]

        result = []

        for file_path in file_path_list[:]:

            with open(file_path, encoding="utf-8") as file:
                data = json.load(file)

            words = data["transcript_detailed"]["words"]

            greeting_words = "您好 / 大金 / 客服 / 请问 / 先生 / 女士 / 空调 / 为您服务 / 需要 / 帮助 / 售后 / 高兴"
            greeting_words = greeting_words.split("/")
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