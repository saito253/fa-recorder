#!/usr/bin/env python3
### -*- coding: utf-8 -*-
import socket #UDP送信
import time #待機時間用
import struct #数値→バイト列変換用
import os #subprocess kill
import signal #subprocess kill
import subprocess #Shellコマンド
import glob
import shutil
from subprocess import PIPE
from contextlib import closing #with用
import ipaddress #入力IPアドレスの形式確認用
import datetime
import logging
import configparser

#パラメータ変数
param_ram = "/mnt/ramdisk/"
param_file = param_ram + "file%04d.h264"
global param_wrap
global param_data1
global param_data2
global param_log
global param_pview

param_wrap = 5 #30,90,150
param_seg = 1000 #1000
param_home = "/home/pi/"
param_data1 = "fa-data1"
param_data2 = "fa-data2"
param_fsize = 14
param_log = "fa-recorder.log"
param_pview = 1

logging.basicConfig(level=logging.DEBUG,filename=param_log,format="%(asctime)s %(levelname)-7s %(message)s")

def read_config():
    global param_wrap
    global param_data1
    global param_data2
    global param_pview
    config_ini = configparser.ConfigParser()
    #config_ini.read('/home/pi/config.ini', encoding='utf-8')
    config_ini.read('/home/pi/fa-config.ini')
    param_wrap = int(config_ini.get('RECORD', 'Wrap'))
    param_data1 = config_ini.get('RECORD', 'Data1')
    param_data2 = config_ini.get('RECORD', 'Data2')
    param_pview = int(config_ini.get('RECORD', 'Preview'))
    logging.info('get config: %s',param_wrap)
    logging.info('get config: %s',param_data1)
    logging.info('get config: %s',param_data2)
    logging.info('get config: %s',param_pview)

def proc_kill():
    print("PID = {}".format(proc.pid))
    #os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    #ps --no-heading -C raspivid -o pid
    subprocess_cmd = "kill -9 %s" % (proc.pid+1)
    subprocess.run(subprocess_cmd,shell=True)

def socksend():
    #IPアドレスの入力関係
    print("Destination IP address:")
    while True:
      try:
        # print(">",end="") #>を改行無しで表示
        inputip = "169.254.37.145" # input() #入力させる
        ipaddress.ip_address(inputip) #入力が誤った形式だとエラーを吐く
      except KeyboardInterrupt:
        exit() #Ctrl+Cが入力されたらプログラムを抜ける
      except:
        print("Incorrect IP address. input IP address again.(xxx.xxx.xxx.xxx)")
      else:
        break #正しいIPアドレスだったらwhileを抜ける
    #送信の設定

    host = inputip # 送信先（相手）IPアドレス
    send_port = 60000 # 送信ポート番号
    #受信の設定
    recv_ip = "" #このままでいい
    recv_port = 60000 #ポート番号
    #2つのsocketを設定
    socksend = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #送信ソケットの設定
    sockrecv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #受信ソケットの生成
    sockrecv.bind((recv_ip, recv_port)) #ソケットを登録する

    #送受信
    with closing(socksend), closing(sockrecv): #プログラム終了時にソケットを自動的に閉じる
      while True: 
      
        #受信
        print("Waiting for receive...") #受信待機中であることを示す
        # 受信を待機する
        sr, addr = sockrecv.recvfrom(1024) #受信する
        #--受信していない間はここで止まる--
        r = struct.unpack('>i' , sr)[0] #受信したバイト列を数値に変換
        print ( "receive: " , str( r )) #数値に変換して表示
        
        #処理
        s = 1.0 / ( 2.0 * r - 1.0 )
        if r % 2 == 0 :
          s = -s
        #送信
        # 受信があったときのみ送信する
        print("send: ", str( s )) #送信するバイト列を自分側に表示
        ss = struct.pack('>d', s ) #計算結果をバイト列に変換
        socksend.sendto(ss, (host, send_port)) #ソケットにUDP送信

        break
    return

def waitWrapNum(num):
    DIR = param_ram
    while True:
        cnt = len([name for name in os.listdir(DIR) if os.path.isfile(os.path.join(DIR, name))])
        print(cnt)
        if cnt < num:
            pass
            time.sleep(1)
        else:
            break

def debug_timeStamp():
    #check data
    global param_log
    subprocess_cmd = "ls -ltr --full-time %s%s | tee -a %s%s" % (param_home,param_data1,param_home,param_log)
    subprocess.run(subprocess_cmd,shell=True)
    subprocess_cmd = "ls -ltr --full-time %s%s | tee -a %s%s" % (param_home,param_data2,param_home,param_log)
    subprocess.run(subprocess_cmd,shell=True)

