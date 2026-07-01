# Car Selector – Architecture Overview

## Purpose

The Car Selector application helps users find suitable vehicles based on their requirements, preferences, and budget. Users interact through a modern web interface, while the backend combines AI-powered requirement analysis with vehicle data stored in a centralized database.

---

# High-Level Architecture

```text
+--------------------------------------------------+
|                     FRONTEND                     |
+--------------------------------------------------+
|                                                  |
|  React / Vue.js                                  |
|  - Car selection wizard                          |
|  - Chat interface                                |
|  - Search & filtering                            |
|  - Recommendation display                        |
|                                                  |
+------------------------|-------------------------+
                         |
                         | REST API / HTTPS
                         v
+--------------------------------------------------+
|                      BACKEND                     |
+--------------------------------------------------+
|                                                  |
|  FastAPI (Python)                                |
|  - API Endpoints                                 |
|  - Request Processing                            |
|  - Business Logic                                |
|  - Recommendation Engine                         |
|                                                  |
|  +--------------------------------------------+  |
|  | Claude AI API                              |  |
|  | - Requirement extraction                   |  |
|  | - Preference analysis                      |  |
|  | - Recommendation explanation               |  |
|  +--------------------------------------------+  |
|                                                  |
|  +--------------------------------------------+  |
|  | PostgreSQL Database                        |  |
|  | - Vehicle catalog                          |  |
|  | - Technical specifications                 |  |
|  | - Pricing data                             |  |
|  | - Vehicle features                         |  |
|  +--------------------------------------------+  |
|                                                  |
|  +--------------------------------------------+  |
|  | Web Scraping Service                       |  |
|  | - Manufacturer websites                    |  |
|  | - Dealer portals                           |  |
|  | - Vehicle specifications                   |  |
|  | - Price lists                              |  |
|  +--------------------------------------------+  |
|                                                  |
+--------------------------------------------------+
```

---

# Frontend Layer

## Technologies

- React or Vue.js
- TypeScript
- Axios
- Material UI / Vuetify

## Responsibilities

### User Interface
- Vehicle recommendation wizard
- Search and filtering options
- User preference configuration
- Recommendation results visualization

### AI Chat Interface
- Natural language conversation
- Requirement collection
- Follow-up questions
- Recommendation explanations

### API Communication
- Send user requirements to backend
- Retrieve recommendations
- Display vehicle details and pricing

---

# Backend Layer

## Technologies

- Python
- FastAPI
- SQLAlchemy
- Pydantic

## Responsibilities

### API Management
- Expose REST endpoints
- Handle request validation
- Manage application workflows

### Recommendation Engine

Processes:

1. Receive user requirements
2. Analyze preferences
3. Retrieve matching vehicles
4. Calculate ranking score
5. Return optimized recommendations

Examples of criteria:

- Budget
- Vehicle type
- Brand preference
- Fuel type
- Family size
- Driving style

---

# AI Integration

## Claude API

The Claude AI service is responsible for understanding natural language requests and transforming them into structured requirements.

### Example

User Input:

> "I need a reliable family SUV under €40,000 with low fuel consumption."

Claude extracts:

```json
{
  "vehicle_type": "SUV",
  "budget": 40000,
  "priority": "reliability",
  "fuel_efficiency": true,
  "usage": "family"
}
```

### AI Responsibilities

- Requirement extraction
- Intent detection
- User preference analysis
- Recommendation explanation generation

---

# Data Layer

## PostgreSQL Database

### Main Tables

#### Cars

```text
cars
├── id
├── brand
├── model
├── category
├── year
└── description
```

#### Specifications

```text
car_specs
├── car_id
├── fuel_type
├── horsepower
├── transmission
├── consumption
└── drivetrain
```

#### Pricing

```text
car_prices
├── car_id
├── market
├── price
├── currency
└── last_updated
```

#### Features

```text
car_features
├── car_id
├── feature_name
└── feature_value
```

---

# Data Collection Layer

## Web Scraping Service

A dedicated Python service collects vehicle information from external sources.

### Sources

- Manufacturer websites
- Dealer websites
- Vehicle marketplaces
- Public price lists

### Collected Data

- Vehicle models
- Technical specifications
- Features
- Pricing information
- Vehicle descriptions

### Recommended Tools

- BeautifulSoup
- Scrapy
- Playwright

### Workflow

```text
Data Sources
      |
      v
Web Scraper
      |
      v
Data Cleaning
      |
      v
PostgreSQL
      |
      v
Recommendation Engine
```

---

# End-to-End Flow

```text
User
  |
  v
React / Vue Frontend
  |
  v
FastAPI Backend
  |
  +------------------+
  |                  |
  v                  v
Claude API      PostgreSQL
  |                  ^
  |                  |
  +-------> Recommendation Engine
                     ^
                     |
               Web Scraper
```

---

# Benefits

- Clear separation between frontend and backend
- Scalable microservice-ready architecture
- AI-assisted requirement gathering
- Automated vehicle data collection
- Centralized PostgreSQL data storage
- Modern frontend framework support (React/Vue)
- Easy deployment to Azure, AWS, or Kubernetes