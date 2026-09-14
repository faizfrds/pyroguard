"""Train and Export PyroGuard AI Wildfire Risk ONNX Model.

Builds and exports a PyTorch neural network that takes 30-day radar/optical features,
weather forecasts, and peatland indicators to predict:
1. Wildfire Vulnerability Index (WVI: 0.0 - 1.0)
2. 14-Day Forward Risk Trajectory Curve
"""

import os
import torch
import torch.nn as nn
import numpy as np


class TropicalWildfireRiskModel(nn.Module):
    def __init__(self, input_dim: int = 45, trajectory_days: int = 14):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(64, 32),
            nn.ReLU()
        )
        
        # WVI Head (single risk index 0.0 - 1.0)
        self.wvi_head = nn.Sequential(
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, 1),
            nn.Sigmoid()
        )
        
        # 14-day forward trajectory head
        self.trajectory_head = nn.Sequential(
            nn.Linear(32, 24),
            nn.ReLU(),
            nn.Linear(24, trajectory_days),
            nn.Sigmoid()
        )

    def forward(self, x: torch.Tensor):
        features = self.encoder(x)
        wvi = self.wvi_head(features)
        trajectory = self.trajectory_head(features)
        return wvi, trajectory


def generate_synthetic_training_data(n_samples: int = 2000, input_dim: int = 45):
    """Generates synthetic training dataset mimicking Indonesian fire seasons."""
    X = np.random.randn(n_samples, input_dim).astype(np.float32)
    
    # Feature indices alignment:
    # 0: ndwi (0.2 to 0.6)
    # 1: sar_vv_drop (0 to 4 dB)
    # 2: lst_anomaly (-1 to +6 C)
    # 3: rain_14d (0 to 120 mm)
    # 4: dry_days (0 to 20)
    # 5: is_peatland (0 or 1)
    # 6: enso_oni (-0.5 to 2.0)
    X[:, 0] = np.random.uniform(0.15, 0.65, n_samples)
    X[:, 1] = np.random.uniform(0.0, 4.5, n_samples)
    X[:, 2] = np.random.uniform(-1.0, 6.0, n_samples)
    X[:, 3] = np.random.exponential(20.0, n_samples)
    X[:, 4] = np.random.uniform(0, 20, n_samples)
    X[:, 5] = np.random.choice([0.0, 1.0], size=n_samples, p=[0.3, 0.7])
    X[:, 6] = np.random.uniform(-0.5, 2.2, n_samples)
    
    # Calibrated risk formula for target ground truth
    # Higher risk when SAR VV drop is high (dry peat), dry days > 7, El Niño is positive, NDWI is low
    sar_factor = np.clip(X[:, 1] / 3.5, 0, 1)
    dry_factor = np.clip(X[:, 4] / 14.0, 0, 1)
    enso_factor = np.clip((X[:, 6] + 0.5) / 2.5, 0, 1)
    ndwi_factor = np.clip((0.6 - X[:, 0]) / 0.4, 0, 1)
    peat_factor = X[:, 5] * 0.2
    
    raw_risk = (
        0.35 * sar_factor +
        0.25 * dry_factor +
        0.15 * enso_factor +
        0.15 * ndwi_factor +
        peat_factor
    )
    y_wvi = np.clip(raw_risk + np.random.normal(0, 0.03, n_samples), 0.05, 0.98).astype(np.float32)[:, None]
    
    # Generate monotonic trajectory for drying periods
    y_traj = np.zeros((n_samples, 14), dtype=np.float32)
    for i in range(14):
        trend = (i / 14.0) * 0.12 if np.random.rand() > 0.3 else -(i / 14.0) * 0.05
        y_traj[:, i] = np.clip(y_wvi[:, 0] + trend + np.random.normal(0, 0.02, n_samples), 0.02, 0.98)
        
    return torch.tensor(X), torch.tensor(y_wvi), torch.tensor(y_traj)


def train_and_export():
    os.makedirs("backend/models", exist_ok=True)
    model_path = "backend/models/wildfire_risk_v1.onnx"
    
    model = TropicalWildfireRiskModel()
    model.train()
    
    X_train, y_wvi_train, y_traj_train = generate_synthetic_training_data(3000)
    
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.005, weight_decay=1e-4)
    loss_fn_mse = nn.MSELoss()
    
    print("Training Tropical Wildfire Risk Neural Network...")
    dataset = torch.utils.data.TensorDataset(X_train, y_wvi_train, y_traj_train)
    loader = torch.utils.data.DataLoader(dataset, batch_size=64, shuffle=True)
    
    for epoch in range(15):
        epoch_loss = 0.0
        for batch_x, batch_wvi, batch_traj in loader:
            optimizer.zero_grad()
            pred_wvi, pred_traj = model(batch_x)
            loss = loss_fn_mse(pred_wvi, batch_wvi) * 1.5 + loss_fn_mse(pred_traj, batch_traj)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
            
    print(f"Training complete. Final epoch loss: {epoch_loss / len(loader):.4f}")
    
    # Export to ONNX
    model.eval()
    dummy_input = torch.randn(1, 45, dtype=torch.float32)
    
    torch.onnx.export(
        model,
        dummy_input,
        model_path,
        export_params=True,
        opset_version=14,
        do_constant_folding=True,
        input_names=["input_features"],
        output_names=["wildfire_vulnerability_index", "trajectory_14d"],
        dynamic_axes={
            "input_features": {0: "batch_size"},
            "wildfire_vulnerability_index": {0: "batch_size"},
            "trajectory_14d": {0: "batch_size"}
        }
    )
    print(f"Successfully exported ONNX model to: {model_path}")


if __name__ == "__main__":
    train_and_export()

