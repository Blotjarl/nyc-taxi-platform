# This is the script that Amazon SageMaker would run on a dedicated server.

import argparse
import os
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
import joblib
import numpy as np

if __name__ == '__main__':
    # SageMaker passes command-line arguments to the script.
    parser = argparse.ArgumentParser()
    parser.add_argument('--model-dir', type=str, default=os.environ.get('SM_MODEL_DIR'))
    parser.add_argument('--train', type=str, default=os.environ.get('SM_CHANNEL_TRAIN'))
    
    args, _ = parser.parse_known_args()
    
    # Read all Parquet files from the training data directory
    training_dir = args.train
    df_list = []
    for filename in os.listdir(training_dir):
        if filename.endswith(".parquet"):
            df = pd.read_parquet(os.path.join(training_dir, filename))
            df_list.append(df)
    
    df_ml = pd.concat(df_list)

    # --- This is the same model code from our notebook ---
    
    # Convert all columns to numeric
    for col in df_ml.columns:
        df_ml[col] = pd.to_numeric(df_ml[col], errors='coerce')
    df_ml.dropna(inplace=True)

    # Define features and target
    features = ['trip_distance', 'passenger_count', 'fare_amount', 'tip_amount', 'tolls_amount']
    target = 'trip_duration_minutes'

    X = df_ml[features]
    y = df_ml[target]

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Train the model
    model = LinearRegression()
    model.fit(X_train, y_train)

    # Evaluate and print metrics
    predictions = model.predict(X_test)
    mse = mean_squared_error(y_test, predictions)
    rmse = np.sqrt(mse)
    print(f"Root Mean Squared Error: {rmse}")

    # Save the trained model to the location SageMaker expects
    joblib.dump(model, os.path.join(args.model_dir, "model.joblib"))
