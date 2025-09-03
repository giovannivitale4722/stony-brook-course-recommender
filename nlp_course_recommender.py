import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import os
from typing import List, Dict, Tuple
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NLPCourseRecommender:
    """
    NLP-powered course recommendation system using TF-IDF vectorization
    """
    
    def __init__(self):
        """
        Initialize the recommender with TF-IDF vectorization
        """
        self.vectorizer = None
        self.courses_df = None
        self.course_vectors = None
        self.vectors_file = 'course_vectors.pkl'
        
        logger.info("Initializing NLP Course Recommender with TF-IDF")
        
    def load_courses(self, csv_file: str = 'cse_courses_simple.csv'):
        """
        Load course data from CSV file
        
        Args:
            csv_file: Path to the CSV file containing course information
        """
        try:
            self.courses_df = pd.read_csv(csv_file)
            logger.info(f"Loaded {len(self.courses_df)} courses from {csv_file}")
            
            # Clean and prepare course descriptions
            self._prepare_course_data()
            
        except Exception as e:
            logger.error(f"Error loading courses: {e}")
            raise
    
    def _prepare_course_data(self):
        """
        Prepare and clean course data for vectorization
        """
        # Combine code, title, and description for better semantic understanding
        self.courses_df['full_text'] = (
            self.courses_df['code'] + ' ' + 
            self.courses_df['title'] + ' ' + 
            self.courses_df['description'].fillna('')
        )
        
        # Clean the text
        self.courses_df['full_text'] = self.courses_df['full_text'].apply(self._clean_text)
        
        logger.info("Course data prepared for vectorization")
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text for better vectorization quality
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text
        """
        if pd.isna(text):
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove special characters that might interfere with vectorization
        text = text.replace('"', '').replace("'", '')
        
        return text.strip()
    
    def generate_vectors(self, force_regenerate: bool = False):
        """
        Generate TF-IDF vectors for all course descriptions
        
        Args:
            force_regenerate: If True, regenerate vectors even if they exist
        """
        # Check if vectors already exist
        if not force_regenerate and os.path.exists(self.vectors_file):
            try:
                logger.info("Loading existing vectors...")
                with open(self.vectors_file, 'rb') as f:
                    data = pickle.load(f)
                    self.course_vectors = data['vectors']
                    self.vectorizer = data['vectorizer']
                logger.info("Vectors loaded successfully")
                return
            except Exception as e:
                logger.warning(f"Could not load existing vectors: {e}")
        
        if self.courses_df is None:
            raise ValueError("No course data loaded. Call load_courses() first.")
        
        logger.info("Generating TF-IDF vectors for course descriptions...")
        
        # Initialize TF-IDF vectorizer
        self.vectorizer = TfidfVectorizer(
            max_features=1000,  # Limit features for efficiency
            stop_words='english',  # Remove common English words
            ngram_range=(1, 2),  # Use unigrams and bigrams
            min_df=2,  # Minimum document frequency
            max_df=0.95  # Maximum document frequency
        )
        
        # Get the full text for each course
        course_texts = self.courses_df['full_text'].tolist()
        
        # Generate vectors
        self.course_vectors = self.vectorizer.fit_transform(course_texts)
        
        # Save vectors for future use
        try:
            with open(self.vectors_file, 'wb') as f:
                pickle.dump({
                    'vectors': self.course_vectors,
                    'vectorizer': self.vectorizer
                }, f)
            logger.info(f"Vectors saved to {self.vectors_file}")
        except Exception as e:
            logger.warning(f"Could not save vectors: {e}")
        
        logger.info(f"Generated vectors for {len(course_texts)} courses")
        logger.info(f"Vector dimensions: {self.course_vectors.shape}")
    
    def search_courses(self, query: str, top_k: int = 10) -> List[Dict]:
        """
        Search for courses based on semantic similarity to the query
        
        Args:
            query: User's search query
            top_k: Number of top results to return
            
        Returns:
            List of dictionaries containing course information and similarity scores
        """
        if self.vectorizer is None:
            raise ValueError("No vectorizer available. Call generate_vectors() first.")
        
        if self.course_vectors is None:
            raise ValueError("No course vectors available. Call generate_vectors() first.")
        
        logger.info(f"Searching for courses matching: '{query}'")
        
        # Clean the query
        clean_query = self._clean_text(query)
        
        # Generate vector for the query
        query_vector = self.vectorizer.transform([clean_query])
        
        # Calculate cosine similarity between query and all courses
        similarities = cosine_similarity(query_vector, self.course_vectors).flatten()
        
        # Create list of (index, similarity_score) tuples and sort by score
        course_scores = list(enumerate(similarities))
        course_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Get top-k results
        top_results = []
        for idx, score in course_scores[:top_k]:
            course_info = self.courses_df.iloc[idx].to_dict()
            course_info['similarity_score'] = float(score)
            course_info['rank'] = len(top_results) + 1
            top_results.append(course_info)
        
        logger.info(f"Found {len(top_results)} relevant courses")
        return top_results
    
    def get_course_details(self, course_code: str) -> Dict:
        """
        Get detailed information for a specific course
        
        Args:
            course_code: Course code (e.g., 'CSE 101')
            
        Returns:
            Dictionary containing course information
        """
        if self.courses_df is None:
            raise ValueError("No course data loaded.")
        
        course = self.courses_df[self.courses_df['code'] == course_code]
        if course.empty:
            return None
        
        return course.iloc[0].to_dict()
    
    def get_similar_courses(self, course_code: str, top_k: int = 5) -> List[Dict]:
        """
        Find courses similar to a given course
        
        Args:
            course_code: Course code to find similar courses for
            top_k: Number of similar courses to return
            
        Returns:
            List of similar courses with similarity scores
        """
        if self.course_vectors is None:
            raise ValueError("No course vectors available.")
        
        # Find the course index
        course_idx = self.courses_df[self.courses_df['code'] == course_code].index
        if len(course_idx) == 0:
            return []
        
        course_idx = course_idx[0]
        
        # Get the course vector
        course_vector = self.course_vectors[course_idx:course_idx+1]
        
        # Calculate similarity with all other courses
        similarities = cosine_similarity(course_vector, self.course_vectors).flatten()
        
        # Create list of (index, similarity_score) tuples, excluding the course itself
        course_scores = [(i, score) for i, score in enumerate(similarities) if i != course_idx]
        course_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Get top-k results
        similar_courses = []
        for idx, score in course_scores[:top_k]:
            course_info = self.courses_df.iloc[idx].to_dict()
            course_info['similarity_score'] = float(score)
            similar_courses.append(course_info)
        
        return similar_courses
    
    def get_model_info(self) -> Dict:
        """
        Get information about the current model and vectors
        
        Returns:
            Dictionary containing model and vector information
        """
        info = {
            'model_type': 'TF-IDF Vectorizer',
            'vectorizer_loaded': self.vectorizer is not None,
            'courses_loaded': self.courses_df is not None,
            'vectors_generated': self.course_vectors is not None,
            'total_courses': len(self.courses_df) if self.courses_df is not None else 0,
            'vector_dimensions': self.course_vectors.shape if self.course_vectors is not None else None,
            'features': self.vectorizer.get_feature_names_out().shape[0] if self.vectorizer is not None else None
        }
        return info

def main():
    """
    Main function to demonstrate the NLP course recommender
    """
    print("🚀 NLP Course Recommendation System (TF-IDF)")
    print("=" * 50)
    
    # Initialize the recommender
    recommender = NLPCourseRecommender()
    
    try:
        # Load courses
        print("📚 Loading course data...")
        recommender.load_courses()
        
        # Generate vectors
        print("🧠 Generating course vectors...")
        recommender.generate_vectors()
        
        # Display model info
        info = recommender.get_model_info()
        print(f"\n📊 Model Information:")
        print(f"Model Type: {info['model_type']}")
        print(f"Total courses: {info['total_courses']}")
        print(f"Vector dimensions: {info['vector_dimensions']}")
        print(f"Features: {info['features']}")
        
        # Demo search
        print(f"\n🔍 Demo Search Examples:")
        
        # Example 1: Ethics and social responsibility
        print(f"\n1. Searching for 'ethics and social responsibility in technology':")
        results = recommender.search_courses("ethics and social responsibility in technology", top_k=3)
        for course in results:
            print(f"   {course['rank']}. {course['code']}: {course['title']} (Score: {course['similarity_score']:.3f})")
        
        # Example 2: Machine learning
        print(f"\n2. Searching for 'machine learning and artificial intelligence':")
        results = recommender.search_courses("machine learning and artificial intelligence", top_k=3)
        for course in results:
            print(f"   {course['rank']}. {course['code']}: {course['title']} (Score: {course['similarity_score']:.3f})")
        
        # Example 3: Software development
        print(f"\n3. Searching for 'software development and programming':")
        results = recommender.search_courses("software development and programming", top_k=3)
        for course in results:
            print(f"   {course['rank']}. {course['code']}: {course['title']} (Score: {course['similarity_score']:.3f})")
        
        print(f"\n✅ NLP Course Recommender is ready!")
        print(f"💡 You can now use this system to find relevant courses based on your interests!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error(f"Error in main: {e}")

if __name__ == "__main__":
    main()
