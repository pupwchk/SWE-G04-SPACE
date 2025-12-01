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

## Group Members

| Name | Organization | Email |
|------|-------------|--------|
| Junho Uh | Department of Information Systems, Hanyang University | djwnsgh0248@hanyang.ac.kr |
| Yeonseong Shin | Department of Data Science, Hanyang University | dustjd2651@gmail.com |
| Dogyeom Kim | Department of Computer Science, Hanyang University | dogyeom74@hanyang.ac.kr |
| Donghyun Lim | Department of Computer Science, Hanyang University | limdongxian1207@gmail.com |

---

## Key Features

🔹 1) Wellness State Analysis from Wearable HRV

Real-time streaming of HRV (RMSSD, SDNN), heart rate, sleep data, and activity levels

Fatigue and stress levels estimated on a 0–4 scale

Time-slot-based pattern recognition of daily behavior

Support for anomaly detection in physiological signals

🔹 2) LLM-Powered Smart Appliance Control

GPT models generate natural-language policies such as
“dim the lights,” “set AC to 24°C,” or “increase humidity to 40%”

Hybrid rule-based + LLM reasoning control architecture

Natural-language policies are parsed into executable device-control commands

Appliance recommendations are logged and fed back into the user preference model

🔹 3) Context-Aware Multi-Modal Data Fusion

HARU combines multiple data sources to understand the user’s situation holistically:

HRV, heart rate, sleep, and activity (wearable)

Weather forecasts (KMA, nx/ny grid)

GPS-based indoor/outdoor classification

Time-of-day behavioral patterns

Detailed appliance usage logs

This enables a highly adaptive environment that goes beyond simple “if tired → dim lights” logic and considers contextual and environmental factors simultaneously.

🔹 4) Adaptive User Preference Learning

Learns user preferences based on historical device interactions

Predicts preferred appliance states for each fatigue level

Continuously refines lighting, temperature, and humidity settings over time

Improves accuracy and personalization as more data is collected

🔹 5) Natural Chat-Based Interaction (Sendbird)

Users can interact via chat:
“Turn on the AC,” “How’s my condition right now?”

HARU processes the message through GPT and replies naturally

Chat-based control integrates seamlessly with automated control flows

🔹 6) Weather-Aware Environmental Automation

Weather API integration with caching for performance

Contextual decisions based on outside temperature, humidity, and rainfall

Enables predictive behaviors such as pre-cooling before temperature rises

🔹 7) Modular FastAPI + Docker Backend

FastAPI RESTful architecture

PostgreSQL database with SQLAlchemy ORM

Docker Compose for environment reproducibility

NGINX reverse proxy for stable deployment

Modular service-layer design for maintainability

---

## Architecture

<img width="984" height="626" alt="Architecture" src="https://github.com/user-attachments/assets/683cfb21-6f4d-4ca1-a63b-5c5cc4cadb07" />





