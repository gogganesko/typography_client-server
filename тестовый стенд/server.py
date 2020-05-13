# -*- coding: utf-8 -*-
import random
import string
import datetime
import json  # Подключаем библиотеку для преобразования данных в формат JSON
import socket
import os # Подключаем библиотеку для работы с функциями операционной системы (для проверки файла)
import win32event
import win32api
import win32file
from winerror import ERROR_ALREADY_EXISTS
from sys import exit
import threading

def start_server():
    serv_sock = create_serv_sock(8080)
    cid = 0
    
    while True:
        client = accept_client_conn(serv_sock, cid)
        client_sock = client[0]
        client_addr = client[1]
        t = threading.Thread(target=serve_client, args=(client_sock, cid, client_addr))
        t.start()
        cid += 1

def create_serv_sock(serv_port):
    serv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM,  proto=0)
    serv_sock.bind(('', serv_port))
    serv_sock.listen()
    print('Сервер запущен')
    print('Ожидаем подключения')
    return serv_sock

def accept_client_conn(serv_sock, cid):
    client_sock, client_addr = serv_sock.accept()
    print(f'Клиент #{cid} подключен ' f'{client_addr[0]}:{client_addr[1]}')
    return client_sock, client_addr

def serve_client(client_sock, cid, client_addr):
    while True:
        answer = fulfill_request(client_sock, client_addr, cid)
        if answer is None:
            print(f'Клиент #{cid} преждевременно отключился')
            break
        else:
            client_sock.send(bytes(json.dumps(answer), 'UTF-8')) # Отправка данных клиенту

def fulfill_request(clientConnection, clientAddress, cid):
    try:
        in_data = clientConnection.recv(4096)# Получение данных от клиента
    except:
        return None 
        
    msg = in_data.decode() # Декодирование данных от клиента
    data = json.loads(msg) # Преобразование данных из формата JSON в словарь Python
    answer = None 

    if data["command"] == 'log': # Получена команда отключение клиента
        print("Клиент отключен....")
        answer = add_operation_in_journal("mutextest", clientAddress)
    return answer




class FileMutex:
    def __init__(self):
        self.mutexname = "typography_filemutex"

        self.mutex = win32event.CreateMutex(None, 1, self.mutexname)
        self.lasterror = win32api.GetLastError()
    
    def release(self):
        return win32event.ReleaseMutex(self.mutex)
        
    def waitForOne(self):
        if self.mutex:
            self.res = win32event.WaitForSingleObject(self.mutex, win32event.INFINITE )

mutex = FileMutex()
mutex.release()

def add_operation_in_journal(opeartion,clientAddress):
    import time
    mutex = FileMutex()
    date=datetime.datetime.now()
    date = str(date)
    row = str(opeartion) + "=====" + str(clientAddress) + "=====" + str(date) + '\n'
    while True:
        mutex.waitForOne()
        print(str(clientAddress) + " " + " зашёл")       
        clientAddress = str(clientAddress)
        time.sleep(5)
        f = open('journal.txt', 'a')
        f.write(row)
        f.close()
        mutex.release()
        return ""

class singleinstance:
    """ Limits application to single instance """

    def __init__(self):
        self.mutexname = "testmutex_{b5123b4b-e59c-4ec7-a912-51be8ebd5819}" #GUID сгенерирован онлайн генератором
        self.mutex = win32event.CreateMutex(None, False, self.mutexname)
        self.lasterror = win32api.GetLastError()


    def aleradyrunning(self):
        return (self.lasterror == ERROR_ALREADY_EXISTS)
        
    def __del__(self):
        if self.mutex:
            win32api.CloseHandle(self.mutex)




from sys import exit
myapp = singleinstance()


if myapp.aleradyrunning():
    print("Another instance of this program is already running")
    exit(0)


start_server() # Запускаем функцию старта сервера. Вызов функции должен быть ниже, чем определение этой функции в файле
