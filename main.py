import pandas as pd
import json
import numpy as np
import streamlit as st
# from catboost_install import install 
import ast
import os
import catboost as cb 
import re

def get_folders_sorted_by_size(directory):
    folders = [os.path.join(directory, d) for d in os.listdir(directory) if os.path.isdir(os.path.join(directory, d))]

    folder_sizes = {folder: sum(os.path.getsize(os.path.join(dirpath, filename)) 
                                for dirpath, dirnames, filenames in os.walk(folder) 
                                for filename in filenames) 
                    for folder in folders}

    sorted_folders = sorted(folder_sizes.items(), key=lambda x: x[1], reverse=False)

    return sorted_folders


def find_matching_combination_in_dataframe(dataframe, target_input):
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
    longest_match_price = None
    elements_not_in_longest_match = None

    # Итерация по каждому кортежу в индексе DataFrame
    for features_str in dataframe.index:
        features_tuple = eval(features_str)

        # Подсчет совпадающих элементов в последовательности до возникновения несоответствия
        matches = 0
        for i, j in zip(features_tuple, target_tuple):
            if i == j:
                matches += 1
            else:
                break  # Найдено несоответствие, дальнейшее сравнение прекращается

        # Обновление информации о наибольшем совпадении, если это наибольшее совпадение на данный момент
        if matches > longest_match_count:
            longest_match = features_tuple[:matches]
            longest_match_count = matches
            elements_not_in_longest_match = target_tuple[matches:]
            # Попытка найти цену для наибольшего совпадения в DataFrame
            try:
                longest_match_price = dataframe.loc[str(longest_match), 'price']
            except KeyError:
                # В случае отсутствия совпадения, по умолчанию используется свойства элемента 'root'
                longest_match = ('root',)
                longest_match_count = 1
                longest_match_price = dataframe.loc["('root',)", 'price']
                elements_not_in_longest_match = target_tuple[matches:]

    return longest_match, longest_match_count, longest_match_price, elements_not_in_longest_match


