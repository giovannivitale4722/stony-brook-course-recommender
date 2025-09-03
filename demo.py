#!/usr/bin/env python3
"""
Demo script for the NLP Course Recommendation System
"""

from nlp_course_recommender import NLPCourseRecommender
import time

def print_header():
    """Print a beautiful header"""
    print("=" * 80)
    print("🧠 CSE Course Recommender - AI-Powered Course Discovery")
    print("=" * 80)
    print()

def print_section(title):
    """Print a section header"""
    print(f"\n{'='*20} {title} {'='*20}")

def demo_search_examples(recommender):
    """Demonstrate various search examples"""
    print_section("Search Examples")
    
    examples = [
        ("machine learning and artificial intelligence", "AI and ML courses"),
        ("web development and user interface design", "Web development courses"),
        ("ethics and social responsibility in technology", "Ethics and social issues"),
        ("data structures and algorithms", "Core CS fundamentals"),
        ("computer networks and security", "Networking and security"),
        ("software engineering and project management", "Software development lifecycle"),
        ("database systems and management", "Data management"),
        ("computer graphics and visualization", "Graphics and visualization")
    ]
    
    for query, description in examples:
        print(f"\n🔍 {description}:")
        print(f"   Query: '{query}'")
        
        try:
            results = recommender.search_courses(query, top_k=3)
            for i, course in enumerate(results, 1):
                print(f"   {i}. {course['code']}: {course['title']}")
                print(f"      Score: {course['similarity_score']:.3f}")
                print(f"      Credits: {course['credits']}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        time.sleep(0.5)  # Small delay for readability

def demo_similar_courses(recommender):
    """Demonstrate finding similar courses"""
    print_section("Similar Course Discovery")
    
    test_courses = ["CSE 214", "CSE 300", "CSE 353"]
    
    for course_code in test_courses:
        print(f"\n🔗 Courses similar to {course_code}:")
        try:
            similar = recommender.get_similar_courses(course_code, top_k=3)
            for i, course in enumerate(similar, 1):
                print(f"   {i}. {course['code']}: {course['title']}")
                print(f"      Similarity: {course['similarity_score']:.3f}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        time.sleep(0.5)

def demo_custom_queries(recommender):
    """Allow user to try custom queries"""
    print_section("Custom Query Testing")
    
    print("💡 Try your own queries! Type 'quit' to exit.")
    print("Examples: 'cybersecurity', 'mobile apps', 'game development'")
    
    while True:
        try:
            query = input("\n🔍 Enter your search query: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                break
            
            if not query:
                print("   Please enter a query.")
                continue
            
            print(f"   Searching for: '{query}'")
            results = recommender.search_courses(query, top_k=5)
            
            if results:
                print(f"   Found {len(results)} courses:")
                for i, course in enumerate(results, 1):
                    print(f"   {i}. {course['code']}: {course['title']}")
                    print(f"      Score: {course['similarity_score']:.3f}")
                    print(f"      Credits: {course['credits']}")
                    if course['description']:
                        desc = course['description'][:100] + "..." if len(course['description']) > 100 else course['description']
                        print(f"      Description: {desc}")
            else:
                print("   No courses found. Try different keywords.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Demo interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"   ❌ Error: {e}")

def main():
    """Main demo function"""
    print_header()
    
    try:
        # Initialize the recommender
        print("🚀 Initializing the NLP Course Recommender...")
        recommender = NLPCourseRecommender()
        
        print("📚 Loading course data...")
        recommender.load_courses()
        
        print("🧠 Generating course vectors...")
        recommender.generate_vectors()
        
        # Display system info
        info = recommender.get_model_info()
        print(f"\n✅ System Ready!")
        print(f"📊 Total courses: {info['total_courses']}")
        print(f"🔢 Vector dimensions: {info['vector_dimensions']}")
        print(f"🎯 Features: {info['features']}")
        
        # Run demos
        demo_search_examples(recommender)
        demo_similar_courses(recommender)
        demo_custom_queries(recommender)
        
    except Exception as e:
        print(f"\n❌ Error initializing system: {e}")
        print("💡 Make sure you have the required dependencies installed:")
        print("   pip install -r requirements.txt")
        return
    
    print("\n🎉 Demo completed! Thanks for exploring the CSE Course Recommender!")
    print("🌐 To use the web interface, run: python3 app.py")

if __name__ == "__main__":
    main()
