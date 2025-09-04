# CSE Course Recommender

A course recommendation system that uses Natural Language Processing (NLP) to help students find relevant Computer Science and Engineering (CSE) courses at Stony Brook University based on their interests and learning goals.

## Features

-   **Semantic Search**: Uses NLP to understand the semantic meaning of your queries, going beyond simple keyword matching.
-   **Relevance Ranking**: Ranks courses by relevance using cosine similarity scores.
-   **Web Interface**: A modern, responsive design for search and results display.
-   **Course Discovery**: Find courses that are conceptually similar to a selected course.
-   **Real-time Search**: Displays instant results as you type.

## Architecture

### Data Collection
-   **Web Scraping**: Extracts course information (code, title, credits, description) from Stony Brook University's course catalog.
-   **Data Cleaning**: Normalizes and prepares text for NLP processing.
-   **CSV Storage**: Maintains a clean dataset of all CSE courses.

### NLP Processing
-   **TF-IDF Vectorization**: Converts course descriptions into high-dimensional vectors using Term Frequency-Inverse Document Frequency.
-   **Semantic Understanding**: The system understands word relationships and context through n-gram analysis.
-   **Vector Storage**: Saves vectors for fast retrieval and comparison.

### Search
-   **Query Processing**: Converts user queries into the same vector space as the course descriptions.
-   **Cosine Similarity**: Calculates the angle between query and course vectors to measure semantic similarity.
-   **Ranking**: Returns courses ordered by their relevance score.

## Quick Start

### Prerequisites
-   Python 3.8 or higher
-   pip package manager

### Installation

1.  **Clone or download the project files.**
2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run the NLP recommender demo**:
    ```bash
    python3 nlp_course_recommender.py
    ```
4.  **Start the web application**:
    ```bash
    python3 app.py
    ```
5.  **Open your browser** and navigate to `http://localhost:5001`.
