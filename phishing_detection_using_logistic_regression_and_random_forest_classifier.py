# -*- coding: utf-8 -*-
"""Phishing Detection Using Logistic Regression and Random Forest Classifier

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1hd_9cJo7J9eJLyuc-xHKWXMkfJEMLEDW

##Importing Libraries
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

pd.set_option('display.max_columns', None)
plt.rcParams['figure.figsize'] = (12,6)

"""## Predicting Phishing Web Page Using Machine Learning

Phishing is a method of trying to gather personal information using deceptive e-mails and websites.

In this notebook, we will read the data and look at what are the features that can give us information on what are the attributes of a phishing website

## Loading the dataset
"""

data = pd.read_csv("https://raw.githubusercontent.com/khuynh22/Phishing-Detection/main/Phishing_Legitimate_full.csv")

"""## Converting dataset

In this phase we will convert float64 and int64 data to type 32, by doing this we can save the memory usage and we can prepare the data for using with sklearn random forest later for training purpose

As we can see the data has 10k rows and 50 columns including labels
"""

float_cols = data.select_dtypes('float64').columns
for c in float_cols:
    data[c] = data[c].astype('float32')
    
int_cols = data.select_dtypes('int64').columns
for c in int_cols:
    data[c] = data[c].astype('int32')
    
data.info()

data.rename(columns = {'CLASS_LABEL': 'labels'}, inplace = True)

"""## Viewing the data"""

data.sample(5)

"""## Summarizing Statistics

By using the describe method, we can see some of the columns have high variance and some have smaller variance, this is due to the fact that some of the column have bigger values and bigger ranges
"""

data.describe()

"""## Balanced/Imbalanced Checking"""

data['labels'].value_counts().plot(kind = 'bar')

"""## Spearman Correlation

By looking the spearman correlation, we can find which features are linearly correlated in terms of predicting if a site is phising or not
"""

def corr_heatmap(data, idx_s, idx_e):
  y = data['labels']
  temp = data.iloc[:, idx_s:idx_e]
  if 'id' in temp.columns:
    del temp['id']
  temp["labels"] = y
  sns.heatmap(temp.corr(), annot= True, fmt = '.2f')
  plt.show()

"""## Heatmap of first 50 columns

By looking at the first 10 columns against labels, we can concluded that non of the features have strong correlation with the labels, however, NumDash has some significant negative effect towards the labels, which could mean if there is less number of dash then it is more likely to be phising site
"""

# First 10 columns
corr_heatmap(data, 0, 10)

"""## Columns 10 to 20

There are no strong or even medium level strength correlation features with labels
"""

# Column 11 to 20
corr_heatmap(data, 10, 20)

"""##Columns 20 to 30

Columns 20 to 30
Still no strong correlation feature
"""

# Column 21 to 30
corr_heatmap(data, 20, 30)

"""## Columns 30 to 40

Well here we have a few features that are linearly correlated to our dep variable

* InsecureForms shows that as the value is higher so the probability of being a phising site

* PctNullSelfRedirectHyperlinks shows the same positive correlation as InsecureForms

* FequentDomainNameMismatch shows that it has medium linear correlation in positive direction

* SubmitInfoToEmail seems to indicate that sites that ask users to submit their details to emails seems to be more high probability for phising
"""

# Column 31 to 40
corr_heatmap(data, 30, 40)

"""##Columns 40 to 50

The only column in this group that has some correlation with labels is PctExtNullSelfRedirectHyperlinksRT and it has negative effect towards labels which could mean that when the number of percent of null self redirect hyperlinks occur hence the probabiliy of phising increases
"""

# Column 41 to 50
corr_heatmap(data, 40, 50)

"""##Mutual Info Classifier

We will use mutual info classifier to find non linear and linear correlation betweem the features and labels
"""

from sklearn.feature_selection import mutual_info_classif

X = data.drop(['id', 'labels'], axis = 1)
y = data['labels']

discrete_features = X.dtypes == int

"""Here we process the scores and we can see that now mutual info is showing a bit different list from spearman corr"""

# Process the scores and compare with spearman corr
mi_scores = mutual_info_classif(X, y, discrete_features=discrete_features)
mi_scores = pd.Series(mi_scores, name = 'MI Scores', index = X.columns)
mi_scores = mi_scores.sort_values(ascending = False)
mi_scores

def plot_mi_scores(scores):
    scores = scores.sort_values(ascending=True)
    width = np.arange(len(scores))
    ticks = list(scores.index)
    plt.barh(width, scores)
    plt.yticks(width, ticks)
    plt.title("MI Scores")
    
plt.figure(dpi=100, figsize=(12,12))
plot_mi_scores(mi_scores)

"""##Prediction
We will first use logistic regression as for baseline, then try to beat the baseline using random forest classifer

Our evaluation metrics will be accuracy, precision, recall and f1 score

Below we import all the required modules
"""

# import sys
# !cp ../input/rapids/rapids.0.15.0 /opt/conda/envs/rapids.tar.gz
# !cd /opt/conda/envs/ && tar -xzvf rapids.tar.gz > /dev/null
# sys.path = ["/opt/conda/envs/rapids/lib/python3.7/site-packages"] + sys.path
# sys.path = ["/opt/conda/envs/rapids/lib/python3.7"] + sys.path
# sys.path = ["/opt/conda/envs/rapids/lib"] + sys.path 
# !cp /opt/conda/envs/rapids/lib/libxgboost.so /opt/conda/lib/
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier as cuRfc
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

