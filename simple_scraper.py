import requests
import csv
import re
import time
import json
from bs4 import BeautifulSoup
from typing import Dict, List, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleStonyBrookCourseScraper:
    def __init__(self):
        # Base URL template for Stony Brook catalog
        self.base_url = "https://catalog.stonybrook.edu/content.php?filter%5B27%5D={dept}&filter%5B29%5D=&filter%5B32%5D=1&cur_cat_oid=7&expand=1&navoid=225&print=1&filter%5Bexact_match%5D=1"
        
        # All departments with their codes
        self.departments = {
            # College of Arts and Sciences
            'AFR': 'Africana Studies',
            'ANT': 'Anthropology',
            'ARH': 'Art History and Criticism',
            'ARS': 'Art, Studio',
            'AAS': 'Asian and Asian American Studies',
            'AST': 'Astronomy/Planetary Sciences',
            'ATM': 'Atmospheric and Oceanic Sciences',
            'BCP': 'Biochemistry',
            'BIO': 'Biology',
            'CHE': 'Chemistry',
            'CCS': 'Cinema and Cultural Studies',
            'CLS': 'Classical Civilization',
            'COL': 'Comparative Literature',
            'CSE': 'Computer Science',
            'CWL': 'Creative Writing and Literature',
            'DAS': 'Digital Arts and Sciences',
            'ECO': 'Economics',
            'EGL': 'English',
            'EDP': 'Environmental Design, Policy, and Planning',
            'ENS': 'Environmental Studies',
            'FRN': 'French Language and Literature',
            'GEO': 'Geology',
            'GER': 'German Language and Literature',
            'GLI': 'Globalization Studies and International Relations',
            'HIS': 'History',
            'HEB': 'Human Evolutionary Biology',
            'IAS': 'Italian American Studies',
            'ITL': 'Italian Studies',
            'JPS': 'Japanese Studies',
            'JRN': 'Journalism',
            'KOR': 'Korean Studies',
            'LAC': 'Latin American and Caribbean Studies',
            'LIN': 'Linguistics',
            'MAR': 'Marine Sciences',
            'MVB': 'Marine Vertebrate Biology',
            'MAT': 'Mathematics',
            'MVL': 'Medieval Studies',
            'MUS': 'Music',
            'PHI': 'Philosophy',
            'PHY': 'Physics',
            'POL': 'Political Science',
            'PSY': 'Psychology',
            'RLS': 'Religious Studies',
            'RUS': 'Russian Language and Literature',
            'SOC': 'Sociology',
            'SPN': 'Spanish Language and Literature',
            'THR': 'Theatre Arts',
            'WST': 'Women\'s, Gender, and Sexuality Studies',
            
            # College of Engineering and Applied Sciences
            'AMS': 'Applied Mathematics and Statistics',
            'BME': 'Biomedical Engineering',
            'CME': 'Chemical and Molecular Engineering',
            'CIV': 'Civil Engineering',
            'ECE': 'Computer Engineering',
            'ELE': 'Electrical Engineering',
            'ESG': 'Engineering Science',
            'ISE': 'Information Systems',
            'MEC': 'Mechanical Engineering',
            'TSM': 'Technological Systems Management',
            
            # College of Business
            'ACC': 'Accounting',
            'BUS': 'Business Management',
            'FIN': 'Finance',
            'MKT': 'Marketing',
            'OPM': 'Operations Management',
            
            # School of Health Professions
            'HSC': 'Health Science',
            'RSR': 'Respiratory Care',
            'SWK': 'Social Work',
            
            # School of Nursing
            'NUR': 'Nursing'
        }
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Rate limiting to be respectful to the server
        self.delay_between_requests = 1.0  # seconds
        
    def get_department_url(self, dept_code: str) -> str:
        """Generate URL for a specific department"""
        return self.base_url.format(dept=dept_code)
    
    def scrape_department(self, dept_code: str, dept_name: str) -> List[Dict]:
        """
        Scrape courses from a specific department
        """
        try:
            url = self.get_department_url(dept_code)
            logger.info(f"Scraping {dept_code} ({dept_name}) from {url}")
            
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            html_content = str(soup)
            
            courses = self.parse_department_html(html_content, dept_code)
            
            logger.info(f"Found {len(courses)} courses in {dept_code}")
            return courses
            
        except Exception as e:
            logger.error(f"Error scraping {dept_code}: {e}")
            return []
    
    def parse_department_html(self, html_content: str, dept_code: str) -> List[Dict]:
        """
        Parse HTML content to extract course information for a specific department
        """
        courses = []
        
        # Use regex to find course sections
        course_pattern = rf'(?=<h3[^>]*>{dept_code}\s+\d+)'
        course_sections = re.split(course_pattern, html_content)
        
        for section in course_sections:
            if re.search(rf'{dept_code}\s+\d+', section):
                course_info = self.extract_course_info(section, dept_code)
                if course_info:
                    courses.append(course_info)
        
        return courses
    
    def extract_course_info(self, section: str, dept_code: str) -> Dict:
        """
        Extract basic course information: code, title, credits, and description
        """
        course_info = {
            'department': dept_code,
            'code': '',
            'title': '',
            'credits': '',
            'description': ''
        }
        
        # Extract course code and title from h3 tags
        h3_pattern = rf'<h3[^>]*>({dept_code}\s+\d+)\s*[-–—]\s*(.+?)</h3>'
        h3_match = re.search(h3_pattern, section, re.IGNORECASE)
        if h3_match:
            course_info['code'] = h3_match.group(1)
            course_info['title'] = self.clean_html(h3_match.group(2))
        else:
            # Fallback: look for course code anywhere in section
            code_pattern = rf'({dept_code}\s+\d+)\s*[-–—]\s*(.+)'
            code_match = re.search(code_pattern, section)
            if code_match:
                course_info['code'] = code_match.group(1)
                course_info['title'] = self.clean_html(code_match.group(2))
            else:
                return None
        
        # Extract credits
        credits_match = re.search(r'(\d+)\s*credit', section, re.IGNORECASE)
        if credits_match:
            course_info['credits'] = credits_match.group(1)
        
        # Extract description
        course_info['description'] = self.extract_description(section, course_info['title'])
        
        return course_info
    
    def extract_description(self, section: str, title: str) -> str:
        """
        Extract description using multiple methods
        """
        description = ""
        
        # Method 1: Look for text content after title but before other fields
        if title:
            title_pos = section.find(title)
            if title_pos != -1:
                desc_start = title_pos + len(title)
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
                lines = text_after_h3.split('\n')
                for line in lines:
                    line = self.clean_html(line)
                    if len(line) > 20 and not re.match(r'^\d+\s*credit', line, re.IGNORECASE):
                        description = line
                        break
        
        # Clean up the description
        if description:
            description = re.sub(r'\d+\s*credit[s]?', '', description, flags=re.IGNORECASE)
            for field in ['Prerequisite', 'SBC', 'Repeatable', 'Anti-requisite']:
                description = re.sub(rf'{field}[:\s]+.+?(?=\s*$)', '', description, flags=re.IGNORECASE)
            description = re.sub(r'\s+', ' ', description)
            description = description.strip()
            description = re.sub(r'[.,]\s*$', '', description)
        
        return description
    
    def clean_html(self, text: str) -> str:
        """Clean HTML tags and normalize text content"""
        if not text:
            return ""
        
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        text = re.sub(r'[.,]\s*$', '', text)
        
        return text
    
    def scrape_all_departments(self, max_workers: int = 3) -> Dict[str, List[Dict]]:
        """
        Scrape courses from all departments using parallel processing
        """
        all_courses = {}
        successful_depts = []
        failed_depts = []
        
        logger.info(f"Starting to scrape {len(self.departments)} departments with {max_workers} workers")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all scraping tasks
            future_to_dept = {
                executor.submit(self.scrape_department, dept_code, dept_name): dept_code
                for dept_code, dept_name in self.departments.items()
            }
            
            # Process completed tasks
            for future in as_completed(future_to_dept):
                dept_code = future_to_dept[future]
                try:
                    courses = future.result()
                    if courses:
                        all_courses[dept_code] = courses
                        successful_depts.append(dept_code)
                        logger.info(f"✅ {dept_code}: {len(courses)} courses")
                    else:
                        failed_depts.append(dept_code)
                        logger.warning(f"⚠️ {dept_code}: No courses found")
                    
                    # Rate limiting
                    time.sleep(self.delay_between_requests)
                    
                except Exception as e:
                    failed_depts.append(dept_code)
                    logger.error(f"❌ {dept_code}: {e}")
        
        # Summary
        total_courses = sum(len(courses) for courses in all_courses.values())
        logger.info(f"\n🎉 Scraping completed!")
        logger.info(f"✅ Successful departments: {len(successful_depts)}")
        logger.info(f"❌ Failed departments: {len(failed_depts)}")
        logger.info(f"📚 Total courses collected: {total_courses}")
        
        if failed_depts:
            logger.warning(f"Failed departments: {', '.join(failed_depts)}")
        
        return all_courses
    
    def scrape_single_department(self, dept_code: str) -> List[Dict]:
        """
        Scrape courses from a single department (for testing)
        """
        if dept_code not in self.departments:
            print(f"❌ Department {dept_code} not found")
            return []
        
        dept_name = self.departments[dept_code]
        print(f"🔄 Scraping {dept_code} ({dept_name})...")
        
        courses = self.scrape_department(dept_code, dept_name)
        
        if courses:
            print(f"✅ Found {len(courses)} courses in {dept_code}")
            return courses
        else:
            print(f"❌ No courses found in {dept_code}")
            return []
    
    def save_to_csv(self, all_courses: Dict[str, List[Dict]], filename: str = 'all_departments_courses.csv'):
        """
        Save all courses to a single CSV file
        """
        if not all_courses:
            print("❌ No courses to save.")
            return
        
        # Flatten all courses into a single list
        flat_courses = []
        for dept_code, courses in all_courses.items():
            for course in courses:
                flat_courses.append(course)
        
        # Define fields
        fieldnames = ['department', 'code', 'title', 'credits', 'description']
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(flat_courses)
        
        print(f"✅ Saved {len(flat_courses)} courses to {filename}")
    
    def save_department_summary(self, all_courses: Dict[str, List[Dict]], filename: str = 'department_summary.json'):
        """
        Save a summary of courses per department
        """
        summary = {}
        for dept_code, courses in all_courses.items():
            summary[dept_code] = {
                'name': self.departments[dept_code],
                'course_count': len(courses),
                'courses': [{'code': c['code'], 'title': c['title'], 'credits': c['credits']} for c in courses]
            }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Saved department summary to {filename}")
    
    def display_course_summary(self, all_courses: Dict[str, List[Dict]]):
        """
        Display a summary of all scraped courses
        """
        if not all_courses:
            print("❌ No courses to display.")
            return
        
        total_courses = sum(len(courses) for courses in all_courses.values())
        successful_depts = len(all_courses)
        
        print(f"\n📊 Course Summary:")
        print(f"Total departments: {successful_depts}")
        print(f"Total courses: {total_courses}")
        
        # Show top departments by course count
        dept_counts = [(dept, len(courses)) for dept, courses in all_courses.items()]
        dept_counts.sort(key=lambda x: x[1], reverse=True)
        
        print(f"\n🏆 Top 10 departments by course count:")
        for i, (dept, count) in enumerate(dept_counts[:10], 1):
            dept_name = self.departments[dept]
            print(f"   {i:2d}. {dept} ({dept_name}): {count} courses")
        
        # Show sample courses from top department
        if dept_counts:
            top_dept, top_count = dept_counts[0]
            print(f"\n📋 Sample courses from {top_dept} ({top_count} courses):")
            for i, course in enumerate(all_courses[top_dept][:3], 1):
                print(f"\n{i}. {course['code']}: {course['title']}")
                if course['credits']:
                    print(f"   Credits: {course['credits']}")
                if course['description']:
                    desc = course['description'][:150] + "..." if len(course['description']) > 150 else course['description']
                    print(f"   Description: {desc}")

