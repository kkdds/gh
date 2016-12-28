#! /usr/bin/python3.4
# -*- coding: utf-8 -*-
import requests
import asyncio, os, json, time
import jinja2
import aiohttp_jinja2
import urllib.request
import configparser
import threading
import RPi.GPIO as GPIO
from aiohttp import web
ttim=0
t=object

ver='20161228'
stapwd='abc'
setpwd='gh2016'
softPath='/home/pi/gh/'

kconfig=configparser.ConfigParser()
if os.path.exists(softPath+"setting.ini"):
    kconfig.read(softPath+"setting.ini")
else: 
    f = open(softPath+"setting.ini", 'w')
    f.close()
    kconfig.read(softPath+"setting.ini")
    kconfig.add_section('gh')
    kconfig.write(open(softPath+"setting.ini","w"))

try:
    shell_ud_t1_set=kconfig.getint("gh","shell_ud_t1_set")
except:
    kconfig.add_section('gh')
    shell_ud_t1_set=2000
    kconfig.set("gh","shell_ud_t1_set",str(shell_ud_t1_set))

try:
    shell_ud_t2u_set=kconfig.getint("gh","shell_ud_t2u_set")
except:
    shell_ud_t2u_set=9000
    kconfig.set("gh","shell_ud_t2u_set",str(shell_ud_t2u_set))

try:
    shell_ud_t2d_set=kconfig.getint("gh","shell_ud_t2d_set")
except:
    shell_ud_t2d_set=7000
    kconfig.set("gh","shell_ud_t2d_set",str(shell_ud_t2d_set))

try:
    shell_ud_t3_set=kconfig.getint("gh","shell_ud_t3_set")
except:
    shell_ud_t3_set=5000
    kconfig.set("gh","shell_ud_t3_set",str(shell_ud_t3_set))

try:
    stapwd = kconfig.get("gh","stapwd")
except:
    stapwd = 'abc'
    kconfig.set("gh","stapwd",stapwd)

try:
    sn = kconfig.get("gh","sn")
except:
    sn = 'gh001'
    kconfig.set("gh","sn",sn)


kconfig.write(open(softPath+"setting.ini","w"))

seled_cai=[]
seled_cai_cn=[]

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
io_dy=23 #锅炉电源
io_zq=24 #蒸汽
GPIO.setup(io_dy, GPIO.OUT)
GPIO.setup(io_zq, GPIO.OUT)
GPIO.output(io_dy, 1)
GPIO.output(io_zq, 1)

io_in1=12
GPIO.setup(io_in1,GPIO.IN,pull_up_down=GPIO.PUD_UP)

moto_1_p=13 #脉宽输出
moto_1_f=19 #正转
moto_1_r=26 #反转
GPIO.setup(moto_1_f, GPIO.OUT)
GPIO.setup(moto_1_r, GPIO.OUT)
GPIO.setup(moto_1_p, GPIO.OUT)
p = GPIO.PWM(moto_1_p, 1500)
p.start(0)


guolupower=0
watchdog=0
eTimer1=False
eIntval1=5
sta_shell=0
sta_onoff=0
shell_up_down=0

'''
sta_shell
0 top stop
1 running
2 bottom stop

shell_up_down
0 to up
2 to bottom

running_sta
0 stop
1 running
'''


from os import system
system('sudo ifdown wlan0')
import pexpect
import re
from threading import Thread
from time import sleep


class WAM_AP(object):
    def _get_end(self):
        while True:
            sleep(5)
    def __init__(self):
        self._process = pexpect.spawn('sudo create_ap --no-virt -n -g 192.168.2.105 wlan0 '+sn+' 66341703')
        self._end_thread = Thread(target=self._get_end)
        self._end_thread.start()
WAM_AP()


