# HARU
**Home Adaptive Routine Understanding**

---

## 📄 Project Overview

HARU is an intelligent smart-home automation platform that integrates wearable health data with contextual information to create a personalized and adaptive living environment. The system continuously collects real-time biometric metrics from the Apple Watch—such as heart rate, heart rate variability (HRV), sleep patterns, and activity levels. Then, It estimates the user’s physiological and psychological state through HRV range. Unlike traditional rule-based smart-home systems, HARU leverages LLM-based reasoning to interpret the user’s condition and generate natural-language policies for controlling home appliances. These policies are then converted into structured commands to adjust lighting, temperature, humidity, and other devices automatically. By combining physiological signals with contextual data such as weather forecasts, GPS location, time-of-day patterns, and user preferences, HARU provides **context-aware, proactive home automation**. HARU aims to shift the paradigm from “A user controlling smart home” to “a home that understands the user and adapts itself accordingly.”

---
## Architecture

<img width="1112" height="680" alt="archi" src="https://github.com/user-attachments/assets/8ef7a965-4e6c-4752-84e3-689b64984b1a" />

HARU is designed as a modular, cloud-based smart-home automation platform that seamlessly connects wearable devices, backend services, external APIs, and LLM-powered chat interaction. The architecture ensures scalability, low latency, and clear separation of concerns across each component.

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
| **Database** | Supabase (managed PostgreSQL), PostgreSQL 15, PostGIS (optional future extension) |
| **AI / Chat** | OpenAI GPT APIs, Sendbird Chat Platform |
| **External APIs** | KMA Weather API (Ultra-short-term forecast) |
| **DevOps / Tools** | GitHub Actions (optional future CI), Postman / Bruno (API testing), VSCode Remote SSH |
---
---
## 🎥 Video

---

## 🗂️ Installation & Run Guide
This guide explains how to run the HARU backend system using Docker, either locally or on an AWS EC2 instance.

The backend includes FastAPI, PostgreSQL, NGINX, Sendbird webhooks, and integration with external APIs such as OpenAI and KMA.

### Prerequisites
Required Tools
- Docker (24.x or higher recommended)
- Docker Compose
- Git
- Python 3.11 (pyproject.toml run at 3.11, docker server set on 3.10)
- (Optional) Supabase CLI

Required API Keys
- OpenAI API Key ->	LLM reasoning & decision-making
- Sendbird App ID / API Token -> Chat server & webhook integration
- KMA Weather API Key	-> Ultra-short-term weather forecast
- Supabase Project URL / Service Role Key	-> Managed PostgreSQL database

### Clone the Repository
```
git clone https://github.com/pupwchk/SWE-G04-SPACE.git
cd SWE-G04-SPACE
```

### Create a .env File
Create an .env file in the project root and fill it with your credentials:

POSTGRES_USER=postgres

POSTGRES_PASSWORD=yourpassword

POSTGRES_DB=haru

And set Sendbird, OpenAI, KMA API Key on .env File.

### Run the System With Docker
HARU uses the following Dockerized components:
- FastAPI backend
- PostgreSQL
- NGINX reverse proxy
- Alembic auto-migrations

**Default exposed ports:**

FastAPI	8000

NGINX	80

PostgreSQL 5432

**Start System:**

docker-compose up --build

**Run in detached mode:**

docker-compose up -d

**View Running Containers:**

docker ps

**View All Containers(including stopped):**

docker ps -a

**Stop Containers:**

docker-compose down


## 🧑🏻‍💻👩🏻‍💻 Group Members

| Name | Organization | Email |
|------|-------------|--------|
| Dogyeom Kim | Department of Computer Science, Hanyang University | dogyeom74@hanyang.ac.kr |
| Yeonseong Shin | Department of Data Science, Hanyang University | dustjd2651@gmail.com |
| Junho Uh | Department of Information Systems, Hanyang University | djwnsgh0248@hanyang.ac.kr |
| Donghyun Lim | Department of Computer Science, Hanyang University | limdongxian1207@gmail.com |
---


