# -*- coding: utf-8 -*-
"""
Created on Thu Jul 19 15:01:47 2018

@author: martin
"""

import pandas as pd
import numpy as np
from scipy.stats import chisquare
from scipy.stats import linregress

csv_file = "ccrb_datatransparencyinitiative_20170207.csv"
# exported the excel spreadsheet into a csv for ease of use with python
data = pd.read_csv(csv_file)

data_complete = data.dropna(axis = 0)
# I searched through the data, but there doesn't appear to be any values which
# represent missing data other than NaN's. I treated "other" values as complete data.
data_unique = data.drop_duplicates(["UniqueComplaintId"], keep=False)
data_unique_complete = data_unique.dropna(axis=0)

# Q: How many unique complaints (identified by 'UniqueComplaintId') with 
# complete information (i.e. there are no missing values) appear in the dataset?
n_unique = len(data_unique_complete.index)

# Q: What proportion of complaints occur in the borough with the largest number of complaints? 
counts = data_unique_complete['Borough of Occurrence'].value_counts()
max_count = counts[0]
max_borough = counts.index[0] # value_counts delivers a sorted array
proportion = max_count / n_unique


# Q: How many complaints per 100k residents were there in the borough with the 
# highest number of complaints per capita resulting from incidents in 2016?
b = ["Manhattan", "Bronx", "Brooklyn", "Queens", "Staten Island"]
pops = [1664727, 1471160, 2648771, 2358582, 479458] # from wikipedia
populations = pd.Series(pops, b)

data_2016 = data_unique_complete[data_unique_complete["Received Year"] == 2016]
counts_2016 = data_2016["Borough of Occurrence"].value_counts()
per_capita = (counts_2016/populations).sort_values(ascending=False)*100000
max_per_capita = per_capita[0]

# Q: What is the average number of years it takes for a complaint to be closed? 
n_years = (data_unique_complete["Close Year"] - data_unique_complete["Received Year"]).mean()
# This result is probably extremely wrong. We only have data on a resolution of
# 1 year, which means the figure is very inaccurate. 

# Q: Use linear regression from the year complaints about stop and frisk peaked
# through 2016 (inclusive) to predict how many stop and frisk incidents in 2018
# will eventually lead to a complaint.

stop_frisk_bool = ((data["Reason For Initial Contact"] == "Stop/Question/Frisk")
                   | (data["Allegation Description"] == "Frisk"))
                  # | (data["Allegation Description"] == "Question and/or stop"))

year_bool = (data["Received Year"] >= 2006) & (data["Received Year"] < 2017)

stop_and_frisk = data[stop_frisk_bool & year_bool]
year_totals = stop_and_frisk["Received Year"].value_counts()

x = year_totals.index
y = year_totals.values

slope, intercept, _, _,_ = linregress(x, y)
predicted = int(intercept + slope * 2018)

# Q: Each row in the data set corresponds with a specific allegation. 
# Therefore a particular complaint, designated by 'UniqueComplaintId', may have
# multiple allegations. Consider only allegations with complete information.
# Is the presence of a certain type of allegation (i.e. 'Allegation FADO Type')
# indicative that a complaint will contain multiple allegations? 
# Create indicator variables for whether a complaint contains each type of
# allegation, and perform a linear regression of the number of allegations per 
# complaint against these indicator variables. 
# What is the maximum coefficient of the linear regression?

# I'm not answering this question because performing linear regression on 
# categorical variables is statistically dubious, and far from the best solution.

# Q: Calculate the chi-square test statistic for testing whether a complaint is 
# more likely to receive a full investigation when it has video evidence.

x = data_unique_complete["Complaint Has Video Evidence"].values.astype(int)
y = data_unique_complete["Is Full Investigation"].values.astype(int)
n_points = len(x)

observed = np.zeros((2,2))
for i,j in zip(x, y):
    observed[i,j] += 1
  
expected = np.outer(observed.sum(axis=1), observed.sum(axis=0)) / n_points
chi2, pvalue = chisquare(observed.ravel(), expected.ravel(), ddof=2)

# Q: Assuming that complaints per capita are proportional to officers per 
# capita in each borough, calculate the average number of officers per precinct
# in each borough (ignore complaints from outside of NYC). What is the ratio of
# the highest number of officers per precinct to the lowest number of officers 
#per precinct?

b = ["Manhattan", "Bronx", "Brooklyn", "Queens", "Staten Island"]
n_precincts = [34, 13, 23, 16, 4]
precincts_per_borough = pd.Series(n_precincts, b)

officer_estimate = per_capita*3600 / precincts_per_borough
ratio = max(officer_estimate)/min(officer_estimate)
# Note that the question was ambgiuous. I interpreted it to mean that complaints
# are evently distributed within precincts within a borough.