"""##Train logistic models
This method is to perform a repetative training process using logistic regression model, the purpose for this is to find the optimal number of features that can be used to find the best fitted model without adjusting much of the hyperparameters, hence the idea here is to go with Data-Centric training, basically the method takes number of top N features to be used for training the model and all the evaluation metrics are returned for evaluation purpose
"""

def train_logistic(data, top_n):
    top_n_features = mi_scores.sort_values(ascending=False).head(top_n).index.tolist()
    X = data[top_n_features]
    y = data['labels']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=True)
    
    lr = LogisticRegression(max_iter=10000)
    lr.fit(X_train, y_train)
    
    y_pred = lr.predict(X_test)
    
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    accuracy = accuracy_score(y_test, y_pred)
    
    return precision, recall, f1, accuracy

"""Here the loop will be starting from 20 as we will start training with top 20 features up to all 50 features to find optimal number of features needed for this problem"""

arr = []
for i in range(20,51,1):
    precision, recall, f1, accuracy = train_logistic(data, i)
    print("Performance for Logistic Model with Top {} features is precision : {}, recall : {}, f1 score : {}, accuracy : {}".format(i, precision, recall, f1, accuracy))
    arr.append([i, precision, recall, f1, accuracy])

df = pd.DataFrame(arr, columns=['num_of_features', 'precision', 'recall', 'f1_score', 'accuracy'])
df

"""## Visualize Logistic Regression Performance

As we can see, the model had ups and downs during the training as more number of features were added, as our target is to maximize all the metrics we have to find the number of features that gives us the best of all metrics, from the figure below, we can see that recall is constantly performing good but our model tend to have problem with precision score, hence to choose the best N of features, we have to pick the area where all the metrics are performing and based on the figure I would say its around 39 features
"""

sns.lineplot(x = 'num_of_features', y = 'precision', data = df, label = 'Precision Score')
sns.lineplot(x = 'num_of_features', y = 'recall', data = df, label = 'Recall Score')
sns.lineplot(x = 'num_of_features', y = 'f1_score', data = df, label = 'F1 Score')
sns.lineplot(x = 'num_of_features', y = 'accuracy', data = df, label = 'Accuracy Score')

"""##Training Random Forest Classifier on GPU

It is the same method as logistic reg, the only diff is that we are now using random forest classifier for training and trying to beat the logistic baseline
"""

def train_rfc(data, top_n):
    top_n_features = mi_scores.sort_values(ascending=False).head(top_n).index.tolist()
    X = data[top_n_features]
    y = data['labels']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=True)
    
    rfc = cuRfc(n_estimators=500, 
                criterion="gini",  
                max_depth=32, 
                max_features=1.0,
                n_jobs=128)
    
    rfc.fit(X_train, y_train)
    
    y_pred = rfc.predict(X_test)
    
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    accuracy = accuracy_score(y_test, y_pred)
    
    return precision, recall, f1, accuracy

arr = []
for i in range(20,51,1):
    precision, recall, f1, accuracy = train_rfc(data, i)
    print("Performance for RFC Model with Top {} features is precision : {}, recall : {}, f1 score : {}, accuracy : {}".format(i, precision, recall, f1, accuracy))
    arr.append([i, precision, recall, f1, accuracy])

df = pd.DataFrame(arr, columns=['num_of_features', 'precision', 'recall', 'f1_score', 'accuracy'])
df.head()

"""##Visualize Random Forest Performance

Our goal is to beat logistic regression baseline which is

* accuracy = 0.947162
* precision = 0.957468
* recall = 0.952287
* f1_score = 0.9515

So by visualizing the figure below, we can conclude that the best number of features for this model would be 32, one less than logistic regression, the reason why I chose 32 is because that is the number of features that allowed the model to perform the best across all the evaluation metric
"""

sns.lineplot(x='num_of_features', y='precision', data=df, label='Precision Score')
sns.lineplot(x='num_of_features', y='recall', data=df, label='Recall Score')
sns.lineplot(x='num_of_features', y='f1_score', data=df, label='F1 Score')
sns.lineplot(x='num_of_features', y='accuracy', data=df, label='Acc Score')

"""##Final Random Forest Mode

Lets train the final random forest model based on the optimal N number of features
"""

top_n_features = mi_scores.sort_values(ascending=False).head(32).index.tolist()
X = data[top_n_features]
y = data['labels']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=True)

rfc = cuRfc(n_estimators=500, 
            criterion="gini",  
            max_depth=32, 
            max_features=1.0,
            n_jobs=128)

rfc.fit(X_train, y_train)

y_pred = rfc.predict(X_test)

precision = precision_score(y_test, y_pred)
recall = recall_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred)
accuracy = accuracy_score(y_test, y_pred)

print("Performance for RFC Model with Top {} features is precision : {}, recall : {}, f1 score : {}, accuracy : {}".format(27, precision, recall, f1, accuracy))

"""##Performance

The model is now capable of predicting at up to 98% accuracy and also precision and recall, this shows the model has high confidence in predicting phishing or non-phishing site
"""

from sklearn.metrics import classification_report
print(classification_report(y_test, y_pred))