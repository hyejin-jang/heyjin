"""
AI Power Model - Linear Regression
Trains a model to predict SSD power consumption based on workload characteristics
"""
import json
import numpy as np
from typing import Dict, List, Tuple
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import pickle


class PowerModel:
    """
    Linear regression model for SSD power prediction
    
    Model: Power = a*Read + b*Write + c*WAF + d
    """
    
    def __init__(self):
        self.model = LinearRegression()
        self.coefficients = {}
        self.metrics = {}
        self.is_trained = False
    
    def prepare_data(self, raw_data: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Convert raw data to training format
        
        Args:
            raw_data: List of measurement dictionaries
            
        Returns:
            (X, y) where X = features, y = target (power)
        """
        X = []
        y = []
        
        for point in raw_data:
            features = [
                point["read_mbps"],
                point["write_mbps"],
                point["waf"]
            ]
            X.append(features)
            y.append(point["power_watts"])
        
        return np.array(X), np.array(y)
    
    def train(self, training_data: List[Dict], test_size: float = 0.2) -> Dict:
        """
        Train the power prediction model
        
        Args:
            training_data: List of measurement dictionaries
            test_size: Fraction of data to use for testing
            
        Returns:
            Training metrics
        """
        print("\n🤖 Training AI Power Model...")
        print("="*60)
        
        # Prepare data
        X, y = self.prepare_data(training_data)
        
        # Split train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )
        
        print(f"Training samples: {len(X_train)}, Test samples: {len(X_test)}")
        
        # Train model
        self.model.fit(X_train, y_train)
        
        # Extract coefficients
        self.coefficients = {
            "read_coefficient": round(self.model.coef_[0], 6),
            "write_coefficient": round(self.model.coef_[1], 6),
            "waf_coefficient": round(self.model.coef_[2], 6),
            "intercept": round(self.model.intercept_, 6)
        }
        
        # Evaluate
        y_pred_train = self.model.predict(X_train)
        y_pred_test = self.model.predict(X_test)
        
        self.metrics = {
            "train_mse": round(mean_squared_error(y_train, y_pred_train), 4),
            "test_mse": round(mean_squared_error(y_test, y_pred_test), 4),
            "train_r2": round(r2_score(y_train, y_pred_train), 4),
            "test_r2": round(r2_score(y_test, y_pred_test), 4)
        }
        
        self.is_trained = True
        
        # Print results
        print("\n📊 Model Coefficients:")
        print(f"   Power = {self.coefficients['read_coefficient']:.6f} * Read_MB/s")
        print(f"         + {self.coefficients['write_coefficient']:.6f} * Write_MB/s")
        print(f"         + {self.coefficients['waf_coefficient']:.6f} * WAF")
        print(f"         + {self.coefficients['intercept']:.6f}")
        
        print(f"\n📈 Model Performance:")
        print(f"   Train R²: {self.metrics['train_r2']:.4f}")
        print(f"   Test R²:  {self.metrics['test_r2']:.4f}")
        print(f"   Test MSE: {self.metrics['test_mse']:.4f}")
        print("="*60 + "\n")
        
        return self.metrics
    
    def predict(self, read_mbps: float, write_mbps: float, waf: float) -> float:
        """
        Predict power consumption for given workload
        
        Args:
            read_mbps: Read throughput (MB/s)
            write_mbps: Write throughput (MB/s)
            waf: Write Amplification Factor
            
        Returns:
            Predicted power (watts)
        """
        if not self.is_trained:
            raise ValueError("Model not trained yet. Call train() first.")
        
        X = np.array([[read_mbps, write_mbps, waf]])
        return self.model.predict(X)[0]
    
    def save_model(self, filename: str = "power_model.pkl") -> None:
        """Save trained model to file"""
        if not self.is_trained:
            raise ValueError("Cannot save untrained model")
        
        model_data = {
            "model": self.model,
            "coefficients": self.coefficients,
            "metrics": self.metrics
        }
        
        with open(filename, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"💾 Model saved to: {filename}")
    
    def load_model(self, filename: str = "power_model.pkl") -> None:
        """Load trained model from file"""
        with open(filename, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data["model"]
        self.coefficients = model_data["coefficients"]
        self.metrics = model_data["metrics"]
        self.is_trained = True
        
        print(f"📂 Model loaded from: {filename}")


if __name__ == "__main__":
    # Load training data
    with open("training_data.json", 'r') as f:
        data = json.load(f)
    
    # Train model
    model = PowerModel()
    model.train(data)
    
    # Save model
    model.save_model()
    
    # Example prediction
    print("🔮 Example Prediction:")
    read = 3000  # MB/s
    write = 1500  # MB/s
    waf = 2.0
    
    predicted_power = model.predict(read, write, waf)
    print(f"   Workload: {read} MB/s read, {write} MB/s write, WAF={waf}")
    print(f"   Predicted Power: {predicted_power:.2f}W")
