import pandas as pd

# Reformatting columns:
def course_code(row):
    '''
    This function should add one column called 'Kurskod' with the correct course code from column 'Kurs', which
    is cut from the 'Kurs' column.
    The function also reformat the 'Läsperiod' column, such that 'LP1-2' -> 'LP1'. We are only interested in when
    the course starts, and now how long it spans.

    The function is meant to be used on the survey set.
    '''
    row['Kurskod'] = row['Kurs'][:6]
    row['Kurs'] = row['Kurs'][9:]

    #old_lp = row['Läsperiod']
    #new_lp = row['Läsperiod'][:3]
    #row['Läsperiod'] = new_lp
    row['Läsperiod'] = row['Läsperiod'][:3]

    return row

def study_period(row):
    '''
    This function converts the startdate of a course to study period and study year.
    E.g. '2016-01-01' -> Study period: 3, Study year: 2015
    Note that we assume that that the study year is different from the calendar year,
    so when a course starts in January 2016, it should be in study period 3 in study 
    year 2015. The study year is assumed to start with the first study period in August/September.

    The function is meant to be used on the gender_set.
    '''
    m = row['start_datum_kurs'].month
    y = row['start_datum_kurs'].year
    if m < 2:
        lp = 3
    elif m < 8:
        lp = 4
    elif m < 10:
        lp = 1
    else:
        lp = 2
        
    if lp > 2:
        la = str(y-1) + '/' + str(y)
    else:
        la = str(y) + '/' + str(y+1)
    lp = 'LP' + str(lp)    
    row['Läsperiod'] = lp
    row['Läsår'] = la
    
    return row

def preprocess_gender_set(df_raw: pd.DataFrame) -> pd.DataFrame:
    '''
    A function for processing the gender set. Includes removing unused columns, renaming the rest, dropping values.
    It also sums values up to compute the total number of male and female student.

    The function is meant to be used on the raw gender_set.
    '''

    df = df_raw[df_raw.columns[[0, 1, 3, 4, 13, 21, 29, 37, 38]]]
    # Rename columns
    df = df.rename(columns={'Unnamed: 0': 'Kurskod', 'Unnamed: 1': 'Kurs', 'Unnamed: 3': 'start_termin', 'Unnamed: 4': 'start_datum_kurs', 'FFG.7': 'FFG_kvinna_total', 'FFG.15': 'FFG_man_total', 'OM.7': 'OM_kvinna_total', 'OM.15': 'OM_man_total'})

    # Drop first 2 rows (contains no information)
    df = df.drop([0,1])

    # Replace null values with 0
    df = df.fillna(0)
    df = df.replace('-', 0)

    # Drop rows without course code. Course code is the key value we use for joining with the other dataframes, hence
    # courses without course code is of no use to us. It was beyond the scope of this project to find out the course code
    # in any other way:
    df = df.drop(df[df.Kurskod == 0].index)

    # Convert some formats to others:
    df = df.astype({'start_datum_kurs':'datetime64','FFG_kvinna_total': float, 'FFG_man_total': float, 'OM_kvinna_total': float, 'OM_man_total': float})

    # Removes all courses taught before 2012 (Assuming we don't need these, 
    # since we only have data from this year in the other sets.)
    df.drop(df[df.start_datum_kurs.dt.year < 2013].index, inplace=True)

    # Sum FFG and OM for women and men
    df['female_total'] = df.apply(lambda x: x['FFG_kvinna_total'] + x['OM_kvinna_total'], axis=1)
    df['male_total'] = df.apply(lambda x: x['FFG_man_total'] + x['OM_man_total'], axis=1)
    gender_set = df.groupby(['Kurskod', 'start_datum_kurs']).agg({'female_total': 'sum', 'male_total': 'sum'}).reset_index()

    # Convert start date to study period (Läsperiod). Also adds a column of study year (Läsår).
    gender_set = gender_set.apply(study_period,axis=1)

    return gender_set

def preprocess_survey_set(df_raw: pd.DataFrame) -> pd.DataFrame:
    '''
    Function for preprocessing the survey set.
    '''

    df = df_raw[['Kursägare', 'Kurs', 'Läsår', 'Läsperiod', 'Svar (Antal)', 'Svar (%)',
       'Fråga 1', 'Fråga 2', 'Fråga 3A', 'Fråga 3B', 'Fråga 3C', 'Fråga 4',
       'Fråga 5', 'Fråga 6', 'Fråga 7']]
    survey_set = df.apply(course_code,axis=1)

    return survey_set


def correct_sp(row, surv_data: pd.DataFrame):
    '''
    Function that should correct the mislabled study periods in the gender_set.
    '''

    # Subset of the missing value with matching study year:
    c1 = surv_data[surv_data['Läsår'] == row['Läsår']]
    # Subset of these that matches the course code:
    c2 = c1[c1['Kurskod'] == row['Kurskod']]

    # If there are still values in this set, this means that the row
    # are missing from the original join, so we will increment the study period with 1.
    if c2.shape[0]>0:
        old = row['Läsperiod']
        new = 'LP' + str(int(old[2])+1)
        row['Läsperiod'] = new
    
    return row

def correct_study_period(gender_set: pd.DataFrame, survey_set: pd.DataFrame) -> pd.DataFrame:
    '''
    Function for finding mislabled datapoints and correcting the mislabled study period.
    '''
    # Make a temporary outer join of the two sets:
    temp_set = pd.merge(survey_set, gender_set,how='outer',indicator=True,on=["Kurskod", "Läsperiod", "Läsår"])
    # Find the data points that don't between sets:
    temp_set = temp_set[(temp_set._merge != 'both')]

    # This set should now contain all rows that have corresponding rows in gender_set wrongly labeled:
    missing_vals = temp_set[temp_set['_merge'] == 'left_only']
    print(f'There are {missing_vals.shape[0]} mismatching values from the gender set')

    # Applying function for correcting the study period:
    gender_set_correct = gender_set.apply(correct_sp, surv_data=missing_vals,axis=1)

    return gender_set_correct

