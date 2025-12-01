# HARU
**Home Adaptive Routine Understanding**

---

## Project Overview

HARU (Home Adaptive Routine Understanding) is an intelligent smart-home automation platform that integrates wearable health data with contextual information to create a personalized and adaptive living environment.
The system continuously collects real-time biometric metrics from the Apple Watch—such as heart rate, heart rate variability (HRV), sleep patterns, and activity levels—and estimates the user’s physiological and psychological state through AI-driven analysis.

Unlike traditional rule-based smart-home systems, HARU leverages LLM-based reasoning (OpenAI GPT) to interpret the user’s condition and generate natural-language policies for controlling home appliances. These policies are then converted into structured commands to adjust lighting, temperature, humidity, and other devices automatically.

By combining physiological signals with contextual data such as weather forecasts, GPS location, time-of-day patterns, and user preferences, HARU provides context-aware, proactive home automation. Through Sendbird-powered chat interaction, users can also communicate naturally with the system for device control and health feedback.

HARU aims to shift the paradigm from “a user controlling a smart home” to “a home that understands the user and adapts itself accordingly.”

---

## Key Features

### 🔹 1) Wellness State Analysis from Wearable HRV

Real-time streaming of HRV (RMSSD, SDNN), heart rate, sleep data, and activity levels

Fatigue and stress levels estimated on a 0–4 scale

Time-slot-based pattern recognition of daily behavior

Support for anomaly detection in physiological signals

### 🔹 2) LLM-Powered Smart Appliance Control
GPT models generate natural-language policies such as “dim the lights,” “set AC to 24°C,” or “increase humidity to 40%”

Hybrid rule-based + LLM reasoning control architecture

Natural-language policies are parsed into executable device-control commands

Appliance recommendations are logged and fed back into the user preference model

### 🔹 3) Context-Aware Multi-Modal Data Fusion
HARU combines multiple data sources to understand the user’s situation holistically:

HRV, heart rate, sleep, and activity (wearable)

Weather forecasts (KMA, nx/ny grid)

GPS-based indoor/outdoor classification

Time-of-day behavioral patterns

Detailed appliance usage logs

This enables a highly adaptive environment that goes beyond simple “if tired → dim lights” logic and considers contextual and environmental factors simultaneously.

### 🔹 4) Adaptive User Preference Learning
Learns user preferences based on historical device interactions

Predicts preferred appliance states for each fatigue level

Continuously refines lighting, temperature, and humidity settings over time

Improves accuracy and personalization as more data is collected

### 🔹 5) Natural Chat-Based Interaction (Sendbird)
Users can interact via chat: “Turn on the AC,” “How’s my condition right now?”

HARU processes the message through GPT and replies naturally

Chat-based control integrates seamlessly with automated control flows

### 🔹 6) Weather-Aware Environmental Automation
Weather API integration with caching for performance

Contextual decisions based on outside temperature, humidity, and rainfall

Enables predictive behaviors such as pre-cooling before temperature rises

### 🔹 7) Modular FastAPI + Docker Backend
FastAPI RESTful architecture

PostgreSQL database with SQLAlchemy ORM

Docker Compose for environment reproducibility

NGINX reverse proxy for stable deployment

Modular service-layer design for maintainability

---

## Architecture

<img width="1112" height="680" alt="archi" src="https://github.com/user-attachments/assets/8ef7a965-4e6c-4752-84e3-689b64984b1a" />


The HARU system is designed as a modular, cloud-based smart-home automation platform that seamlessly connects wearable devices, backend services, external APIs, and LLM-powered chat interaction.

The architecture ensures scalability, low latency, and clear separation of concerns across each component.

### 1. User / Client Layer (iOS + watchOS)
The client application runs on iPhone and Apple Watch, built with SwiftUI and integrated with:
- HealthKit: Collects HRV, heart rate, sleep, and activity metrics
- MapKit: Provides location information and indoor/outdoor context
- Watch Connectivity: Syncs data between Apple Watch and iPhone in real time
  
