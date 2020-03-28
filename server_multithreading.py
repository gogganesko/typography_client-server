# -*- coding: utf-8 -*-
import random
import string
import datetime
import json  # Подключаем библиотеку для преобразования данных в формат JSON
import socket
import os # Подключаем библиотеку для работы с функциями операционной системы (для проверки файла)
import pymongo
from bson.json_util import dumps, loads
from bson import json_util
import win32event
import win32api
from winerror import ERROR_ALREADY_EXISTS
from sys import exit
import threading

mongoclient = pymongo.MongoClient("mongodb://localhost:27017/")
dblist = mongoclient.list_database_names()
db = mongoclient["Typography"]

def check_database():    
    if "Typography" in dblist:
        print("База данных найдена")
    else:
        db = mongoclient["Typography"]
        creationdata = {"test":"test"} # Монгодб создает коллекции только после того в них ставили объекты, заполняем базу тестовыми данными
        col = db["Persons"]
        col.insert_one(creationdata)
        col.delete_one(creationdata)
        col = db["Services"]
        col.insert_one(creationdata)
        col.delete_one(creationdata)
        col = db["Sales"]
        col.insert_one(creationdata)
        col.delete_one(creationdata)
        col = db["Orders"]
        col.insert_one(creationdata)
        col.delete_one(creationdata)
        col = db["ChatMessages"]
        col.insert_one(creationdata)
        col.delete_one(creationdata)
        print("База данных не найдена\nСоздана новая база данных")

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
    check_database()
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

    if data["command"] == 'bye': # Получена команда отключение клиента
        print("Клиент отключен....")
        add_operation_in_journal("bye", clientAddress)
        clientConnection.close() # Закрываем соединение с клиентом

    if data["command"] == 'stop': # Получена команда остановки сервера
        print("Отключаем сервер")
        add_operation_in_journal("stop", clientAddress)
        clientConnection.close() # Закрываем соединение с клиентом
        #server.close() # Отключаем сервер
        exit(0) # Выходим из программы

    if data["command"] == 'auth':
        print("Попытка авторизоваться")
        add_operation_in_journal("auth", clientAddress)
        if user_auth(data["login"], data["password"]):
            print("Попытка авторизоваться прошла успешно")
            token = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for x in range(16))
            x = db["Persons"].find_one({"Login":data["login"], "Password":data["password"]})
            x["Token"] = token
            x["TokenDate"] = datetime.datetime.now()
            db["Persons"].save(x)
            answer = {}
            answer["Auth"] = 1
            answer["UserName"] = x["Name"]
            answer["UserId"] = x["_id"]

        else:
            print("Попытка авторизоваться прошла неудачно")
            answer = {}
            answer["Auth"] = 0

    if data["command"] == 'logout':
        x = find_by_id(data["authuserid"], "Persons")
        x["Token"] = None
        x["TokenDate"] = None                
        db["Persons"].save(x)
        add_operation_in_journal('logout', clientAddress)
        print("Клиент вышел из профиля:", clientAddress)

    if data["command"] == 'add':
        print("Добавляем заказ")
        add_operation_in_journal('add', clientAddress)
        answer = add_order(data["object"]) # Передаем объект из полученного словаря в функцию добавления книги.  В данном случае объект - это книга

    if data["command"] == 'changepswd':
        x = db["Persons"].find_one({"_id":data["authuserid"]})                
        x["Password"] = data["password"]
        db["Persons"].save(x)
        add_operation_in_journal('changepswd', clientAddress)
        print("Попытка смены пароля прошла успешно ", clientAddress)
        answer = "Ваш пароль был успешно изменён"

    if data["command"] == 'readservices': # Получена команда чтения списка книг
        print("Считываем список услуг")
        add_operation_in_journal('readservices', clientAddress)
        answer = read_services() # Вызывается функция чтения книг, данные из функции записываются в переменную answer

    if data["command"] == 'readsales':
        print("Считываем список акций")
        add_operation_in_journal('readsales', clientAddress)
        answer = read_sales()

    if data["command"] == 'readorders':
        print("Считываем список закаов")
        add_operation_in_journal('readorders', clientAddress)
        answer = read_orders(data["authuserid"])

    if data["command"] == 'showorder':
        add_operation_in_journal('showorder', clientAddress)
        answer = read_order(data["OrderID"])
        
    if data["command"] == 'addmessage':
        add_operation_in_journal('addmessage', clientAddress)
        answer = add_chatmessage(data["object"])

    if data["command"] == 'showmessages':
        add_operation_in_journal('showmessages', clientAddress)
        answer = read_chatmessages(data["OrderID"])

    if data["command"] == 'findordesbydate':
        add_operation_in_journal('findordersbydate', clientAddress)
        answer = read_orders_by_date(data["authuserid"], data["StartDate"], data["EndDate"])

    return answer

