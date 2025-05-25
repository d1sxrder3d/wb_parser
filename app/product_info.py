import requests



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
        return None
    products = json_data.get("data", {}).get("products", [])
    if not products:
        return None

    name = products[0].get("name") 
    sizes = products[0].get("sizes")

    return name, products[0].get("sizes")

def get_product_info(article: int | str) -> dict:

    
    json_data = fetch_product_data(article)
    parse_data = parse_product_data(json_data)
    # print(parse_data)

    if parse_data: 
        out = {}
        out["Имя продукта:"] = parse_data[0]
        out["Размеры:"] = {}
        for i in parse_data[1]:
            name_of_size = i.get("name")
            if i.get("price") == None:
                continue
            price_of_size = f"{i.get("price").get("product") // 100} ₽"
            out["Размеры:"][name_of_size] = [price_of_size]
            # print(i)

        return out
    else: 
        return None





if __name__ == "__main__":
    art = input("Введите артикул товара Wildberries:") 

    print(get_product_info(art))
