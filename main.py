import pandas as pd
import json
import numpy as np
import streamlit as st
# from catboost_install import install 
import os
import catboost as cb 




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
model = model.load_model(f"model/{prof_id}.json", format  = 'json')

vahta = 1 if st.checkbox('Вахта') else 0
is_parttime = 1 if st.checkbox('Неполная занятость') else 0


st.header(f"Оценка стоимости навыков {inp_species}")

st.subheader("Выберите регион вакансии")
region = st.selectbox(
    'Напишите регион вакансии',
    (regions_list))

industry_group = str(regions[regions['region_name'] == region.split('_')[1]]['industry_group'].iloc[0])



st.subheader("Выберите опыт работы")
left_column1, right_column1 = st.columns(2)

#['year', 'is_vahta', 'experience_id', 'region_name', 'industry_group', 'is_parttime',
with left_column1:

    experience = st.radio(
        'Опыт работы:',
        [0,1,2])

    st.subheader(model.feature_names_)


    st.subheader("Выберите навыки для подсчета зарплаты по вакансии.")
    skills = [i if st.checkbox(i) else 0 for i in model.feature_names_[6:]]


    
    if st.button('Рассчитать зарплату'):
        prediction  = model.predict([2021,vahta,experience,region,industry_group,is_parttime]+skills)

        st.write(f"ЗП: {round(prediction,2)}")
    
