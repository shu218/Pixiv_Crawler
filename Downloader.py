import os
import os.path as op
import re
import json
import threading
from PIL import Image
import imageio
import zipfile
import requests
from fake_useragent import UserAgent

class Downloader(object):
    def __init__(self, path):
        self.root = os.getcwd()
        self.Download_path = path
        self.ua = UserAgent()
        self.headers = {"User-Agent": self.ua.random}
        self.Gif_Threads_Pool = []

    def Set_Path(self, path):
        self.Download_path = path

    def Check_Pach(self):
        if not op.exists(self.Download_path):
            os.makedirs(self.Download_path) 

    def Pic_Download(self, url, file_name, Dir_Path = ""):
        self.Check_Pach()   
        # 生成文件名和存储路径                        
        New_Path = self.Download_path + Dir_Path + file_name
        # 如果文件名不重复则开始下载
        if not op.isfile(New_Path): 
            r = requests.get(url.replace("i.pximg.net","i.pixiv.cat"), stream = True, headers = self.headers)
            if r.status_code == 200:
                open(New_Path, 'wb').write(r.content)
#                print("\n图片 {} 下载完成".format(file_name[:-4]))

    def Gif_Download(self, url, file_name, Dir_Path = ""):
        self.Check_Pach()
#        print("\n开始下载")       
        # 生成文件名和存储路径                        
        New_Path = self.Download_path + Dir_Path + file_name
        New_Path_Gif = self.Download_path + Dir_Path + re.sub(r'[@][0-9]{1,}[m][s]',"",file_name[:-3]) + "gif"
        # 如果文件名不重复则开始下载动图压缩包（zip格式）
        if not op.isfile(New_Path) and not op.isfile(New_Path_Gif): 
            r = requests.get(url.replace("i.pximg.net","i.pixiv.cat"), stream = True, headers = self.headers)
            if r.status_code == 200:
                open(New_Path, 'wb').write(r.content)

        # 解压缩zip文件，拖慢下载速度，暂且取消
        if zipfile.is_zipfile(New_Path):     
            fz = zipfile.ZipFile(New_Path, 'r')
            os.makedirs(New_Path[:-4] + "\\")
            for file in fz.namelist():
                fz.extract(file, New_Path[:-4] + "\\")  
            fz.close()
            # 制作gif文件
            image_list = []
            for i in range(len(fz.namelist())):
                image_list.append(New_Path[:-4] + "\\" + fz.namelist()[i])
            frames = []
            duration = file_name[file_name.rfind("@")+1 : -6]
            for image in image_list:
                frames.append(imageio.imread(image))
            imageio.mimsave(New_Path_Gif, frames, "GIF", duration = int(duration)*0.001)
            # 删除多余文件
            for file in image_list:
                os.remove(file)
            os.rmdir(New_Path[:-4] + "\\")
            os.remove(New_Path) 

#        print("\n动图 {} 下载完成".format(file_name[:-4]))

    def Artist_Download(self, Artist_ID):
        # 加载本地缓存文件
        filelist = os.listdir(self.root + "\\cache\\")
        for file in filelist: 
            if re.match("[(]" + str(Artist_ID) + "[)]" + ".{1,}", file):
                File_Name = file
                Illust_List = self.Load_List(File_Name)
                Total_Illusts = len(Illust_List) - 2
                break

        self.Check_Pach()        
        filelist = os.listdir(self.Download_path)
        DP = "({}){}\\".format(Illust_List[0], Illust_List[1])
        for file in filelist: 
            if re.match("[(]" + str(Illust_List[0]) + "[)]" + ".{1,}", file):
                DP = file + "\\"
                break
        isExists = op.exists(self.Download_path + DP)
        if not isExists:
            os.makedirs(self.Download_path + DP) 
            
        n = 0
        for illust in Illust_List[2:]:
            n += 1
            if illust["is_block"]:
                if int(illust["Illust_Date"]) < 20180101:
                    print("\n后续插画的完成时间过早，停止下载", end="")
                    break
                else:
                    continue
            else:
                Name = "({}){}".format(illust["ID"], illust["Title"])
                if illust["Muti_Page"]:
                    url = illust["Image_Urls"]
                    name = []
                    file_name = "{}{}".format(Name, url[0][-4:])
                    for i in range(len(url)):
                        name.append("{}_P{}{}".format(file_name[:-4], i, file_name[-4:]))     
                    for i in range(5,len(url),5):
                        Threads = []
                        for j in range(5):
                            Threads.append(threading.Thread(target = self.Pic_Download, args = (url[i+j-5], name[i+j-5], DP)))
                        for Thread in Threads:  Thread.start()
                        for Thread in Threads:  Thread.join()                                                       
