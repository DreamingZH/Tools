import re
import os
import sys
import string
import datetime
import requests
import tkinter as tk
from tkinter import ttk
from urllib.parse import quote
from urllib.parse import unquote

province = '浙江省'
city = '杭州市'
district = '西湖区'
address = '浙江省杭州市西湖区三墩镇杨家桥社区浙江大学（紫金港校区）'
area = '{} {} {}'.format(province, city, district)

u_city = quote(city, 'utf-8')
u_province = quote(province, 'utf-8')
u_area = quote(area, 'utf-8')
uaddress = quote(address, 'utf-8')

def_dict = old_dict = time = eai_sess_list = ''
url = 'https://healthreport.zju.edu.cn/ncov/wap/default/index'


def get_old_eai_sess():
    global eai_sess_list
    if not os.path.exists('eai-sess.txt'):
        with open('eai-sess.txt', 'w') as f:
            f.write('Initialize.')
            return 0
    file = open('eai-sess.txt', 'rt')
    eai_sess_list = file.readlines()
    file.close()
    return eai_sess_list


def get_new_eai_sess():
    win = tk.Tk()
    win.title("健康打卡")
    win.geometry('280x175+600+250')
    win.iconbitmap(r'透明校徽.ico')
    win.rowconfigure(0, weight=1)
    win.columnconfigure(0, weight=1)
    win.attributes('-alpha', 0.85)

    label_1 = tk.Label(win, text='Setting', bg='white', fg='grey', font=('Lucida Sans', 15, "italic"), width=25,
                       height=0)
    label_1.pack()

    monty = tk.LabelFrame(font=('Lucida Sans', 10, "italic"), text='Cookie')
    ttk.Label(monty, text="Your eai-sess:", font=('Lucida Sans', 8, "italic")).grid(column=0, row=0, sticky='W')
    start = ttk.Entry(monty, font=('Lucida Sans', 10), width=20)
    start.grid(column=0, row=1, sticky='W')
    monty.pack()

    label_2 = tk.Label(win, text='', width=25, height=0)
    label_2.pack()

    def quit_window():
        win.destroy()

    def exit_win():
        sys.exit(0)

    def get():
        global eai_sess
        eai_sess = start.get()
        with open('eai-sess.txt', 'w') as eai_file:
            eai_file.write(eai_sess + '\n')
        quit_window()

    button = tk.Button(win, text="Finish!", bg="white", font=('Comic Sans MS', 10), width=15, height=0,
                       command=get)
    button.pack()

    button_ = tk.Button(win, text="Shut Down", bg="white", fg='red', font=('Comic Sans MS', 10), width=15, height=0,
                        command=exit_win)
    button_.pack()

    win.mainloop()


def encode_uri_component(s):
    s = list(str(s))
    for i in range(len(s)):
        if s[i] not in string.ascii_letters and s[i] not in string.digits and s[i] not in "~!*()'_-.":
            if ord(s[i]) > 256:
                s[i] = quote(s[i])
            else:
                s[i] = hex(ord(s[i])).replace('0x', '%').upper()
    return ''.join(s)


def decode_uri_component(s):
    list_s = list(s)
    for i in range(len(list_s)):
        if list_s[i] == '%':
            list_s[i] = chr(int(list_s[i + 1] + list_s[i + 2], 16))
            list_s[i + 1] = list_s[i + 2] = ''
    return ''.join(list_s)


def get_params(obj):
    data = []
    for key in obj:
        value = obj[key]
        if type(value) == list:
            for k in value:
                data.append('{}'.format(encode_uri_component(key + "[]") + '=' + encode_uri_component(k)))
        else:
            data.append('{}'.format(encode_uri_component(key) + '=' + encode_uri_component(value)))
    return "&".join(data)