@asyncio.coroutine
def return_sta(request):
    global eTimer1,eIntval1,sta_onoff,watchdog
    global shell_up_down,sta_shell,guolupower
    global stapwd,setpwd,softPath,tempeture_1,tempeture_2,ttim,t

    hhdd=[('Access-Control-Allow-Origin','*')]
    po = yield from request.post()
    #if po['p'] == stapwd:
    if 1:
        
        if po['m'] == 'login':
            sta_shell=0
            sta_onoff=0
            tbody= '{"p":"ok"}'
            return web.Response(headers=hhdd ,body=tbody.encode('utf-8'))
        
        elif po['m'] == 'sta':
            watchdog=0
            tbody= '{"shell_sta":'+str(sta_shell)
            tbody+= ',"guolupower":'+str(guolupower)
            tbody+= ',"tmp1":'+str(tempeture_1)+'}'
            return web.Response(headers=hhdd ,body=tbody.encode('utf-8'))
        
        elif po['m'] == 'addtime':
            watchdog=0
            #print('old stop at'+str(eIntval1))
            eIntval1+=int(po['d'])
            #print('shall stop at '+str(eIntval1))
            tbody= '{"addtime":'+str(eIntval1-int(time.time()))+'}'
            return web.Response(headers=hhdd ,body=tbody.encode('utf-8'))
                
        elif po['m'] == 'gpioon':
            delaytime=po['t']
            eTimer1=True
            eIntval1=int(time.time())+int(delaytime)
            ttim=time.time()
            print('eTimer1 start')

            sta_onoff=1

            if po['d']== 'dy':
                guolupower=1
                GPIO.output(io_dy, 0)
                tbody= '{"a":"dy","b":"on"}'
            if po['d']== 'zq':
                GPIO.output(io_zq, 0)
                tbody= '{"a":"zq","b":"on"}'
            print(tbody)
            return web.Response(headers=hhdd ,body=tbody.encode('utf-8'))
                
        elif po['m'] == 'gpiooff':
            if po['d']== 'all':
                sta_onoff=0
                GPIO.output(io_zq, 1)
                eTimer1=False
                tbody= '{"a":"all","b":"off"}'
            elif po['d']== 'dy':
                guolupower=0
                GPIO.output(io_dy, 1)
                tbody= '{"a":"dy","b":"off"}'
            elif po['d']== 'dy':
                GPIO.output(io_zq, 1)
                tbody= '{"a":"zq","b":"off"}'
            print(tbody)
            return web.Response(headers=hhdd ,body=tbody.encode('utf-8'))
                
        elif po['m'] == 'shell':
            if po['d']== 'up' and sta_shell!=1:
                t = threading.Timer(shell_ud_t1_set/1000, tt2)
                GPIO.output(moto_1_r, 0)
                GPIO.output(moto_1_f, 1)
                p.ChangeDutyCycle(100)
                t.start()
                shell_up_down=0
                sta_shell=1
                tbody= '{"a":"shell","b":"up"}'
            elif po['d']== 'dw' and sta_shell!=1:
                t = threading.Timer(shell_ud_t1_set/1000, tt2)
                GPIO.output(moto_1_r, 1)
                GPIO.output(moto_1_f, 0)
                p.ChangeDutyCycle(100)
                t.start()
                shell_up_down=2
                sta_shell=1
                tbody= '{"a":"shell","b":"dw"}'
            elif sta_shell==1:
                tbody= '{"a":"shell","b":"smil stop"}'
            print(tbody)
            ttim=time.time()
            return web.Response(headers=hhdd ,body=tbody.encode('utf-8'))

    else:
        tbody= '{"p":"error"}'
        return web.Response(headers=hhdd ,body=tbody.encode('utf-8'))


def tt2():
    global t,shell_ud_t2d_set,shell_ud_t2u_set,shell_up_down,ttim
    if shell_up_down==0:
        shell_t2=shell_ud_t2u_set/1000
    else:
        shell_t2=shell_ud_t2d_set/1000
    t = threading.Timer(shell_t2, tt3)
    p.ChangeDutyCycle(100)
    t.start()
    print('tt2 '+str(ttim-time.time()))

def tt3():
    global t,shell_ud_t3_set,shell_up_down,ttim
    t = threading.Timer(shell_ud_t3_set/1000, tt4)
    if shell_up_down==0:
        p.ChangeDutyCycle(20)
    else:
        p.ChangeDutyCycle(20)
    t.start()
    print('tt3 '+str(ttim-time.time()))

def tt4():
    global t,ttim
    t = threading.Timer(6, ttfin)
    p.ChangeDutyCycle(4)
    t.start()
    print('tt4 '+str(ttim-time.time()))

def ttfin():
    global ttim,shell_up_down,sta_shell
    p.ChangeDutyCycle(0)
    sta_shell=shell_up_down
    print('shell run end '+str(ttim-time.time()))


cut_name=''
cai_name=''
wat_name=''