This layer continuously streams physiological and contextual data to the backend and receives personalized appliance recommendations or automated control actions.

### 2. Backend Layer (FastAPI on AWS EC2)
The backend is built using FastAPI, containerized with Docker, and deployed behind an NGINX reverse proxy on AWS EC2.

Key responsibilities:
- Processing HRV and biometric submissions
- Predicting fatigue/stress levels
- Managing smart appliance rules and user preferences
- Communicating with external APIs (weather, LG ThinQ)
- Handling chat-webhook requests from Sendbird
- Providing RESTful endpoints to mobile clients
The backend follows a modular service-oriented architecture using SQLAlchemy ORM and clean service layers.

### 3. Database Layer (Supabase + PostgreSQL)
Supabase hosts a managed PostgreSQL instance used for:
- User authentication and profile
- HRV and health logs
- TimeSlot data
- Weather caching
- Appliance control rules and status
- Command logs and user preference learning
- All tables and relationships are managed through SQLAlchemy and Supabase’s PostgreSQL driver.

### 4. External APIs
HARU integrates several external systems to enrich user context and support real-world device automation:
- KMA (Korea Meteorological Agency): Retrieves short-term weather forecasts (nx/ny grid)
- LG ThinQ API: Enables control and monitoring of actual home appliances (AC, humidifier, washer, etc.)
  
These APIs allow the system to make context-aware predictions and control real smart devices.

### 5. Chat Server (Sendbird + OpenAI)
Sendbird handles all messaging between the user and HARU’s backend.

Workflow:
- User sends a message in the chat app
- Sendbird triggers a webhook to the FastAPI backend
- Backend forwards the message + user context to OpenAI GPT
- GPT generates a natural-language response and potential appliance action
- Backend executes the command (if applicable) and returns a message to Sendbird
- User receives the final response in the chat
- This integration enables a natural conversational interface that can trigger real device actions.

---

## Tech Stack
### Client (iOS / watchOS)
- SwiftUI
- HealthKit
- MapKit
- WatchConnectivity
- URLSession / async networking

### Backend
- Python 3.10
- FastAPI (REST API)
- SQLAlchemy ORM
- Pydantic
- Docker + Docker Compose
- NGINX reverse proxy
- AWS EC2 (Ubuntu)

### Database
- Supabase (managed PostgreSQL)
- PostgreSQL 15
- PostGIS (optional future extension)

### AI / Chat
- OpenAI GPT APIs
- Sendbird Chat Platform

### External APIs
- KMA Weather API (Ultra-short-term forecast)

### DevOps / Tools
- GitHub Actions (optional future CI)
- Postman / Bruno (API testing)
- VSCode Remote SSH

---

## Database Structure
```
User
 ├── UserPhone (1:1)
 ├── UserDevice (1:1)
 ├── HRV_logs (1:N)
 ├── HealthHourly (1:N)
 ├── TimeSlot (1:N)
 ├── SleepSession (1:N)
 ├── WorkoutSession (1:N)
 ├── ApplianceConditionRule (1:N)
 ├── UserAppliancePreferences (1:N)
 ├── ApplianceStatus (1:N)
 └── ApplianceCommandLog (1:N)

TimeSlot
 ├── WeatherObservation (Mapped by nx, ny, timestamp)

WeatherObservation
 └── Cached for all time-based logic
```

---

## Installation & Run Guide
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

---
## Demo Section

---
## Group Members

| Name | Organization | Email |
|------|-------------|--------|
| Dogyeom Kim | Department of Computer Science, Hanyang University | dogyeom74@hanyang.ac.kr |
| Yeonseong Shin | Department of Data Science, Hanyang University | dustjd2651@gmail.com |
| Junho Uh | Department of Information Systems, Hanyang University | djwnsgh0248@hanyang.ac.kr |
| Donghyun Lim | Department of Computer Science, Hanyang University | limdongxian1207@gmail.com |