def merge_sets(gender_set: pd.DataFrame, survey_set: pd.DataFrame) -> pd.DataFrame:
    '''
    Function for merging the processed gender set and survey set. Also renames all columns to English.
    '''

    # Performing the join between the corrected gender_set and the survey_set. Note that this is an
    # inner join, so only matching values will transfer over to the merged set.
    merged_set = pd.merge(gender_set, survey_set, on=["Kurskod", "Läsperiod", "Läsår"],how='inner')
    print('Number of datapoints in gender set: {}'.format(gender_set.shape[0]),
        'Number of datapoints in survey set: {}'.format(survey_set.shape[0]),
        'Number of datapoints in merged set: {}'.format(merged_set.shape[0])
        )

    # Looking for null-values in the survey-set:
    if not merged_set.isnull().values.any():
        print('No missing values in the merged set.')

    # Translating the column names to english:
    english_names = {'Kurskod':'code',
                    'start_datum_kurs':'start_date',
                    'Läsperiod':'period',
                    'Läsår':'year', 
                    'Kursägare':'course_owner',
                    'Kurs':'course',
                    'Svar (Antal)':'no_respondents',
                    'Svar (%)':'ratio_respondents',
                    'Fråga 1':'Question 1',
                    'Fråga 2':'Question 2',
                    'Fråga 3A':'Question 3A',
                    'Fråga 3B':'Question 3B',
                    'Fråga 3C':'Question 3C',
                    'Fråga 4':'Question 4',
                    'Fråga 5':'Question 5',
                    'Fråga 6':'Question 6',
                    'Fråga 7':'Question 7'}

    merged_set = merged_set.rename(columns=english_names)

    return merged_set

    
def remove_multiple_examiners(row):
    '''
    Function for removing multiple examiners. That is, we only count the first examiner listed.
    (This is obviously a weakness with the study, but it was beyond the scope of the project to
    do something more sophisticated.)
    '''
    if len(row.examiners) > 1:
        new_exam = row.examiners[0]
        row.examiners = [new_exam]
    return row

def fill_missing_genders(survey_comments: pd.DataFrame) -> pd.DataFrame:
    '''
    Function for filling in missing genders of examiners when possible. Originally, the gender
    was assigned automatically with reference to a dictionary of the most common gender per name.
    However, in some cases with unusual or misspelled names, this algorithm failed. We manually
    looked the genders of these names up when possible in the Chalmers personnel list. 
    '''
    # Fills in missing genders:
    name_dct = {'Yiannis': 'M','Frank':'M', 'Joosef':'M', 'Saroj': 'M', 'Yujing': 'M', 'Jan-alve': 'M', 'Giada': 'F', 'Joosef': 'M', 'Jelke': 'M',
                'Serik': 'M', 'Gauti': 'M', 'Avgust': 'M', 'Romaric': 'M', 'Zhongxia': 'M', 'Reto': 'M', 'Huadong': 'M',
                'Arkady': 'M', 'Vessen': 'M', 'Fang': 'F', 'Walter': 'M', 'Elad': 'M', 'Wengang': 'M', 'Ignasi': 'M', 
                'Kengo': 'M', 'Moritz': 'M', 'Kamyab': 'M', 'Jan-philipp': 'M',  'Yemao': 'M',  'Peiyuan': 'M',  'Scott': 'M',
                'Luping': 'M',  'Jaan-henrik': 'M',  'Philippas': 'M',  'Sheng': 'M',  'Xiaobo': 'M', 'Xuezhi': 'F',
                'Devdatt': 'M', 'Hendry': 'M', 'Ergang': 'M',  'Sampsa': 'M',  'Ali': 'M',  'Sus': 'F', 'Graham': 'M',
                'Ida-maja': 'F', 'Mozhdeh': 'F', 'Witlef': 'M', 'Changfu': 'M',  'Patrizio': 'M',  'Yu': 'F', 
                'Karinne': 'F', 'Ahmed': 'M',  'Antal': 'M'}

    for n, g in name_dct.items():
        c = survey_comments.examiners == n
        #survey_comments[c]=survey_comments
        survey_comments[c]=survey_comments[c].fillna({'gender':g})

    return survey_comments

def period_fixer_only(row):
    '''
    Fixes study periods and nothing more, such that 'LP2-3' -> 'LP2'
    '''
    old_lp = row['period']
    new_lp = row['period'][:3]
    row['period'] = new_lp
    return row

def merge_all_sets(survey_gender_set: pd.DataFrame, survey_comment_set: pd.DataFrame) -> pd.DataFrame:
    '''
    Function for merging all sets together. Selects only the relevant columns for our investigations.
    '''

    # Some relevant columns from comments-set (This can be changed if we want to include other columns):
    rel_cols = ['year', 'code', 'period','mean','gender','examiners','lang',
    'comments.8.question', 'comments.8.text',
    'comments.8.words', 'comments.8.polarity.afinn',
    'comments.8.polarity.vader-text', 'comments.8.polarity.vader-sents',
    'allcomments.text', 'allcomments.words', 'allcomments.polarity.afinn',
    'allcomments.polarity.vader-text', 'allcomments.polarity.vader-sents']

    # Merging with the previous "full" set:
    print('Comments set:', survey_comment_set.shape)
    print('Gender and survey set:', survey_gender_set.shape)

    full_set = pd.merge(survey_gender_set, survey_comment_set[rel_cols], on=["code", "period", "year"], how='left')
    print('Full set:', full_set.shape)

    return full_set