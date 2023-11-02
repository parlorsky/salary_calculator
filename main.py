import pandas as pd
import json
import numpy as np
import streamlit as st



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

data = json.load(open(f'models/{prof_id}.json'))

available_choices =  {0: {0:{0:0,1:0,2:0},\
                      1:{0:0,1:0,2:0},\
                      2:{0:0,1:0,2:0}},\
                      1:{0:0,1:0,2:0}}

is_vahta_here = 0

for is_vahta in [0,1]:
    for industry_group in [0,1,2]:
        for experience_id in [0,1,2]:
            if is_vahta == 0:
                if len(list(data[str(is_vahta)][str(industry_group)][str(experience_id)].keys())) != 0:
                    available_choices[is_vahta][industry_group][experience_id] = 1
            else:
                if len(list(data[str(is_vahta)][str(experience_id)].keys())) != 0:
                    available_choices[is_vahta][experience_id] = 1
                    is_vahta_here = 1


if is_vahta_here:
    vahta = '1' if st.checkbox('Вахта') else '0'

else:
    vahta = '0'


if vahta == '0':
    st.header(f"Оценка стоимости навыков {inp_species}")

    st.subheader("Выберите регион вакансии")
    region = st.selectbox(
        'Напишите регион вакансии',
        (regions_list))

    industry_group = str(regions[regions['region_name'] == region.split('_')[1]]['industry_group'].iloc[0])

    available_exp = []
    for i in range(3):
        if available_choices[0][int(industry_group)][i] != 0:
            available_exp += [exp_conv_reverse[str(i)]]


    st.subheader("Выберите опыт работы")
    left_column1, right_column1 = st.columns(2)
    with left_column1:

        experience = st.radio(
            'Опыт работы:',
            np.unique(available_exp))



    st.subheader(f"Базовые навыки {inp_species} {experience}")
    for number,skill in enumerate(data[str(vahta)][str(industry_group)][exp_conv[experience]]['base_skills']):
        st.write(f'{number+1}) {skill}')

    st.subheader("Выберите навыки для подсчета зарплаты по вакансии.")
    regular_skills = [i if st.checkbox(i) else 0 for i in data[str(vahta)][str(industry_group)][exp_conv[experience]]['regular_skills']]
    rare_skills = [i if st.checkbox(i) else 0 for i in data[str(vahta)][str(industry_group)][exp_conv[experience]]['rare_skills']]


    try:
        region_coef = float(data[str(vahta)][str(industry_group)][exp_conv[experience]]['region_coefs'][region])
    except:
        region_coef =1
    
    if st.button('Рассчитать зарплату'):
        prediction  = data[str(vahta)][str(industry_group)][exp_conv[experience]]['base_salary'] 
        for i in regular_skills:
            if i != 0:
                prediction += data[str(vahta)][str(industry_group)][exp_conv[experience]]["regular_values"][i]
        for i in rare_skills:
            if i != 0:
                prediction += data[str(vahta)][str(industry_group)][exp_conv[experience]]["rare_values"][i]

        prediction *= region_coef

        st.write(f"ЗП: {round(prediction,2)}")
    
else:
    st.header(f"Оценка стоимости навыков {inp_species}")

    st.subheader("Выберите регион вакансии")
    region = st.selectbox(
        'Напишите регион вакансии',
        (regions_list))


    available_exp = []

    for i in range(3):
        if available_choices[1][i] != 0:
            available_exp += [exp_conv_reverse[str(i)]]


    st.subheader("Выберите опыт работы")
    left_column1, right_column1 = st.columns(2)
    with left_column1:

        experience = st.radio(
            'Опыт работы:',
            np.unique(available_exp))



    st.subheader(f"Базовые навыки {inp_species} {experience}")
    for number,skill in enumerate(data[str(vahta)][exp_conv[experience]]['base_skills']):
        st.write(f'{number+1}) {skill}')

    st.subheader("Выберите навыки для подсчета зарплаты по вакансии.")
    regular_skills = [i if st.checkbox(i) else 0 for i in data[str(vahta)][exp_conv[experience]]['regular_skills']]
    rare_skills = [i if st.checkbox(i) else 0 for i in data[str(vahta)][exp_conv[experience]]['rare_skills']]

#1

    try:
        region_coef = float(data[str(vahta)][exp_conv[experience]]['region_coefs'][region])
    except:
        region_coef =1
        
    if st.button('Рассчитать зарплату'):
        prediction  = data[str(vahta)][exp_conv[experience]]['base_salary'] 
        for i in regular_skills:
            if i != 0:
                prediction += data[str(vahta)][exp_conv[experience]]["regular_values"][i]
        for i in rare_skills:
            if i != 0:
                prediction += data[str(vahta)][exp_conv[experience]]["rare_values"][i]

        prediction *= region_coef

        st.write(f"ЗП: {round(prediction,2)}")
    
