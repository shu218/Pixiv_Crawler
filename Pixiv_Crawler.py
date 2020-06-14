import re
import os
import os.path as op
import sys
import json
import colorama
from colorama import init,Fore,Back,Style
from New_api import *
from Downloader import *

init(autoreset=True)

class Pixiv(object):
    def __init__(self):
        self.root = sys.path[0]
        self.cache_path = "{}\\cache\\".format(self.root)
        if not op.exists(self.cache_path):
            os.makedirs(self.cache_path)

        self.User_Info = self.Load_List("User_Info")
        if not self.User_Info:
            self.User_Info = {"User_Name": "", "Password": "", "Collect_Progress": 0, "Download_Path": ""}
        self.USER_ID = ""
        self.USER_NAME = ""      
        self.api = New_api()
        self.Log_in()
            
    def Log_in(self):
        while not self.User_Info["User_Name"]:
            self.User_Info["User_Name"] = input("请输入用户名：")
        while not self.User_Info["Password"]:    
            self.User_Info["Password"] = input("请输入密码：")
        self.api.require_appapi_hosts()
        self.api.set_accept_language('zh-CN')
        Login_Messgae = self.api.login(self.User_Info["User_Name"], self.User_Info["Password"]).response
        self.USER_ID = Login_Messgae.user.id
        self.USER_NAME = Login_Messgae.user.name
        print("Welcome Back {}".format(self.USER_NAME))
        
    #从本地读取json文件
    def Load_List(self, File_Name):
        path = "{}{}_cache.json".format(self.cache_path, File_Name)
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
        with open("{}{}_cache.json".format(self.cache_path, File_Name), 'w') as Cache_File:      
            json.dump(Target_List, Cache_File)
        
    def Get_Follow_List(self):  
        # 如果存在缓存文件，则从本地读取该用户的关注列表
        Follow_List = self.Load_List("{}_Follow_List".format(self.USER_NAME))
        # 向Api请求关注人数
        Total_Follow = self.api.user_detail(self.USER_ID).profile.total_follow_users
        # 如果关注人数未增加，不抓取新列表
        if Total_Follow == len(Follow_List):
            print("成功从缓存中进行加载, 你关注了 {} 名作者。\n".format(len(Follow_List)))
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
                if not self.Find_Follow_ID(Follow_List, ID):
                    Follow_List.append([ID, Name])
            self.Save_List("{}_Follow_List".format(self.USER_NAME), Follow_List)
            print("已关注的作者列表正在收集中, 进度：{}/{}".format(len(Follow_List),Total_Follow))
            # 如果当前页面为最后一页则退出循环
            if not json_result.next_url:
                break
            # 请求清单下一页
            json_result = self.api.next_page_f(json_result.next_url)

        print("已关注的作者列表收集完成, 你关注了 {} 名作者。\n".format(len(Follow_List))) 
            
    def Find_Follow_ID(self, List, ID):
        for i in range(len(List)):
            if List[i][0] == ID:
                return i+1
        return False
            
    def Get_Follow_Illust_List(self):
        Follow_List = self.Load_List("{}_Follow_List".format(self.USER_NAME))
        if not Follow_List:
            print("请先获取关注列表")
            return

        n = len(Follow_List) - self.User_Info["Collect_Progress"]
        for Artist in Follow_List[self.User_Info["Collect_Progress"]:]:                  
            self.Get_Illust_List(Artist[0])
            self.User_Info["Collect_Progress"] += 1
            self.Save_List("User_Info", self.User_Info)
            n -= 1
            if n%10 == 0:
                print("剩余 {} 个作者\n".format(n))
        self.User_Info["Collect_Progress"] = 0
        self.Save_List("User_Info", self.User_Info)

    def Get_Illust_List(self, Artist_ID):
        # 利用用户ID向Api请求作者的信息
        Artist_Detail = self.api.user_detail(Artist_ID)
        try:
            Name = self.Filter_Name(Artist_Detail.user.name)
        except:
            return
        Total_Illusts = Artist_Detail.profile.total_illusts

        Catch_Name = "{}({})_Illust_List".format(Artist_ID, Name)
        Illust_List = self.Load_List(Catch_Name)
        # 如果发现新作品则重新获取一次作品列表
        if Total_Illusts == len(Illust_List) - 2:
            print("成功从缓存中加载作者 \033[32m{}\033[0m 的作品列表，共有 \033[33m{}\033[0m 副作品。\n".format(Name, Total_Illusts))
            return
        Illust_List = [Artist_ID, Name]

        # 利用用户ID向Api请求作品列表
        json_result = self.api.user_illusts(Artist_ID)       
        while True:
            for Illust_Info in json_result.illusts:            
                Illust_ID = str(Illust_Info.id)   
                if not self.Find_Illust_ID(Illust_List[2:], Illust_ID):
                    Title = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fa5]+-,\'()',' ',Illust_Info.title)
                    Title = re.sub(r'[(].{1,}[)]',' ',Title)
                    Illust_Dict = {"ID": Illust_ID, "Title": Title,"Illust_Date": ''.join(list(filter(str.isdigit, Illust_Info.create_date)))[:8], 
                                    "Image_Urls": Illust_Info.meta_single_page if Illust_Info.page_count == 1 else Illust_Info.meta_pages, 
                                    "Tags": Illust_Info.tags, "Page_Count": Illust_Info.page_count, "is_block": False}
                    Illust_Dict = self.Filter(Illust_Dict)
                    Illust_List.append(Illust_Dict)
            self.Save_List(Catch_Name, Illust_List)
            print("作者 \033[32m{}\033[0m 的作品信息正在收集中, 进度：\033[33m{}/{}\033[0m".format(Name,len(Illust_List) - 2, Total_Illusts))
            if not json_result.next_url:
                break
            # 请求清单下一页
            json_result = self.api.next_page_i(json_result.next_url)              
                    
        print("作者 \033[32m{}\033[0m 的全部作品收集完成，共有 \033[33m{}\033[0m 副作品。\n".format(Name, Total_Illusts))
            
    def Find_Illust_ID(self, Illust_List, Illust_ID):
        for Illust in Illust_List:
            if Illust['ID'] == Illust_ID:
                return True
        return False

    def Filter(self, Illust_Dict):
        Tag = Illust_Dict["Tags"]
        for i in range(len(Tag)):
            if Tag[i]["translated_name"] is not None:
                Tag[i] = Tag[i]["translated_name"]
            else:
                Tag[i] = Tag[i]["name"]


        if int(Illust_Dict["ID"]) < 20180101:
            Illust_Dict["is_block"] = True
        else:
            Black_List = ["LINE stickers", "sticker", "creator's stickers", "manga", "comic", "summer Comiket", "练习", 
                      "冬CM", "草图", "刀剑乱舞", "讲座", "抱枕", "notification", "四格漫画"]
            for Keyword in Black_List:
                if Tag.count(Keyword):
                    # 包含黑名单中tag的图片直接排除
                    Illust_Dict["is_block"] = True
        return Illust_Dict

    def Filter_Name(self, Name):
        Name = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fa5]+-,\'()',"",Name)
        Name = re.sub(r'[@＠/🔞■◆].{1,}',"",Name)
        Name = re.sub(r'[Cc][0-9]{2,3}.{1,}',"",Name)
        return Name