#                    print("\n图片集 {} 下载完成".format(file_name[:-4]))
                elif illust["Ugoira"]:
                    url = illust["Image_Urls"][0]
                    name = "{}@{}ms{}".format(Name, illust["Image_Urls"][1], url[-4:])
                    self.Gif_Threads_Pool.append(threading.Thread(target = self.Gif_Download, args = (url, name, DP)))
                    self.Gif_Threads_Pool[-1].start()
                    if len(self.Gif_Threads_Pool) == 10:
                        for Thread in self.Gif_Threads_Pool:     Thread.join()
                        self.Gif_Threads_Pool = []
                    #self.Gif_Download(url, name, Dir_Path = DP)
                else:
                    url = illust["Image_Urls"]
                    name = "{}{}".format(Name, url[-4:])
                    self.Pic_Download(url, name, Dir_Path = DP)
            print("\r剩余{}副作品未下载".format(Total_Illusts - n), end="")

    def Bookemark_Download(self):
        Illust_List = self.Load_List("Bookmark_List_cache")
        Total_Illusts = len(Illust_List)

        self.Check_Pach()
        DP = "Bookmark_Public\\"
        isExists = op.exists(self.Download_path + DP)
        if not isExists:
            os.makedirs(self.Download_path + DP) 
            
        n = 0
        for illust in Illust_List:
            print("\r剩余{}副作品未下载".format(Total_Illusts - n), end="")
            n += 1
            Name = "({}){}".format(illust["ID"], illust["Title"])
            if illust["Muti_Page"]:
                url = illust["Image_Urls"]
                name = []
                file_name = "{}{}".format(Name, url[0][-4:])
                for i in range(len(url)):
                    name.append("{}_P{}{}".format(file_name[:-4], i, file_name[-4:]))     
                for i in range(5,len(url),5):
                    Threads = []
                    for j in range(i):
                        Threads.append(threading.Thread(target = self.Pic_Download, args = (url[j], name[j], DP)))
                    for Thread in Threads:  Thread.start()
                    for Thread in Threads:  Thread.join()                                                       
#                print("\n图片集 {} 下载完成".format(file_name[:-4]))
            elif illust["Ugoira"]:
                url = illust["Image_Urls"][0]
                name = "{}@{}ms{}".format(Name, illust["Image_Urls"][1], url[-4:])
                self.Gif_Threads_Pool.append(threading.Thread(target = self.Gif_Download, args = (url, name, DP)))
                self.Gif_Threads_Pool[-1].start()
                if len(self.Gif_Threads_Pool) == 10:
                    for Thread in self.Gif_Threads_Pool:     Thread.join()
                    self.Gif_Threads_Pool = []
#                self.Gif_Download(url, name, Dir_Path = DP)
            else:
                url = illust["Image_Urls"]
                name = "{}{}".format(Name, url[-4:])
                self.Pic_Download(url, name, Dir_Path = DP)

    def Load_List(self, File_Name):
        path = "{}\\Cache\\{}".format(self.root, File_Name)
        if op.isfile(path):
            with open(path, 'r') as Cache_File:
                L = json.load(Cache_File)
        else:
            L = []
        return L