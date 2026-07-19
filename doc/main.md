# Car Selector

## Goal

**AI-Powered Car Selection Assistant**

Inspired by: https://www.autohled.cz/

## Challenge Title

**DriveWise AI – Intelligent Car Selection Platform**

---

# Functional Requirements

## Core Features

### 1. Vehicle Database

Store information about cars such as:

- Brand
- Model
- Year
- Body type
- Number of seats
- Fuel type
- Engine power
- Consumption
- Trunk size
- Price
- AWD availability

### Example

```json
{
  "brand": "Skoda",
  "model": "Kodiaq",
  "seats": 7,
  "fuel_type": "Diesel",
  "body_type": "SUV",
  "trunk_capacity": 835
}
```

### 2. AI Requirement Interpreter

The chatbot should:

- Understand user needs
- Ask follow-up questions if required
- Transform the conversation into structured search parameters

### Example

**User:**

> I want a car to transport my whole family to our cottage.

**AI Output:**

```json
{
  "min_seats": 5,
  "body_type": "SUV",
  "large_trunk": true,
  "suitable_for_long_trips": true
}
```

### 3. Recommendation Engine

Based on extracted requirements:

- Filter vehicle database
- Rank matching vehicles
- Present recommendations with explanations

### Example

**Recommended:** Skoda Kodiaq

**Reason:**

- 7 seats
- Large luggage compartment
- Suitable for family trips
- Available with AWD

### 4. Vehicle Comparison

Users can compare:

- Multiple vehicles
- Technical parameters
- Cost-related metrics

### 5. User Interface

Provide:

- Chat window
- Vehicle recommendations
- Vehicle details page
- Comparison page

# Suggested Architecture

```text
Frontend
   |
   v
Flask / FastAPI Backend
   |
   +------------------+
   |                  |
   v                  v
AI Assistant     Car Database
   |
   v
Requirement Extraction
   |
   v
Recommendation Engine
```

# Recommended Technology Stack

## Backend
- Python 3.11+
- FastAPI or Flask

## Frontend
- React
- Vue
- HTMX
- Flask templates

## Database
- PostgreSQL
- SQLite (acceptable for prototype)

## AI
- Azure OpenAI
- OpenAI
- LangChain
- Hugging Face
- Ollama

## DevOps
- Docker
- GitHub Actions
- Unit Testing

# Bonus Features

## AI Features
- Voice interface
- Sentiment analysis
- Personalized recommendations
- Retrieval-Augmented Generation (RAG)
- Multi-language support

## Technical Features
- Containerized deployment
- CI/CD pipeline
- Authentication
- Analytics dashboard
- API documentation (Swagger/OpenAPI)

# Success Scenario

A user enters:

> "We are a family with three children and often travel to our cottage on gravel roads. We need enough luggage space and our budget is 35,000 EUR."

The AI assistant asks follow-up questions if needed, extracts requirements, searches the database, and recommends suitable vehicles.

Example recommendations:
- Skoda Kodiaq
- Volkswagen Tiguan Allspace
- Toyota RAV4
- Hyundai Santa Fe

# Expected Outcomes

This challenge validates:
- Teamwork
- AI integration
- Python development skills
- System design
- Practical business problem solving
