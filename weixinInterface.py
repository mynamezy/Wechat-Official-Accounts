# -*- coding: utf-8 -*-
import hashlib
import web
import lxml
import time
import os
import urllib2,json,cookielib
import pylibmc
from lxml import etree

def youdao(word):
        qword = urllib2.quote(word)
        baseurl =r'http://fanyi.youdao.com/openapi.do?keyfrom=zyapplication&key=1442035535&type=data&doctype=json&version=1.1&q='
        url = baseurl+qword
        resp = urllib2.urlopen(url)
        fanyi = json.loads(resp.read())
        for k,v in fanyi.items():
           print '%s:%s'%(k,v)
        if fanyi['errorCode'] == 0:        
           if ('basic' in fanyi.keys()) and ('phonetic' in fanyi['basic'].keys()) :   
              trans1 = u'%s:\n%s\n'%(fanyi['query'],''.join(fanyi['basic']['phonetic']))
              trans2 = u''
              for i in fanyi['basic']['explains']:  
                  trans2+=i+'\n'
              trans=trans1+trans2      
              return trans  
           else:
              trans =u'%s:\n基本翻译:%s\n'%(fanyi['query'],''.join(fanyi['translation']))        
              return trans

def weather_cn(weather):    
        url = "http://apis.baidu.com/apistore/weatherservice/recentweathers?cityname="
        url=url+weather
        req = urllib2.Request(url)
        req.add_header("apikey", "e52ac9e357f627b74ff2e8de9c2bde80")
        resp = urllib2.urlopen(req)
        content = resp.read()
        info = json.loads(content)
        info1=info['retData']['today']['index']
        info2=info['retData']['forecast']
        if(info['errNum'] == -1):
            return info['errMsg']
        else:
            re1 = u'%s天气预报\n%s %s发布\n'%(info['retData']['city'],''.join(info['retData']['today']['date']),''.join(info['retData']['today']['week']))
            re2 = u'当前温度：%s\n最高温度：%s\n最低温度：%s\n'%(info['retData']['today']['curTemp'],''.join(info['retData']['today']['hightemp']),''.join(info['retData']['today']['lowtemp']))  
            re3 = u'pm值：%s   风力：%s\n天气状态：%s'%(info['retData']['today']['aqi'],''.join(info['retData']['today']['fengli']),''.join(info['retData']['today']['type']))
            re4 = u'\n温馨提示：%s%s'%(info1[1]['details'],''.join(info1[2]['details']))
            re5 = u'\n未来两天天气情况：\n明天\n%s~%s %s\n后天\n%s~%s %s\n大后天\n%s~%s %s'%(info2[0]['lowtemp'],''.join(info2[0]['hightemp']),''.join(info2[0]['type']),''.join(info2[1]['lowtemp']),''.join(info2[1]['hightemp']),''.join(info2[1]['type']),''.join(info2[2]['lowtemp']),''.join(info2[2]['hightemp']),''.join(info2[2]['type']))  
            re  = re1+re2+re3+re4+re5
            return re
        
def music_info(word1):
        baseurl = r'http://s.music.163.com/search/get/?type=1&s='
        qword = urllib2.quote(word1)
        url = baseurl + qword + r'&limit=1&offset=0' 
        resp = urllib2.urlopen(url)
        music1 = json.loads(resp.read())
        return music1               
        
