import re
import os
import os.path as op
import sys
import json
import threading
import colorama
from colorama import init,Fore,Back,Style
from New_api import *
from Downloader import *
from RSA import *

init(autoreset=True)

class Pixiv(object):
    def __init__(self):
        self.root = os.getcwd()
        self.cache_path = "{}\\cache\\".format(self.root)
        if not op.exists(self.cache_path):
            os.makedirs(self.cache_path)

        self.User_Info = self.Load_List("User_Info")
        if not self.User_Info:
            self.User_Info = {"User_Name": "", "Password": "", "Collect_Progress": 0, "Download_Path": "", "Upadte_Mode": True}
        self.USER_ID = ""
        self.USER_NAME = ""      
        self.api = New_api()
        self.RSA = rsacrypt(self.root)
        self.Log_in()
            
    def Log_in(self):
        if not self.User_Info["User_Name"]:
            self.User_Info["User_Name"] = input("请输入用户名：")
        if not self.User_Info["Password"]:    
            #对输入的密码进行加密
            self.User_Info["Password"] = self.RSA.encrypt(input("请输入密码："))
        self.api.require_appapi_hosts()
        self.api.set_accept_language('zh-CN')
        Login_Messgae = self.api.login(self.User_Info["User_Name"], self.RSA.decrypt(self.User_Info["Password"])).response
        self.USER_ID = Login_Messgae.user.id
        self.USER_NAME = Login_Messgae.user.name
        print("Welcome Back {}".format(self.USER_NAME))
        
    #从本地读取json文件
    def Load_List(self, File_Name):
        path = "{}{}_cache".format(self.cache_path, File_Name)
        if op.isfile(path):
            try:
                with open(path, 'r') as Cache_File:
                    L = json.load(Cache_File)
            except:
                # 缓存文件格式出现问题，删除缓存文件
                os.remove(path)
                return []
            else:              
                return L
        else:
            return []
         
    #保存指定变量到json文件
    def Save_List(self, File_Name, Target_List):
        with open("{}{}_cache".format(self.cache_path, File_Name), 'w') as Cache_File:      
            json.dump(Target_List, Cache_File, cls = MyEncoder)
        
    def Get_Follow_List(self):  
        # 如果存在缓存文件，则从本地读取该用户的关注列表
        Follow_List = self.Load_List("{}_Follow_List".format(self.USER_NAME))
        # 向Api请求关注人数
        Total_Follow = self.api.user_detail(self.USER_ID).profile.total_follow_users
        # 如果关注人数未增加，不抓取新列表
        if Total_Follow == len(Follow_List):
            print("成功从缓存中进行加载, 你关注了 \033[33m{}\033[0m 名作者。\n".format(len(Follow_List)))
            return
        elif op.isfile("{}{}_Follow_List_cache.json".format(self.cache_path, self.USER_NAME)):
                os.remove("{}{}_Follow_List_cache.json".format(self.cache_path, self.USER_NAME))
        Follow_List = []
        # 向Api请求关注清单
        json_result = self.api.user_following(self.USER_ID)
        while True:
            for users in json_result.user_previews:
                ID = users.user.id
                Name = self.Filter_Name(users.user.name)
                Follow_List.append([ID, Name])
            self.Save_List("{}_Follow_List".format(self.USER_NAME), Follow_List)
            print("\r已关注的作者列表正在收集中, 进度：\033[33m{}/{}\033[0m".format(len(Follow_List),Total_Follow), end="")
            # 如果当前页面为最后一页则退出循环
            if not json_result.next_url:
                break
            # 请求清单下一页
            json_result = self.api.next_page_f(json_result.next_url)

        self.User_Info["Collect_Progress"] = 0
        self.Save_List("User_Info", crawler.User_Info)
        print("\r已关注的作者列表收集完成, 你关注了 \033[33m{}\033[0m 名作者。\n".format(len(Follow_List)))            

    def Collect_Illust_Info(self, Illust_Info, ID = ""):
        if ID:
            Illust_Info = self.api.illust_detail(ID).illust        
        # 提取出有用信息存入字典
        Illust_Dict = {"ID": str(Illust_Info.id), "Title": Illust_Info.title,"Illust_Date": "".join(list(filter(str.isdigit, Illust_Info.create_date)))[:8],
                       "Caption": Illust_Info.caption[:50], "Tags": Illust_Info.tags,
                       "Ugoira": True if Illust_Info.type == "ugoira" else False, 
                       "Muti_Page": True if Illust_Info.page_count > 1 else False, "is_block": False,
                       "Image_Urls": Illust_Info.meta_single_page["original_image_url"] if Illust_Info.page_count == 1 else Illust_Info.meta_pages
                       }
        # 对初步提取出的信息进行精简化，并进行分析，过滤掉不必下载的内容
        Illust_Dict = self.Filter(Illust_Dict)
        return Illust_Dict       

    def Filter(self, Illust_Dict):
        Tag = Illust_Dict["Tags"]
        if not Tag:    
            Illust_Dict["is_block"] = True
            return Illust_Dict

        try:
            Tag[0]["name"]
        except:
            pass
        else:
            for i in range(len(Tag)):
                if Tag[i]["translated_name"] is not None:
                    Tag[i] = Tag[i]["translated_name"]
                else:
                    Tag[i] = Tag[i]["name"]

            if Illust_Dict["Muti_Page"]:
                for i in range(len(Illust_Dict["Image_Urls"])):
                    Illust_Dict["Image_Urls"][i] = Illust_Dict["Image_Urls"][i]["image_urls"]["original"]
            elif Illust_Dict["Ugoira"]:
                Ugoira_Data = self.api.ugoira_metadata(Illust_Dict["ID"]).ugoira_metadata
                Illust_Dict["Image_Urls"] = [Ugoira_Data.zip_urls["medium"], Ugoira_Data.frames[0]["delay"]]

        path = self.root + "\\Pixiv_Crawler_Filter.json"
        if op.isfile(path):
            with open(path, 'r') as Cache_File:
                Filter_Dict = json.load(Cache_File)
        if not Filter_Dict:
            Filter_Dict = {"Illust_Date": 20180101, "Caption": "C[0-9]{1,2}|サンプ|原作",
                           "Title" :"抱き枕|単行本|コミ|品書|永遠娘|例大祭|C[0-9]{1,2}|宣伝|紹介|お知らせ|総集編|商業告知|サンプル",
                           "Black_List": ["LINE stickers", "sticker", "creator's stickers", "oshinagaki", "manga", "comic", "Comike",
                                          "summer Comiket", "练习", "冬CM", "草图", "刀剑乱舞", "讲座", "抱枕", "notification", "四格漫画",
                                          "抱枕套", "Sunshine Creation", "绘图方法", "作画过程", "腐向", "轻小说", "汇总", "绘图方法",
                                          "アイマスクリーチャー"]}
            with open(self.root + "\\Pixiv_Crawler_Filter.json", 'w') as Cache_File:      
                json.dump(Filter_Dict, Cache_File)


        # 利用正则对作品标题进行处理
        Title = Illust_Dict["Title"].replace("|","")
        Title = Title.replace("\\","")
        Title = re.sub(r'[*]|[/]|[:]|[>]|[<]|["]',"",Title)
        Illust_Dict["Title"] = re.sub(r'[?]',"？",Title)
