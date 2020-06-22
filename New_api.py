from pixivpy3 import *
import sys
import time
import random
import traceback

class New_api(object):
    def __init__(self):
        self.api = ByPassSniApi()  # Same as AppPixivAPI, but bypass the GFW

    def require_appapi_hosts(self):
        self.api.require_appapi_hosts()

    def set_accept_language(self,char): 
        self.api.set_accept_language(char)            

    def login(self,USERNAME, PASSWORD):
        return self.api.login(USERNAME, PASSWORD)

    # 用户详情 
    def user_detail(self, user_id):
        self.randSleep()
        while True:
            try:
                M = self.api.user_detail(user_id)
            except:
 #                traceback.print_exc()
                self.randSleep(5,0)
            else:
                if M.error:
                    return 0
                else:
                    break        
        return M

    # 用户作品列表 
    def user_illusts(self, user_id, type='illust'):
        while True:
            try:
                M = self.api.user_illusts(user_id)
            except:
 #                traceback.print_exc()
                self.randSleep(5,0)
            else:
                break
        self.randSleep()
        return M

    # 返回作品列表的下一页
    def next_page_i(self, next_url):
         next_qs = self.api.parse_qs(next_url)
         while True:
             try:
                M = self.api.user_illusts(**next_qs)
             except:
 #                traceback.print_exc()
                self.randSleep(5,0)
             else:
                break
         self.randSleep()
         return M

    # 用户收藏作品列表 
    def user_bookmarks_illust(self, user_id, restrict='public'):
        while True:
            try:
                M = self.api.user_bookmarks_illust(user_id)
            except:
 #                traceback.print_exc()
                self.randSleep(5,0)
            else:
                break
        self.randSleep()
        return M

    # 返回收藏列表的下一页
    def next_page_b(self, next_url):
         next_qs = self.api.parse_qs(next_url)
         while True:
             try:
                M = self.api.user_bookmarks_illust(**next_qs)
             except:
 #                traceback.print_exc()
                self.randSleep(5,0)
             else:
                break
         self.randSleep()
         return M

    # 作品详情 (无需登录，同PAPI.works)
    def illust_detail(self, illust_id):
        while True:
            try:
                M = self.api.illust_detail(illust_id)
            except:
 #                traceback.print_exc()
                self.randSleep(5,0)
            else:
                break
        self.randSleep()
        return M

    # Following用户列表 
    def user_following(self, user_id, restrict='public', offset=None):
        while True:
            try:
                M = self.api.user_following(user_id, restrict='public', offset=None)
            except:
 #                traceback.print_exc()
                self.randSleep(5,0)
            else:
                break
        self.randSleep()
        return M

    # 返回关注列表的下一页
    def next_page_f(self, next_url):
         next_qs = self.api.parse_qs(next_url)
         while True:
             try:
                M = self.api.user_following(**next_qs)
             except:
 #                traceback.print_exc()
                self.randSleep(5,0)
             else:
                break
         self.randSleep()
         return M

    # 获取ugoira信息
    def ugoira_metadata(self, illust_id):
        while True:
            try:
                M = self.api.ugoira_metadata(illust_id)
            except:
 #              traceback.print_exc()
                self.randSleep(5,0)
            else:
                break
        self.randSleep()
        return M

    # 关注用户的新作
    # restrict: [public, private]
    def illust_follow(self, restrict='public'):
        self.api.illust_follow()
        self.randSleep()

    # 相关作品列表 
    def illust_related(self, illust_id):
        self.api.illust_related(illust_id)
        self.randSleep()

    # 插画推荐 (Home - Main) 
    # content_type: [illust, manga]
    def illust_recommended(self, content_type='illust'):
        self.api.illust_recommended()
        self.randSleep()

    # 作品排行
    # mode: [day, week, month, day_male, day_female, week_original, week_rookie, day_manga]
    # date: '2016-08-01'
    # mode(r18榜单需登录): [day_r18, day_male_r18, day_female_r18, week_r18, week_r18g]
    def illust_ranking(self, mode='day', date=None, offset=None):
        self.api.illust_ranking(mode='day', date=None, offset=None)
        self.randSleep()

    # 趋势标签 (Search - tags) 
    def trending_tags_illust(self):
        self.api.trending_tags_illust()
        self.randSleep()

    # 搜索 (Search) 
    # search_target - 搜索类型
    #   partial_match_for_tags  - 标签部分一致
    #   exact_match_for_tags    - 标签完全一致
    #   title_and_caption       - 标题说明文
    # sort: [date_desc, date_asc]
    # duration: [within_last_day, within_last_week, within_last_month]
    def search_illust(self, word, search_target='partial_match_for_tags', sort='date_desc', duration=None):
        self.api.search_illust(word, search_target='partial_match_for_tags', sort='date_desc', duration=None)
        self.randSleep()

    # 搜索小说 (Search Novel)
    # search_target - 搜索类型
    #   partial_match_for_tags  - 标签部分一致
    #   exact_match_for_tags    - 标签完全一致
    #   text                    - 正文
    #   keyword                 - 关键词
    # sort: [date_desc, date_asc]
    # start_date/end_date: 2020-06-01 (最长1年)
    def search_novel(self, word, search_target='partial_match_for_tags', sort='date_desc', start_date=None, end_date=None):
        self.api.search_novel(word, search_target='partial_match_for_tags', sort='date_desc', start_date=None, end_date=None)
        self.randSleep()

    # 用户搜索
    def search_user(self, word, sort='date_desc', duration=None):
        self.api.search_user(word, sort='date_desc', duration=None)
        self.randSleep()

    # 作品收藏详情 
    def illust_bookmark_detail(self, illust_id):
        self.api.illust_bookmark_detail(illust_id)
        self.randSleep()

    # 新增收藏
    def illust_bookmark_add(self, illust_id, restrict='public', tags=None):
        self.api.illust_bookmark_add(illust_id, restrict='public', tags=None)
        self.randSleep()

    # 删除收藏
    def illust_bookmark_delete(self, illust_id):
        self.api.illust_bookmark_delete(illust_id)
        self.randSleep()

    # 用户收藏标签列表
    def user_bookmark_tags_illust(self, restrict='public', offset=None):
        self.api.user_bookmark_tags_illust(restrict='public', offset=None)
        self.randSleep()

    # Followers用户列表 
    def user_follower(self, user_id, filter='for_ios', offset=None):
        self.api.user_follower(user_id, filter='for_ios', offset=None)
        self.randSleep()

    # 好P友 
    def user_mypixiv(self, user_id, offset=None):
        self.api.user_mypixiv(user_id, offset=None)
        self.randSleep()

    # 黑名单用户 
    def user_list(self, user_id, filter='for_ios', offset=None):
        self.api.user_list(user_id, filter='for_ios', offset=None)
        self.randSleep()

    #休眠随机的时间
    def randSleep(self, base = 1, rand = 0.5):
        time.sleep(base + rand*random.random())