\# Car Selector



\## Goal



\*\*AI-Powered Car Selection Assistant\*\*



Inspired by: https://www.autohled.cz/



\## Challenge Title



\*\*DriveWise AI – Intelligent Car Selection Platform\*\*



\---



\# Functional Requirements



\## Core Features



\### 1. Vehicle Database



Store information about cars such as:



\- Brand

\- Model

\- Year

\- Body type

\- Number of seats

\- Fuel type

\- Engine power

\- Consumption

\- Trunk size

\- Price

\- AWD availability



\### Example



```json

{

&#x20; "brand": "Skoda",

&#x20; "model": "Kodiaq",

&#x20; "seats": 7,

&#x20; "fuel\_type": "Diesel",

&#x20; "body\_type": "SUV",

&#x20; "trunk\_capacity": 835

}



2\. AI Requirement Interpreter



The chatbot should:



Understand user needs

Ask follow-up questions if required

Transform the conversation into structured search parameters

Example



User:



I want a car to transport my whole family to our cottage.



AI Output:



{

&#x20; "min\_seats": 5,

&#x20; "body\_type": "SUV",

&#x20; "large\_trunk": true,

&#x20; "suitable\_for\_long\_trips": true

}



3\. Recommendation Engine



Based on extracted requirements:



Filter vehicle database

Rank matching vehicles

Present recommendations with explanations

Example



Recommended: Skoda Kodiaq



Reason:



7 seats

Large luggage compartment

Suitable for family trips

Available with AWD

4\. Vehicle Comparison



Users can compare:



Multiple vehicles

Technical parameters

Cost-related metrics

5\. User Interface



Provide:



Chat window

Vehicle recommendations

Vehicle details page

Comparison page

Suggested Architecture

Frontend

&#x20;  |

&#x20;  v

Flask / FastAPI Backend

&#x20;  |

&#x20;  +------------------+

&#x20;  |                  |

&#x20;  v                  v

AI Assistant     Car Database

&#x20;  |

&#x20;  v

Requirement Extraction

&#x20;  |

&#x20;  v

Recommendation Engine



Recommended Technology Stack

Backend

Python 3.11+

FastAPI or Flask

Frontend

React

Vue

HTMX

Flask templates

Database

PostgreSQL

SQLite (acceptable for prototype)

AI

Azure OpenAI

OpenAI

LangChain

Hugging Face

Ollama

DevOps

Docker

GitHub Actions

Unit Testing

Bonus Features



Teams may earn bonus points by implementing:



AI Features

Voice interface

Sentiment analysis

Personalized recommendations

Retrieval-Augmented Generation (RAG)

Multi-language support

Technical Features

Containerized deployment

CI/CD pipeline

Authentication

Analytics dashboard

API documentation (Swagger/OpenAPI)

Success Scenario



A user enters:



"We are a family with three children and often travel to our cottage on gravel roads. We need enough luggage space and our budget is 35,000 EUR."



The AI assistant:



Asks follow-up questions if needed.

Extracts requirements.

Searches the database.

Recommends suitable vehicles.



Example recommendations:



Skoda Kodiaq

Volkswagen Tiguan Allspace

Toyota RAV4

Hyundai Santa Fe



Each recommendation includes explanations showing how the vehicle matches the stated needs.



Expected Outcomes



This challenge validates:



Teamwork

AI integration

Python development skills

System design

Practical business problem solving



