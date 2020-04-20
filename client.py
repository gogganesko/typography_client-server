# -*- coding: utf-8 -*-
import socket
import json # Подключаем библиотеку для преобразования данных в формат JSON



def start_client(): # Основная функция, запускающая клиента. Эта функция вызывается в конце файла, после определения всех нужных деталей

    SERVER = "127.0.0.1"
    PORT = 8080
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((SERVER, PORT))
    isauth = 0
    authuserid = 0

    print ("Подключились к серверу")

    while True: # Бесконечный цикл работы с сервером

        print("Главное меню:")
        print("0 - Просмотреть список услуг")
        print("1 - Просмотреть список акций")
        if isauth == 1:
            print("2 - Сделать заказ")
        print("3 - Выйти из программы")
        print("4 - Выключить сервер")
        if isauth == 1:
            print("5 - Просмотреть мои заказы")
        if isauth == 0:
            print("6 - Авторизоваться")
        else:
            print("7 - Выйти из профиля")
            print("8 - Забыли пароль|Смена пароля")
            print("9 - Отправить сообщение в чат заказа")
            print("10 - Подробная информация о заказе")
            print("11 - Просмотреть сообщения в чате заказа")
            print("12 - Поиск заказов по датам")
        task = input() # Считывание данных с клавиатуры

        if not task.isdigit() or int(task) > 20: # Если ввод пользователя содержит что-то кроме цифр 
            print ("Неправильная команда!")
            continue # В этом случае начинаем цикл заново, пусть пользователь заново вводит текст

        task=int(task) # Преобразовываем номер задачи в числовой формат

        msg = {} # Создаем пустой словарь Python

        if task == 0: # Если пользователь ввел 0
            msg["command"] = "readservices" # Команда, передаваемая серверу будет read
        if task == 1:
            msg["command"] = "readsales" # Команда, передаваемая серверу будет add        
        if task == 2:                       
            msg["command"] = "add"            
            msg["object"] = create_order(authuserid)
        if task == 3:
            msg["command"] = "bye"
        if task == 4:
            msg["command"] = "stop"
        if task == 5:
            msg["command"] = "readorders"
            msg["authuserid"] = authuserid
        if task == 6:
            msg["command"] = "auth"
            msg["login"] = input("Введите логин:")
            msg["password"] = input("Введите пароль:")
        if task == 7:                        
            msg["command"] = "logout"
            msg["authuserid"] = authuserid
            isauth = 0
        if task == 8:
            while True:
                password1 = input("Введите пароль:")
                password2 = input("Повторите пароль:")
                if password1 == password2:
                    msg["command"] = "changepswd"
                    msg["authuserid"] = authuserid
                    msg["password"] = password1
                    break
                else:
                    print("Пароли не совпадают, повторите попытку")
                    continue
        if task == 9:
            msg["command"] = "addmessage"
            msg["authuserid"] = authuserid
            msg["object"] = create_message(authuserid)
        if task == 10:
            msg["command"] = "showorder"
            msg["OrderID"] = int(input("Введите ID заказа:"))
            msg["authuserid"] = authuserid
        if task == 11:
            msg["command"] = "showmessages"
            msg["OrderID"] = int(input("Введите ID заказа:"))
        if task == 12:
            msg["command"] = "findordesbydate"
            msg["StartDate"] = str(input("Введите начальную дату для поиска в формате\nгггг,мм,дд:"))
            msg["EndDate"] = str(input("Введите конечную дату для поиска в формате\nгггг,мм,дд:"))
            msg["authuserid"] = authuserid
        js_string=json.dumps(msg) # Преобразовываем словарь в строку JSON
        client.sendall(bytes(js_string, 'UTF-8')) # Преобразовываем строку в набор байтов и отправляем ее клиенту

        content={} # Создаем пустой словарь Python

        if task < 20: # Нет смысла получать данные от сервера, которому дали команду отключаться
            in_data = client.recv(4096).decode() # Получаем данные от сервера
            try: # Пытаемся преобразоывать данные
                content=json.loads(in_data) # Преобразываем данные из строки в формат словаря Python
            except Exception as error: # Преобразование не получилось - возникла ошибка
                print("Ошибка получения данных от сервера: ", error)
                print("Клиент выключается...")
                client.close() # Закрываем соединение с сервером
                exit(0) # Выключаем программу

        # Начинаем обработку данных, полученных от сервера
        if task == 0: # Если пользователь ввел 0
            if content: # Если словарь с данным от сервера не пустой
                #print(content)
                print_services(content) # Печатаем список книг
            else: # Иначе
                print("Список пуст")
        if task == 1: # Если пользователь ввел 1
            if content:
                print_sales(content)
            else:
                print("Список пуст") # Печатаем полученный текст на экране
        if task == 2:
            print(content)
        if task == 3:
            print("Клиент выключается...")
            client.close() # Закрываем соединение с сервером
            exit(0) # Выключаем программу
        if task == 4:
            print ("Сервер выключен, клиент выключается...")
            client.close()
            exit(0)
        if task == 5:
            if content:
                print_orders(content)                
            else:
                print("Список пуст")             
        if task == 6:
            if content["Auth"] == 1:
                isauth = 1
                authuserid = content["UserId"]                                                
                print("Вы авторизовались, %s" % content["UserName"])                
            else:
                print("Неправильный логин или пароль")
        #if task == 7:
            #pass
        if task == 8:
            if content:
                print(content)
            else:
                print("Ошибка сервера")
        if task == 9:
            if content:
                print(content)
            else:
                print("Ошибка сервера")
        if task == 10:
            if content:
                print_order(content)
            else:
                print("Ошибка сервера")
        if task == 11:
            if content:
                print_chat(content)
            else:
                print("Сообщений нет")
        if task == 12:
            if content:
                print_orders_by_date(content)
            else:
                print("Заказов не найдено")
               
def print_services(services): #вернулся список, на экран вывести список
    print("="*45)
    for service in services:
        print("%s - %s - %s Руб." % (service["_id"], service["Name"], service["Price"]))

def print_chat(ChatMessages):
    for message in ChatMessages:
        author = message["Author"]
        print("Автор:%s\nДата:%s\nСообщение:%s" %(author["Name"], message["Date"], message["Message"]))

def print_sales(sales):
    print("="*45)
    for sale in sales:
        print("%s - %s - %s - %s - %s" % (sale["_id"], sale["Name"], sale["DateStart"], sale["DateEnd"], sale["Percent"]))

def print_orders(orders):
    print('='*45)
    for order in orders:
        print("%s - %s" % (order["_id"], order["State"]))        

def print_order(order):
    print('='*45)
    client = order["Client"]
    service = order["Service"]
    print("ID:%s \nВладелец:%s \nУслуга:%s \nКоличество:%s \nСтатус:%s \n" %(order["_id"], client["Name"], service["Name"], order["Count"], order["State"]))

def print_orders_by_date(orders):
    print("="*45)
    for order in orders:
        print("%s - %s - %s" % (order["_id"], order["State"], order["Date"]))

def create_order(authuserid):
    order = {}    
    order["ServiceID"] = int(input("Введите ID услуги:"))
    order["Count"] = input("Введите количество:")    
    order["ClientID"] = authuserid
    return order

def create_message(authuserid):
    chatmessage = {}
    chatmessage["OrderID"] = int(input("Введите ID заказа:"))
    chatmessage["Message"] = str(input("Введите текст сообщения"))
    chatmessage["ClientID"] = authuserid
    return chatmessage

   
start_client() # Запускаем функцию старта клиента. Вызов функции должен быть ниже, чем определение этой функции в файле