def main():
    """
    Main function to run the multi-department scraper
    """
    print("🚀 Multi-Department Course Scraper for Stony Brook University")
    print("=" * 70)
    
    scraper = SimpleStonyBrookCourseScraper()
    
    # Ask user what they want to do
    print("\n🔍 What would you like to do?")
    print("1. Scrape all departments (comprehensive)")
    print("2. Test with a single department")
    print("3. Scrape specific departments")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    try:
        if choice == "1":
            # Scrape all departments
            print(f"\n📚 Scraping courses from {len(scraper.departments)} departments...")
            print("⚠️ This will take 10-30 minutes and make many requests to the server.")
            confirm = input("Continue? (y/n): ").strip().lower()
            
            if confirm == 'y':
                all_courses = scraper.scrape_all_departments(max_workers=3)
                
                if all_courses:
                    # Save results
                    scraper.save_to_csv(all_courses)
                    scraper.save_department_summary(all_courses)
                    
                    # Display summary
                    scraper.display_course_summary(all_courses)
                    
                    print(f"\n🎉 Successfully scraped courses from {len(all_courses)} departments!")
                    print(f"📁 Data saved to: all_departments_courses.csv")
                    print(f"📊 Summary saved to: department_summary.json")
                else:
                    print("❌ No courses were scraped. Check the logs for errors.")
            else:
                print("Scraping cancelled.")
                
        elif choice == "2":
            # Test with single department
            dept_code = input("Enter department code (e.g., CSE, AMS, BIO): ").strip().upper()
            courses = scraper.scrape_single_department(dept_code)
            
            if courses:
                scraper.display_course_summary({dept_code: courses})
                scraper.save_to_csv({dept_code: courses}, f'{dept_code.lower()}_courses.csv')
                
        elif choice == "3":
            # Scrape specific departments
            print("Available departments:")
            for code, name in scraper.departments.items():
                print(f"  {code}: {name}")
            
            dept_codes = input("Enter department codes separated by commas (e.g., CSE,AMS,BIO): ").strip().upper().split(',')
            dept_codes = [code.strip() for code in dept_codes if code.strip()]
            
            selected_depts = {code: scraper.departments[code] for code in dept_codes if code in scraper.departments}
            
            if selected_depts:
                print(f"\n📚 Scraping {len(selected_depts)} selected departments...")
                all_courses = {}
                
                for dept_code, dept_name in selected_depts.items():
                    courses = scraper.scrape_department(dept_code, dept_name)
                    if courses:
                        all_courses[dept_code] = courses
                    time.sleep(scraper.delay_between_requests)
                
                if all_courses:
                    scraper.save_to_csv(all_courses, 'selected_departments_courses.csv')
                    scraper.display_course_summary(all_courses)
                else:
                    print("❌ No courses found in selected departments.")
            else:
                print("❌ No valid department codes entered.")
        else:
            print("❌ Invalid choice. Please run again and select 1, 2, or 3.")
            
    except KeyboardInterrupt:
        print("\n\n⏹️ Scraping interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during scraping: {e}")
        logger.error(f"Main error: {e}")

if __name__ == "__main__":
    main()
