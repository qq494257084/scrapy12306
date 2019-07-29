"""
    @author: liyaling
    @email: ts_liyaling@qq.com
    @date: {2019/7/29} {TIME}
"""
import datetime
import re
import json
import time

import scrapy


class ScrapyCheci(scrapy.Spider):
    # spider采集器的名字，要保证唯一性
    name = 'ScrapyCheci'
    # 当前采集的个数
    count = 1
    # 爬取日期
    dateCC = datetime.datetime.now().strftime("%Y%m%d")
    # 车次前面的字母
    headerCC = ["C", "G", "D", "Z", "T", "K"]
    # 当前采集车次字母的索引，indexCC < headerCC.length
    indexCC = 0
    # 车次后面的开始的数字，每次headerCC循环一次重置为1,最高90
    numberCC = 1
    # 是否将采集的网址写入到文件，以便于下次判断采集位置
    is_file = False
    # 是否采集完毕
    is_finish = False
    # 读取上次采集的位置
    read_line = []
    # 当前页数
    curr_page = 1
    #  1 天津政府采购 2	河北政府采购 3	山东政府采购 4	北京政府采购 5 全国政府采购
    source = "全国政府采购"
    days = 3
    # 要爬取的网址
    urls = [
        'https://search.12306.cn/search/v1/train/search',
    ]

    """
        spider初始化类
    """

    def __init__(self, name=None, **kwargs):
        super().__init__(name=None, **kwargs)

    """
        开始采集
    """

    def start_requests(self):
        # 读取上次采集的位置并清空
        try:
            f = open("last.txt", "r+", encoding="UTF-8")
            self.read_line = f.readlines(-1)
            for index, string in enumerate(self.read_line):
                self.read_line[index] = str(string).replace("\n", '')
            f.seek(0)
            f.truncate()
            f.close()
            f = open("result.json", "w", encoding="UTF-8")
            f.truncate()
            f.close()
        except IOError:
            pass
        # 要采集的网址

        for url in self.urls:
            yield scrapy.Request(url=self.urls[0] + "?keyword=" + self.headerCC[self.indexCC] + str(
                self.numberCC) + "&date=" + self.dateCC, callback=self.parse)

    """
        采集标题以及公告日期，然后进入页详细信息页
    """

    def parse(self, response):
        result = {}
        text = str(response.text)
        result_json = json.loads(text)
        if text.__len__() > 2 << 4 and "data" in result_json and result_json["data"].__len__() is not 0:
            data = list(result_json["data"])
            result["data"] = data
            yield result
        self.numberCC += 1
        if self.numberCC >= 100:
            self.indexCC += 1
            self.numberCC = 1
            if self.indexCC >= self.headerCC.__len__():
                return None
        url = self.urls[0] + "?keyword=" + self.headerCC[self.indexCC] + str(self.numberCC) + "&date=" + self.dateCC
        yield scrapy.Request(url=url, callback=self.parse, dont_filter=True)

    """
        采集规则
    """

    @staticmethod
    def extract_info(p_label):
        result = {}
        p_label = p_label.strip()
        if p_label.__len__() >= 1 << 8:
            return None
        regex_dict = {"projectName": "[^:：]*项目(?!代理)[^:：]*名[^:：]*[:：]+.+",
                      "contact": "[^:：]*项目(?!代理)[^:：]*联系人[^:：]*[:：]+.+",
                      "contactTelephone": "[^:：]*项目(?!代理)[^:：]*[电话手机方式]+[^:：]*[:：]+[^:：]*[\\d]",
                      "deadlineTime": "[^:：]*标[^:：]*截[^:：]*[日期时]+[^:：]*[:：]+.+",
                      "projectCode": "[^:：]*项目[^:：]*编号[^:：]*[:：]+.+",
                      "address": "([^:：]*采购(?!代理)[^:：]*[地址][^:：]*[:：]+.+)|(^地址[:：].+)",
                      "purchasingUnit": "[^:：]*采购[^:：]*[单位]+[名称全]*[^:：]*[:：]+.+",
                      "budget": "[^:：]*预[^:：]*[金额元币]+[^:：]*[:：]+.+",
                      "bidTime": "[^:：]*开标[^:：]*[日期时]+[^:：]*[:：]+.+",
                      "proxyAddress": "[^:：]*代理[^:：]*[地址位置]+[^:：]*[:：]+.+",
                      "file": "[^:：]*\\.(doc|jpg|png|pdf|DOC|PDF)[^:：]*",
                      "proxyContact": "[^:：]*代理[^:：]*[联系人]+[^:：]*[:：]+.+",
                      "proxyUnit": "[^:：]*代理[^:：]*[单位机构]+[^:：]*[:：]+.+",
                      "proxyTelephone": "[^:：]*代理[^:：]*[电话手机]+[^:：]*[:：]+[^:：]*[\\d]+"}
        for key, value in regex_dict.items():
            r = re.fullmatch(value, p_label)
            if r:
                if key.__eq__("file"):
                    result = {key: p_label}
                    return result
                else:
                    result = {key: re.split("[:：]+", p_label, 1), }
                    return result
        else:
            return None

    """
        采集结束标志判断
    """

    def finish_judge(self, response):
        to_be_finished = -1
        if self.is_finish:
            to_be_finished = 1
        return to_be_finished

    """
        格式化日期
        如：2019年03月04日 14:09 至 2019年03月11日 23:59(双休日及法定节假日除外)
        将会被格式化为2019-03-11 23:59
        如果不匹配任何正则表达式，则日期将默认为None
    """

    @staticmethod
    def date_format(item):
        item1 = item
        for key, value in item.items():
            if key.__contains__("Time") or key.__contains__("time"):
                pattern_str1 = "[^:：]*([\\d]{4})[^\\d\\s]([\\d]{1,2})[^\\d\\s]([\\d]{1,2})[日号]?[^\\d]" \
                               "*?([\\d]{1,2})[^\\d\\s]([\\d]{1,2})[^\\d\\s]([\\d]{1,2})[秒]?[^\\d]*"
                pattern_str2 = "[^:：]*([\\d]{4})[^\\d\\s]([\\d]{1,2})[^\\d\\s]([\\d]{1,2}" \
                               ")[日号]?[^\\d]*?([\\d]{1,2})[^\\d\\s]([\\d]{1,2})[分]?[^\\d]*"
                pattern_str3 = "[^:：]*([\\d]{4})[^\\d\\s]([\\d]{1,2})[^\\d\\s]([\\d]{1,2})[日号]?[^\\d]*"
                if re.fullmatch(pattern_str1, item[key]):
                    pattern = re.compile(pattern_str1)
                    item1[key] = datetime.datetime.strptime(pattern.sub("\\1-\\2-\\3 \\4:\\5:\\6", item[key]),
                                                            "%Y-%m-%d %H:%M:%S").__str__()
                elif re.fullmatch(pattern_str2, item[key]):
                    pattern = re.compile(pattern_str2)
                    item1[key] = datetime.datetime.strptime(pattern.sub("\\1-\\2-\\3 \\4:\\5:00", item[key]),
                                                            "%Y-%m-%d %H:%M:%S").__str__()
                elif re.fullmatch(pattern_str3, item[key]):
                    pattern = re.compile(pattern_str3)
                    item1[key] = datetime.datetime.strptime(pattern.sub("\\1-\\2-\\3", item[key]), "%Y-%m-%d").__str__()
                else:
                    item1[key] = None
        return item1
