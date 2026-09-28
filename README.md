# Smart Zone-Based Classroom Automation

AI/ML + computer vision + IoT system for zone-aware classroom energy management.

## Planned pipeline

Camera → YOLO person detection → configurable zones → occupancy data → database → EDA/feature engineering →
Random Forest energy prediction + Isolation Forest anomaly detection → smart control → Arduino/relays → dashboard.

## Development stages

1. Project setup and Git/GitHub
2. Dummy dataset generation
3. EDA
4. Feature engineering
5. Random Forest energy model
6. Isolation Forest anomaly model
7. Zone drawing/calibration
8. YOLO integration
9. Database integration
10. Arduino/relay integration
11. Flask API and dashboard
12. Full integration

## Note
The initial ML work uses demo/synthetic data. The same schema will later accept real classroom logs.
