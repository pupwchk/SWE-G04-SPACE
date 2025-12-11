# HARU
**Home Adaptive Routine Understanding**

---

## 📄 Project Overview
[<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/33b8282c-ec06-42ec-a378-6ed671ab247e" />](https://drive.google.com/file/d/1IWtvyqR6cUTZ7u4qVTK3rLaoMkPGpOMv/view?usp=sharing))


HARU is an intelligent smart-home automation platform that integrates wearable health data with contextual information to create a personalized and adaptive living environment. The system continuously collects real-time biometric metrics from the Apple Watch—such as heart rate, heart rate variability (HRV), sleep patterns, and activity levels. Then, It estimates the user’s physiological and psychological state through HRV range. Unlike traditional rule-based smart-home systems, HARU leverages LLM-based reasoning to interpret the user’s condition and generate natural-language policies for controlling home appliances. These policies are then converted into structured commands to adjust lighting, temperature, humidity, and other devices automatically. By combining physiological signals with contextual data such as weather forecasts, GPS location, time-of-day patterns, and user preferences, HARU provides **context-aware, proactive home automation**. HARU aims to shift the paradigm from “A user controlling smart home” to “a home that understands the user and adapts itself accordingly.”

## [🎥 Video](https://youtu.be/I9-Sp5B4hgw)
---
## Architecture

<img width="1018" height="658" alt="archi_fin" src="https://github.com/user-attachments/assets/5d244110-1a52-4219-a70c-c7448b89a24c" />



---

## System Workflow

1. Apple Watch collects HRV, HR, sleep, and activity data.
2. Client app sends metrics to FastAPI backend.
3. Backend estimates fatigue level using HRV ranges.
4. Context data (weather, GPS, timeslot) is integrated.
5. LLM (GPT) generates natural-language appliance control policies.
6. Policies are parsed and executed (AC, lights, humidifier, etc.).
7. Actions are logged and used to update user preferences.
8. Sendbird chatbot allows conversation-based control and feedback.

---
## Key Features

### 1) Wellness State Analysis from Wearable HRV
- Real-time streaming of HRV(SDNN), heart rate, sleep data, and activity levels
- Fatigue and stress levels estimated on a 1–4 scale

### 2) LLM-Powered Smart Appliance Control
- Hybrid rule-based + LLM reasoning control architecture
- Natural-language policies are parsed into executable device-control commands
- Appliance recommendations are logged and fed back into the user preference table


### 3) Context-Aware Multi-Modal Data Fusion
HARU combines multiple data sources to understand the user’s situation holistically:
- HRV (wearable)
- Weather forecasts (KMA, nx/ny grid)
- GPS-based indoor/outdoor classification
- Time-of-day behavioral patterns
- Detailed appliance usage logs
This enables a highly adaptive environment that goes beyond simple “if tired → dim lights” logic and considers contextual and environmental factors simultaneously.

### 4) Adaptive User Preference Learning
- Learns user preferences based on historical device interactions
- Predicts preferred appliance states for each fatigue level
- Continuously refines lighting, temperature, and humidity settings over time
- Improves accuracy and personalization as more data is collected

---

## Tech Stack
| classification | stack |
|------|-----------|
| **Client (iOS / watchOS)** | SwiftUI, HealthKit, MapKit, WatchConnectivity, URLSession / async networking |
| **Backend** | Python 3.10, FastAPI (REST API), SQLAlchemy ORM, Pydantic, Docker + Docker Compose, NGINX reverse proxy, AWS EC2 (Ubuntu) |
| **Database** | Supabase (managed PostgreSQL), PostgreSQL 15 |
| **AI / Chat** | OpenAI GPT APIs, Sendbird Chat Platform |
| **External APIs** | KMA Weather API (Ultra-short-term forecast) |
| **DevOps / Tools** |Postman / Bruno (API testing), VSCode Remote SSH |

---

## 🧑🏻‍💻👩🏻‍💻 Group Members

| Name | Organization | Email |
|------|-------------|--------|
| Junho Uh | Department of Information Systems, Hanyang University | djwnsgh0248@hanyang.ac.kr |
| Yeonseong Shin | Department of Data Science, Hanyang University | dustjd2651@gmail.com |
| Donghyun Lim | Department of Computer Science, Hanyang University | limdongxian1207@gmail.com |
| Dogyeom Kim | Department of Computer Science, Hanyang University | dogyeom74@hanyang.ac.kr |
---

## License

Copyright (c) 2025 HARU
This project is licensed under the MIT License — see the [LICENSE](./LICENSE) file for details.











