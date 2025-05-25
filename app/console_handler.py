from .product_info import get_product_info
from .json_writer import write_json

console_help = """
Это скрипт для получения информации о товарах с Wildberries

Команды: 
/help - получить это сообщение 
/exit - выйти из программы
/getjson - выбор режима getjson, каждый введенный далее артикул товара будет записан в json (выход - /exit)
/getinfo - выбор режима getinfo, каждый введенный далее артикул товара будет выведен в консоль (выход - /exit)
"""

def get_json():
    print("Вы в режиме getjson")
    console_input = input("Введите артикул товара:")

    while console_input != "/exit":
        write_json(console_input)

        console_input = input("Введите артикул товара:")

        if console_input == "/exit":
            return
        


def get_info():
    print("Вы в режиме getinfo")
    console_input = input("Введите артикул товара:")

    while console_input != "/exit":

        print(get_product_info(console_input))

        console_input = input("Введите артикул товара:")

        if console_input == "/exit":
            return
        
   


def start_console():
    while True:
        console_input = input("Введите команду (/help - получить справку):")
        if console_input == "/help":
            print(console_help)
        elif console_input == "/getjson":
            get_json()
        elif console_input == "/getinfo":
            get_info()
        
        
        elif console_input == "/exit":
            break
        
        