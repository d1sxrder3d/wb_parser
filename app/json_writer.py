from .product_info import get_product_info
import json



def write_json(article: int | str):
    product_info = get_product_info(article)

    output_filename = f"product_{article}_info.json"
    try:
        with open(output_filename, 'w', encoding='utf-8') as json_file:
            json.dump(product_info, json_file, ensure_ascii=False, indent=4)
        print(f"Информация о товаре успешно сохранена в файл {output_filename}")
        return True
    except IOError:
        print(f"Ошибка при записи в файл {output_filename}")
        return False
