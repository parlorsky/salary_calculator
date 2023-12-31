import pandas as pd
import json
import numpy as np
import streamlit as st
# from catboost_install import install 
import os
import catboost as cb 
import re
from tree_models import get_predict_tree
import ast
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

# aval_profs = [prof.rstrip('\n') for prof in open('avaliable_profs.txt', 'r', encoding='UTF-8').readlines()]

# prof_list = sorted(set(professions.keys()) & set(aval_profs))

prof_list = list(professions.keys())

left_column, right_column = st.columns(2)

exp_conv = {'Без опыта':'0', 'От 1 до 3 лет':'1','От 3 лет':'2'}
exp_conv_reverse = {'0':'Без опыта', '1':'От 1 до 3 лет','2':'От 3 лет'}

inp_species = st.sidebar.selectbox( 
        'Наименование вакансии',
        np.unique(prof_list))


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
region_out = {reg: reg.split('_')[-1] for reg in regions_list}
region_in = {value: key for key, value in region_out.items()}
region = st.sidebar.selectbox(
    'Напишите регион вакансии',
    (list(region_out.values())), on_change=set_zp_null)

region = region_in[region]

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
pattern_spk = r'_(\d+)[^)]*'
for skill_name in skills_all:
    spk_i = re.findall(pattern_spk, skill_name)[-1]
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

top_skills = pd.read_csv(f'best_skills/{prof_id}/{prof_id}_vht_{vahta}_exp_{experience}_ind_{industry_group}.csv')
top_k_skills = [x[:x.index('(')-1] for x in list(top_skills["Unnamed: 0"])][:8]
# skill_stats = pdx.read_csv(f'skills_salary_stats/results_version1/{prof_id}.csv')
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

        for index, name in enumerate(sorted(available_skills, key = lambda x: x.lower())):
            col_index = int(index > len(available_skills) // 2)
            if names_to_skill_id[name.replace(' ' + name.split()[-1], '')] in parents_to_children:
                if name in used:
                    continue
                used.add(name)
                names_view = name[:re.search(PATTERN, name).start() - 1]
                parent_check[name] = cols[col_index].checkbox(names_view, value = True if names_view in top_k_skills else False)
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


            prediction, rg_cf, nearest = get_predict_tree(int(prof_id), int(vahta), int(experience), int(industry_group), region.split('_')[-1], skills_pciked)


            # prediction = js[str(float(experience))][str(True if vahta else False)][str(industry_group)][str(True if is_parttime else False)]['base']
            # for skill in skills_pciked:
            #     prediction += js[str(float(experience))][str(True if vahta else False)][str(industry_group)][str(True if is_parttime else False)].get(skill, 0)
            # change_prev_zp(str(prediction))
            if rg_cf != 0 :
                st.write(f"Предсказание: {round(prediction//100*100)} руб. Коэффициент региона: {round(rg_cf,3)}")
            else:
                st.write('Такой комбинации нет, ближайшее значение:', nearest)
                st.write(f"Предсказание: {round(prediction//100*100)} руб.")
            # st.write(st.session_state)

            # st.subheader(f'{old_pred }')
            # st.subheader(f'{get_stats_predict} - stats pred..')

                
    else:
        if arr_spk:
            st.error('К сожалению, нет доступных навыков. Попробуйте добавить ещё категорий.')
    
