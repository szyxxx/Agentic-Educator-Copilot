# EduCopilot 🎓🤖

**EduCopilot** is a prototype Agentic AI system designed to streamline and enhance higher education curriculum management and the learning process. Powered by **LangGraph**, **FastAPI**, and **Next.js**, it serves as an intelligent assistant for lecturers to automate administrative tasks, validate curriculum standards, and generate actionable insights from student data.

---

## 🌟 Key Features

EduCopilot provides an end-to-end ecosystem for course management through specialized AI agents:

1. **RPS (Rencana Pembelajaran Semester) Builder**
   Automatically draft structured syllabuses and course plans based on course descriptions, Learning Outcomes (CPL/CPMK), and weekly topics.

2. **Compliance & Review Engine**
   Validates the generated or uploaded RPS against 24 strict national higher education standards (SN-Dikti) criteria to ensure administrative and academic compliance.

3. **Knowledge Base (RAG-based)**
   Upload reference materials (PDFs, docs). The system chunks, embeds, and stores them in ChromaDB to provide precise, context-aware AI responses using Retrieval-Augmented Generation (RAG).

4. **Quiz Generator & Editor**
   Generate contextual quizzes (Multiple Choice and Essay) based on RPS materials and Bloom's Taxonomy. Includes a built-in draft editor and dynamic CSV template generation for student submissions.

5. **AI Auto-Grading**
   Automatically grade student submissions (especially essays) based on predefined rubrics. It provides detailed, personalized feedback for each student.

6. **Remedial & Auto-Material Generation**
   Analyzes grading results to identify weak topics across the class and automatically generates targeted supplementary learning materials and remedial recommendations.

7. **Dashboard & Analytics**
   Get a bird's-eye view of course performance, student progress, quiz statistics, and RPS compliance ratios.

---

## 🏗️ Architecture

The system follows a modern decoupled architecture:

- **Frontend (Presentation Layer)**: Built with **Next.js**, **TypeScript**, and **Tailwind CSS**. Provides a responsive, dashboard-driven UI for lecturers.
- **Backend API Layer**: Powered by **FastAPI** (Python). Handles routing, business logic, and communication between the frontend and the AI layer.
- **Agentic AI Layer**: Uses **LangGraph** to orchestrate goal-driven agents (RPS Agent, Quiz Agent, Grading Agent, etc.) that perform multi-step reasoning. Uses Anthropic's LLM API.
- **Data & Tools Layer**: 
  - **Relational Data**: SQLite (`educopilot.db`) via SQLAlchemy ORM.
  - **Vector Database**: ChromaDB (for document embeddings).
  - **Search Tool**: Tavily Search integration for external information gathering.

---

## 🚀 Getting Started

### Prerequisites

- **Node.js** (v18+ recommended)
- **Python** (v3.10+ recommended)
- **uv** (ast Python package installer and resolver)
- **Git**

### 1. Clone the Repository

```bash
git clone https://github.com/szyxxx/Agentic-Educator-Copilot.git
cd Agentic-Educator-Copilot/app
```

### 2. Backend Setup

The backend relies on FastAPI and `uv` for dependency management.

```bash
cd backend

# Create a virtual environment and install dependencies
uv venv
uv pip install -r requirements.txt

# Configure Environment Variables
# Create a .env file based on the provided .env.example (if available)
# Make sure to add your ANTHROPIC_API_KEY
echo "ANTHROPIC_API_KEY=your_api_key_here" > .env

# Run the development server
uv run uvicorn app.main:app --reload
```
*The backend API will be available at `http://localhost:8000`*

### 3. Frontend Setup

The frontend is a Next.js application.

```bash
cd frontend

# Install dependencies
npm install

# Run the development server
npm run dev
```
*The frontend application will be available at `http://localhost:3000`*

---

## 🧠 AI Agents in EduCopilot

EduCopilot utilizes a Multi-Agent architecture where each agent has a specific domain of responsibility:

- **RPS Agent**: Formulates initial drafts of the semester learning plan.
- **RPS Review Agent**: Runs the compliance engine to find missing elements in the RPS.
- **Quiz Agent**: Uses RAG to generate relevant quiz questions and rubrics.
- **Grading Agent**: Evaluates student answers against rubrics and provides personalized feedback.
- **Remedial Agent**: Analyzes overall scores to recommend actions for underperforming students.
- **Auto Material Agent**: Searches or generates new supplementary materials based on class weaknesses.

---

## 🔒 Privacy & Limitations

- **Decision Support System**: EduCopilot is designed to *assist* lecturers, not replace them. All generated RPS, quizzes, and grades should be reviewed by a human before final publication.
- **Data Privacy**: Ensure that sensitive student data is anonymized before using the AI auto-grading features, as data is processed by external LLMs (Anthropic).

---

## 📝 License

This project was developed as a Final Project for the II5003 Applied Artificial Intelligence course. All rights reserved.