def main():
    crawler = Pixiv()
    download = Downloader(crawler.User_Info["Download_Path"])
    # 用户界面
    while True:        
        print("功能：\n\t1. 收集个人关注列表\n\t2. 收集指定作者的作品列表\n\t3. 收集全部已关注画师的作品列表")
        print("\t4. 下载单个作品\n\t5. 下载指定作者的作品\n\t6. 下载全部已关注画师的作品（未完工）")
        print("\t7. 设置\n\t8. 退出程序")
        order = "5"
        order = input("请输入指令（1-8）：")


        if order == "1":
            crawler.Get_Follow_List()
            print("收集完成，缓存文件位于{}\\cache\\文件夹下，请不要删除。".format(crawler.root))

        elif order == "2":
            ID = input("请输入作者ID：")
            if int(ID) <= 0 :
                print("作者ID不正确")
                continue
            crawler.Get_Illust_List(ID)
            print("收集完成，缓存文件位于{}\\cache\\文件夹下，请不要删除。".format(crawler.root))

        elif order == "3":
            crawler.Get_Follow_Illust_List()
            print("收集完成，缓存文件位于{}\\cache\\文件夹下，请不要删除。".format(crawler.root))

        elif order == "4":
            Pic_ID = input("请输入作品ID：")
            if int(Pic_ID) <= 0 :
                print("作品ID不正确")
                continue
            Pic_Detail = crawler.api.illust_detail(Pic_ID).illust
            Title = crawler.Filter_Name(Pic_Detail.title)
            Sub_Title = Pic_Detail.image_urls["large"][-3:]
            name = "({}){}.{}".format(Pic_ID, Title, Sub_Title)
            if Pic_Detail.page_count > 1:
                url = Pic_Detail.meta_pages
                download.Pic_Download(url, name, s = True)
            else:
                url = Pic_Detail.meta_single_page
                download.Pic_Download(url, name)

        elif order == "5":
            ID = "50258193"
            ID = input("请输入作者ID：")
            if int(ID) <= 0 :
                print("作者ID不正确")
                continue
            crawler.Get_Illust_List(ID)
            download.Artist_Download(ID)

#        elif order == "6":

        elif order == "7":
            while True:
                print("1. 登陆邮箱\n2. 密码\n3. 下载路径\n4. 退出")
                order = input("请输入指令（1-4）：")
                if order == "1":
                    crawler.User_Info["User_Name"] = input("请输入：\n")
                elif  order == "2":
                    crawler.User_Info["Password"] = input("请输入：\n")
                elif  order == "3":
                    print("当前下载路径为： {}".format(crawler.User_Info["Download_Path"]))
                    Path = input("请输入：\n")
                    crawler.User_Info["Download_Path"] =  Path + "\\"
                    download.Set_Path(Path)
                    print("当前下载路径为： {}".format(crawler.User_Info["Download_Path"]))
                elif  order == "4":
                    break

        elif order == "8":
            crawler.Save_List("User_Info", crawler.User_Info)
            break
        os.system('cls')

if __name__ == '__main__':
    main()