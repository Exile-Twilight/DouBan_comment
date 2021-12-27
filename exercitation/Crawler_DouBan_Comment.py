import random
import time
import tkinter

import pymongo
import requests
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED
from lxml import etree


class Crawler:
    def __init__(self, film, city):
        """
        初始化各类对象并设置请求参数
        """
        self.film = film
        self.base_url = "https://www.douban.com/search?source=suggest&q={}".format(self.film)
        self.cookies = {
            'cookie': 'bid=q0MLddV1zwU; gr_user_id=66a4600e-ff47-484d-bcfb-8a375cfbd6d9; ll="118220"; douban-fav-remind=1; __yadk_uid=JUeAbnIUFxaHtkNN4Sv3xoZzGySWXseE; viewed="30351288_11577300_34951096_4889838_30434690_30459548_10583161_6966465"; push_noty_num=0; push_doumail_num=0; __utmv=30149280.23431; ct=y; __utmz=30149280.1638521468.41.30.utmcsr=baidu|utmccn=(organic)|utmcmd=organic; dbcl2="234312237:edn4lvh+9Q8"; ck=MacJ; ap_v=0,6.0; _pk_ref.100001.8cb4=["","",1638771259,"https://www.baidu.com/link?url=7YlqyeSUtH5MDZ1bUmQZIeiVaYjJ-0nXoaSNPwk1O7FUIi6qcjMLnPyzAAEIY_NIfvdYZqqbaaDMp3OS5FZee_&wd=&eqid=e378e2a0000acba90000000461a9d94e"]; _pk_ses.100001.8cb4=*; __utma=30149280.1534172975.1622599128.1638758013.1638771260.44; __utmc=30149280; __utmt=1; _pk_id.100001.8cb4=ec7476c951550e0e.1622613105.32.1638771263.1638758041.; __utmb=30149280.4.10.1638771260'}
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36 Edg/96.0.1054.29'}
        self.db = pymongo.MongoClient()['DouBan_comment'][self.film]
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.task_list = []  # 进程列表
        self.page_num = 1
        self.comment_url = ''  # 短评详情通用url前缀
        self.get_user_city = city  # 选择是否获取用户常居城市数据

    def get_content(self, url):
        """
        向服务器发送get请求
        :param url: 需要请求的URL
        :return: 服务器返回响应的二进制数据
        """
        time.sleep(random.random())  # 防止以一定频率请求服务器，被判断为程序操作
        content = requests.get(url, headers=self.headers, cookies=self.cookies)
        return content.content

    def search(self):
        """
        请求豆瓣搜索页
        :return: 返回响应的第一条搜索结果
        """
        content = self.get_content(self.base_url)  # 获取搜索页结果
        temp = etree.HTML(content)
        detail_url = temp.xpath('//div[@class="title"]//a/@href')[0]
        print("影片详情", detail_url)
        film = self.get_content(detail_url)
        return film

    def parser(self, url: str):
        """
        解析每一短评详情页，提取所需数据
        :param url:短评详情页URL
        :return:None
        """
        print('正在爬取第{}页'.format(self.page_num))
        print('当前URL：{}'.format(url))
        self.page_num += 1

        content = self.get_content(url)
        html = etree.HTML(content)

        info_list = html.xpath('//div[@class="comment"]//span[@class="comment-info"]')
        detail_list = html.xpath('//div[@class="comment"]//span[@class="short"]/text()')
        like_list = html.xpath('//span[@class="comment-vote"]/span/text()')

        one_page_data = []  # 单页全部数据
        for info, like, detail, in zip(info_list, like_list, detail_list):
            try:  # 用户已评分
                comment = {
                    'user': info.xpath('./a/text()')[0],
                    'star': Crawler.convert(info.xpath('./span[2]/@title')[0]),
                    'time': info.xpath('./span[3]/@title')[0],
                    'like': like,
                    'detail_context': detail}

            except:  # 用户未评分
                comment = {
                    'user': info.xpath('./a/text()')[0],
                    'star': None,
                    'time': info.xpath('./span[2]/@title')[0],
                    'like': like,
                    'detail_context': detail}
            finally:
                # 若需获得用户城市数据，将访问500个URL，导致程序执行缓慢，并造成IP封锁。
                if self.get_user_city:
                    try:
                        comment['city'] = etree.HTML(self.get_content(info.xpath('./a/@href')[0])).xpath(
                            '//div[@class="user-info"]/a/text()')[0]
                    except:
                        comment['city'] = None
                one_page_data.append(comment)

        print(one_page_data)
        self.save_to_mangoDB(one_page_data)

    def save_to_mangoDB(self, item):
        """
        将爬取的数据存放到MangoDB中
        :param item: 解析后的单页(20条)数据列表
        :return: None
        """
        self.db.insert_many(item)

    def run(self):
        """
        启动爬虫程序，创建并启动多线程进行爬取
        :return: None
        """
        print("正在爬取【" + self.film + "】影片数据...")
        film = self.search()
        html = etree.HTML(film)
        comment_url = html.xpath('//*[@id="comments-section"]/div[1]/h2/span/a/@href')[0]
        temp = str(comment_url)
        self.comment_url = temp[:-9]
        print("影片全部短评", self.comment_url)

        '''构造URL参数，通过submit提交执行的方法到线程池中，直到所有线程任务全部执行完成'''
        url_list = [self.comment_url + '?start={}&limit=20&sort=new_score&status=P&percent_type='.format(str(i)) for i
                    in range(0, 500, 20)]
        self.task_list = [self.executor.submit(self.parser, url) for url in url_list]
        wait(self.task_list, return_when=ALL_COMPLETED)
        tkinter.messagebox.showinfo(title='提示', message='数据爬取成功')

    @staticmethod
    def convert(s):
        """
        HTML与页面显示的类别进行等价转换
        :param s: HTML源码中评价（文字）表示
        :return: 转换后星级表示
        """
        convert_dict = {'推荐': "4星", "还行": "3星",
                        "力荐": "5星", "较差": "2星",
                        "很差": "1星"}
        s = convert_dict[s]
        return s


if __name__ == '__main__':
    crawler = Crawler("八佰", False)
    crawler.run()
