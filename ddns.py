import json
import logging
import smtplib
import os
import traceback
from email.mime.text import MIMEText
from email.utils import formataddr
from urllib.request import urlopen

from aliyunsdkalidns.request.v20150109.AddDomainRecordRequest import AddDomainRecordRequest
from aliyunsdkalidns.request.v20150109.DescribeSubDomainRecordsRequest import DescribeSubDomainRecordsRequest
from aliyunsdkalidns.request.v20150109.UpdateDomainRecordRequest import UpdateDomainRecordRequest
from aliyunsdkcore.auth.credentials import AccessKeyCredential
from aliyunsdkcore.client import AcsClient

"""
变量
    IPv4 是否开启ipv4 ddns解析,True为开启，False为关闭
    IPv6 是否开启IPv6 ddns解析,True为开启，False为关闭
    accessKeyId 阿里云的accessKeyId
    accessSecret 阿里云的accessSecret
    DomainName 主域名名称
    SubDomain 子域名
    alapi_ipv4 阿里云获取子域名解析记录列表 Type值为A 
    alapi_ipv6 阿里云获取子域名解析记录列表 Type值为AAAA
    dir 获取当前目录
    所有必填项全部用***代替
"""
IPv4 = False
IPv6 = False
accessKeyId = "***"
accessSecret = "***"
DomainName = "***"
SubDomain_list = ["***", "***", "***"]
alapi_ipv4 = "0"
urlapi_ipv4 = "0"
alapi_ipv6 = "0"
urlapi_ipv6 = "0"
date = []
dir = os.path.dirname(__file__)


credentials = AccessKeyCredential(accessKeyId, accessSecret)
client = AcsClient(region_id='cn-chengdu', credential=credentials)
# client = AcsClient(accessKeyId, accessSecret, 'cn-hangzhou')

"""方法参数实例
名称          类型   必填      描述                                                      示例值及参考API
Lang        String  否       语言                                                      示例值：en
DomainName  String  是       域名名称                                                   示例值：example.com
RecordId    String  是       解析记录的ID                                                示例值：9999985
RR          String  是       主机记录   如果要解析@.exmaple.com，主机记录要填写”@”，而不是空   示例值：www
Type        String  是       解析记录类型，参见解析记录类型格式                              示例值：A，AAA
Value       String  是       记录值                                                     示例值：202.106.0.20
TTL         Long    否       解析生效时间，默认为600秒（10分钟）参见TTL定义说明                示例值：600
"""

class Logger:
    def __init__(self, path, clevel=logging.DEBUG, Flevel=logging.DEBUG):
        self.logger = logging.getLogger(path)
        self.logger.setLevel(logging.DEBUG)
        fmt = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')
        # 设置CMD日志
        sh = logging.StreamHandler()
        sh.setFormatter(fmt)
        sh.setLevel(clevel)
        # 设置文件日志
        fh = logging.FileHandler(path)
        fh.setFormatter(fmt)
        fh.setLevel(Flevel)
        self.logger.addHandler(sh)
        self.logger.addHandler(fh)

    def debug(self, message):
        self.logger.debug(message, exc_info=True)

    def info(self, message):
        self.logger.info(message)

    def war(self, message):
        self.logger.warn(message, exc_info=True)

    def error(self, message):
        self.logger.error(message)

    def cri(self, message):
        self.logger.critical(message, exc_info=True, stack_info=True)

logddns = Logger(os.path.join(dir, 'ddns.log'), logging.DEBUG)

def update(Lang, RecordId, RR, Type, Value, TTL):  # 修改域名解析记录
    try:
        request = UpdateDomainRecordRequest()
        request.set_accept_format('json')
        request.set_Lang(Lang)
        request.set_RecordId(RecordId)
        request.set_RR(RR)
        request.set_Type(Type)
        request.set_Value(Value)
        request.set_TTL(TTL)
        update_response = client.do_action_with_exception(request)
    except Exception:
        logddns.error(traceback.format_exc())
    else:
        return update_response


def add(Lang, DomainName, RR, Type, Value, TTL):  # 添加新的域名解析记录
    try:
        request = AddDomainRecordRequest()
        request.set_accept_format('json')
        request.set_Lang(Lang)
        request.set_DomainName(DomainName)
        request.set_RR(RR)
        request.set_Type(Type)
        request.set_Value(Value)
        request.set_TTL(TTL)
        add_response = client.do_action_with_exception(request)
    except Exception:
        logddns.error(traceback.format_exc())
    else:
        return add_response


def get(Lang, Type, SubDomain):
    try:
        request = DescribeSubDomainRecordsRequest()
        request.set_accept_format('json')
        request.set_Lang(Lang)
        request.set_Type(Type)
        request.set_SubDomain(SubDomain)
        response = client.do_action_with_exception(request)
    except Exception:
        logddns.error(traceback.format_exc())
    else:
        return response


