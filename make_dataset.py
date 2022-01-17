from pathlib import Path
import pandas as pd
import json

from preprocessing_functions import *

# Paths to directories. Change if need to, but you might want to change the notebook later on:
gender_path = Path.cwd() / 'gender_data'
surveys_path = Path.cwd() / 'surveys'
comments_path = Path.cwd() / 'comments_data'
output_path = Path.cwd() / 'output'

# Reading gender set (genusuppdelad_kursstatistik.csv)
raw_gender_set = pd.read_csv(gender_path / 'genusuppdelad-kursstatistik.csv', delimiter=';')
# Some preprocessing:
gender_set = preprocess_gender_set(raw_gender_set)

# Reading survey-score files (files named 'Alla enkäter lå [...].xlsx):
pathlist = Path(surveys_path).glob('*.xlsx')
surv_lst = []

for fname in pathlist:
    surv = pd.read_excel(fname)
    surv_lst.append(surv[1:-3]) # Drops the first and last three rows, which should not contain any information.

# Read list to DataFrame:
raw_surveys = pd.concat(surv_lst, ignore_index=True)

# Some preprocessing:
survey_set = preprocess_survey_set(raw_surveys)

print('Size of survey data set:', survey_set.shape)
print('Size of gender distribution data set:', gender_set.shape)

# Notice that there is a huge difference. This is most likely due to that there are more courses registered 
# in the gender_set than in the survey_set. For example, we are examining the number of courses from 2013 
# in the gender set compared to the survey set:

print('Number of courses from 2013/14 in gender set:',len(gender_set[gender_set.Läsår == '2013/2014']))
print('Number of courses from 2013/14 in survey set:',len(survey_set[survey_set.Läsår == '2013/2014']))

# After some investigation, we found out that some study periods were labled in a different way in the gender_set.
# It turned out that the starting date in the gender set referred to  when the course was registered in the system.
# This meant that some courses that were given in the 4th study period (according to the survey set) sometimes was
# labled with study period = 3, because these courses were registered in January in the system.
# Hence, we apply a function for correcting these mislabled study periods. This means that we assumed that the
# course periods in the survey set showed the correct value.
gender_set = correct_study_period(gender_set, survey_set)

# Finally, merging the two sets into a full set:
gender_survey_merged = merge_sets(gender_set, survey_set)


# Saving the full set so far as csv:
fname_survey_gender = 'gender_survey_merged.csv'
gender_survey_merged.to_csv(output_path / fname_survey_gender)
print('File saved as ',fname_survey_gender)

# Creating the survey set, containing all written comments from course evaluations:

# The following path should be one director above Pt1 and Pt2.
# (E.g. in this case, the folders Pt1 and Pt2 are placed in the current directory.)
path_list = 'Pt1', 'Pt2'
coms_ = []
for dir_ in path_list:
    pathlist = Path(comments_path / dir_).glob('*.json')
    for fname in pathlist:
        with open(fname) as data_file:    
            tmp_data = json.load(data_file)
        coms_.append(pd.json_normalize(tmp_data))
        
survey_comments = pd.concat(coms_, ignore_index=True)
survey_comments.to_csv(output_path / 'raw_comments.csv')

# In some cases multiple examiners are listed for a course, which we
# don't take into consideration in this study. We only count the first
# examiner.
survey_comments = survey_comments.apply(remove_multiple_examiners,axis=1)

# In the original dataframe, the examiners are stored as lists. THis should fix that:
survey_comments = survey_comments.explode('examiners')

# Filling in missing gender values:
survey_comments = fill_missing_genders(survey_comments)

# Reformatting some study periods:
survey_comments = survey_comments.apply(period_fixer_only, axis = 1)

# Finally, merging ALL sets:
full_set = merge_all_sets(gender_survey_merged, survey_comments)

# Saving the csv:
full_set.to_csv(output_path / 'full_set.csv')