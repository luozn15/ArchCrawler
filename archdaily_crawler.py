import requests
import socket
import urllib
import re
import os
import pandas as pd
import bs4
from bs4 import BeautifulSoup
import time

def main():
    print('This is a simple Archdaily Crawler...')
    url='https://www.archdaily.com'

#set searching target
    type_ = input('What type of architecture project are you searching for?\n')
    type_ ='%20'.join(type_.split(' '))
    url_search='/search/projects/text/'+type_
    url_origin = url + url_search
    print('Copy this link to your browser to check your searching page:\n')
    print(url_origin)
    print('')

#set begin pages
    start_number = input('Location of project you want to start with:\n\tfor example, input:\n\t1 2\n\tfor the 2nd project in the 1st page\nnow, your input:\n')
    start_page = int(start_number.split(' ')[0])
    start_project_of_the_page = int(start_number.split(' ')[1])

#set num of pages
    num_of_pages = input('How many pages are you going to crawl?\n')
    num_of_pages = int(num_of_pages)

#set out-put dir:
    out_dir= input('Name your out-put directory:\n')
    out_dir= './' + out_dir

    time.sleep(3)

    project_links=[]
    headers={'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36'}
    print('QUERYING SEARCH PAGES: ......')
    for i in range(num_of_pages):
        page = start_page + i
        url_page = url_origin + '?page=' + str(page)
        print('Querying Search Pages:  '+ str(url_page))
        try:
            r = requests.get(url_page,headers=headers)
            print('Success: ' + str(r.status_code))
            #状态码200表示请求成功
            text=r.text
            project_links += get_links(text)
        except:
            print('Failed')
    print(str(len(project_links))+ ' projects are found in chosen pages')  
    print(project_links)
    print('')

    photos_links=[]
    i = start_project_of_the_page
    print('QUERYING PROJECTS: ......')
    while(i < len(project_links)+1):
        link=project_links[i-1]
        print('Querying Projects:  '+ str(i) +' of ' + str(len(project_links)) + ' projects')
        i+=1
        try:
            url_photos=get_photos_pageURL(link)
            photos_links.append(url_photos)
        except:
            continue
    print(photos_links)
    print('')

    df=pd.DataFrame()
    print('CRAWLING PROJECT INFOS: ......')
    i=start_project_of_the_page
    while(i<len(project_links)+1):
        link=project_links[i-1]
        i+=1
        soup=get_soup(link)
        project_name=soup.h1.string.strip().split('/')[0]
        print('Project Name: ' + project_name)
        info=['name']
        value=[project_name]
        h3s=soup.find_all(name='h3',class_='afd-char-title')
        h3s=list(set(h3s))
        for j in range(len(h3s)):
            info.append(h3s[j].string.strip())
            contents=h3s[j].next_sibling.next_sibling.contents
            temp=''
            for c in contents:
                if(isinstance(c,bs4.element.NavigableString)):
                    temp += c.strip()
                elif(isinstance(c,bs4.element.Tag)):
                    temp += c.string.strip()
            value.append(temp)  
        dict1 = dict(zip(info,value))
        df=df.append(dict1,ignore_index=True)
    print(df.head(10))
    print('')

    if(not os.path.exists(out_dir)):
        os.mkdir(out_dir)
        print('create ' + out_dir)
    df.to_csv(os.path.join(out_dir,'project_infos.csv'),encoding='utf-8')
    print('PROJECT INFO SUCCESSFULLY SAVED')

    j = 1
    print('DOWNLOADING PICS: ......')
    while(j<len(photos_links)+1):
        url_photos=photos_links[j-1]
        print('Photo Url: ' + url_photos)

        try:
            r = requests.get(url_photos)
        except BaseException:
            continue
            
        #print(r.status_code)
        text=r.text
        
        try:
            result=re.findall("url_large&quot;:&quot;(.*?)&quot;,&quot;url_slideshow",text)
        except BaseException:
            continue
        project_name2 = url_photos.split('/')[-2]
        path = os.path.join(out_dir, str(j + start_project_of_the_page-1 + (start_page-1)*24) + '__' + project_name2)
        if(not os.path.exists(path)):
            os.mkdir(path)
        
        i=1 #断点，当前项目起始图片序号
        for pic in result:
            print('Downloading: ' + str(i)+'.jpg')
            try:
                res=re.search("jpg/(.*?)\.jpg",pic)    
                name=res.group(1)
                r = requests.get(pic)
                with open(os.path.join(path, str(i)+'.jpg'), 'wb')as fp:
                    fp.write(r.content)
                print('Done')
            except BaseException:
                print('Failed')
            i+=1
        j+=1

def get_links(text_search_page):
    result=re.findall('<a class="afd-search-list__link" href="(.*?)">',text_search_page,re.S)
    return result

def get_soup(link):
    url='https://www.archdaily.com'
    url_project = url + link
    r = requests.get(url_project)
    ht=r.text
    soup = BeautifulSoup(ht , 'lxml')
    return soup

#从项目页获取gallery页url
def get_photos_pageURL(link):
    url='https://www.archdaily.com'
    url_project = url + link
    r = requests.get(url_project)
    text=r.text
    #result = re.findall("<a class='js-image-size__link.*?' href='(.*?)'.*?style",text,re.S)
    #result = re.findall("<a class='js-image-size__link.*?href='(/.*?)'.*?style",text,re.S)
    #result = re.findall("<a class='js-image-size__link.*?href='"+link+"(.*?).*?style",text,re.S)
    result = re.findall("href='"+link+"(.*?-jpg|.*?-photo|.*?-image)",text,re.S)
    url_photos = url_project + result[0]
    print('photosURL: ' + url_photos)
    return url_photos

if __name__ == "__main__":
    main()