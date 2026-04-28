# AuraPass V2: Automated Biometric Access Control System
**Developed by:** Peters Elijah Temidayo  
**Institution:** Olabisi Onabanjo University (OOU)  
**Supervised by:** Dr. A.A. Okubanjo

## Project Overview
AuraPass V2 is a vision-based biometric access control mechanism designed to eliminate manual inefficiency, impersonation, and security breaches in examination halls. The system utilizes a **Co-Simulation** framework to bridge a high-level Python "Software Brain" with a virtualized hardware environment in Proteus VSM.

## Technical Stack
- **Software:** Python 3.12, OpenCV (Haar Cascade), and Google’s FaceNet architecture.
- **Hardware Simulation:** Proteus VSM hosting an Arduino Uno (ATmega328P).
- **Communication:** Virtual Serial Bridge via COM0COM (9600 Baud).

## System Architecture
The project is divided into three functional blocks:
1. **Software Environment:** Real-time facial data capture and FaceNet verification (128-byte embeddings).
2. **Communication Bridge:** A virtual serial pipeline transmitting authorization signals ('1' for access; '0' for denial).
3. **Control Logic:** An Arduino-based circuit that triggers a 12V DC Motor (Turnstile Actuator) and provides LCD/LED feedback.

## Mathematical Basis
The authentication engine employs **Cosine Similarity** to compare live embeddings against an authorized database for 1-Shot learning verification:

$$\text{similarity} = \frac{A \cdot B}{\|A\| \|B\|}$$

## 🚀 Key Features
- **Liveness Detection:** Essential for preventing "Presentation Attacks" (photos or video replays).
- **Automated Seating:** Implementated via Constraint Satisfaction for randomized, conflict-free seat allocation.
- **Power Isolation:** Logic-level protection using an SPDT Relay and 2N2222 Transistor to handle 12V actuation.