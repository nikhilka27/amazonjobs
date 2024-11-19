from urllib.parse import urlencode
import urllib3
import json
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from pathlib import Path

class AmazonJobsTracker:
    def __init__(self):
        self.seen_jobs_file = 'seen_jobs.json'
        self.seen_jobs = self.load_seen_jobs()
        
        # Get email configuration from environment variables
        self.smtp_server = 'smtp.gmail.com'
        self.smtp_port = 587
        self.email_address = os.environ['EMAIL_ADDRESS']
        self.email_password = os.environ['EMAIL_PASSWORD']
        self.cc_email = os.environ['CC_EMAIL']
        self.bcc_recipients = os.environ['BCC_RECIPIENTS'].split(',')
        
    def load_seen_jobs(self):
        """Load previously seen job IDs from file"""
        if os.path.exists(self.seen_jobs_file):
            with open(self.seen_jobs_file, 'r') as f:
                return set(json.load(f))
        return set()
    
    def save_seen_jobs(self):
        """Save seen job IDs to file"""
        with open(self.seen_jobs_file, 'w') as f:
            json.dump(list(self.seen_jobs), f)
    
    def is_recent_posting(self, posted_date_str, days=1):
        """Check if the job was posted within the last specified days"""
        try:
            posted_date = datetime.strptime(posted_date_str, "%B %d, %Y")
            current_date = datetime.now()
            difference = current_date - posted_date
            return difference.days <= days
        except Exception as e:
            print(f"Error parsing date {posted_date_str}: {e}")
            return False

    def generate_html_content(self, new_jobs):
        """Generate HTML email content for new jobs"""
        html = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; }
                .job { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
                .job-title { color: #232F3E; font-size: 18px; font-weight: bold; }
                .job-details { margin: 10px 0; }
                .apply-button {
                    background-color: #FF9900;
                    color: white;
                    padding: 10px 20px;
                    text-decoration: none;
                    border-radius: 3px;
                    display: inline-block;
                }
            </style>
        </head>
        <body>
            <h2>🚀 New Amazon Entry-Level Software Jobs 🚀</h2>
            <p>Oyeee Jobs Agaiiy oyeeeee!!! Apply karo benchoooo!!!</p>
        """
        
        for job in new_jobs:
            html += f"""
            <div class="job">
                <div class="job-title">{job['title']}</div>
                <div class="job-details">
                    <p><strong>📍 Location:</strong> {job['location']}</p>
                    <p><strong>📅 Posted Date:</strong> {job['posted_date']}</p>
                    <p><strong>📊 Level:</strong> {job.get('level', 'N/A')}</p>
                    <p><strong>📝 Basic Qualifications:</strong> {job.get('basic_qualifications', 'N/A')}</p>
                </div>
                <a href="https://www.amazon.jobs/en/jobs/{job['id_icims']}" class="apply-button">Apply Now 🔥</a>
            </div>
            """
        
        html += """
        </body>
        </html>
        """
        return html

    def send_email(self, new_jobs):
        """Send email with new job listings"""
        if not new_jobs:
            print("No new jobs to send email about.")
            return
        
        msg = MIMEMultipart('alternative')
        msg['From'] = self.email_address
        msg['To'] = self.email_address
        msg['Cc'] = self.cc_email
        msg['Subject'] = f"Oye {len(new_jobs)} New Amazon Jobs Agaiiy oyeeeee!!!"
        
        html_content = self.generate_html_content(new_jobs)
        msg.attach(MIMEText(html_content, 'html'))
        
        try:
            # Save jobs data to CSV
            csv_content = "Title,Location,Posted Date,Level,Job ID,Apply Link\n"
            for job in new_jobs:
                csv_content += f"\"{job['title']}\",\"{job['location']}\",\"{job['posted_date']}\",\"{job.get('level', 'N/A')}\",\"{job['id_icims']}\",\"https://www.amazon.jobs/en/jobs/{job['id_icims']}\"\n"
            
            csv_filename = "amazon_new_jobs.csv"
            with open(csv_filename, 'w') as f:
                f.write(csv_content)
            
            # Attach CSV file
            with open(csv_filename, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename={csv_filename}',
                )
                msg.attach(part)
            
            # Connect to the server and send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_address, self.email_password)
            
            all_recipients = [self.cc_email] + self.bcc_recipients
            server.sendmail(self.email_address, all_recipients, msg.as_string())
            server.quit()
            
            print(f"Email sent successfully with {len(new_jobs)} new jobs!")
            print(f"Recipients: CC -> {self.cc_email}, BCC -> {', '.join(self.bcc_recipients)}")
            
            os.remove(csv_filename)
            
        except Exception as e:
            print(f"Error sending email: {e}")

    def check_new_jobs(self):
        """Check for new jobs and send email if found"""
        searches = [
            "software dev engineer",
            "software developer 2025",
            "system development engineer",
            "entry level software 2025",
            "software development engineer",
            "graduate software engineer 2025",
            "university graduate software 2025",
            "sde 2025"
        ]
        
        new_jobs = []
        http = urllib3.PoolManager()
        
        for search_term in searches:
            print(f"\nSearching for: {search_term}")
            
            params = {
                "normalized_country_code[]": "USA",
                "offset": 0,
                "result_limit": 20,
                "sort": "recent",
                "country": "USA",
                "base_query": search_term,
                "category[]": ["software-development"],
                "experience[]": ["entry-level"],
                "level[]": ["entry-level"],
                "posted_within[]": ["1d"],
            }
            
            try:
                query_string = urlencode(params, doseq=True)
                url = f"https://www.amazon.jobs/en/search.json?{query_string}"
                
                response = http.request('GET', url, headers={
                    "Accept": "application/json",
                    "Accept-Language": "en-US,en;q=0.5",
                })
                
                if response.status == 200:
                    data = json.loads(response.data.decode('utf-8'))
                    jobs = data.get("jobs", [])
                    
                    for job in jobs:
                        job_id = job['id_icims']
                        if (job_id not in self.seen_jobs and 
                            self.is_recent_posting(job['posted_date'])):
                            new_jobs.append(job)
                            self.seen_jobs.add(job_id)
                
            except Exception as e:
                print(f"Error with search term '{search_term}': {e}")
                print(f"Full error details: {str(e)}")
        
        # Remove duplicates while preserving order
        unique_new_jobs = []
        seen = set()
        for job in new_jobs:
            if job['id_icims'] not in seen:
                seen.add(job['id_icims'])
                unique_new_jobs.append(job)
        
        if unique_new_jobs:
            self.send_email(unique_new_jobs)
            self.save_seen_jobs()
            print(f"\nFound {len(unique_new_jobs)} new jobs!")
        else:
            print("\nNo new jobs found.")

def main():
    try:
        tracker = AmazonJobsTracker()
        tracker.check_new_jobs()
    except Exception as e:
        print(f"Error in main execution: {str(e)}")
        raise

if __name__ == "__main__":
    main()
