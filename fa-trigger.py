#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import socket #UDP送信
import time #待機時間用
import struct #数値→バイト列変換用
from contextlib import closing #with用
import ipaddress #入力IPアドレスの形式確認用

import RPi.GPIO as GPIO
import time

GPIO_BTN=25

def btn_callback(gpio_no):
    socksend()

GPIO.setmode(GPIO.BCM)
GPIO.setup(GPIO_BTN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(GPIO_BTN, GPIO.FALLING, bouncetime=300)
GPIO.add_event_callback(GPIO_BTN, btn_callback)

def socksend():
    #IPアドレスの入力関係
    print("Destination IP address:")
    while True:
      try:
        # print(">",end="") #>を改行無しで表示
        inputip = "169.254.25.191" #input() #入力させる
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
    sockrecv.setblocking(0) #ノンブロッキング受信に設定
    print("OK") #準備完了であることを示す
    sum = 0.0
    s = 1
    #送受信
    with closing(socksend), closing(sockrecv): #プログラム終了時にソケットを自動的に閉じる
      while True: #無限ループ
        #送信
        # 1秒ごとに一方的に送信する
        print("send: ", str( s )) #送信する数値を送信側に表示
        ss = struct.pack('>i', s ) #バイト列に変換
        socksend.sendto(ss, (host, send_port)) #ソケットにUDP送信
        #待機
        time.sleep(1) #1秒待機
        
        #受信
        # パケットを受信した場合のみ、結果を表示する。それ以外は何もせずスルーする
        try: #try構文内でエラーが起こるとexceptに飛ぶ、なければelseへ
          sr, addr = sockrecv.recvfrom(1024) #受信する
        except socket.error: #受信していなければなにもしない
          pass
        else: #受信していたら表示
          r = struct.unpack('>d' , sr)[0] #バイト列を数値に変換
          print ( "receive: " , str( r )) #数値に変換して表示
          #処理
          sum += r
          print(s , ": pi = " , sum * 4 )
          s += 1
          
          break

def main():
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
            GPIO.cleanup()


if __name__ == "__main__":
    main()
    exit(1)

