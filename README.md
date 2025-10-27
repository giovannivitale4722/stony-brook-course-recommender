# CSE Course Recommender

A course recommendation system that uses Natural Language Processing (NLP) to help students find relevant Computer Science and Engineering (CSE) courses at Stony Brook University based on their interests and learning goals.

---

## Features

-   **Semantic Search**: Uses NLP to understand the semantic meaning of your queries, going beyond simple keyword matching.
-   **Relevance Ranking**: Ranks courses by relevance using cosine similarity scores.
-   **Web Interface**: A modern, responsive design for search and results display.
-   **Course Discovery**: Find courses that are conceptually similar to a selected course.
-   **Real-time Search**: Displays instant results as you type.

---

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

---

## Quick Start

### Prerequisites
-   Python 3.8 or higher
-   pip package manager

---

### Part 1: Data Collection (Scraper)

This is the standalone scraper used to collect course data. You **must** run this first to generate the CSV file that the main application needs.

1.  **Clone or download the project files.**

2.  **Install dependencies for the project**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the scraper script**:
    ```bash
    python3 scraper.py
    ```
    This will create a `stony_brook_all_course_data.csv` file, which is required for Part 2.

---

### Part 2: Running the Recommender App

Once you have the `stony_brook_all_course_data.csv` file from Part 1, you can run the main recommendation application.

1.  **Run the NLP processor**:
    This script reads the CSV, processes the text, and builds the recommendation model.
    ```bash
    python3 nlp_course_recommender.py
    ```

2.  **Start the web application**:
    ```bash
    python3 app.py
    ```

3.  **Open your browser** and navigate to `http://localhost:5001`.