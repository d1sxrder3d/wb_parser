import requests
import pprint


def fetch_product_data(article: int | str) -> dict | None:

    url = f"https://card.wb.ru/cards/v2/detail?dest=-1255987&nm={article}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе: {e}")
        return None


def parse_product_data(json_data: dict) -> tuple[str | None, list | None]:
    if not json_data:
        return None, None
    products = json_data.get("data", {}).get("products", [])
    if not products:
        return None, None

    name = products[0].get("name") 
    sizes = products[0].get("sizes")
    # pprint.pprint(products[0])

    return name, sizes

def get_product_info_4_bot(article: int | str, size: str = None) -> dict | None | str:
    json_data = fetch_product_data(article)
    name, sizes = parse_product_data(json_data)
    price = None
    color = None
    if name and sizes:
        out = {
            "name": name,
            "size": size,
            "price": price,
            "Except": 0
        }


        

        if len(sizes) == 0:
            return None
        elif len(sizes) == 1:
            price_info = sizes[0].get("price")
            if price_info is None:
                return None
            price = price_info.get("product")
            if price is not None:
                price_of_size = price // 100
                out["price"] = price_of_size
            return out
        elif len(sizes) > 1:
            # size_names = []
            size_orig_names = []
            if size is None:
                for size_info in sizes:
                    # name_of_size = size_info.get("name")
                    orig_name_of_size = size_info.get("origName")

                    # size_names.append(name_of_size)
                    size_orig_names.append(orig_name_of_size)

                return {"Except": "need_more_details",
                        # "sizeNames": size_names,
                        "sizeOrigNames": size_orig_names}
            
            for size_info in sizes:
                name_of_size = size_info.get("origName")
                print(name_of_size)
                if name_of_size == size:
                    price_info = size_info.get("price")
                    if price_info is None:
                        
                        return {"Except": "size is not available"}
                    price = price_info.get("product")
                    if price is not None:
                        price_of_size = price // 100
                        out["price"] = price_of_size
                    return out
            print("Размер не найден")
            return None
    
def get_product_info(article: int | str) -> dict | None:
    json_data = fetch_product_data(article)
    name, sizes = parse_product_data(json_data)

    if name and sizes:
        out = {
            "Имя продукта:": name,
            "Размеры:": {}
        }
        for size_info in sizes:
            name_of_size = size_info.get("name")
            price_info = size_info.get("price")
            if price_info is None:
                continue
            # The price is in kopecks, converting to rubles
            price = price_info.get("product")
            if price is not None:
                price_of_size = f"{price // 100} ₽"
                out["Размеры:"][name_of_size] = price_of_size

        return out
    return None

if __name__ == "__main__":
    art = input("Введите артикул товара Wildberries:") 

    print(get_product_info_4_bot(art))