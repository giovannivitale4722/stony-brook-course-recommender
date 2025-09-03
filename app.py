from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
from nlp_course_recommender import NLPCourseRecommender
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Initialize the recommender
recommender = None

def initialize_recommender():
    """Initialize the NLP course recommender"""
    global recommender
    try:
        recommender = NLPCourseRecommender()
        recommender.load_courses()
        recommender.generate_vectors()
        logger.info("Recommender initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing recommender: {e}")
        return False

@app.route('/')
def index():
    """Main page with search interface"""
    return render_template('index.html')

@app.route('/api/search', methods=['POST'])
def search_courses():
    """API endpoint for course search"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        top_k = data.get('top_k', 10)
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        if recommender is None:
            return jsonify({'error': 'Recommender not initialized'}), 500
        
        # Search for courses
        results = recommender.search_courses(query, top_k=top_k)
        
        # Format results for frontend
        formatted_results = []
        for course in results:
            formatted_results.append({
                'rank': course['rank'],
                'code': course['code'],
                'title': course['title'],
                'credits': course['credits'],
                'description': course['description'],
                'similarity_score': round(course['similarity_score'], 3)
            })
        
        return jsonify({
            'query': query,
            'results': formatted_results,
            'total_results': len(formatted_results)
        })
        
    except Exception as e:
        logger.error(f"Error in search: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/course/<course_code>')
def get_course_details(course_code):
    """Get detailed information for a specific course"""
    try:
        if recommender is None:
            return jsonify({'error': 'Recommender not initialized'}), 500
        
        course = recommender.get_course_details(course_code)
        if course is None:
            return jsonify({'error': 'Course not found'}), 404
        
        return jsonify(course)
        
    except Exception as e:
        logger.error(f"Error getting course details: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/similar/<course_code>')
def get_similar_courses(course_code):
    """Get courses similar to a given course"""
    try:
        top_k = request.args.get('top_k', 5, type=int)
        
        if recommender is None:
            return jsonify({'error': 'Recommender not initialized'}), 500
        
        similar_courses = recommender.get_similar_courses(course_code, top_k=top_k)
        
        # Format results
        formatted_results = []
        for course in similar_courses:
            formatted_results.append({
                'code': course['code'],
                'title': course['title'],
                'credits': course['credits'],
                'description': course['description'],
                'similarity_score': round(course['similarity_score'], 3)
            })
        
        return jsonify({
            'course_code': course_code,
            'similar_courses': formatted_results
        })
        
    except Exception as e:
        logger.error(f"Error getting similar courses: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/status')
def get_status():
    """Get system status and information"""
    try:
        if recommender is None:
            return jsonify({'status': 'not_initialized'})
        
        info = recommender.get_model_info()
        return jsonify({
            'status': 'ready',
            'info': info
        })
        
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({'status': 'error', 'error': str(e)})

@app.route('/api/examples')
def get_example_queries():
    """Get example search queries for users"""
    examples = [
        "machine learning and artificial intelligence",
        "software development and programming",
        "ethics and social responsibility in technology",
        "data structures and algorithms",
        "computer networks and security",
        "database systems and management",
        "web development and user interface design",
        "computer graphics and visualization",
        "operating systems and system programming",
        "software engineering and project management"
    ]
    return jsonify({'examples': examples})

if __name__ == '__main__':
    # Initialize the recommender before starting the app
    if initialize_recommender():
        print("✅ Recommender initialized successfully!")
        print("🌐 Starting Flask web application...")
        app.run(debug=True, host='0.0.0.0', port=5001)
    else:
        print("❌ Failed to initialize recommender. Check the logs for details.")
