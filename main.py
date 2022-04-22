# -*- coding: utf-8 -*-
import datetime
import io
import json
import sys
import time
from random import random

import execjs
import requests
from bs4 import BeautifulSoup

def getLastDate(style):
    return datetime.datetime.now().strftime('%Y-%m-%d' if style == 1 else '%Y-%m')

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36 Edg/100.0.1185.44',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Host': 'client.v.just.edu.cn',
    'Origin': 'https://client.v.just.edu.cn',
    'Upgrade-Insecure-Requests': '1',
    'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="100", "Microsoft Edge";v="100"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
}

mainUrl = 'http://ids2.just.edu.cn/cas/login?service=http%3A%2F%2Fmy.just.edu.cn%2F'
dcTokenURL = 'http://ids2.just.edu.cn/cas/login?service=http%3A%2F%2Fdc.just.edu.cn%2F%23%2Fdform%2FgenericForm%2F'
validateLoginURL = 'http://dc.just.edu.cn/dfi/validateLogin?service=http%3A%2F%2Fdc.just.edu.cn%2F%23%2Fdform%2FgenericForm%2F'
getFormWidUrl = 'http://dc.just.edu.cn/dfi/formOpen/loadFormListBySUrl'


class Ding:
    def __init__(self, username=None, password=None):
        self.username = username
        self.password = password
        self.args = [] if args is None else args
        self.loginURL = 'http://ids2.just.edu.cn/cas/login?service=http%3A%2F%2Fmy.just.edu.cn%2F'
        self.session = requests.Session()

    def get_sUrl(self):
        response = requests.get('http://dc.just.edu.cn/jkdk.html')
        sUrl = response.text.split('window.location = "http://dc.just.edu.cn/#/dform/genericForm/')[1].split('";')[0]
        return sUrl

    def getExecution(self):
        try:
            response = self.session.get(mainUrl)
            soup = BeautifulSoup(response.text, 'lxml')
            return soup.find('input', {'name': 'execution'})['value']
        except Exception as e:
            raise e

    def start(self):
        return self.login()

    def login(self):
        try:
            execution = self.getExecution()  # 获得 execution
        except Exception:
            return False
        data = {
            'username': self.username,
            'password': self.password,
            'execution': execution,
            '_eventId': 'submit',
            'loginType': '1',
            'submit': '登 录'
        }  # 构造表单
        try:
            global dcTokenURL, validateLoginURL
            # 执行POST请求 self.loginURL 为登录地址  verify=False 关闭验证，不知道为什么要这个，反正我没有这个会报错
            response = self.session.post(self.loginURL, data=data, allow_redirects=False, verify=False)
            # 如果是重定向请求那么说明登录成功
            if response.status_code == 302:
                # 获得重定向的地址(地址存放在上次请求response头部的Location里) 同样注意要禁止重定向
                res = self.session.get(response.headers['Location'], allow_redirects=False, verify=False)
                # 下面的一次请求是再次重定向，当然你也可以允许上面这条的重定向，那么这一行就可以删掉了
                self.session.get(res.headers['Location'], verify=False)
                # 跳转到主页，欺骗服务器，已经成功登陆（如果没有这一步那么服务器可能认为我们登录失败了，导致ticket无效）
                islogin = True if self.session.get(mainUrl, allow_redirects=False,
                                                   verify=False).status_code == 302 else False
                if islogin:
                    # 获得surl
                    surl = self.get_sUrl()
                    dcTokenURL = dcTokenURL + surl
                    validateLoginURL = validateLoginURL + surl
                    # 带着cookie访问打卡网站，由于学校采用CAS一键登陆系统，因此一次登陆就可以访问所有系统
                    res = self.session.get(dcTokenURL, allow_redirects=False, verify=False)
                    # 从重定向地址中截取ticket
                    ticket = res.headers['Location'].split('ticket=')[1].split('#')[0]
                    # 执行获得Authentication函数
                    form_wid = json.loads(self.session.get(getFormWidUrl + '?sUrl=' + surl).text)['data'][0]['WID']
                    return self.getToken(ticket,form_wid)
                else:
                    return False
            else:
                return False
        except Exception as e:
            print(e)
            return False

    @staticmethod
    def get_int_ruid():
        base_time = round(time.mktime(time.strptime('1970-01-02 00:00:00', '%Y-%m-%d %H:%M:%S')) * 10 ** 3)
        ruid = round(time.time() * 10 ** 3) - base_time
        return str(ruid)

    def getHistory(self, token,formWid):
        historyUrl = f'http://dc.just.edu.cn/dfi/formData/loadFormFillHistoryDataList?formWid={formWid}&auditConfigWid='
        headers = {
            'Authentication':token
        }
        response = self.session.get(historyUrl,headers=headers)
        json_ = json.loads(response.text)
        data = json_['data'][0]
        formData = {
            'formWid': formWid,
            'userId': 'AM@' + Ding.get_int_ruid(),
            'dataMap': {
                'wid':'',
                'RADIO_L11NMCAA': data['RADIO_L11NMCAA'],
                'RADIO_L11NMCAC': data['RADIO_L11NMCAC'],
                'INPUT_L1BTINV4': data['INPUT_L1BTINV4'],
                'INPUT_L11NMCAO': data['INPUT_L11NMCAO'],
                'RADIO_L1MVAKG2': data['RADIO_L1MVAKG2'],
                'INPUT_L11NMCAM': data['INPUT_L11NMCAM'],
                'INPUT_L11NMCAQ': data['INPUT_L11NMCAQ'],
                'INPUT_L11NMC9H': data['INPUT_L11NMC9H'],
                'RADIO_L11NMCA8': data['RADIO_L11NMCA8'],
                'INPUT_L1RTT90Z': data['INPUT_L1RTT90Z'],
                'INPUT_L1BG7AIY': data['INPUT_L1BG7AIY'],
                'RADIO_L15XZ9SA': data['RADIO_L15XZ9SA'],
                'INPUT_L17ZLMTZ': data['INPUT_L17ZLMTZ'],
                'LOCATION_L1OELUCJ': data['LOCATION_L1OELUCJ'],
                'RADIO_L1WY3PV5': data['RADIO_L1WY3PV5'],
                'INPUT_L1BRQPYU': data['INPUT_L1BRQPYU'],
                'INPUT_L15XZ9SD': data['INPUT_L15XZ9SD'],
                'INPUT_L1Y90DS0': data['INPUT_L1Y90DS0'],
                'RADIO_L11NMCAJ': data['RADIO_L11NMCAJ'],
                'RADIO_L11NMCAK': data['RADIO_L11NMCAK'],
                'RADIO_L1RTT90Y': data['RADIO_L1RTT90Y'],
                'RADIO_L11NMCAF': data['RADIO_L11NMCAF']
            },
            "commitDate": getLastDate(1),
            "commitMonth": getLastDate(2),
            "auditConfigWid": ""
        }
        return formData

    def getToken(self, ticket,formWid):
        try:
            url = validateLoginURL + f'&ticket={ticket}'
            response = self.session.get(url)
            json_ = json.loads(response.text)
            token = json_['data']['token']
            form = self.getHistory(token,formWid)
            encrypt_str = self.encrypt(form)
            return self.ding(token, encrypt_str)
        except Exception as e:
            print(f'{self.username},获取token失败:{e}')
            return False

    def ding(self, token, encrypt_str):
        try:
            url = 'http://dc.just.edu.cn/dfi/formData/saveFormSubmitDataEncryption'
            headers = {
                'Authentication': token,
            }
            response = requests.post(url, data=encrypt_str, headers=headers)
            json_ = json.loads(response.text)
            if json_['data']['result']:
                return True
        except Exception as e:
            print(f'line:185,{e}')
            return False

    def encrypt(self, form):
        try:
            js = execjs.compile(open(r'./js/ding.js', encoding='utf-8').read(),
                                cwd='./js/node_modules/')
            return js.call('encrypt', form)
        except Exception as e:
            sys.exit(-4)


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    args = sys.argv
    # args[1] 为学号 args[2] 为密码
    d = Ding(args[1], args[2])
    try:
        if d.start():
            sys.exit(1)
        else:
            sys.exit(-1)
    except Exception as e:
        print(e)
        sys.exit(-666)