def add_order(order):
    neworder = {}
    neworder["_id"] = (get_max_id("Orders")) + 1
    neworder["Client"] = find_by_id(order["ClientID"], "Persons")
    neworder["Service"] = find_by_id(order["ServiceID"], "Services")
    neworder["Count"] = order["Count"]
    neworder["Date"] = datetime.datetime.now()
    neworder["State"] = "В обработке"
    db["Orders"].save(neworder)
    return "Заказ был добавлен"

def add_chatmessage(chatmessage):
    newchatmessage = {}
    newchatmessage["_id"] = (get_max_id("ChatMessages")) + 1
    newchatmessage["Author"] = find_by_id(chatmessage["ClientID"], "Persons")
    newchatmessage["Order"] = find_by_id(chatmessage["OrderID"], "Orders")
    newchatmessage["Message"] = chatmessage["Message"]
    newchatmessage["Date"] = datetime.datetime.now()
    db["ChatMessages"].save(newchatmessage)
    return "Сообщение было отправлено в заказ"

def find_by_id(id, collection):
    col = db[collection]
    obj = {}
    for x in col.find():
        if x["_id"] == id:
            obj = x
    return obj
            
def read_order(OrderID):
     x = db["Orders"].find_one({"_id":OrderID})
     content = (loads(dumps(x, default = myconverter)))
     return content

def user_auth(login, password):
    col = db["Persons"]
    for x in col.find():
        if x["Login"] == login and x["Password"] == password:
            return True
        else:
            continue

def read_services(): # Считываем список книг
    col = db["Services"]
    for x in col.find():
        print(x)
    cursor = col.find()
    content = (loads(dumps(cursor)))
    return content

def read_sales():
    col = db["Sales"]
    for x in col.find():
        print(x)
    cursor = col.find()
    content = (loads(dumps(cursor, default = myconverter)))
    return content

def read_orders(userid):
    col = db["Orders"]
    for x in col.find({"Client._id":userid}):
        print(x)
    cursor = col.find({"Client._id":userid})
    content = (loads(dumps(cursor, default = myconverter)))
    return content

def read_orders_by_date(userid, stringdatestart, stringdateend):
    date1 = stringdatestart.split(',')
    date2 = stringdateend.split(',')
    from_date = datetime.datetime(int(date1[0]), int(date1[1]), int(date1[2]))
    to_date = datetime.datetime(int(date2[0]), int(date2[1]), int(date2[2]))
    cursor = db["Orders"].find({"Date": {"$gte": from_date, "$lt": to_date}, "Client._id":userid})
    content = (loads(dumps(cursor, default = myconverter)))
    return content

def read_persons():
    col = db["Persons"]
    for x in col.find():
        print(x)
    cursor = col.find()
    content = (loads(dumps(cursor)))
    return content

def read_chatmessages(OrderID):
    col = db["ChatMessages"]
    for x in col.find({"Order._id":OrderID}):
        print(x)
    cursor = col.find()
    content = (loads(dumps(cursor)))
    return content

def read_printtypes():
    col = db["PrintTypes"]
    for x in col.find():
        print(x)
    cursor = col.find()
    content = (loads(dumps(cursor)))
    return content


def get_max_id(collection):
    col = db[collection]
    maxid = 1
    for x in col.find().sort("_id"):
        maxid = x["_id"]
    return maxid

def myconverter(o):
    if isinstance(o, datetime.datetime):
        return o.__str__()

def add_operation_in_journal(opeartion,clientAddress):
    date=datetime.datetime.now()
    date = str(date)
    clientAddress = str(clientAddress)
    f = open('journal.txt', 'a')
    f.write(opeartion + "=====" + clientAddress + "=====" + date + '\n')
    f.close()

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

#t.daemon = True
mutex = threading.Lock()
start_server() # Запускаем функцию старта сервера. Вызов функции должен быть ниже, чем определение этой функции в файле