def get_page():
    global def_dict, old_dict, header, Cookie
    while True:
        try:
            page = requests.Session().get(url, headers=header)
            break
        except UnicodeEncodeError:
            get_new_eai_sess()
        Cookie = 'eai-sess={}'.format(eai_sess.rstrip('\n'))
        header = {"Cookie": Cookie,
                  'User-Agent':
                      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.54 Safari/537.36 Edg/101.0.1210.39'}

        get_page()

    encoding = page.apparent_encoding
    text_doc = page.content.decode(encoding)
    text_list = text_doc.split('\n')
    for i in range(len(text_list)):
        text_list[i] += '\n'

    def_dict = old_dict = ''
    for i in text_list:
        define = re.findall('(\{.+?\});\n', i)
        old_info = re.findall('(\{.+?\}),\n', i)
        if define:
            for j in define:
                def_dict = j
        if old_info:
            for k in old_info:
                try:
                    k = k.replace('null', 'None')
                    dictionary = eval(k)
                    if 'uid' in dictionary:
                        old_dict = k
                        break
                except NameError:
                    pass

    if not def_dict:  # 格式问题
        define = re.findall('def = (\{(.|\\n)+?\});\\n', text_doc)
        for i in define:
            for j in i:
                j = j.strip('\n')
                j = j.strip(' ')
                if j:
                    j = j.split('\n')
                    for k in range(len(j)):
                        j[k] = j[k].strip(' ')
                    j = list('"'.join(j).replace(':', '":'))
                    j[-2] = ''
                    def_dict = eval(''.join(j))
                    for k in def_dict:
                        if def_dict[k] == 0:
                            def_dict[k] = '0'

    if not def_dict:  # eai-sess 输入错误
        get_new_eai_sess()  # 重新获取
        Cookie = 'eai-sess={}'.format(eai_sess.rstrip('\n'))  # 更新 Cookie
        header = {"Cookie": Cookie,
                  'User-Agent':
                      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.54 Safari/537.36 Edg/101.0.1210.39'}

        get_page()  # 重新访问

    if not old_dict:  # 无打卡记录
        win = tk.Tk()
        win.title("健康打卡")
        win.geometry('280x170+600+250')
        win.rowconfigure(0, weight=1)
        win.columnconfigure(0, weight=1)
        win.iconbitmap(r'透明校徽.ico')
        win.attributes('-alpha', 0.85)

        label = tk.Label(win, text='请先手动上报一次\n随后再使用本方式打卡', bg='white', fg='black',
                         font=('华文新魏', 20), width=30,
                         height=5)
        label.pack()

        def quit_window():
            win.destroy()

        button = tk.Button(win, text="OK", bg="white", font=('Century Schoolbook', 12), width=30, height=1,
                           command=quit_window)
        button.pack()

        win.mainloop()

        sys.exit(0)


def exception(dic):
    window = tk.Tk()
    window.title("健康打卡")
    window.geometry('280x170+600+250')
    window.rowconfigure(0, weight=1)
    window.columnconfigure(0, weight=1)
    window.iconbitmap(r'透明校徽.ico')
    window.attributes('-alpha', 0.85)

    label1 = tk.Label(window, text='{}'.format(dic['m']), bg='white', fg='black',
                      font=('华文新魏', 20), width=30,
                      height=2)
    label1.pack()

    label2 = tk.Label(window, text='{}'.format(time), bg='white', fg='black',
                      font=('Lucida Sans', 15), width=30,
                      height=3)
    label2.pack()

    def quit_win():
        window.destroy()

    button1 = tk.Button(window, text="OK", bg="white", font=('Century Schoolbook', 12), width=30, height=1,
                        command=quit_win)
    button1.pack()

    window.mainloop()


def run():
    global time, header
    get_page()
    r = eval(def_dict)
    d = eval(old_dict)

    if d['jrdqtlqk']:
        d['jrdqtlqk'] = eval(d['jrdqtlqk'])
    else:
        d['jrdqtlqk'] = ["0"]
    d['uid'] = r['uid']
    d['id'] = r['id']
    d['created'] = r['created']
    d['date'] = r['date']
    d['address'] = decode_uri_component(uaddress)
    d['area'] = decode_uri_component(u_area)
    d['province'] = decode_uri_component(u_province)
    d['city'] = decode_uri_component(u_city)

    tar_doc = quote(get_params(d))
    target_file = unquote(tar_doc, 'utf-8')

    target_page = 'https://healthreport.zju.edu.cn/ncov/wap/default/save'

    header = {"Cookie": Cookie,
              'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
    tar_page = requests.Session().post(target_page, headers=header, files={'file': target_file})

    time = str(datetime.datetime.today())[0:19].replace(' ', '\n')
    t = tar_page.content.decode("utf-8").replace('true', 'True')

    dic = eval(t)
    if dic['m'] == '今天已经填报了' or dic['m'] == '操作成功':
        print(dic['m'])
    else:
        exception(dic)


if __name__ == '__main__':
    while not get_old_eai_sess():
        get_new_eai_sess()
    for eai_sess in eai_sess_list:
        if not eai_sess:
            continue
        Cookie = 'eai-sess={}'.format(eai_sess.rstrip('\n'))
        header = {"Cookie": Cookie,
                  'User-Agent':
                      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.54 Safari/537.36 Edg/101.0.1210.39'}
        run()
    sys.exit(0)
