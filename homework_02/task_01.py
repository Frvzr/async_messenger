import csv
import re


files = ['info_1.txt', 'info_2.txt', 'info_3.txt']

def get_data():
    os_prod_list = []
    os_name_list = []
    os_code_list = []
    os_type_list = []
    main_data = [['Изготовитель системы', 'Название ОС', 'Код продукта', 'Тип системы']]
    

    for i in range(len(files)):
        data = []
        with open(files[i], 'r') as f:
            f_read = f.read()
            try:
                os_prod = re.compile(r'Изготовитель системы:\s*\S*')
                os_prod_list.append(os_prod.findall(f_read)[0].split()[2])
                data.append(os_prod_list[i])
            except:
                data.append('')

            try:
                os_name = re.compile(r'Название ОС:\s*\S*')
                os_name_list.append(os_name.findall(f_read)[0].split()[2])
                data.append(os_name_list[i])
            except:
                data.append('')

            try:
                os_code = re.compile(r'Код продукта:\s*\S*')
                os_code_list.append(os_code.findall(f_read)[0].split()[2])
                data.append(os_code_list[i])
            except:
                data.append('')
            
            try:
                os_type = re.compile(r'Тип системы:\s*\S*')
                os_type_list.append(os_type.findall(f_read)[0].split()[2])
                data.append(os_type_list[i])
            except:
                data.append('')

            main_data.append(data)

    return main_data


def write_to_csv(file_link):
    data = get_data()
    with open(file_link, 'w', encoding='utf-8') as f:
        f_writer = csv.writer(f)
        for row in data:
            f_writer.writerow(row)

    with open('task_1.csv', encoding='utf-8') as f_n:
        print(f_n.read())

if __name__ == '__main__':
    write_to_csv('task_1.csv')
