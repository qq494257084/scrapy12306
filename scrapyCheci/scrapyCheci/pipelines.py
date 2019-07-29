# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import pymysql
import uuid
import datetime

"""
    @author: liyaling
    @email: ts_liyaling@qq.com
    @date: {2019/7/29} {TIME}
"""


class ScrapycheciPipeline(object):
    all_che_ci = list()

    conn = pymysql.connect(host="localhost", user="root",
                           password="LIyaling15", database="12306", charset="utf8")
    cursor = conn.cursor()

    def process_item(self, item, spider):
        sql_values = ""
        if item is not None and "data" in item and item["data"].__len__() is not 0:
            list_cc = list(item["data"])
            for d in list_cc:
                d = dict(d)
                if d["station_train_code"] not in self.all_che_ci:
                    checi_uuid = uuid.uuid4().__str__().replace("-", "").upper()
                    sql_values += ("('" + checi_uuid + "','" + d[
                        "station_train_code"] + "','" + d["from_station"] + "','" + d[
                                       "to_station"] + "','" + d["train_no"] + "'," + d[
                                       "total_num"] + ",'" + d[
                                       "date"] + "','" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "'),")
                    # sql_values += ("(checi_uuid='" + checi_uuid + "',station_train_code='" + d[
                    #     "station_train_code"] + "',from_station='" + d["from_station"] + "',to_station='" + d[
                    #                    "to_station"] + "',train_no='" + d["train_no"] + "',total_num=" + d[
                    #                    "total_num"] + ",start_date='" + d[
                    #                    "date"] + "',create_time='" + datetime.datetime.now().__str__() + "'),")
                    self.all_che_ci.append(d["station_train_code"])
            sql = "insert into CHECI ( checi_uuid,station_train_code,from_station,to_station,train_no,total_num," \
                  "start_date,create_time ) values" + sql_values[:-1]
            try:
                self.cursor.execute(sql)
                self.conn.commit()
            except:
                self.conn.rollback()
            print(item)
            return item
