# -*- coding: utf-8 -*-
import requests as req
from flask import Flask, request
from binascii import *
import os
import base64
import json
from Crypto.Cipher import AES

app = Flask(__name__)


def send_group_message(group, message):
    global group_message_id_list
    message = req.get('http://127.0.0.1:5700/send_group_msg?group_id={}&message={}'.format(group, message))
    group_message_id_list.append(eval(message.content.decode())['data']['message_id'])
    print(group_message_id_list)


def send_private_message(user_id, message):
    global private_message_id_list
    message = req.get('http://127.0.0.1:5700/send_private_msg?user_id={}&message={}'.format(user_id, message))
    private_message_id_list.append(eval(message.content.decode())['data']['message_id'])
    print(private_message_id_list)

def delete_group_message():
    global group_message_id_list
    req.get('http://127.0.0.1:5700/delete_msg?message_id={}'.format(group_message_id_list[len(group_message_id_list) - 1]))
    del group_message_id_list[len(group_message_id_list) - 1]

def delete_private_message():
    global private_message_id_list
    req.get('http://127.0.0.1:5700/delete_msg?message_id={}'.format(private_message_id_list[len(private_message_id_list) - 1]))
    del private_message_id_list[len(private_message_id_list) - 1]

class SongSearchFail(object):
    pass


class Encrypyed():
    '''加密生成'params'、'encSecKey 返回'''
    def __init__(self):
        self.pub_key = '010001'
        self.modulus = '00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7b725152b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf695280104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932575cce10b424d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b3ece0462db0a22b8e7'
        self.nonce = '0CoJUm6Qyw8W8jud'

    def create_secret_key(self, size):
        return hexlify(os.urandom(size))[:16].decode('utf-8')

    def aes_encrypt(self, text, key):
        iv = '0102030405060708'
        pad = 16 - len(text) % 16
        text = text + pad * chr(pad)
        key = key.encode('utf-8')
        iv = iv.encode('utf-8')
        encryptor = AES.new(key, AES.MODE_CBC, iv)
        text = text.encode('utf-8')
        result = encryptor.encrypt(text)
        result_str = base64.b64encode(result).decode('utf-8')
        return result_str

    def rsa_encrpt(self, text, pubKey, modulus):
        text = text[::-1]
        rs = pow(int(hexlify(text.encode('utf-8')), 16), int(pubKey, 16), int(modulus, 16))
        return format(rs, 'x').zfill(256)

    def work(self, ids, br=128000):
        text = {'ids': [ids], 'br': br, 'csrf_token': ''}
        text = json.dumps(text)
        i = self.create_secret_key(16)
        encText = self.aes_encrypt(text, self.nonce)
        encText = self.aes_encrypt(encText, i)
        encSecKey = self.rsa_encrpt(i, self.pub_key, self.modulus)
        data = {'params': encText, 'encSecKey': encSecKey}
        return data

    def search(self, text):
        text = json.dumps(text)
        i = self.create_secret_key(16)
        encText = self.aes_encrypt(text, self.nonce)
        encText = self.aes_encrypt(encText, i)
        encSecKey = self.rsa_encrpt(i, self.pub_key, self.modulus)
        data = {'params': encText, 'encSecKey': encSecKey}
        return data
class search():
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/55.0.2883.87 Safari/537.36',
            'Host': 'music.163.com',
            'Referer': 'http://music.163.com/search/'}
        self.main_url = 'http://music.163.com/'
        self.session = req.Session()
        self.session.headers = self.headers
        self.ep = Encrypyed()

    def search_song(self, search_content, search_type=1, limit=9):
        url = 'http://music.163.com/weapi/cloudsearch/get/web?csrf_token='
        text = {'s': search_content, 'type': search_type, 'offset': 0, 'sub': 'false', 'limit': limit}
        data = self.ep.search(text)
        resp = self.session.post(url, data=data)
        result = resp.json()
        if result['result']['songCount'] <= 0:
            return SongSearchFail()
        else:
            songs = result['result']['songs']
            retsult = []
            for song in songs:
                song_id, song_name, singer, alia = song['id'], song['name'], song['ar'][0]['name'], song['al']['name']
                retsult.append([song['id'], song['name'], song['ar'][0]['name'], song['al']['name']])
            return retsult


def diange(name_song, n=0):
    songsearch = search()
    if "宽宽" in name_song:
        return "别欺负宽宽"
    if '鹤子' in name_song:
        return '别欺负鹤子'
    if 'cxk' in name_song:
        return '别欺负坤坤'
    retsult = songsearch.search_song(name_song)
    if type(retsult) == SongSearchFail:
        return "对不起哦没找到名为《" + name_song + "》的歌"
    if len(retsult) > 10:
        retsult = retsult[:10]
    print(retsult)
    if n != None:
        try:
            n = int(n)
        except Exception as err:
            return "n值不合法:" + n
        if n > len(retsult):
            return "n值超过范围"
        else:
            retsult = "[CQ:music,type=163,id=" + str(retsult[n][0]) + "]"
            return retsult
    returnValues = ""
    for i in range(len(retsult)):
        returnValues += "---%d---\n歌曲:%s\n歌手:%s\n专辑:%s\n" % (
            i, retsult[i][1], retsult[i][2], retsult[i][3])
    return returnValues
