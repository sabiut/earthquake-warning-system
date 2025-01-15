import numpy as np
import pandas as pd
import joblib
import tensorflow as tf
from django.utils import timezone
from django.db import transaction
from django.db import models
from .models import Earthquake
import reverse_geocoder as rg
import os

# Disable GPU since we're using CPU only
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

# Load the trained LSTM model and scalers
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
LSTM_MODEL_PATH = os.path.join(CURRENT_DIR, "earthquake_lstm_model.h5")
SCALER_PATH = os.path.join(CURRENT_DIR, "scalers.pkl")

# Load model and scalers
lstm_model = tf.keras.models.load_model(LSTM_MODEL_PATH, compile=False)
lstm_model.compile(optimizer="adam", loss="mse")
scalers = joblib.load(SCALER_PATH)

class EarthquakePredictionService:
    @classmethod
    def delete_existing_predictions(cls):
        """Delete all existing predictions with thorough cleanup."""
        try:
            with transaction.atomic():
                # Delete by status
                status_deleted = Earthquake.objects.filter(status="predicted").delete()[0]
                print(f"✅ Deleted {status_deleted} predictions by status")
                
                # Delete by usgs_id pattern
                id_deleted = Earthquake.objects.filter(usgs_id__startswith='predicted_').delete()[0]
                print(f"✅ Deleted {id_deleted} predictions by ID pattern")
                
                # Double check no predictions exist
                remaining_status = Earthquake.objects.filter(status="predicted").count()
                remaining_ids = Earthquake.objects.filter(usgs_id__startswith='predicted_').count()
                
                if remaining_status > 0 or remaining_ids > 0:
                    print(f"⚠️ Warning: Still found predictions: status={remaining_status}, ids={remaining_ids}")
                    return False
                    
                return True
        except Exception as e:
            print(f"❌ Error deleting predictions: {e}")
            return False

    @classmethod
    def fetch_past_earthquakes(cls):
        # Get past earthquakes, excluding predictions
        past_earthquakes = (Earthquake.objects
            .exclude(status="predicted")
            .exclude(usgs_id__startswith='predicted_')
            .order_by("-time")[:30]
        )
        
        if len(past_earthquakes) < 30:
            print("⚠️ Not enough past earthquake data for prediction. Need at least 30 records.")
            return []
        
        print(f"✅ Found {len(past_earthquakes)} past earthquakes")
        return [
            {
                "magnitude": quake.magnitude,
                "latitude": quake.latitude,
                "longitude": quake.longitude,
                "depth": quake.depth,
                "time": quake.time
            }
            for quake in reversed(past_earthquakes)
        ]

    @classmethod 
    def predict_future_earthquakes(cls):
        try:
            # First ensure all existing predictions are deleted
            if not cls.delete_existing_predictions():
                print("⚠️ Could not delete existing predictions. Aborting.")
                return

            past_earthquakes = cls.fetch_past_earthquakes()
            if not past_earthquakes:
                return

            # Convert to NumPy array with all 4 features
            input_data = np.array([
                [quake["magnitude"], quake["latitude"], quake["longitude"], quake["depth"]]
                for quake in reversed(past_earthquakes[:30])
            ])

            print(f"✅ Input Data Shape: {input_data.shape}")

            # Normalize input data - all 4 features
            input_data_scaled = np.array([
                scalers[col].transform(input_data[:, i].reshape(-1, 1)).flatten()
                for i, col in enumerate(["magnitude", "latitude", "longitude", "depth"])
            ]).T

            # Reshape for LSTM model
            X_input = np.array([input_data_scaled])
            print(f"✅ LSTM Model Input Shape: {X_input.shape}")

            # Predict next 30 days
            print("Starting 30-day predictions...")
            future_predictions = []
            
            for day in range(30):
                predicted_values = lstm_model.predict(X_input, verbose=0)[0]
                future_predictions.append(predicted_values)
                
                # Update input window based on prediction shape
                if len(predicted_values) == 4:
                    next_input = predicted_values
                else:
                    next_input = np.array([
                        predicted_values[0],
                        predicted_values[1],
                        predicted_values[2],
                        X_input[0, -1, 3]
                    ])
                
                X_input = np.append(X_input[:, 1:, :], [[next_input]], axis=1)

            # Convert predictions back to original scale
            future_predictions = np.array(future_predictions)
            
            predicted_magnitudes = scalers["magnitude"].inverse_transform(future_predictions[:, 0].reshape(-1, 1)).flatten()
            predicted_latitudes = scalers["latitude"].inverse_transform(future_predictions[:, 1].reshape(-1, 1)).flatten()
            predicted_longitudes = scalers["longitude"].inverse_transform(future_predictions[:, 2].reshape(-1, 1)).flatten()
            
            if future_predictions.shape[1] == 4:
                predicted_depths = scalers["depth"].inverse_transform(future_predictions[:, 3].reshape(-1, 1)).flatten()
            else:
                predicted_depths = np.full(30, input_data[-1, 3])
                print(f"Using default depth: {predicted_depths[0]}")
                
            # Store predictions
            future_dates = pd.date_range(start=timezone.now(), periods=30, freq="D")
            print("\nPreparing predictions for storage...")

            # Prepare all predictions first
            predictions_to_create = []
            for i, date in enumerate(future_dates):
                try:
                    location = rg.search((predicted_latitudes[i], predicted_longitudes[i]))[0]
                    place_name = f"{location['name']}, {location['cc']}"
                except Exception as e:
                    print(f"❌ Reverse geocoding failed for {predicted_latitudes[i]}, {predicted_longitudes[i]}: {e}")
                    place_name = "Unknown Location"

                predictions_to_create.append(
                    Earthquake(
                        usgs_id=f"predicted_{date.date()}",
                        magnitude=float(predicted_magnitudes[i]),
                        latitude=float(predicted_latitudes[i]),
                        longitude=float(predicted_longitudes[i]),
                        depth=float(predicted_depths[i]),
                        time=date,
                        place=place_name,
                        status="predicted"
                    )
                )

            # Store all predictions in a single transaction
            print(f"Creating {len(predictions_to_create)} predictions...")
            try:
                with transaction.atomic():
                    # Final check for existing predictions
                    remaining_predictions = (
                        Earthquake.objects.filter(status="predicted").count() +
                        Earthquake.objects.filter(usgs_id__startswith='predicted_').count()
                    )
                    
                    if remaining_predictions > 0:
                        raise Exception(f"Found {remaining_predictions} existing predictions before creation")
                        
                    Earthquake.objects.bulk_create(predictions_to_create)
                    print(f"✅ Successfully stored {len(predictions_to_create)} predictions")
                    
                    # Verify creation
                    final_count = Earthquake.objects.filter(status="predicted").count()
                    print(f"✅ Final prediction count: {final_count}")
                    
                    return final_count
            except Exception as e:
                print(f"❌ Failed to store predictions: {e}")
                return 0
            
        except Exception as e:
            print(f"❌ Error during prediction process: {e}")
            import traceback
            traceback.print_exc()
            return 0