def get_predict_tree(n_bundle, vht, exp, ind, region_name, skills_pciked):
    base_path = ''


    file_name = f'{n_bundle}_vht_{vht}_exp_{exp}_ind_{ind}'

    with open(f'results/results3011_reg_coefs/{n_bundle}/{file_name}.json','r') as f:
        reg_coefs = json.load(f)
    # print(x.get(region_name))

    try:
        table_model = pd.read_excel(f'results/results2911_tabels_tree/{n_bundle}/{file_name}.xlsx')
    except Exception as e:
        return e
    
    table_model['features_tuple'] = table_model['features'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
    table_model['second_item'] = table_model['features_tuple'].apply(lambda x: x[1] if len(x) > 1 else None)
    arr = list(table_model['second_item'].iloc[1:])
    first_indexes = dict(sorted({x:arr.index(x)+1 for x in list(set(arr))}.items(), key=lambda x:x[1]))
    table_model = pd.read_excel(f'results/results2911_tabels_tree/{n_bundle}/{file_name}.xlsx', index_col = 0)



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

    nearest_match, _, salary, not_in_match = find_matching_combination_in_dataframe(table_model.iloc[first_index:last_index+1].append(table_model.iloc[-1]), active_skills)

    salary *= reg_coefs.get(region_name, 1)

    return salary

PATTERN = r'\((\d+)'

def set_zp_null():
    st.session_state['prev_zp'] = '0'


if 'prev_zp' not in st.session_state:
    st.session_state['prev_zp'] = '0'


def change_prev_zp(zp):
    st.session_state['prev_zp'] = zp
    
regions = pd.read_csv('regions.csv')
# data = json.load(open('values.json'))
professions = json.load(open('professions.json'))

prof_list = list(professions.keys())

left_column, right_column = st.columns(2)

exp_conv = {'Без опыта':'0', 'От 1 до 3 лет':'1','От 3 лет':'2'}
exp_conv_reverse = {'0':'Без опыта', '1':'От 1 до 3 лет','2':'От 3 лет'}

inp_species = st.sidebar.selectbox( 
        'Наименование вакансии',
        np.unique(prof_list), on_change=set_zp_null)


regions_list = []
# reg_list_view = []

for i in range(regions.shape[0]):
    regions_list += [f'{regions["industry_group"].iloc[i]}_{regions["region_name"].iloc[i]}']
    # reg_list_view += [f'{regions["region_name"].iloc[i]}']


prof_id = professions[inp_species]

# st.text(prof_id)

model = cb.CatBoostRegressor()
model = model.load_model(f"model/{prof_id}.cbm")

# st.subheader('Проверка ')
st.sidebar.subheader(f"Выберите особый вид занятости (необязательно)")
vahta = 1 if st.sidebar.checkbox('Вахта', on_change=set_zp_null) else 0
is_parttime = 1 if st.sidebar.checkbox('Неполная занятость', on_change=set_zp_null) else 0


st.header(f"Оценка стоимости навыков {inp_species}")

st.sidebar.subheader("Выберите регион вакансии")
region = st.sidebar.selectbox(
    'Напишите регион вакансии',
    (regions_list), on_change=set_zp_null)

industry_group = str(regions[regions['region_name'] == region.split('_')[1]]['industry_group'].iloc[0])

parents_and_children = dict(json.load(open(f'jsones_new/Bundles_{prof_id}.json')))
parents_to_children = {}
for skill in parents_and_children:
    if not parents_and_children[skill][0]:
        if not skill in parents_to_children:
            parents_to_children[skill] = set()
    else:
        for parent in parents_and_children[skill][0]:
            parent = str(parent)
            if not parent in parents_to_children:
                parents_to_children[parent] = set()
            parents_to_children[parent].add(skill)

    if parents_and_children[skill][1]:
        for child in parents_and_children[skill][1]:
            child = str(child)
            if not skill in parents_to_children:
                parents_to_children[skill] = set()
            parents_to_children[skill].add(child)

df_id_name = pd.read_csv('v3_competencies_bundles_20231010.csv')
df_id_name['bundle_id'] = df_id_name['bundle_id'].astype(str)
# df_id_name['bundle_name'] = df_id_name['bundle_name'].str.replace('\xa0', ' ')

skill_id_to_names = dict(zip(df_id_name['bundle_id'], df_id_name['bundle_name']))
names_to_skill_id = dict(zip(df_id_name['bundle_name'], df_id_name['bundle_id']))
skills_all = model.feature_names_[6:]
bd_to_model_skills = {' '.join(model_skill.split()[:-1]): model_skill for model_skill in skills_all}


st.sidebar.subheader("Выберите опыт работы")
# left_column1, right_column1 = st.columns([1, 1.2])

skill_groups = ['(СК)', '(ЯС)', 'СПК', '(ИС)', '(УТУТ)', '(ОПТ)', 'Другие']
group_decryption = {'(СК)': 'Личностные компетенции', '(ЯС)': 'Языки сквозные',
                     'СПК': 'Совет по профессиональным квалификациям', '(ИС)': 'Инструменты сквозные',
                     '(УТУТ)': 'Условия по трудоустройству, условия труда (универсальные требования)',
                     '(ОПТ)': 'Обобщённые профессиональные требования', 'Другие': 'Другие'}

groups_distr = {'Другие': []}
for skill in skills_all:
    for group in skill_groups:
        if group in skill:
            group_view = group_decryption[group]
            if not group_view in groups_distr:
                groups_distr[group_view] = []
            groups_distr[group_view].append(skill)
            break
    else:
        groups_distr['Другие'].append(skill)

spk_to_names = pd.read_csv('nark_spk_20231010.csv') #перевод из id в name
spk_to_names = dict(zip(spk_to_names['id'], spk_to_names['name']))

spk_distr = {}
for skill_name in skills_all:
    spk_i = skill_name.split()[-1].split('_')[1][:-1]
    spk_name = spk_to_names.get(int(spk_i), spk_i)
    if not spk_i.isdigit():
        continue
    if not spk_name in spk_distr:
        spk_distr[spk_name] = []
    spk_distr[spk_name].append(skill_name)
    
#['year', 'is_vahta', 'experience_id', 'region_name', 'industry_group', 'is_parttime',

exp_vars = ['Нет опыта', 'От одного года до трёх лет', 'Более трёх лет опыта']
experience_ans = st.sidebar.radio(
    'Опыт работы:',
    exp_vars, on_change=set_zp_null)

experience = exp_vars.index(experience_ans)

# st.subheader(model.feature_names_)
parent_check = {}
children_check = {}
st.subheader("Выберите виды навыков")
arr = st.multiselect('Виды:', groups_distr.keys())

js = dict(json.load(open(f'jsones_skill_salary/{prof_id}.json')))


# skill_stats = pd.read_csv(f'skills_salary_stats/results_version1/{prof_id}.csv')
# skills_predict_stats = skill_stats[(skill_stats.is_vahta == True if vahta else False)
#                              & (skill_stats.is_parttime == True if is_parttime else False)
#                              & (skill_stats.experience_id == experience)
#                              & (skill_stats.region_name == region.split('_')[1]) 
#                              & (skill_stats.industry_group == int(industry_group))]
# if skills_predict_stats.shape[0] == 0:
#     skills_predict_stats = skill_stats[(skill_stats.is_vahta == False)
#                              & (skill_stats.is_parttime == False)
#                              & (skill_stats.experience_id == experience)
#                              & (skill_stats.region_name == region.split('_')[1]) 
#                              & (skill_stats.industry_group == int(industry_group))]


if arr:
    skills_all = model.feature_names_[6:]
    st.subheader("Выберите вид СПК")
    arr_spk = st.multiselect('СПК:', list(spk_distr.keys()))
    used = set()

    group_set = set()
    spk_set = set()
    for group_choice in arr:
        group_set |= set(groups_distr[group_choice])
    for spk in arr_spk:
        spk_set |= set(spk_distr[spk])

    num_cols = 2
    cols = st.columns([1, 1])
    
    available_skills = group_set & spk_set
    if available_skills:

        for index, name in enumerate(available_skills):
            col_index = int(index > len(available_skills) // 2)
            if names_to_skill_id[name.replace(' ' + name.split()[-1], '')] in parents_to_children:
                if name in used:
                    continue
                used.add(name)
                names_view = name[:re.search(PATTERN, name).start() - 1]
                parent_check[name] = cols[col_index].checkbox(names_view)
                parent_name = name
                if parent_check[parent_name]:
                    bd_parent_name = parent_name.replace(' ' + parent_name.split()[-1], '')
                    if names_to_skill_id[bd_parent_name] in parents_to_children and parents_to_children[names_to_skill_id[bd_parent_name]]:
                        # st.write(parent_name)
                        for children_id in parents_to_children[names_to_skill_id[bd_parent_name]]:
                            if skill_id_to_names[children_id] in bd_to_model_skills and not bd_to_model_skills[skill_id_to_names[children_id]] in parents_to_children:
                                children_name = bd_to_model_skills[skill_id_to_names[children_id]]
                                if children_name in used:
                                    continue
                                used.add(children_name)
                                names_view = children_name[:re.search(PATTERN, children_name).start() - 1]
                                # cols[col_index].write(['1231', children_name, used])
                                children_check[children_name] = cols[col_index].checkbox(names_view)
                                    

            




            # st.subheader("Выберите навыки для подсчета зарплаты по вакансии.")
        skills = [int(parent_check.get(name, 0) or  children_check.get(name, 0)) for name in model.feature_names_[6:]]
        skills_pciked = np.array(model.feature_names_[6:])[[True if el else False for el in skills]]

        # st.subheader(f'{skills_pciked}')
        # st.subheader(f'{skills}')


        if st.button('Рассчитать зарплату'):
            # get_stats_predict = 0
            # if skills_predict_stats.shape[0] != 0:
            #     get_stats_predict = skills_predict_stats[skills_pciked].sum(axis=1).iloc[0]

            # prediction  = model.predict([2021,vahta,experience,region,industry_group,is_parttime]+skills)
            # old_pred = prediction
            # # st.subheader(f"prev_zp {st.session_state['prev_zp']}")
            # if st.session_state['prev_zp'] == '0':
            #         st.session_state['prev_zp'] = str(prediction)
            #         # st.session_state['cur_zp'] = str(prediction)
            # else:
            #         st.subheader(f"BEFORE lala:   prev_zp: {st.session_state['prev_zp']}  predict: {prediction}")
            #         prediction = float(st.session_state['prev_zp']) + abs(prediction - float(st.session_state['prev_zp']))
            #         # st.session_state['prev_zp'] = str(prediction)
            #         change_prev_zp(str(prediction))
            #         st.subheader(f"AFTER:   prev_zp: {st.session_state['prev_zp']} predict: {prediction}")

            st.subheader(f'Проверка sample')

            prediction = get_predict_tree(23, 1, 0, 1, 'Республика Дагестан', np.array(['Аккуратность (СК) (575_4)']))


            # prediction = js[str(float(experience))][str(True if vahta else False)][str(industry_group)][str(True if is_parttime else False)]['base']
            # for skill in skills_pciked:
            #     prediction += js[str(float(experience))][str(True if vahta else False)][str(industry_group)][str(True if is_parttime else False)].get(skill, 0)
            # change_prev_zp(str(prediction))
            
            st.subheader(f"Предсказание: {prediction} руб.")
            # st.write(st.session_state)

            # st.subheader(f'{old_pred }')
            # st.subheader(f'{get_stats_predict} - stats pred..')

                
    else:
        if arr_spk:
            st.error('К сожалению, нет доступных навыков. Попробуйте добавить ещё категорий.')
    
