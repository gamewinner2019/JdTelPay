#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
@Time    : 2023/11/22 16:21
@Author  : Jhon
@File    : main.py
"""
import datetime
import hashlib
import json
import re
from io import BytesIO

import redis
import requests
import time
from pyzbar.pyzbar import decode
from PIL import Image
from loguru import logger
from urllib.parse import quote
from flask import Flask, request
from lxml import etree

app = Flask(__name__)

app.config['JSON_AS_ASCII'] = False

proxyCity = {}


def proxy_ip(pid=-1, cid=-1):
    """
    获取代理IP
    :return:
    :param pid: 省份
    :param cid: 城市
    """
    """
        orderId:提取订单号
        secret:用户密钥
        num:提取IP个数
        pid:省份
        cid:城市
        type：请求类型，1=http/https,2=socks5
        unbindTime:使用时长，秒/s为单位
        noDuplicate:去重，0=不去重，1=去重
        lineSeparator:分隔符
        singleIp:切换,0=切换，1=不切换
    """
    for i in range(1, 10):
        orderId = "O23082900494105859346"
        secret = "2b4def38271448a7b31d7854bdf7424e"
        num = "1"
        pid = str(pid)
        cid = str(cid)
        unbindTime = "60"
        noDuplicate = "0"
        lineSeparator = "0"
        singleIp = "0"
        times = str(int(time.time()))  # 时间戳
        # 计算sign
        txt = "orderId=" + orderId + "&" + "secret=" + secret + "&" + "time=" + times
        sign = hashlib.md5(txt.encode()).hexdigest()
        # 访问URL获取IP
        url = "http://api.hailiangip.com:8422/api/getIp?type=1" + "&num=" + num + "&pid=" + pid + "&unbindTime=" + \
              unbindTime + "&cid=" + cid + "&orderId=" + orderId + "&time=" + times + "&sign=" + sign + "&dataType=0" + \
              "&lineSeparator=" + lineSeparator + "&noDuplicate=" + noDuplicate + "&singleIp=" + singleIp + "&type=1"
        my_response = requests.get(url, timeout=3).content
        js_res = json.loads(my_response)

        for dic in js_res["data"]:
            ip = dic["ip"]
            port = dic["port"]
            proxyUrl = "http://" + ip + ":" + str(port)
            logger.success(f'获取到代理IP: {proxyUrl}')
            proxy = {'http': proxyUrl, "https": proxyUrl}
            r = requests.get(f"https://www.baidu.com", proxies=proxy, verify=False)
            if r.status_code == 200:
                return proxy
            else:
                continue


def loads_jsonp(_jsonp):
    try:
        return json.loads(re.match(".*?({.*}).*", _jsonp, re.S).group(1))
    except:
        raise ValueError('Invalid Input')


class JdThor:
    def __init__(self):
        self.http = requests.session()

    #   获取二维码
    def getQrcode(self, proxy):
        res = self.http.get('https://passport.jd.com/new/login.aspx?ReturnUrl=https%3A%2F%2Fwww.jd.com%2F')
        self.http.cookies.update(res.cookies)
        url = f'https://qr.m.jd.com/show?appid=133&size=147&t={int(time.time() * 1000)}'
        headers = {
            "Host": "qr.m.jd.com",
            "Connection": "keep-alive",
            "sec-ch-ua": "\"Google Chrome\";v=\"119\", \"Chromium\";v=\"119\", \"Not?A_Brand\";v=\"24\"",
            "sec-ch-ua-mobile": "?0",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "sec-ch-ua-platform": "\"macOS\"",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            "Sec-Fetch-Site": "same-site",
            "Sec-Fetch-Mode": "no-cors",
            "Sec-Fetch-Dest": "image",
            "Referer": "https://passport.jd.com/",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
        res = self.http.get(url, headers=headers, cookies=self.http.cookies, proxies=proxy)
        decocdeQR = decode(Image.open(BytesIO(res.content)))
        qRcode = decocdeQR[0].data.decode('utf-8')
        wlfstk_smdl = res.cookies.get('wlfstk_smdl')
        QRCodeKey = res.cookies.get('QRCodeKey')
        liginInfo = {"category": "jump", "des": "ScanLogin", "key": QRCodeKey, "sourceType": "JSHOP_SOURCE_TYPE",
                     "sourceValue": "JSHOP_SOURCE_VALUE", "M_sourceFrom": "mxz"}
        IosUrl = f"openapp.jdmobile://virtual?params={quote(json.dumps(liginInfo, ensure_ascii=False))}"

        #   安卓
        AndroidUrl = '{"category":"jump","des":"scanLogin","key":"' + QRCodeKey + '","sourceType":"JSHOP_SOURCE_TYPE","sourceValue":"JSHOP_SOURCE_VALUE","M_sourceFrom":"mxz","msf_type":"adod","m_param":{"YINLIUhuanqi":"' + qRcode + '"},"SE":{"mt_subsite":"","__jdv":"76161171|direct|-|none|-|1699953818958","unpl":"","__jda":"122270672.169995381895748475813.1699953819.1699953819.1699956205.2"}};package=com.jingdong.app.mall;end'
        AndroidUrl = f'openapp.jdmobile://virtual?params={quote(AndroidUrl, safe="")}'

        return {'code': 0, 'data':
            {'IosUrl': IosUrl, 'AndroidUrl': AndroidUrl, 'qrToken': wlfstk_smdl, 'QRCodeKey': QRCodeKey}}

    #   检测二维码状态
    def checkQrcode(self, wlfstk_smdl, QRCodeKey, proxy):
        headers = {
            "Referer": "https://union.jd.com/index",
            "Cookie": f"QRCodeKey={QRCodeKey}; wlfstk_smdl={wlfstk_smdl}"
        }
        url = f'https://qr.m.jd.com/check?appid=133&token={wlfstk_smdl}&callback=jsonp'
        logger.success(f'检测二维码状态: {proxy}')
        req = self.http.get(url, headers=headers, proxies=proxy)
        data = loads_jsonp(req.text)
        if data.get('code') == 201:
            return {'code': 201, 'msg': '请前往京东'}
        elif data.get('code') == 202:
            return {'code': 202, 'msg': '请在手机点击确认'}
        elif data.get('code') == 205:
            return {'code': 205, 'msg': '用户取消授权'}
        elif data.get('code') == 203:
            return {'code': 203, 'msg': '授权登陆过期'}
        elif data.get('code') == 200:
            ticket = data.get("ticket")
            logger.success(f'扫码成功: {ticket}')
            url = f'https://passport.jd.com/uc/qrCodeTicketValidation?t={ticket}&ReturnUrl=https%3A%2F%2Fhome.m.jd.com%2FmyJd%2Fnewhome.action%3Fsceneval%3D2%26ufc%3D%26%2FmyJd%2Fhome.action'
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                "Accept": "*/*",
                "Referer": "https://passport.jd.com/uc/login?ltype=logout&ReturnUrl=https://app.jd.com/"
            }
            req = self.http.get(url, headers=headers, proxies=proxy, timeout=2)  # 走代理，就不行

            logger.success(f'登陆成功: {req.cookies}')
            ckdict = req.cookies.get_dict()
            if ckdict is None:
                return {'code': -1, 'msg': f'登陆失败: 检查pid, cid是否与用户ip归属地一致正确'}
            if len(ckdict) == 0:
                return {'code': -1, 'msg': f'登陆失败: 检查pid, cid是否与用户ip归属地一致正确'}
            cookie = ''
            for key in ckdict:
                cookie += key + '=' + ckdict[key] + ';'
            return {'code': 0, 'msg': '登陆成功', 'cookie': cookie}
        else:
            return {'code': -1, 'msg': '未知错误'}


#   获取缴费前信息
def getPhoneInfo(phone, cookie, money):
    url = f'https://chongzhi.jd.com/json/order/search_searchPhone.action?mobile={phone}'
    headers = {
        "Host": "chongzhi.jd.com",
        "Connection": "keep-alive",
        "sec-ch-ua": "\"Google Chrome\";v=\"119\", \"Chromium\";v=\"119\", \"Not?A_Brand\";v=\"24\"",
        "Accept": "*/*",
        "X-Requested-With": "XMLHttpRequest",
        "sec-ch-ua-mobile": "?0",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "sec-ch-ua-platform": "\"macOS\"",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": "https://chongzhi.jd.com/iframe_fast.action",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Cookie": cookie,
    }
    res = requests.get(url, headers=headers, proxies=proxy_ip())
    if res.status_code != 200:
        return {'code': -1, 'msg': '获取号码信息失败'}
    area = res.json().get('area')
    providerName = res.json().get('providerName')
    ISP = ''
    if providerName == '联通':
        ISP = 0
    if providerName == '移动':
        ISP = 1
    if providerName == '电信':
        ISP = 2
    url = f'https://chongzhi.jd.com/json/order/search_searchSkuId.action?ISP={ISP}&area={area}&filltype=0&faceValue={money}'
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        return {'code': -1, 'msg': '获取号码信息失败'}
    skuId = res.json().get('skuId')
    if skuId == '':
        return {'code': -1, 'msg': '获取号码信息失败'}
    return {'code': 0, 'skuId': skuId}


def order_confirm(skuId, mobile, cookies, proxy):
    params = {
        'skuId': skuId,
        'mobile': mobile,
        'entry': '4',
        't': str(time.time() * 1000),
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/114.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Referer': 'https://chongzhi.jd.com/iframe_fast.action',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
        'Cookie': cookies,
    }
    response = requests.get('https://chongzhi.jd.com/order/order_confirm.action', params=params,
                            headers=headers, proxies=proxy)
    tree = etree.HTML(response.text)
    try:
        hideKey = tree.xpath('//*[@id="hideKey"]/@value')[0]
    except Exception as e:
        return False
    if hideKey:
        logger.info(f"{datetime.datetime.now()}--order_confirm--{hideKey}")
        return hideKey


def encode_chinese(string):
    chinese_pattern = re.compile('[\u4e00-\u9fa5]')  # 匹配中文字符的正则表达式
    chinese_characters = chinese_pattern.findall(string)  # 提取中文字符
    for ch in set(chinese_characters):  # 去重
        encoded_ch = quote(ch, encoding='utf-8')  # 对中文字符进行编码
        string = string.replace(ch, encoded_ch)  # 替换原始字符串中的中文字符
    return string


#   创建订单
@app.route('/api/jd/mobile/createOrder', methods=['POST'])
@logger.catch
def createOrder():
    cookie = encode_chinese(request.json.get('cookie'))
    if cookie is None or cookie == '':
        return {'code': -1, 'msg': 'cookie不能为空'}
    phone = request.json.get('phone')
    money = request.json.get('money')
    mch = request.json.get('mch')
    proxy = None
    phoneInfo = getPhoneInfo(phone, cookie, money)
    if phoneInfo.get('code') != 0:
        return phoneInfo
    skuId = phoneInfo.get('skuId')
    Password = ""
    hideKey = order_confirm(skuId, phone, cookie, proxy)  # 下单
    if hideKey is False:
        url = f'https://chongzhi.jd.com/order/order_confirm.action?skuId={skuId}&mobile={phone}&entry=4&t={time.time() * 1000}'
        headers = {
            "Host": "chongzhi.jd.com",
            "Connection": "keep-alive",
            "sec-ch-ua": "\"Google Chrome\";v=\"119\", \"Chromium\";v=\"119\", \"Not?A_Brand\";v=\"24\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"macOS\"",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
            "Referer": "https://chongzhi.jd.com/iframe_fast.action",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Cookie": cookie,
        }
        try:
            res = requests.get(url, headers=headers, proxies=proxy, allow_redirects=False)  # 下单
            orderId = re.findall(r'orderId=(.*?)&', res.headers['location'])[0]
        except Exception as e:
            if 'login.aspx' in res.headers['location']:
                return {'code': -1, 'msg': '登陆失效'}
        payUrl = {"category": "jump", "des": "m",
                  "url": f"https://st.jingxi.com/order/n_detail_v2.shtml?deal_id={orderId}", "keplerID": "0",
                  "keplerFrom": "1", "kepler_param": {"source": "kepler-open", "otherData": {"mopenbp7": "0"},
                                                      "channel": "8bfd09e186324410bd59504c345afd85"},
                  "union_open": "union_cps"}
        payUrl = f"openapp.jdmobile://virtual?params={quote(json.dumps(payUrl, ensure_ascii=False))}"
        return {'code': 0, 'msg': '创建订单成功', 'data': {'orderNo': orderId, 'payUrl': payUrl, 'cookie': cookie}}
    else:
        t = int(time.time() * 1000)
        params = {
            'mobile': phone,
            'messageId': '',
            'skuId': skuId,
            'hideKey': hideKey,
            'payType': '0',
            'paymentPassword': hashlib.md5(Password.encode('utf-8')).hexdigest().lower(),
            'usedJingdouNum': '0',
            'couponIds': '',
            'checkMessage': 'true',
            'messageCode': '',
            'entry': '4',
            'onlinePay': str(money),
        }
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
            'Referer': f'https://chongzhi.jd.com/order/order_confirm.action?skuId={skuId}&mobile={phone}&entry=4&t={t}',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
            'Cookie': cookie,
        }
        try:
            response = requests.get('https://chongzhi.jd.com/order/order_createOrder.action', params=params,
                                    headers=headers, allow_redirects=False)  # 下单
            location = response.headers["location"]
        except Exception as e:
            if '充值次数超出上限' in response.text:
                return {'code': -2, 'msg': '您好，当月充值次数超出上限，请换其他账号下单'}
            logger.error(response.headers)
            ErrInfo = re.findall(r'#RISK#(.*?)~', response.text)[0]
            return {'code': -1, 'msg': f'系统异常：{ErrInfo}\n请更换京东账号重试'}
        logger.success(f'创建订单成功: {location}')
        orderId = re.findall("orderId=(.*?)&", location)[0]
        payUrl = {"category": "jump", "des": "m",
                  "url": f"https://st.jingxi.com/order/n_detail_v2.shtml?deal_id={orderId}", "keplerID": "0",
                  "keplerFrom": "1", "kepler_param": {"source": "kepler-open", "otherData": {"mopenbp7": "0"},
                                                      "channel": "8bfd09e186324410bd59504c345afd85"},
                  "union_open": "union_cps"}
        payUrl = f"openapp.jdmobile://virtual?params={quote(json.dumps(payUrl, ensure_ascii=False))}"
        return {'code': 0, 'msg': '创建订单成功', 'data': {'orderNo': orderId, 'payUrl': payUrl, 'cookie': cookie}}


#   查询订单
@app.route('/api/jd/mobile/queryOrder', methods=['POST'])
def queryOrder():
    #   orderNo, cookies
    orderNo = request.json.get('orderNo')
    cookie = encode_chinese(request.json.get('cookie'))
    mch = request.json.get('mch')
    try:
        url = f'https://chongzhi.jd.com/order/order_autoDetail.action?orderId={orderNo}'
        headers = {
            "Host": "chongzhi.jd.com",
            "Connection": "keep-alive",
            "sec-ch-ua": "\"Google Chrome\";v=\"119\", \"Chromium\";v=\"119\", \"Not?A_Brand\";v=\"24\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"macOS\"",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Sec-Fetch-Site": "same-site",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
            "Referer": "https://order.jd.com/",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cookie": cookie,
        }
        res = requests.get(url, headers=headers, allow_redirects=False, proxies=proxy_ip()).text
        if 'div class=fl>订单号：' not in res:
            return {'code': -1, 'msg': '查询订单失败,登陆失效'}
        orderNo = re.findall(r'<div class=fl>订单号：(.*?) &', res)[0]
        statusMsg = re.findall(r'状态：<span class="ftx-02">(.*?)</span>', res)[0]
        phone = re.findall(r'<li>手机号码：(.*?)</li>', res)[0]
        money = re.findall(r'<li>充值面额：(.*?)</li>', res)[0]
        type = re.findall(r'充值类型：(.*?)</li>', res)[0]
        times = re.findall(r'下单时间：(.*?)</li>', res)[0]
        dataInfo = {'phone': phone, 'money': money, 'type': type, 'times': times}
        if statusMsg == '等待付款':
            return {'code': 0, 'msg': statusMsg, 'data': {'orderNo': orderNo, 'statusCode': 100},
                    'dataInfo': dataInfo}
        elif statusMsg == '正在充值':
            return {'code': 0, 'msg': statusMsg, 'data': {'orderNo': orderNo, 'statusCode': 101},
                    'dataInfo': dataInfo}
        elif statusMsg == '充值成功':
            return {'code': 0, 'msg': statusMsg, 'data': {'orderNo': orderNo, 'statusCode': 102},
                    'dataInfo': dataInfo}
        elif statusMsg == '充值失败,退款处理中':
            return {'code': 0, 'msg': statusMsg, 'data': {'orderNo': orderNo, 'statusCode': 104},
                    'dataInfo': dataInfo}
        elif statusMsg == '充值失败,退款成功':
            return {'code': 0, 'msg': statusMsg, 'data': {'orderNo': orderNo, 'statusCode': 105},
                    'dataInfo': dataInfo}
        elif statusMsg == '订单取消':
            return {'code': 0, 'msg': statusMsg, 'data': {'orderNo': orderNo, 'statusCode': 103},
                    'dataInfo': dataInfo}
        else:
            return {'code': -1, 'msg': f'查询订单失败,未知错误：{statusMsg}'}
    except Exception as e:
        return {'code': -1, 'msg': f'查询订单失败,系统异常：{e}'}


#   获取登陆二维码
@app.route('/api/jd/mobile/getQrcode', methods=['POST'])
@logger.catch
def getQrcode():
    jdThor = JdThor()
    cid = request.json.get('cid')
    pid = request.json.get('pid')
    proxy = None
    if proxy is None or proxy == '':
        proxy = proxy_ip(pid, cid)
    else:
        proxy = {'http': proxy, "https": proxy}
    return jdThor.getQrcode(proxy)


#   检测二维码状态
@app.route('/api/jd/mobile/checkQrcode', methods=['POST'])
def checkQrcode():
    jdThor = JdThor()
    wlfstk_smdl = request.json.get('qrToken')
    QRCodeKey = request.json.get('QRCodeKey')
    cid = request.json.get('cid')
    pid = request.json.get('pid')
    proxy = None
    if proxy is None or proxy == '':
        proxy = proxy_ip(pid, cid)
    else:
        proxy = {'http': proxy, "https": proxy}
    return jdThor.checkQrcode(wlfstk_smdl, QRCodeKey, proxy)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=31123, debug=True, threaded=True)
