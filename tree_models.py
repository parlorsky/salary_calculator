import pandas as pd
import ast
import os
import json
import streamlit as st

def get_folders_sorted_by_size(directory):
    folders = [os.path.join(directory, d) for d in os.listdir(directory) if os.path.isdir(os.path.join(directory, d))]

    folder_sizes = {folder: sum(os.path.getsize(os.path.join(dirpath, filename)) 
                                for dirpath, dirnames, filenames in os.walk(folder) 
                                for filename in filenames) 
                    for folder in folders}

    sorted_folders = sorted(folder_sizes.items(), key=lambda x: x[1], reverse=False)

    return sorted_folders

def find_matching_combination_in_dataframe(dataframe,df, target_input):
    """
    Поиск самой длинной соответствующей последовательности элементов в индексе DataFrame в сравнении с целевым вводом.

    Эта функция проверяет каждый кортеж в индексе DataFrame и сравнивает его с целевым вводом.
    Сравнение происходит поэлементно и в порядке следования. Функция возвращает самую длинную последовательность
    совпадающих элементов до первого несоответствия, а также дополнительную информацию о совпадении.

    Параметры:
    - dataframe: Pandas DataFrame с кортежами в качестве значений индекса.
    - target_input: Последовательность ввода для сопоставления с индексом DataFrame. Может быть строкой или кортежем.

    Возвращает:
    - Кортеж, содержащий:
        1. Самую длинную совпадающую последовательность (до первого несоответствия)
        2. Количество элементов в самой длинной совпадающей последовательности
        3. Цену, связанную с самой длинной совпадающей последовательностью в DataFrame
        4. Элементы целевого ввода, которые не были частью совпадения
    """
    # Преобразование целевого ввода в кортеж, если это строковое представление кортежа
    target_tuple = eval(target_input) if isinstance(target_input, str) else target_input

    # Инициализация переменных для хранения наилучшего найденного совпадения
    longest_match = None
    longest_match_count = 0
    longest_match_price = 0
    elements_not_in_longest_match = None

    # Итерация по каждому кортежу в индексе DataFrame
    for features_str in dataframe.index:
        features_tuple = eval(features_str)

        # Подсчет совпадающих элементов в последовательности до возникновения несоответствия
        matches = 0
        # for i, j in zip(features_tuple, target_tuple):
        #     if i == j:
        #         matches += 1
        #     else:
        #         break  # Найдено несоответствие, дальнейшее сравнение прекращается
        for i in features_tuple:
            if i in target_tuple:
                matches += 1
            
        # Обновление информации о наибольшем совпадении, если это наибольшее совпадение на данный момент
        if matches >= longest_match_count :
            longest_match = features_tuple[:matches]
            longest_match_count = matches
            elements_not_in_longest_match = target_tuple[matches:]
            # Попытка найти цену для наибольшего совпадения в DataFrame
            try:
                match_price = df.loc[str(longest_match), 'price']
                if match_price > longest_match_price:
                    longest_match_price = match_price
                    longest_match = features_tuple[:matches]
                    longest_match_count = matches
                    elements_not_in_longest_match = target_tuple[matches:]
                    
            except KeyError:
                # В случае отсутствия совпадения, по умолчанию используется свойства элемента 'root'
                longest_match = ('root',)
                longest_match_count = 1
                longest_match_price = df.loc["('root',)", 'price']
                elements_not_in_longest_match = target_tuple[matches:]
        

    return longest_match, longest_match_count, longest_match_price, elements_not_in_longest_match

# def find_matching_combination_in_dataframe(dataframe, target_input):
#     """
#     Поиск самой длинной соответствующей последовательности элементов в индексе DataFrame в сравнении с целевым вводом.

#     Эта функция проверяет каждый кортеж в индексе DataFrame и сравнивает его с целевым вводом.
#     Сравнение происходит поэлементно и в порядке следования. Функция возвращает самую длинную последовательность
#     совпадающих элементов до первого несоответствия, а также дополнительную информацию о совпадении.

#     Параметры:
#     - dataframe: Pandas DataFrame с кортежами в качестве значений индекса.
#     - target_input: Последовательность ввода для сопоставления с индексом DataFrame. Может быть строкой или кортежем.

#     Возвращает:
#     - Кортеж, содержащий:
#         1. Самую длинную совпадающую последовательность (до первого несоответствия)
#         2. Количество элементов в самой длинной совпадающей последовательности
#         3. Цену, связанную с самой длинной совпадающей последовательностью в DataFrame
#         4. Элементы целевого ввода, которые не были частью совпадения
#     """
#     # Преобразование целевого ввода в кортеж, если это строковое представление кортежа
#     target_tuple = eval(target_input) if isinstance(target_input, str) else target_input

