import tkinter as tk
from tkinter import ttk

from Crawler_DouBan_Comment import Crawler

from visualization import Visualization


class Gen_Gui:
    def __init__(self, vision: Visualization):
        """
        初始化TK控件
        """
        self.windows = tk.Tk()
        self.windows.title('热点影片豆瓣的影评数据分析')
        self.windows.geometry('280x440')
        self.vision = vision

    def select(self):
        """
        选择影片
        :return: None
        """

        def get_film_name(*args):
            film = select_film.get()
            self.vision.update_film(film)

        select_film = tk.StringVar()
        combobox = ttk.Combobox(self.windows, textvariable=select_film, width=31)
        combobox['values'] = self.vision.db.list_collection_names()
        combobox.bind("<<ComboboxSelected>>", get_film_name)
        combobox.place(x=15, y=210)

    def crawler(self):
        """
        爬虫功能整合
        :return:
        """
        label = ttk.Label(self.windows, text="请输入影片名称:")
        label.place(x=15, y=20)

        entry = ttk.Entry(self.windows, width=33)
        entry.place(x=15, y=45)

        label = ttk.Label(self.windows, text="是否爬取城市数据")
        label.place(x=15, y=75)

        iv_command = tk.BooleanVar()
        radio_button_true = ttk.Radiobutton(self.windows, text='是', value=True, variable=iv_command)
        radio_button_false = ttk.Radiobutton(self.windows, text='否', value=False, variable=iv_command)
        radio_button_true.place(x=130, y=75)
        radio_button_false.place(x=170, y=75)

        def craw():
            try:
                film = entry.get()
                city = iv_command.get()
                crawler = Crawler(film, city)
                crawler.run()
                self.select()
            except Exception:
                tk.messagebox.showerror(title='错误', message="未知错误，可能由于爬取过多IP被封锁，请更换IP重试")

        button = ttk.Button(self.windows, text="开始爬取", command=craw, width=33)
        button.place(x=15, y=110)

    def analysis(self):
        """
        可视化功能整合
        :return: None
        """
        pie = ttk.Button(self.windows, text="评分占比", command=self.vision.gen_pie, width=18)
        pie.place(x=60, y=250)

        bar = ttk.Button(self.windows, text="常居城市", command=self.vision.gen_bar, width=18)
        bar.place(x=60, y=290)

        line = ttk.Button(self.windows, text="评论时间", command=self.vision.gen_line, width=18)
        line.place(x=60, y=330)

        wordcloud = ttk.Button(self.windows, text="词云", command=self.vision.gen_wordcloud, width=18)
        wordcloud.place(x=60, y=370)

    def run(self):
        """
        启动程序
        :return:None
        """
        self.select()
        self.crawler()
        self.analysis()
        self.windows.mainloop()


if __name__ == '__main__':
    visualization = Visualization()
    gui = Gen_Gui(visualization)
    gui.run()
