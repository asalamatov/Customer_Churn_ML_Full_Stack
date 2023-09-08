import streamlit as st
import pandas as pd
import pickle
import os
import json
from utils import transform_data
from matplotlib import pyplot as plt
import seaborn as sns

MEAN_EVE_MINUTES = 200.29 # from training model jyputer notebook

# set title and write output
st.title('Predict Churn 🚀')
st.write('Hit Predict to determine if your customer is likely to churn!')

# load schema
with open('app/schema.json') as f:
    schema = json.load(f)
# st.write(schema)

# set up column order for input and output
column_order_in = list(schema['column_info'].keys())[:-1]
column_order_out = list(schema['transformed_columns']['transformed_columns'])
# st.write(column_order_in)

# SIDEBAR SECTION
st.sidebar.info('Update these features to predict based on your customer!')

# Collect the input features
options = {}
for column, column_properties in schema['column_info'].items():
    if column == 'churn':
        pass
    # create numeric slider inputs
    elif column_properties['dtypes'] in ['int64', 'float64']:
        min_val, max_val = column_properties['values']
        data_type = column_properties['dtypes']

        feature_mean = (min_val + max_val) / 2
        if data_type == 'int64':
            feature_mean = int(feature_mean)
            min_val, max_val = int(min_val), int(max_val)
        elif data_type == 'float64':
            feature_mean = float(feature_mean)
            min_val, max_val = float(min_val), float(max_val)

        options[column] = st.sidebar.slider(column, min_val, max_val, value=feature_mean)


    # create categorical select boxes
    elif column_properties['dtypes'] == 'object':
        options[column] = st.sidebar.selectbox(column, sorted(column_properties['values']))

# load in model and encoder
model_path = os.path.join( 'models', 'experiment_1', 'xg.pkl') # models/experiment_1/xg.pkl
encoder_path = os.path.join('models', 'experiment_1', 'encoder.pkl')
with open(model_path, 'rb') as f:
    model = pickle.load(f)
with open(encoder_path, 'rb') as f:
    onehot = pickle.load(f)

# prediction = model.predict(scoring_sample)

# st.info(prediction)

# st.write(options)

if st.button('Predict', type='primary'):

    scoring_data = pd.Series(options).to_frame().T
    scoring_data = scoring_data[column_order_in]

    for column, column_properties in schema['column_info'].items():
        if column != 'churn':
            dtype = column_properties['dtypes']
            scoring_data[column] = scoring_data[column].astype(dtype)

    scoring_sample = transform_data(scoring_data, column_order_out, MEAN_EVE_MINUTES, onehot)
    prediction = model.predict(scoring_sample)
    st.header('Predicted Outcome')
    if prediction[0]==1:
        st.error('Churn')
    else:
        st.balloons()
        st.success("Not Churn")

# save historical data
try:
    historical = pd.Series(options).to_frame().T
    historical['prediction'] = prediction
    if os.path.isfile('historical_data.csv'):
        historical.to_csv('historical_data.csv', mode='a', header=False, index=False)
    else:
        historical.to_csv('historical_data.csv', header=True, index=False)
except Exception as e:
    pass


# show hist data
st.header('Historical Outcomes')
if os.path.isfile('historical_data.csv'):
    hist = pd.read_csv('historical_data.csv')
    st.dataframe(hist)
    fig, ax = plt.subplots()
    sns.countplot(x='prediction', data=hist, ax=ax).set_title("Historical Predictions")
    st.pyplot(fig)
else:
    st.write('No historical data')

if os.path.isfile('init_report.html'):
    html = open('init_report.html').read()
    st.components.v1.html(html, height=27800)