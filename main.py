import pandas as pd
import json
import numpy as np
import streamlit as st
# from catboost_install import install 
import os
import catboost as cb 


#

regions = pd.read_csv('regions.csv')
# data = json.load(open('values.json'))
professions = json.load(open('professions.json'))

prof_list = list(professions.keys())

left_column, right_column = st.columns(2)

exp_conv = {'Без опыта':'0', 'От 1 до 3 лет':'1','От 3 лет':'2'}
exp_conv_reverse = {'0':'Без опыта', '1':'От 1 до 3 лет','2':'От 3 лет'}

with left_column:
    inp_species = st.selectbox(
        'Наименование вакансии',
        np.unique(prof_list))


regions_list = []

for i in range(regions.shape[0]):
    regions_list += [f'{regions["industry_group"].iloc[i]}_{regions["region_name"].iloc[i]}']

prof_id = professions[inp_species]

st.text(prof_id)

model = cb.CatBoostRegressor()
model = model.load_model(f"model/{prof_id}.cbm")

vahta = 1 if st.checkbox('Вахта') else 0
is_parttime = 1 if st.checkbox('Неполная занятость') else 0


st.header(f"Оценка стоимости навыков {inp_species}")

st.subheader("Выберите регион вакансии")
region = st.selectbox(
    'Напишите регион вакансии',
    (regions_list))

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


st.subheader("Выберите опыт работы")
left_column1, right_column1 = st.columns([1, 1.2])

skill_groups = ['(СК)', '(ЯС)', 'ППКСУП', 'СПК', '(ИС)', '(УТУТ)', '(ОПТ)', 'Другие']
groups_distr = {group: [] for group in skill_groups}
for skill in skills_all:
    for group in skill_groups:
        if group in skill:
            groups_distr[group].append(skill)
            break
    else:
        groups_distr['Другие'].append(skill)

spk_distr = {}
for skill_name in skills_all:
    spk_i = skill_name.split()[-1].split('_')[1][:-1]
    if not spk_i.isdigit():
        continue
    if not spk_i in spk_distr:
        spk_distr[spk_i] = []
    spk_distr[spk_i].append(skill_name)

        
    
#['year', 'is_vahta', 'experience_id', 'region_name', 'industry_group', 'is_parttime',


experience = st.radio(
    'Опыт работы:',
    [0,1,2])

# st.subheader(model.feature_names_)
num_cols = 2
cols = st.columns(num_cols)
parent_check = {}
children_check = {}
cols[0].subheader("Выберите виды навыков.")
arr = cols[0].multiselect('Виды:', skill_groups)
skills_all = model.feature_names_[6:]
cols[1].subheader("Выберите вид СПК.")
arr_spk = cols[1].multiselect('СПК:', list(spk_distr.keys()))

for group_choice in arr:
    for spk in arr_spk:
        available_skills = set(groups_distr[group_choice]) & set(spk_distr[spk])
        for index, name in enumerate(available_skills):
            col_index = index % num_cols
            if names_to_skill_id[name.replace(' ' + name.split()[-1], '')] in parents_to_children:
                parent_check[name] = cols[col_index].checkbox(name)
                parent_name = name
                if parent_check[parent_name]:
                    bd_parent_name = parent_name.replace(' ' + parent_name.split()[-1], '')
                    if names_to_skill_id[bd_parent_name] in parents_to_children and parents_to_children[names_to_skill_id[bd_parent_name]]:
                        # st.write(parent_name)
                        for children_id in parents_to_children[names_to_skill_id[bd_parent_name]]:
                            if skill_id_to_names[children_id] in bd_to_model_skills:
                                children_name = bd_to_model_skills[skill_id_to_names[children_id]]
                                cols[col_index].txt(children_name)
                                children_check[children_name] = cols[col_index].checkbox(children_name)

    




    # st.subheader("Выберите навыки для подсчета зарплаты по вакансии.")
skills = [int(parent_check.get(name, 0) or  children_check.get(name, 0)) for name in model.feature_names_[6:]]

if st.button('Рассчитать зарплату'):
    prediction  = model.predict([2021,vahta,experience,region,industry_group,is_parttime]+skills)

    st.subheader(f"Предсказание: {round(prediction//100*100)} руб.")
        
    