#     # Инициализация переменных для хранения наилучшего найденного совпадения
#     longest_match = None
#     longest_match_count = 0
#     longest_match_price = None
#     elements_not_in_longest_match = None

#     # Итерация по каждому кортежу в индексе DataFrame
#     for features_str in dataframe.index:
#         features_tuple = eval(features_str)

#         # Подсчет совпадающих элементов в последовательности до возникновения несоответствия
#         matches = 0
#         for i, j in zip(features_tuple, target_tuple):
#             if i == j:
#                 matches += 1
#             else:
#                 break  # Найдено несоответствие, дальнейшее сравнение прекращается

#         # Обновление информации о наибольшем совпадении, если это наибольшее совпадение на данный момент
#         if matches > longest_match_count:
#             longest_match = features_tuple[:matches]
#             longest_match_count = matches
#             elements_not_in_longest_match = target_tuple[matches:]
#             # Попытка найти цену для наибольшего совпадения в DataFrame
#             try:
#                 longest_match_price = dataframe.loc[str(longest_match), 'price']
#             except KeyError:
#                 # В случае отсутствия совпадения, по умолчанию используется свойства элемента 'root'
#                 longest_match = ('root',)
#                 longest_match_count = 1
#                 longest_match_price = dataframe.loc["('root',)", 'price']
#                 elements_not_in_longest_match = target_tuple[matches:]

#     return longest_match, longest_match_count, longest_match_price, elements_not_in_longest_match


def get_predict_tree(n_bundle, vht, exp, ind, region_name, skills_pciked):
    base_path = ''


    file_name = f'{n_bundle}_vht_{vht}_exp_{exp}_ind_{ind}'

    with open(f'results/results_reg_coefs/{n_bundle}/{file_name}.json','r') as f:
        reg_coefs = json.load(f)
    # print(x.get(region_name))

    try:
        table_model = pd.read_excel(f'results/results_tabels_tree/{n_bundle}/{file_name}.xlsx')
    except:
        return
    table_model['features_tuple'] = table_model['features'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
    table_model['second_item'] = table_model['features_tuple'].apply(lambda x: x[1] if len(x) > 1 else None)
    arr = list(table_model['second_item'].iloc[1:])
    first_indexes = dict(sorted({x:arr.index(x)+1 for x in list(set(arr))}.items(), key=lambda x:x[1]))
    table_model = pd.read_excel(f'results/results_tabels_tree/{n_bundle}/{file_name}.xlsx', index_col = 0)



    with open(f'jsones_skill_salary/{n_bundle}.json', 'r') as f:
        linear_model = json.load(f)


    base_salary = linear_model[str(float(exp))][str(bool(vht))][str(ind)][str('False')]['base']
    skill_values = linear_model[str(float(exp))][str(bool(vht))][str(ind)][str('False')]

    skill_values = {key.replace('\xa0', ' '): value for key, value in skill_values.items()}

    table_model.loc["('root',)",'price'] = base_salary


    skill_columns = [x for x in list(skill_values.keys()) if x != 'base']
    active_skills = tuple(['root']+sorted([skill for skill in skill_columns if skill in skills_pciked]))
    try:
        first_index = first_indexes[active_skills[1]]
        last_index = list(first_indexes.items())[list(first_indexes.keys()).index(active_skills[1]) + 1][1]
    except:
        first_index = 0
        last_index = 1
    active_skills = str(active_skills).replace('\\xa0',' ')
    # pd.concat([table_model.iloc[first_index:last_index+1], table_model.iloc[-1].to_frame().T])
    nearest_match, _, salary, not_in_match = find_matching_combination_in_dataframe(table_model,table_model, active_skills)
    linear_part = 0
    for lin_skill in not_in_match:
        linear_part += skill_values[lin_skill]
        salary += skill_values[lin_skill]
         
    salary *= reg_coefs.get(region_name, 1)

    st.write('ближайший существующий ',nearest_match)
    st.write('не входят', not_in_match)
    st.write('зп в узле', salary-linear_part)
    st.write('добавлено линейно', linear_part)
    # if len(not_in_match) == 0:
    if salary < 16250:
        salary = 16250
    return salary, reg_coefs.get(region_name, 1),()
    # else:
        # return salary,0,nearest_match




