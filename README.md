# Gender Bias In Course Evaluations

This is the GitHub repository for the project *Gender Bias In Course Evaluations*, written by Karl Griphammar, Evelina Strauss, & Betelhem Desta.

As of 2022-01-17, the only code available is the one for setting up the data frames used for the models and the analyses, and also some preprocessing.

The actual .csv files are not uploaded, since they are not meant to be public. The necessary files for running the scripts are:

- 'genusuppdelad-kursstatistik.csv', 

- 'Alla enkäter lå 15-16.xlsx', 

- 'Alla enkäter lå 20-21 lp1 - lp3.xlsx',

-  'Alla enkäter lå 19-20 lp1 - lp4.xlsx',

-   'Alla enkäter lå 14-15.xlsx',

-    'Alla enkäter lå 13-14.xlsx',

-   'Alla enkäter lå 16-17.xlsx,

- 'Alla enkäter lå 17-18.xlsx',

-    'Alla enkäter lå 18-19.xlsx'

-    Folders Pt1 and Pt2 containing all .json files.


In order for this notebook to work without tweaking anything, you need to structure the uploaded files in the current way:

                              Current directory
                                     |
              ------------------------------------------------------------------
              |                      |                      |                  |
         gender_data             surveys               comments_data         output     
              |                      |                      |                  |
              |                      |                      |           (This is where the output files
    'genusupp ... .csv'    'Alla enkäter ... .xlsx'      --------         will end up)
                                   ...                  |        |
                                                       Pt1      Pt2