#         = re.sub(r'[(].{1,}[)]',"",Title)
        # 根据关键词决定是否下载该图片
        Illust_Dict["is_block"] = False
        if int(Illust_Dict["Illust_Date"]) < Filter_Dict["Illust_Date"]:
            Illust_Dict["is_block"] = True
            return Illust_Dict
        if (not self.ReMatch("新刊表紙", Illust_Dict["Title"])) and self.ReMatch("新刊", Illust_Dict["Title"]):
            Illust_Dict["is_block"] = True
            return Illust_Dict
        if self.ReMatch(Filter_Dict["Title"], Illust_Dict["Title"]):
            Illust_Dict["is_block"] = True
            return Illust_Dict
        if self.ReMatch(Filter_Dict["Caption"], Illust_Dict["Caption"]):
            Illust_Dict["is_block"] = True
            return Illust_Dict
        for Keyword in Filter_Dict["Black_List"]:
            if Tag.count(Keyword):
            # 包含黑名单中tag的图片直接排除
                Illust_Dict["is_block"] = True
                return Illust_Dict
        return Illust_Dict

    def Get_Illust_List(self, Artist_ID):
        if Artist_ID == "342929":
            print("该用户已注销")
            return 0
        # 利用用户ID向Api请求作者的信息
        Artist_Detail = self.api.user_detail(Artist_ID)
        if Artist_Detail:
            Name = self.Filter_Name(Artist_Detail.user.name)
            Total_Illusts = 30 if self.User_Info["Upadte_Mode"] else Artist_Detail.profile.total_illusts

            Catch_Name = "({}){}_Illust_List".format(Artist_ID, Name)
            Illust_List = self.Load_List(Catch_Name)
            # 如果发现新作品则重新获取一次作品列表
            if Total_Illusts == len(Illust_List) - 2:
                for i in range(2,len(Illust_List)):
                    Illust_List[i] = self.Filter(Illust_List[i])
                self.Save_List(Catch_Name, Illust_List)
                print("成功从缓存中加载作者 \033[32m({}){}\033[0m 的作品列表，共有 \033[33m{}\033[0m 副作品。".format(Artist_ID, Name, Total_Illusts))
                return 1
            Illust_List = [Artist_ID, Name]

            # 利用用户ID向Api请求作品列表
            json_result = self.api.user_illusts(Artist_ID)       
            while True:
                for Illust_Info in json_result.illusts:   
                    Illust_Dict = self.Collect_Illust_Info(Illust_Info)
                    Illust_List.append(Illust_Dict)
                self.Save_List(Catch_Name, Illust_List)
                print("\r作者 \033[32m({}){}\033[0m 的作品信息正在收集中, 进度：\033[33m{}/{}\033[0m".format(Artist_ID, Name,len(Illust_List) - 2, Total_Illusts), end="")
                if not json_result.next_url or self.User_Info["Upadte_Mode"]:
                    break
                # 请求清单下一页
                json_result = self.api.next_page_i(json_result.next_url)              
                    
            print("\r作者 \033[32m({}){}\033[0m 的全部作品收集完成，共有 \033[33m{}\033[0m 副作品。".format(Artist_ID, Name, Total_Illusts))
            return 1
        else:
            print("\未获得ID为 \033[32m{}\033[0m 的作者信息，该用户的账号可能已被停用。。".format(Artist_ID))
            return 0


    def Get_Bookmark_List(self):
        Total_Illust_Bookmarks = self.api.user_detail(self.USER_ID).profile.total_illust_bookmarks_public
        # 利用用户ID向Api请求收藏列表
        Catch_Name = "Bookmark_List"      
        Illust_List = self.Load_List(Catch_Name)
        # 如果发现新作品则重新获取一次作品列表
        if Total_Illust_Bookmarks == len(Illust_List):
            print("成功从缓存中加载用户的收藏列表，共有 \033[33m{}\033[0m 副作品。".format(Total_Illust_Bookmarks))
            return
        Illust_List = []

        # 利用用户ID向Api请求收藏列表
        json_result = self.api.user_bookmarks_illust(self.USER_ID)       
        while True:
            for Illust_Info in json_result.illusts:
                Illust_Dict = self.Collect_Illust_Info(Illust_Info)
                Illust_List.append(Illust_Dict)
            self.Save_List(Catch_Name, Illust_List)
            print("用户的收藏列表正在收集中, 进度：\033[33m{}/{}\033[0m".format(len(Illust_List), Total_Illust_Bookmarks))
            if not json_result.next_url:
                break
            # 请求清单下一页
            json_result = self.api.next_page_b(json_result.next_url)              
                    
        print("用户的收藏列表收集完成，共有 \033[33m{}\033[0m 副作品。".format(Total_Illust_Bookmarks))

    def ReMatch(self, Re, str):
        if re.search(Re, str) is not None:
            return True
        else:
            return False

    def Filter_Name(self, Name):
        Name = re.sub(r'[@＠/🔞■◆].{1,}',"",Name)
        Name = re.sub(r'[Cc][0-9]{2,3}.{1,}',"",Name)
        Name = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fa5]+-,\'()',"",Name)
        return Name

