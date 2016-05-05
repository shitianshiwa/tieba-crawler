#coding=utf-8
from scrapy import Request
from cookieSpider import CookieSpider
from dbSpider import DbSpider
from scrapy.selector import Selector
from dirbot.settings import TIEBA_NAMES_LIST
from dirbot.settings import TASK_TAG
from dirbot.items import Post
import logging

class PostSpider(CookieSpider, DbSpider):

    """Docstring for PostSpider. """

    name = 'post'
    request_url_tmpl = 'http://tieba.baidu.com/f?ie=utf-8&kw=%s'

    def _extract_post_id(self, href):# href = /p/123456789
        return href.split('/')[-1]
        #try:
        #    return href.split('/')[-1]
        #except Exception, e:
        #    return -1#没有ID的帖子就是广告，在pipeline里要过滤掉

    def parse_page(self, response):
        """TODO: Docstring for parse_page.

        :response: TODO
        :returns: TODO

        """
        return self._parse_posts(response);

    def url_from_row(self, row):
        """TODO: Docstring for url_from_row.

        :row: TODO
        :returns: TODO

        """
        return self.request_url_tmpl % (row[0])

    def query_some_records(self, start_index = 0, num = 50):
        """TODO: Docstring for query_some_records.

        :start_index: TODO
        :num: TODO
        :returns: TODO

        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT name FROM tieba WHERE tag='%s'
        """ %  (
            TASK_TAG
        ))# 去重
        return cursor.fetchall()

    def _parse_posts(self, response):
        """TODO: Docstring for _parse_posts.

        :response: TODO
        :returns: TODO

        """
        items= []
        tieba_name = response.meta['row'][0]
        post_item_sels = Selector(response).css('#thread_list>li')

        for sel in post_item_sels:
            item = Post()
            item['id'] = self._extract_post_id(sel.css('.j_th_tit a::attr(href)').extract_first())
            #logging.debug('post id: %s' % (sel.css('.j_th_tit a::attr(href)').extract_first()))

            item['tieba_name'] = tieba_name
            item['title'] = sel.css('.j_th_tit a::text').extract_first()# 有时标题过长会被截断，在帖子回复爬虫里再爬一遍完整的标题
            item['reply_num'] = sel.css('.threadlist_rep_num::text').extract_first()# 这里有可能是‘推广’,而非数字，在pipeline里过滤一遍
            item['author_name'] = sel.css('.tb_icon_author a::text').extract_first()
            item['body'] = sel.css('.threadlist_detail .threadlist_abs_onlyline::text').extract_first()
            #遇到取不到帖子内容的情况，有可能是广告或者其它类型的无ID的贴子
            if item['body'] is None:
                item['body'] = ''
            else:
                item['body'] = item['body'].strip()#去掉回车和空格
            #item['post_time'] = sel.css('') #这里拿不到发贴时间，只有最后回复时间
            item['tag'] = TASK_TAG
            items.append(item)

        return items

    def next_page(self, response):
        """TODO: Docstring for next_page.

        :response: TODO
        :returns: TODO

        """
        if len(Selector(response).css('#frs_list_pager .next')):
            #贴吧的分页有的不是完整的链接
            next_page_url = Selector(response).css('#frs_list_pager .next::attr(href)').extract_first()
            if -1 != next_page_url.find('http://tieba.baidu.com'):
                return next_page_url
            else:
                return 'http://tieba.baidu.com' + next_page_url
        else:
            return False