@asyncio.coroutine
def setting(request):
    global shell_ud_t1_set,shell_ud_t2u_set,shell_ud_t2d_set,shell_ud_t3_set
    global ver,sn
    global stapwd,setpwd,softPath,seled_cai,seled_cai_cn
    global cut_name,cai_name,wat_name,seled_cai_cn
    hhdd=[('Access-Control-Allow-Origin','*')]
    tbody= '{"p":"error"}'

    po = yield from request.post()
    if po['m'] == 'l' and po['p'] == setpwd:
        tbody= '{"p":"ok"}'
        return web.Response(headers=hhdd ,body=tbody.encode('utf-8'))

    if po['m'] == 'get':
        cai_name= ''
        for i in seled_cai_cn:
            cai_name = cai_name+i+';'
        cai_name= str(cai_name)

        tbody = '{"p":"ok",'
        tbody+= '"ver":"'+ver+'",'
        tbody+= '"t1":"'+str(shell_ud_t1_set)+'",'
        tbody+= '"t2u":"'+str(shell_ud_t2u_set)+'",'
        tbody+= '"t2d":"'+str(shell_ud_t2d_set)+'",'
        tbody+= '"t3":"'+str(shell_ud_t3_set)+'",'
        tbody+= '"sn":"'+str(sn)+'",'
        tbody+= '"stapwd":"'+str(stapwd)+'"}'
        return web.Response(headers=hhdd ,body=tbody.encode('utf-8'))

    if po['m'] == 'w' and po['p'] == setpwd:
        shell_ud_t1_set=int(po['t1'])
        shell_ud_t2u_set=int(po['t2u'])
        shell_ud_t2d_set=int(po['t2d'])
        shell_ud_t3_set=int(po['t3'])
        sn=po['sn']
        stapwd=po['stapwd']
        kconfig.set("gh","shell_ud_t1_set",po['t1'])
        kconfig.set("gh","shell_ud_t2u_set",po['t2u'])
        kconfig.set("gh","shell_ud_t2d_set",po['t2d'])
        kconfig.set("gh","shell_ud_t3_set",po['t3'])
        kconfig.set("gh","sn",po['sn'])
        kconfig.set("gh","stapwd",stapwd)
        kconfig.write(open(softPath+"setting.ini","w"))
        tbody= '{"p":"ok","w":"ok"}'
        return web.Response(headers=hhdd ,body=tbody.encode('utf-8'))

    if po['m'] == 'addcai':
        scai=po['c']
        scai_cn=po['cn']
        if po['s'] == 'true':
            seled_cai.remove(scai)
            seled_cai_cn.remove(scai_cn)
            tbody= '{"p":"dec"}'
        else:
            seled_cai.append(scai)
            seled_cai_cn.append(scai_cn)
            tbody= '{"p":"add"}'

    if po['m'] == 'get_added_cai':
        tbody= '~'
        for i in seled_cai:
            tbody = tbody+i+';'
        tbody= str(tbody)

    return web.Response(headers=hhdd ,body=tbody.encode('utf-8'))


import zipfile
@asyncio.coroutine
def sys_update(request):
    global softPath
    hhdd=[('Access-Control-Allow-Origin','*')]
    posted = yield from request.post()
    #print(posted)
    tbody= '成功'
    #if posted['tp']=='core':
    try:
        upedfile=posted['cfile']
        ufilename = upedfile.filename
        ufilecont = upedfile.file
        content = ufilecont.read()
        with open(softPath+ufilename, 'wb') as f:
            f.write(content)
    except:
        tbody='上传文件打开失败'
    #解压缩
    try:
        fz = zipfile.ZipFile(softPath+"core.zip",'r')
        for file in fz.namelist():
            fz.extract(file,softPath)
        fz.close()
    except:
        tbody='解压失败'
    return web.Response(headers=hhdd ,body=tbody.encode('utf-8'),content_type='application/json')


@aiohttp_jinja2.template('upgrade.html')
def upgrade(request):
    #使用aiohttp_jinja2  methed 2
    global sn
    return {'html': 'upgrade','sn': sn}


import serial
tempeture_1=0
@asyncio.coroutine
def get_temp():
    global tempeture_1
    tt1=0
    while True:
        # 打开串口 发送 获得接收缓冲区字符
        ser = serial.Serial("/dev/ttyUSB0",parity=serial.PARITY_ODD,timeout=1)
        ser.write(b'\x02\x03\x10\x00\x00\x04\x40\xFA')
        recv = ser.read(7)
        #print(recv)
        if recv and recv[2]==8:
            tt1=(recv[3]*255+recv[4])/10
        else:
            #print(recv)
            tt1=0
        ser.close()
        yield from asyncio.sleep(0.5)

        tempeture_1=tt1
        #print(tempeture_1)


@asyncio.coroutine
def loop_info():
    global eTimer1,eIntval1,sta_shell,sta_onoff
    global watchdog,ttim
    global t,p
    while True:
        yield from asyncio.sleep(0.05)
        watchdog+=1
        if watchdog>100:
            watchdog=0;
            sta_onoff=0
            print('watchdog')
            GPIO.output(io_zq, 1)

        if eTimer1==True:
            #sta_shell=1
            if int(time.time())>=int(eIntval1):
                sta_onoff=0
                sta_shell=2
                GPIO.output(io_zq, 1)
                print('eTimer1 end '+str(time.time()-ttim))
                eTimer1=False
                sta_shell=2
                sta_onoff=0

        if GPIO.input(io_in1)==GPIO.LOW:
            sta_shell=0
            if t!=None:
                t.cancel()
            p.ChangeDutyCycle(0)
            print('shell over load')
    return 1


@asyncio.coroutine
def init(loop):    
    global softPath,ver
    app = web.Application(loop=loop)
    #使用aiohttp_jinja2
    aiohttp_jinja2.setup(app,loader=jinja2.FileSystemLoader(softPath+'tpl'))
    app.router.add_route('POST', '/sta', return_sta)
    app.router.add_route('POST', '/setting', setting)
    app.router.add_route('*', '/sys_update', sys_update)
    app.router.add_route('*', '/upgrade', upgrade)
    srv = yield from loop.create_server(app.make_handler(), '0.0.0.0', 9001)
    print(' gh started at http://9001... '+ver)
    return srv

loop = asyncio.get_event_loop()
tasks = [init(loop), loop_info(), get_temp()]#loop_info持续发送状态
loop.run_until_complete(asyncio.wait(tasks))
loop.run_forever()
