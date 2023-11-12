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
            if not parent in parents_to_children:
                parents_to_children[parent] = set()
            parents_to_children[parent].add(skill)

    if parents_and_children[skill][1]:
        for child in parents_and_children[skill][1]:
            if not skill in parents_to_children:
                parents_to_children[skill] = set()
            parents_to_children[skill].add(child)

df_id_name = pd.read_csv('v3_competencies_bundles_20231010.csv')

skill_id_to_names = dict(zip(df_id_name['bundle_id'], df_id_name['bundle_name']))
names_to_skill_id = dict(zip(df_id_name['bundle_name'], df_id_name['bundle_id']))

st.subheader("Выберите опыт работы")
left_column1, right_column1 = st.columns([1, 2])

#['year', 'is_vahta', 'experience_id', 'region_name', 'industry_group', 'is_parttime',
with left_column1:

    experience = st.radio(
        'Опыт работы:',
        [0,1,2])

    # st.subheader(model.feature_names_)
    skills_all = model.feature_names_[6:]
    parent_check = {}
    children_check = {}
    st.subheader("Выберите навыки для подсчета зарплаты по вакансии.")
    for name in skills_all:
        if names_to_skill_id[name] in parents_to_children:
            parent_check[name] = st.checkbox(name)

    for parent_name in parent_check:
        if parent_check[parent_name]:
            if parents_to_children[parent_name]:
                right_column1.write(parent_name)
                for children_id in parents_to_children[parent_name]:
                    children_name = skill_id_to_names[children_id]
                    children_check[children_name] = right_column1.checkbox(children_name)
    




    # st.subheader("Выберите навыки для подсчета зарплаты по вакансии.")
    skills = [int(parent_check.get(name, 0) or  children_check.get(name, 0)) for name in model.feature_names_[6:]]
    skills_names = model.feature_names_[skills]

    
    if st.button('Рассчитать зарплату'):
        prediction  = model.predict([2021,vahta,experience,region,industry_group,is_parttime]+skills)

        st.subheader(f"Предсказание: {round(prediction//100*100)} руб.")
        
    