@app.route("/", methods=["post"])
def get_json():
    # 接收消息
    json = request.get_json()
    try:
        type = json['message_type']
        group_id = json['group_id']
        message_raw = json['message']
        message = message_raw.split(' ', 4)
        print(message)
        user_id = json['user_id']
        print(json)
        if type == 'group':
            user_id = json['sender']['user_id']
            print(json)
            blacklist = []
            message_raw = json['message']
            message = message_raw.split(' ', 3)
            if user_id in blacklist:
                send_group_message(group_id, '抱歉，你是黑名单成员，无法操作，想要解禁，请联系开发者')

            else:
                if message[0] == '[CQ:at,qq=3554282542]' and message[1] == '计算':
                    number = eval(message[2])
                    if number == 1600:
                        send_group_message(group_id, f'[CQ:at,qq={user_id}] 答案是：十六百')
                    else:
                        send_group_message(group_id, f'[CQ:at,qq={user_id}] 答案是：{number}')

                elif message[0] == '[CQ:at,qq=3554282542]':
                    if message[1] == '你好':
                        send_group_message(group_id, '你好, 我是鹤子爱编程开发的QQ机器人\n目前功能：\n为防止刷屏，请点击https://hezi-biancheng.github.io/branch/help.html')

                    elif message[1] == '早安':
                        send_group_message(group_id, f'[CQ:at,qq={user_id}] 早啊，今天是美好的一天')

                    elif message[1] == '晚安':
                        send_group_message(group_id, f'[CQ:at,qq={user_id}] 晚安，做个好梦')

                    elif message[1] == 'ikun':
                        send_group_message(group_id, f'[CQ:at,qq={user_id}] 不是，你黑我家鸽鸽你什么意思\n我是真ikun')

                    elif message[1] == '撤回':
                        delete_group_message()
                    elif message[1] == '制作人抖音':
                        send_group_message(group_id,
                                           f'[CQ:at,qq={user_id}] 抖音头像：\n[CQ:image,file=tupian.JPG ]\n抖音网站：https://www'
                                           f'.douyin.com/user/MS4wLjABAAAAhCam6cAHHca5ZaNRG-ejJrtkuAf52ZfB7Jz816WgqqE')
                    elif message[1] == '关于':
                        send_group_message(group_id,
                                           f'[CQ:at,qq={user_id}] 作者信息：\n作者抖音：鹤子爱编程 抖音号2052661212 \n作者抖音小号：鹤子玩电脑 '
                                           f'抖音号：25407531998\n特别鸣谢：小井井、宽宽')

                    elif message[1] == '猜拳':
                        send_group_message(group_id, '[CQ:rps]')

                    elif message[1] == '黑名单':
                        if user_id == 3174544841:
                            send_group_message(group_id, f'你好，管理员，黑名单人员：{blacklist}')
                        else:
                            send_group_message(group_id, '抱歉，你不是管理员，没有权利执行')

                    elif message[1] == '鸡你':
                        send_group_message(group_id, f'[CQ:at,qq={user_id}] 实在是太美\n我也很ikun')

                    elif message[1] == '反馈':
                        send_private_message(3174544841, f'用户{user_id}的反馈：' + message[2])
                        send_group_message(group_id, f'[CQ:at,qq={user_id}] 你的反馈已发送')

                    elif message[1] == 'emo':
                        send_group_message(group_id, f'[CQ:at,qq={user_id}] 作者好了，你们也要开开心的的啊[CQ:face,id=21]')

                    elif message[1] == '加密':
                        strInput = message[2]
                        bs = str(base64.b64encode(strInput.encode('utf-8')), "utf-8")
                        send_group_message(group_id, f'[CQ:at,qq={user_id}] 密文是:\n{bs}')

                    elif message[1] == '解密':
                        yuanm = message[2]
                        jiemi = (str(base64.b64decode(yuanm), "utf-8"))
                        send_group_message(group_id, f'[CQ:at,qq={user_id}] 原文是\n{jiemi}')

                    elif message[1] == '听歌':
                        send_group_message(group_id, '[CQ:music,type=163,id=1330348068]')

                    elif message[1] == '点歌':
                        name = message[2]
                        song = diange(name)
                        send_group_message(group_id, song)

                    else:
                        send_group_message(group_id, '抱歉你的消息我无法识别，你可以艾特我并发送"反馈"反馈内容')


        else:
            user_id = json['sender']['user_id']
            print(json)
            message_raw = json['message']
            message = message_raw.split(' ', 3)

            send_private_message(user_id, '你好, 我是QQ机器人\n目前功能：发送“加法”可以计算加法')
            if '加法' == message:
                send_private_message(user_id, '正在改进')
    except Exception:
        pass
    return 'root'


if __name__ == '__main__':
    app.run("0.0.0.0", port=8899)