def main():
    crawler = Pixiv()
    download = Downloader(crawler.User_Info["Download_Path"])
    # 用户界面
    while True:        
        print("\n功能：\n\t1. 下载单个作品\n\t2. 下载指定作者的作品\n\t3. 下载全部已收藏作品\n")
        print("\t4. 收集个人关注列表\n\t5. 下载全部已关注画师的作品\n")
        print("\t6. 设置（初次使用请进入设置修改下载路径）\n\t7. 退出程序")
        order = "2"
        order = input("请输入指令（1-7）：")
        os.system('cls')

        if order == "1":
            ID = input("请输入作品ID：")
            if int(ID) <= 0 :
                print("作品ID不正确")
                continue
            Illust_Dict = crawler.Collect_Illust_Info("", ID = ID)
            Name = "({}){}".format(Illust_Dict["ID"], Illust_Dict["Title"])
            if Illust_Dict["Muti_Page"]:
                url = Illust_Dict["Image_Urls"]
                name = []
                file_name = "{}{}".format(Name, url[0][-4:])
                for i in range(len(url)):
                    name.append("{}_P{}{}".format(file_name[:-4], i, file_name[-4:]))     
                for i in range(5,len(url),5):
                    Threads = []
                    for j in range(5):
                        Threads.append(threading.Thread(target = download.Pic_Download, args = (url[i+j-5], name[i+j-5])))
                    for Thread in Threads:  Thread.start()
                    for Thread in Threads:  Thread.join()                                                       
                print("图片集 {} 下载完成".format(file_name[:-4]))
            elif Illust_Dict["Ugoira"]:
                url = Illust_Dict["Image_Urls"][0]
                name = "{}@{}ms{}".format(Name, Illust_Dict["Image_Urls"][1], url[-4:])
                download.Gif_Threads_Pool.append(threading.Thread(target = download.Gif_Download, args = (url, name)))
                download.Gif_Threads_Pool[-1].start()
                if len(download.Gif_Threads_Pool) == 10:
                    for Thread in download.Gif_Threads_Pool:     Thread.join()
                    download.Gif_Threads_Pool = []
                #download.Gif_Download(url, name)
            else:
                url = Illust_Dict["Image_Urls"]
                name = "{}{}".format(Name, url[-4:])
                download.Pic_Download(url, name)
            

        elif order == "2":
            ID = "50258193"
            ID = input("请输入作者ID：")
            if int(ID) <= 0 :
                print("作者ID不正确")
                continue
            crawler.Get_Illust_List(ID)
            download.Artist_Download(ID)

        elif order == "3":
            crawler.Get_Bookmark_List()
            download.Bookemark_Download()

        elif order == "4":
            crawler.Get_Follow_List()
            print("收集完成，缓存文件位于{}\\cache\\文件夹下，请不要删除。".format(crawler.root))

        elif order == "5":
            crawler.Get_Follow_List()
            # 如果存在缓存文件，则从本地读取该用户的关注列表
            Follow_List = crawler.Load_List("{}_Follow_List".format(crawler.USER_NAME))
            for artist in Follow_List[crawler.User_Info["Collect_Progress"]:]:
                result = crawler.Get_Illust_List(artist[0])
                if result:
                    download.Artist_Download(artist[0])
                crawler.User_Info["Collect_Progress"] += 1
                crawler.Save_List("User_Info", crawler.User_Info)
                print("\n{}个画师已下载，剩余{}个\n".format(crawler.User_Info["Collect_Progress"], len(Follow_List) - crawler.User_Info["Collect_Progress"]))
            crawler.User_Info["Collect_Progress"] = 0
            crawler.Save_List("User_Info", crawler.User_Info)            
            print("全部下载完成")

        elif order == "6":
            while True:
                print("1. 登陆邮箱\n2. 密码\n3. 下载路径\n4. 变更下载模式\n5. 退出")
                order = input("请输入指令（1-4）：")
                if order == "1":
                    crawler.User_Info["User_Name"] = input("请输入：\n")
                    crawler.Save_List("User_Info", crawler.User_Info)
                elif  order == "2":
                    crawler.User_Info["Password"] = self.RSA.encrypt(input("请输入：\n"))
                    crawler.Save_List("User_Info", crawler.User_Info)
                elif  order == "3":
                    print("当前下载路径为： {}".format(crawler.User_Info["Download_Path"]))
                    Path = input("请输入：\n")
                    if Path:
                        if Path[-1] != "\\":
                            Path += "\\"
                        crawler.User_Info["Download_Path"] =  Path
                        download.Set_Path(Path)
                        crawler.Save_List("User_Info", crawler.User_Info)
                    print("当前下载路径为： {}\n".format(crawler.User_Info["Download_Path"]))
                elif  order == "4":
                    print("当前下载模式为： {}".format("增量更新" if crawler.User_Info["Upadte_Mode"] else "全部下载"))
                    if input("是否进行变更？(y/n)\n") == "y" :
                        crawler.User_Info["Upadte_Mode"] = not crawler.User_Info["Upadte_Mode"]
                        crawler.Save_List("User_Info", crawler.User_Info)
                        print("现在的下载模式为： {}".format("增量更新" if crawler.User_Info["Upadte_Mode"] else "全部下载"))
                elif  order == "5":
                    break

        elif order == "7":
            crawler.Save_List("User_Info", crawler.User_Info)
            break

if __name__ == '__main__':
    main()