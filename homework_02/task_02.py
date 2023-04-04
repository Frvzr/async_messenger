import json

def write_order_to_json(item, quantity, price, buyer, date):

    json_obj = {
            "item": item,
            "quantity": quantity,
            "price": price,
            "buyer": buyer,
            "date": date
        }
    
    with open('orders.json', 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except:
            data = {"orders": []}

    with open('orders.json', 'w', encoding='utf-8') as f_n:
        data['orders'].append(json_obj)
        json.dump(data, f_n, sort_keys=True, indent=4)

    with open('orders.json') as f_n:
        print(f_n.read())


if __name__ == '__main__':
    write_order_to_json("Table", 1, 145, "Ivan", "20-02-2023")
    write_order_to_json("Chairs", 4, 50, "Ivan", "21-02-2023")