class WeixinInterface:

    def __init__(self):
        self.app_root = os.path.dirname(__file__)
        self.templates_root = os.path.join(self.app_root,'templates')
        self.render = web.template.render(self.templates_root)

    def GET(self):
        #获取输入参数
        data = web.input()
        signature=data.signature
        timestamp=data.timestamp
        nonce=data.nonce
        echostr=data.echostr
        #自己的token
        token="zhangyu" #这里改写你在微信公众平台里输入的token
        #字典序排序
        list=[token,timestamp,nonce]
        list.sort()
        sha1=hashlib.sha1()
        map(sha1.update,list)
        hashcode=sha1.hexdigest()
        #sha1加密算法        

        #如果是来自微信的请求，则回复echostr
        if hashcode == signature:
            return echostr
    
    
    def POST(self):        
        str_xml = web.data() #获得post来的数据
        xml = etree.fromstring(str_xml)#进行XML解析
       #content=xml.find("Content").text#获得用户所输入的内容
        mstype=xml.find("MsgType").text
        fromUser=xml.find("FromUserName").text
        toUser=xml.find("ToUserName").text
        mc=pylibmc.Client()
        if mstype == "event":
            mscontent = xml.find("Event").text
            if mscontent == "subscribe":
                replayText = u'''欢迎各位少年来到苏州街的猪，这个公众号集合了几种小功能，请输入help查看操作指令'''
                return self.render.reply_text(fromUser,toUser,int(time.time()),replayText)
        if mstype == 'text':
            content=xml.find("Content").text#获得用户所输入的内容
            if content == 'help':
                replayText1 = u'''1.输入翻译+你所要翻译的中文或者英文（如：翻译pig)\n\n2.输入天气+地点（如：天气北京),可以获得天气信息\n\n3.输入歌曲+歌名（如：歌曲虫儿飞）搜歌，可通过增加歌手名来提高搜索结果准确度：“歌曲+歌名+歌手名”>“歌曲+歌名'''
                replayText2 = u'''\n\n4.输入快递+快递单号（如：快递6868686868）可以查询快递信息'''
                replayText=replayText1+replayText2
                return self.render.reply_text(fromUser,toUser,int(time.time()),replayText)    
          
            elif(content[0:2] == u"翻译"):
                content = content[2:].encode('UTF-8')
                Nword = youdao(content)        
                return self.render.reply_text(fromUser,toUser,int(time.time()),Nword) 
            elif(content[0:2] == u"天气"):
                content = content[2:].encode('UTF-8')
                Nweather=weather_cn(content)
                return self.render.reply_text(fromUser,toUser,int(time.time()),Nweather) 
            elif(content[0:2] == u"歌曲"):
                content = content[2:].encode('UTF-8')
                music = music_info(content)
                music1 = music['result']['songs']
                if music1:
                     title = music['result']['songs'][0]['name']
                     desc =  u'来自网易云音乐'  
                     url = music['result']['songs'][0]['audio']
                     return self.render.reply_music(fromUser,toUser,int(time.time()),title,desc,url)
                else:
                     replayText = u'歌曲因为版权问题无法播放，请重新搜索'
                     return self.render.reply_text(fromUser,toUser,int(time.time()),replayText)  
             
            elif(content[0:2] == u"快递"):
                 content = content[2:].encode('UTF-8') 
                 url = "http://www.kuaidi100.com/autonumber/autoComNum?text="+content
                 cookie = cookielib.CookieJar()
                 opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie))
                 opener.addheaders = [('User-agent','Mozilla/5.0 (X11; Linux x86_64; rv:38.0) Gecko/20100101 Firefox/38.0 Iceweasel/38.3.0')]
                 urllib2.install_opener(opener)
                 html = urllib2.urlopen(url).read()
                 info = json.loads(html)
                
                 temp = info["auto"][0]['comCode']
                 if(temp is None):
                    return self.render.reply_text(fromUser,toUser,int(time.time()),u"请检查你的定单号！") 
                 urll = "http://www.kuaidi100.com/query?type="+temp+"&postid="+content
                 html_end = urllib2.urlopen(urll).read()
                 info_end = json.loads(html_end)
                 for k,v in info_end.items():
                        print '%s:%s'%(k,v)   
                 if(info_end["status"] == "201"):
                    return self.render.reply_text(fromUser,toUser,int(time.time()),u"订单号输入有误，请重新输入！") 
                 text = info_end["data"]
                 string = u""
                 for i in text:
                     string = string + i["time"] + i["context"] + "\n"
                 return self.render.reply_text(fromUser,toUser,int(time.time()),string)    
                    
                    
            else:
                replayText = u'''欢迎各位少年来到苏州街的猪，这个公众号集合了几种小功能，请输入help查看操作指令'''
                return self.render.reply_text(fromUser,toUser,int(time.time()),replayText)      