def recording():
    logging.info('--------------------- Start Recording ----------------------')

    global proc

    #clean ramdisk
    for file in glob.glob(param_ram + '*'): os.remove(file)

    #start recording
    if param_pview == 0:
        subprocess_cmd = 'raspivid --nopreview -w 1280 -h 720 -fps 30  -b 2000000 -t 0 --segment %s -sn 01 -wr %s -o %s -vf -hf -k' \
                % (param_seg,param_wrap,param_file)
    else:
        subprocess_cmd = 'raspivid -w 1280 -h 720 -fps 30  -b 2000000 -t 0 --segment %s -sn 01 -wr %s -o %s -vf -hf -k' \
                % (param_seg,param_wrap,param_file)
    proc = subprocess.Popen(subprocess_cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)

    waitWrapNum(param_wrap)

    #wait Trriger
    socksend()

    #make dir1
    DIR = param_home + param_data1
    if(os.path.isdir(DIR) == True): shutil.rmtree(DIR)
    os.makedirs(DIR, exist_ok=True)

    #movie-1: mv
    logging.info('move 1 start')
    subprocess_cmd = "cp --preserve=timestamps %s/* %s%s/." % (param_ram,param_home,param_data1)
    subprocess.run(subprocess_cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    logging.info('move 1 end')

    #subprocess_cmd = "ls -1t %s*.h264 | tail -1" % (param_ram)
    subprocess_cmd = "ls -1t %s*.h264 | head -1" % (param_ram)
    ret = subprocess.run(subprocess_cmd,shell=True,stdout=subprocess.PIPE)
    cmp1 = ret.stdout[-(param_fsize):]
    subprocess_cmd = "ls -1t %s%s/*.h264 | head -1" % (param_home,param_data1)
    ret = subprocess.run(subprocess_cmd,shell=True,stdout=subprocess.PIPE)
    cmp2 = ret.stdout[-(param_fsize):]

    #ramdisk: delete other than the latest
    subprocess_cmd = "rm `ls -1t %s*.h264 | tail -n+2`" % (param_ram)
    subprocess.run(subprocess_cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    logging.info('Boundary delete:%s %s',cmp1,cmp2)

    if cmp1 == cmp2:
        #movie-1: delete latest
        subprocess_cmd = "rm `ls -1t %s%s/*.h264 | head -1`" % (param_home,param_data1)
        subprocess.run(subprocess_cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)

    else:
        logging.info('Boundary no delete:%s %s',cmp1,cmp2)

    waitWrapNum(param_wrap)
    proc_kill()

    #make dir2
    DIR = param_home + param_data2
    if(os.path.isdir(DIR) == True): shutil.rmtree(DIR)
    os.makedirs(DIR, exist_ok=True)

    #movie-2: mv
    logging.info('move 2 start')
    subprocess_cmd = "cp --preserve=timestamps %s/* %s%s/." % (param_ram,param_home,param_data2)
    subprocess.run(subprocess_cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    logging.info('move 2 end')

    #movie-1: list
    subprocess_cmd = "ls -tr --full-time %s%s | grep h264 | \
            nawk '{print $NF}' | sed -e 's/^/file /' 1> %s%s/list.txt" \
            % (param_home,param_data1,param_home,param_data1)
    subprocess.run(subprocess_cmd,shell=True)

    #movie-1: join
    logging.info('join 1 start')
    subprocess_cmd = "ffmpeg -y -f concat -i %s%s/list.txt -c copy %s%s/joint.mp4"\
            % (param_home,param_data1,param_home,param_data1)
    subprocess.run(subprocess_cmd,shell=True)
    logging.info('join 1 end')

    #movie-2: list
    subprocess_cmd = "ls -tr --full-time %s%s | grep h264 | \
            nawk '{print $NF}' | sed -e 's/^/file /' 1> %s%s/list.txt" \
            % (param_home,param_data2,param_home,param_data2)
    subprocess.run(subprocess_cmd,shell=True)

    #movie-2: join
    logging.info('join 2 start')
    subprocess_cmd = "ffmpeg -y -f concat -i %s%s/list.txt -c copy %s%s/joint.mp4"\
            % (param_home,param_data2,param_home,param_data2)
    subprocess.run(subprocess_cmd,shell=True)
    logging.info('join 2 end')

    #movie-all: list
    f = open(param_home + param_data2 + '/list-all.txt', 'w')
    f.write("file " + param_home + param_data1 + "/joint.mp4\n")
    f.write("file " + param_home + param_data2 + "/joint.mp4\n")
    f.close()

    #movie-all: join
    logging.info('join all start')
    subprocess_cmd = "ffmpeg -y -f concat -safe 0 -i %s%s/list-all.txt -c copy %s%s/joint-all.mp4"\
            % (param_home,param_data2,param_home,param_data2)
    subprocess.run(subprocess_cmd,shell=True)
    logging.info('join all end')


def main():
    while True: 
        read_config()
        recording()
        debug_timeStamp()

if __name__ == "__main__":
    main()