def start_ipv4():
    global alapi_ipv4
    global urlapi_ipv4
    global date
    try:
        for SubDomain in SubDomain_list:
            response = get("en", "A", SubDomain + "." + DomainName)
            domain_list = json.loads(response)
            urlapi_ipv4 = str(urlopen('https://api-ipv4.ip.sb/ip').read(), encoding='utf-8').replace('\n', '')
            if domain_list['TotalCount'] == 0:
                add("en", DomainName, SubDomain, "A", urlapi_ipv4, "600")
                date.append("添加域名解析成功  域名为：" + SubDomain + "." + DomainName + "  IP为：" + urlapi_ipv4)
                logddns.info("添加域名解析成功  域名为：" + SubDomain + "." + DomainName + "  IP为：" + urlapi_ipv4)
            elif domain_list['TotalCount'] == 1:
                alapi_ipv4 = domain_list['DomainRecords']['Record'][0]['Value'].strip()
                if alapi_ipv4 == urlapi_ipv4:
                    logddns.info("域名：" + SubDomain + "." + DomainName + "  IP未发生改变：" + alapi_ipv4)
                else:
                    update_response = update("en",
                                             domain_list['DomainRecords']['Record'][0]['RecordId'],
                                             SubDomain,
                                             "A", urlapi_ipv4,
                                             "600")
                    if update_response is not None:
                        date.append("域名：" + SubDomain + "." + DomainName + "  IP变更为：" + urlapi_ipv4)
                        logddns.info("域名：" + SubDomain + "." + DomainName + "  IP变更为：" + urlapi_ipv4)
    except Exception:
        logddns.error(traceback.format_exc())
    return date


def start_ipv6():
    global alapi_ipv6
    global urlapi_ipv6
    global date
    try:
        for SubDomain in SubDomain_list:
            response = get("en", "AAAA", SubDomain + "." + DomainName)
            domain_list = json.loads(response)
            urlapi_ipv6 = str(urlopen('https://api-ipv6.ip.sb/ip').read(), encoding='utf-8').replace('\n', '')
            if domain_list['TotalCount'] == 0:
                add_response = add("en", DomainName, SubDomain, "AAAA", urlapi_ipv6, "600")
                if add_response is not None:
                    date.append("添加域名解析成功  域名为：" + SubDomain + "." + DomainName + "  IP为：" + urlapi_ipv6)
                    logddns.info("添加域名解析成功  域名为：" + SubDomain + "." + DomainName + "  IP为：" + urlapi_ipv6)
            elif domain_list['TotalCount'] == 1:
                alapi_ipv6 = domain_list['DomainRecords']['Record'][0]['Value'].strip()
                if alapi_ipv6 == urlapi_ipv6:
                    logddns.info("域名：" + SubDomain + "." + DomainName + "  IP未发生改变：" + alapi_ipv6)
                else:
                    update_response = update("en",
                                             domain_list['DomainRecords']['Record'][0]['RecordId'],
                                             SubDomain,
                                             "A",
                                             urlapi_ipv6,
                                             "600")
                    if update_response is not None:
                        date.append("域名：" + SubDomain + "." + DomainName + "  IP变更为：" + urlapi_ipv6)
                        logddns.info("域名：" + SubDomain + "." + DomainName + "  IP变更为：" + urlapi_ipv6)
    except Exception:
        logddns.error(traceback.format_exc())
    return date


def send_emile(email_text):
    my_name = "***"  # 发件人姓名
    my_email = "***"  # 发件人邮箱
    my_passwd = "***"  # 发件人pop3授权码 可在qq邮箱开启功能查看
    to_email = "***"  # 收件人邮箱地址
    to_content = email_text  # 邮件内容
    to_subject = "***"  # 邮件主题
    to_name = "***"  # 收件人姓名
    msg = MIMEText(to_content, "plain", "utf-8")  # 写入邮件内容

    msg["From"] = formataddr([my_name, my_email])  # 发件人信息

    msg["To"] = formataddr([to_name, to_email])  # 收件人信息

    msg["Subject"] = to_subject  # 邮件主题
    try:
        server = smtplib.SMTP("smtp.qq.com", 25)  # 连接邮箱服务器
        server.login(my_email, my_passwd)  # 登录自己邮箱 密码为ppo3授权码
        server.sendmail(my_email, [to_email, ], msg.as_string())  # 发送邮件
        server.quit()  # 退出邮箱连接
        logddns.info("已发送邮件")
    except smtplib.SMTPException as e:
        logddns.error(e)


def start():
    if IPv4:
        start_ipv4()
    else:
        logddns.info("IPv4未启用")
    if IPv6:
        start_ipv6()
    else:
        logddns.info("IPv6未启用")
    if len(date) != 0:
        space = " \r\n"
        send_emile(email_text=space.join(date)) #不需要邮件功能直接注释本行


if __name__ == '__main__':
    start()
