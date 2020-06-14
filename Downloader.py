import os
import os.path as op
import re
import sys
import json
import requests

class Downloader(object):
    def __init__(self, path):
        self.Download_path = path
        self.root = sys.path[0] 
   
    def Set_Path(self, path):
        self.Download_path = path

    def Check_Pach(self):
        if not op.exists(self.Download_path):
            os.makedirs(self.Download_path) 

    def Pic_Download(self, url, file_name, path_Add = "", s = False):
        self.Check_Pach()
        print("开始下载")       
        if not s:
            # 生成文件名和存储路径                        
            New_Path = self.Download_path + path_Add + "{}".format(file_name)
            # 如果文件名不重复则开始下载
            if not op.isfile(New_Path): 
                url = url["original_image_url"]
                r = requests.get(url.replace("i.pximg.net","i.pixiv.cat"), stream = True)
                if r.status_code == 200:
                    open(New_Path, 'wb').write(r.content)
        else:
            for i in range(len(url)):
                New_Path = self.Download_path + path_Add + "{}_P{}{}".format(file_name[:-4], i, file_name[-4:])
                if not op.isfile(New_Path):
                    u = url[i]["image_urls"]["original"]
                    r = requests.get(u.replace("i.pximg.net","i.pixiv.cat"), stream = True)
                    if r.status_code == 200:
                        open(New_Path, 'wb').write(r.content)
                print("图片集 {} 下载中，进度{}/{}。".format(file_name[:-4], i+1, len(url)))

        print("图片 {} 下载完成".format(file_name[:-4]))

    def Artist_Download(self, Artist_ID):
        # 加载本地缓存文件
        filelist = os.listdir("{}\\cache\\".format(self.root))
        for file in filelist: 
            if re.match(Artist_ID + ".{1,}", file):
                File_Name = file
                Illust_List = self.Load_List(File_Name)
                Total_Illusts = len(Illust_List) - 2
                print("成功从缓存中加载作品列表，共有 {} 副作品。\n".format(Total_Illusts))
                break

        self.Check_Pach()
        DP = "({}){}\\".format(Illust_List[0], Illust_List[1])
        isExists = op.exists(self.Download_path + DP)
        if not isExists:
            os.makedirs(self.Download_path + DP) 
            
        n = 0
        for illust in Illust_List[2:]:
            print("剩余{}副作品未下载".format(Total_Illusts - n))
            n += 1
            if illust["is_block"]:
                continue
            else:
                Name = "({}){}".format(illust["ID"], illust["Title"].replace("/","-"))
                if illust["Page_Count"] > 1:
                    url = illust["Image_Urls"]
                    name = "{}{}".format(Name, url[0]["image_urls"]["original"][-4:])
                    self.Pic_Download(url, name, path_Add = DP, s = True)
                else:
                    url = illust["Image_Urls"]
                    name = "{}{}".format(Name, url["original_image_url"][-4:])
                    self.Pic_Download(url, name, path_Add = DP)

    def Load_List(self, File_Name):
        path = "{}\\Cache\\{}".format(self.root, File_Name)
        if op.isfile(path):
            with open(path, 'r') as Cache_File:
                L = json.load(Cache_File)
        else:
            L = []
        return L