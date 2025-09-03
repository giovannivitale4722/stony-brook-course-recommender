import requests
import csv
import re
from bs4 import BeautifulSoup
from typing import Dict, List

class SimpleStonyBrookCourseScraper:
    def __init__(self):
        self.url = "https://catalog.stonybrook.edu/content.php?filter%5B27%5D=AMS&filter%5B29%5D=&filter%5B32%5D=1&cur_cat_oid=7&expand=1&navoid=225&print=1&filter%5Bexact_match%5D=1"
    
    def scrape_cse_courses(self) -> List[Dict]:
        """
        Scrape CSE course information focusing only on credits and description
        """
        try:
            print("🔄 Scraping CSE course catalog...")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(self.url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            html_content = str(soup)
            
            print("✅ Successfully scraped the page!")
            return self.parse_html_content(html_content)
            
        except Exception as e:
            print(f"❌ Error during scraping: {e}")
            return []
    
    def parse_html_content(self, html_content: str) -> List[Dict]:
        """
        Parse HTML content to extract course information
        """
        courses = []
        
        # Use regex to find course sections - look for h3 tags containing CSE courses
        course_sections = re.split(r'(?=<h3[^>]*>CSE\s+\d+)', html_content)
        
        for section in course_sections:
            if re.search(r'CSE\s+\d+', section):
                course_info = self.extract_course_info(section)
                if course_info:
                    courses.append(course_info)
        
        print(f"📚 Found {len(courses)} courses in HTML content")
        return courses
    
    def extract_course_info(self, section: str) -> Dict:
        """
        Extract basic course information: code, title, credits, and description
        """
        course_info = {
            'code': '',
            'title': '',
            'credits': '',
            'description': ''
        }
        
        # Extract course code and title from h3 tags
        h3_match = re.search(r'<h3[^>]*>(CSE\s+\d+)\s*[-–—]\s*(.+?)</h3>', section, re.IGNORECASE)
        if h3_match:
            course_info['code'] = h3_match.group(1)
            course_info['title'] = self.clean_html(h3_match.group(2))
        else:
            # Fallback: look for course code anywhere in section
            code_match = re.search(r'(CSE\s+\d+)\s*[-–—]\s*(.+)', section)
            if code_match:
                course_info['code'] = code_match.group(1)
                course_info['title'] = self.clean_html(code_match.group(2))
            else:
                return None
        
        # Extract credits
        credits_match = re.search(r'(\d+)\s*credit', section, re.IGNORECASE)
        if credits_match:
            course_info['credits'] = credits_match.group(1)
        
        # Extract description - comprehensive method
        course_info['description'] = self.extract_description(section, course_info['title'])
        
        return course_info
    
    def extract_description(self, section: str, title: str) -> str:
        """
        Extract description using multiple methods
        """
        description = ""
        
        # Method 1: Look for text content after title but before other fields
        if title:
            # Find the position after the title
            title_pos = section.find(title)
            if title_pos != -1:
                desc_start = title_pos + len(title)
                
                # Find the end of description
                desc_end = len(section)
                for marker in ['Prerequisite', 'Prerequisites', 'Prereq', 'Offered', 'Offering', 'SBC', 'Repeatable', 'Anti-requisite']:
                    marker_pos = section.find(marker, desc_start)
                    if marker_pos != -1 and marker_pos < desc_end:
                        desc_end = marker_pos
                
                if desc_end > desc_start:
                    description = section[desc_start:desc_end].strip()
                    description = self.clean_html(description)
        
        # Method 2: Look for paragraph content
        if not description:
            p_match = re.search(r'<p[^>]*>(.+?)</p>', section, re.DOTALL)
            if p_match:
                description = self.clean_html(p_match.group(1))
        
        # Method 3: Look for direct text content after h3
        if not description:
            h3_end = section.find('</h3>')
            if h3_end != -1:
                text_after_h3 = section[h3_end + 5:].strip()
                # Find first substantial text content
                lines = text_after_h3.split('\n')
                for line in lines:
                    line = self.clean_html(line)
                    if len(line) > 20 and not re.match(r'^\d+\s*credit', line, re.IGNORECASE):
                        description = line
                        break
        
        # Clean up the description
        if description:
            # Remove credit information
            description = re.sub(r'\d+\s*credit[s]?', '', description, flags=re.IGNORECASE)
            # Remove other field markers
            for field in ['Prerequisite', 'SBC', 'Repeatable', 'Anti-requisite']:
                description = re.sub(rf'{field}[:\s]+.+?(?=\s*$)', '', description, flags=re.IGNORECASE)
            # Clean up extra spaces and punctuation
            description = re.sub(r'\s+', ' ', description)
            description = description.strip()
            description = re.sub(r'[.,]\s*$', '', description)
        
        return description
    
    def clean_html(self, text: str) -> str:
        """
        Clean HTML tags and normalize text content
        """
        if not text:
            return ""
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove leading/trailing whitespace
        text = text.strip()
        # Remove trailing punctuation
        text = re.sub(r'[.,]\s*$', '', text)
        
        return text
    
    def save_to_csv(self, courses: List[Dict], filename: str = 'cse_courses_simple.csv'):
        """
        Save course information to a simple CSV file
        """
        if not courses:
            print("❌ No courses to save.")
            return
        
        # Define fields
        fieldnames = ['code', 'title', 'credits', 'description']
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(courses)
        
        print(f"✅ Successfully saved {len(courses)} courses to {filename}")
    
    def display_course_summary(self, courses: List[Dict]):
        """
        Display a summary of the scraped courses
        """
        print(f"\n📊 Course Summary:")
        print(f"Total courses: {len(courses)}")
        
        # Count courses with different types of information
        with_credits = sum(1 for c in courses if c['credits'])
        with_description = sum(1 for c in courses if c['description'])
        
        print(f"📚 Courses with credits: {with_credits}")
        print(f"📝 Courses with description: {with_description}")
        
        # Show sample courses
        print(f"\n📋 Sample courses:")
        for i, course in enumerate(courses[:3], 1):
            print(f"\n{i}. {course['code']}: {course['title']}")
            if course['credits']:
                print(f"   Credits: {course['credits']}")
            if course['description']:
                print(f"   Description: {course['description'][:150]}...")

def main():
    """
    Main function to run the simple scraper
    """
    print("🚀 Simple Stony Brook University CSE Course Scraper")
    print("=" * 60)
    
    # Initialize the scraper
    scraper = SimpleStonyBrookCourseScraper()
    
    # Scrape courses
    courses = scraper.scrape_cse_courses()
    
    if courses:
        # Display summary
        scraper.display_course_summary(courses)
        
        # Save to CSV
        scraper.save_to_csv(courses)
        
        print(f"\n🎉 Successfully scraped {len(courses)} CSE courses!")
        print(f"📁 Data saved to: cse_courses_simple.csv")
        
        # Show examples
        print(f"\n🔍 Example courses:")
        for i, course in enumerate(courses[:2], 1):
            print(f"\nExample {i}:")
            for key, value in course.items():
                if value:
                    print(f"  {key.replace('_', ' ').title()}: {value}")
        
    else:
        print("❌ No courses found. Try again or check the website.")

if __name__ == "__main__":
    main()
