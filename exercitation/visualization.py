import tkinter
from collections import Counter

import jieba
import pymongo
from wordcloud import WordCloud
import matplotlib.pyplot as plt


class Visualization:
    def __init__(self):
        """
        连接本地MangoDB获取已爬取数据
        """
        self.client = pymongo.MongoClient()
        self.db = self.client['DouBan_comment']
        self.film = '沙丘'
        self.collections = self.db[self.film]

    def gen_wordcloud(self):
        """
        生成词云，通过jieba库进行分词，利用WordCloud生产词云
        :return: None
        """
        try:
            comment_list = [i['detail_context'] for i in self.collections.find({}, {'_id': 0, 'detail_context': 1})]
            comment = ''.join(comment_list)
            wordlist = jieba.cut(comment)
            s = ' '.join(wordlist)
            stopword_list = [i.strip() for i in open('cn_stopwords.txt', 'r', encoding='UTF-8').readlines()]
            wc = WordCloud(width=1920, height=1080, font_path="simsun.ttf", background_color='white',
                           stopwords=stopword_list).generate(s)
            plt.imshow(wc)
            plt.axis('off')
            plt.show()
        except Exception:
            tkinter.messagebox.showerror(title='错误', message='数据不存在')

    def gen_pie(self):
        """
        生成评分占比的饼图
        :return:None
        """

        try:
            plt.rcParams['font.sans-serif'] = ['SimHei']  # 正常显示中文标签
            score = list(self.collections.find({}, {'_id': 0, 'star': 1}))
            data = Counter([i['star'] for i in score])
            data['未评分'] = data.pop(None)
            data = dict(sorted(data.items()))
            plt.pie(data.values(), wedgeprops={'width': 0.3}, autopct="%1.2f%%", labeldistance=2, pctdistance=0.55)
            plt.legend(labels=data.keys(), loc=(1, 0.6))
            plt.title("影片『{}』评分占比".format(self.film))
            plt.show()
        except Exception:
            tkinter.messagebox.showerror(title='错误', message='数据不存在')

    def gen_bar(self):
        """
        生成用户常居城市条形图
        :return:None
        """
        try:
            plt.rcParams['font.sans-serif'] = ['SimHei']  # 正常显示中文标签
            city = list(self.collections.find({}, {'_id': 0, 'city': 1}))
            data = Counter([i['city'] for i in city])
            data.pop(None)
            data = dict(data.most_common(8))
            plt.figure(figsize=(12, 6))
            plt.bar(data.keys(), data.values())
            for i, j in enumerate(data.values()):
                plt.text(i, j + 2, "%s" % j, ha="center")
            plt.ylabel('观影人数')
            plt.title("影片『{}』八大观影城市".format(self.film))
            plt.show()
        except Exception:
            tkinter.messagebox.showerror(title='错误', message='城市数据不存在')

    def gen_line(self):
        """
        生成评论时间折线图
        :return:None
        """
        try:
            plt.rcParams['font.sans-serif'] = ['SimHei']  # 正常显示中文标签
            time = list(self.collections.find({}, {'_id': 0, 'time': 1}))
            for d in time:
                d['time'] = d['time'].split()[0][:7]
            data = Counter([i['time'] for i in time])
            data = dict(sorted(data.items()))
            plt.figure(figsize=(12, 7))
            plt.plot(list(data.keys()), list(data.values()))
            plt.xticks(rotation=70)
            plt.ylabel('评论人数')
            plt.title("影片『{}』评论时间".format(self.film))
            plt.show()
        except Exception:
            tkinter.messagebox.showerror(title='错误', message='数据不存在')

    def update_film(self, film):
        """
        获取新数据
        :param film: 电影片名
        :return: None
        """
        self.film = film
        self.collections = self.db[self.film]


if __name__ == '__main__':
    visualization = Visualization()
    # visualization.gen_wordcloud()
    visualization.gen_pie()
    # visualization.gen_bar()
    # visualization.gen_line()
