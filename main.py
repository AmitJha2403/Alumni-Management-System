import mysql.connector
import logging
from contextlib import contextmanager
import re
import csv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def get_email_config():
    """Retrieve email configuration from the database."""
    try:
        with database_connection() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT host, port, email_address, email_password FROM email_config LIMIT 1")
            config = cursor.fetchone()
            return config
    except Exception as e:
        logging.error(f"Error retrieving email config: {e}")
        return None
    
def insert_email_config(host, port, email_address, email_password):
    try:
        with database_connection() as connection:
            cursor = connection.cursor()
            query = """
                INSERT INTO email_config (host, port, email_address, email_password) 
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query, (host, port, email_address, email_password))
            connection.commit()
            print("Email configuration inserted successfully.")
    except Exception as e:
        print(f"Failed to insert email configuration: {e}")

def send_email(recipient, subject, body):
    email_config = get_email_config()
    if not email_config:
        logging.error("Email configuration not found.")
        return

    try:
        # Create MIME message
        msg = MIMEMultipart()
        msg['From'] = email_config[2]
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Connect to server and send email
        server = smtplib.SMTP(email_config[0], email_config[1])
        server.starttls()
        server.login(email_config[2], email_config[3])
        server.send_message(msg)
        server.quit()

        logging.info(f"Email sent to {recipient}")
    except smtplib.SMTPException as e:
        logging.error(f"SMTP error occurred: {e}")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")

@contextmanager
def database_connection():
    connection = None
    try:
        connection = connect_to_db()
        yield connection
    except mysql.connector.Error as err:
        logging.error(f"Database operation failed: {err}")
        raise
    finally:
        if connection:
            connection.close()

# Basic configuration for logging
logging.basicConfig(level=logging.INFO, filename='alumni_system.log', filemode='a', format='%(asctime)s - %(levelname)s - %(message)s')

db_password = None

def connect_to_db():
    """Establish a connection to the MySQL database."""
    global db_password
    if db_password is None:
        logging.error("Database password not set")
        raise ValueError("Database password is not set.")
    
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password=db_password,
            database="AlumniDB"
        )
        return connection
    except mysql.connector.Error as err:
        logging.error(f"Failed to connect to database: {err}")
        raise

# Function to set the global database password
def set_db_password():
    global db_password
    while True:
        try: 
            db_password = input("Enter Database password:")
            mydb = connect_to_db()
            if mydb.is_connected():
                break
        except mysql.connector.Error as err:
            print(f'Connection failed: {err}')

def batch_import(csv_file_path):
    try:
        with database_connection() as connection, open(csv_file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            cursor = connection.cursor()

            for row in reader:
                if not validate_email(row['email']) or not validate_graduation_year(row['graduation_year']):
                    logging.warning(f"Invalid data skipped: {row}")
                    continue  # Skip invalid rows

                # Check for duplicate entry before inserting
                cursor.execute("SELECT * FROM alumni WHERE email = %s", (row['email'],))
                if cursor.fetchone():
                    logging.warning(f"Duplicate entry skipped: {row['email']}")
                    continue  # Skip duplicates

                query = "INSERT INTO alumni (email, first_name, last_name, graduation_year, current_job) VALUES (%s, %s, %s, %s, %s)"
                cursor.execute(query, (row['email'], row['first_name'], row['last_name'], row['graduation_year'], row['current_job']))

            connection.commit()
            logging.info("Batch import completed successfully.")
    except FileNotFoundError:
        logging.error(f"File not found: {csv_file_path}")
    except mysql.connector.Error as db_err:
        logging.error(f"Database error during batch import: {db_err}")
    except Exception as e:
        logging.error(f"Unexpected error during batch import: {e}")

def batch_export(csv_file_path):
    try:
        with database_connection() as connection, open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM alumni")

            columns = [desc[0] for desc in cursor.description]
            writer = csv.DictWriter(file, fieldnames=columns)
            writer.writeheader()

            for row in cursor.fetchall():
                writer.writerow(dict(zip(columns, row)))

            logging.info("Batch export completed successfully.")
    except Exception as e:
        logging.error(f"Failed to complete batch export: {e}")
        print("An error occurred during batch export.")

def validate_name(name):
    """Validate a name."""
    return name.isalpha()

def validate_job_title(title):
    """Validate a job title."""
    # Example validation: checks if title is not empty and consists of letters, spaces, and possibly a few special characters
    return bool(re.match(r"^[A-Za-z .,()-]+$", title))

def validate_email(email):
    """Validate the email format."""
    pattern = r"^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$"
    return re.match(pattern, email)

def validate_graduation_year(year):
    """Validate the graduation year."""
    return year.isdigit() and 1900 <= int(year) <= 2100

def validate_event_name(name):
    """Validate an event name."""
    # Example: Check if the event name is not empty and consists of acceptable characters
    return bool(re.match(r"^[A-Za-z0-9 .,()-]+$", name))

def validate_event_description(description):
    """Validate an event description."""
    # Example: Basic check for non-empty string
    return len(description.strip()) > 0

def validate_skill_name(name):
    """Validate a skill name."""
    return bool(re.match(r"^[A-Za-z0-9 .,()-]+$", name))

def register_alumnus():
    """Register a new alumnus."""
    first_name = str(input("Enter your first name: "))
    while(first_name and not validate_name(first_name)):
        print("Please enter a valid name with only Alphabetical Characters.")
        first_name = str(input("Enter your first name: "))
    last_name = str(input("Enter your Last Name: "))
    while(last_name and not validate_name(last_name)):
        print("Please enter a valid name with only Alphabetical Characters.")
        last_name = str(input("Enter your Last Name: "))
    email = str(input("Enter your email address: "))
    while not validate_email(email):
        print("Invalid email format. Please try again.")
        email = str(input("Enter your email address: "))
    graduation_year = str(input("Enter your graduation year: "))
    while not validate_graduation_year(graduation_year):
        print("Invalid graduation year. Please enter a year between 1900 and 2100.")
        graduation_year = str(input("Enter your graduation year: "))
    current_job = str(input("Enter Current Job: "))
    try:
        with database_connection() as connection:
            cursor = connection.cursor()
            query = "INSERT INTO alumni (first_name, last_name, email, graduation_year, current_job) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(query, (first_name, last_name, email, graduation_year, current_job))
            connection.commit()
            logging.info("New alumnus registered successfully")
            send_email(email, "Welcome to the Alumni Network", "Thank you for registering with our alumni network.")
    except Exception as e:
        logging.error(f"Failed to register alumnus: {e}")
        print("An error occurred during registration.")

def alumnus_login(email):
    """Check if an email exists in the alumni table."""
    try:
        with database_connection() as connection:
            cursor = connection.cursor()
            query = "SELECT * FROM alumni WHERE email = %s"
            cursor.execute(query, (email,))
            result = cursor.fetchone()

            if result is None:
                print(f"No alumni found with the email '{email}'.")
                return False
            else:
                return True
    except mysql.connector.Error as db_err:
        logging.error(f"Database error while checking alumni email: {db_err}")
        return False
    except Exception as e:
        logging.error(f"Failed to check alumni email '{email}': {e}")
        print("An error occurred during the email check.")
        return False

def add_alumnus(first_name, last_name, email, graduation_year, current_job):
    """Insert a new alumnus into the database."""
    try:
        with database_connection() as connection:
            cursor = connection.cursor()
            query = "INSERT INTO alumni (first_name, last_name, email, graduation_year, current_job) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(query, (first_name, last_name, email, graduation_year, current_job))
            connection.commit()

        logging.info("Alumnus added successfully.")
    except mysql.connector.Error as db_err:
        logging.error(f"Database error while adding alumnus: {db_err}")
    except Exception as e:
        logging.error(f"Unexpected error while adding alumnus: {e}")

def get_all_alumni():
    """Fetch all alumni from the database."""
    try:
        with database_connection() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM alumni")
            records = cursor.fetchall()
            return records
    except mysql.connector.Error as db_err:
        logging.error(f"Database error fetching all alumni: {db_err}")
        return []
    except Exception as e:
        logging.error(f"Error fetching all alumni: {e}")
        return []

def update_alumnus(id, first_name=None, last_name=None, email=None, graduation_year=None, current_job=None):
    """Update details of an alumnus in the database."""
    if first_name and not validate_name(first_name):
        logging.error("Invalid first name format.")
        print("Invalid first name format. Please ensure the name contains only letters.")
        return
    if last_name and not validate_name(last_name):
        logging.error("Invalid last name format.")
        print("Invalid last name format. Please ensure the name contains only letters.")
        return
    if current_job and not validate_job_title(current_job):
        logging.error("Invalid job title format.")
        print("Invalid job title format. Please re-enter the job title.")
        return
    try:
        with database_connection() as connection:
            cursor = connection.cursor()

            update_fields = []
            values = []

            if first_name:
                update_fields.append("first_name = %s")
                values.append(first_name)
            if last_name:
                update_fields.append("last_name = %s")
                values.append(last_name)
            if email:
                update_fields.append("email = %s")
                values.append(email)
            if graduation_year:
                update_fields.append("graduation_year = %s")
                values.append(graduation_year)
            if current_job:
                update_fields.append("current_job = %s")
                values.append(current_job)

            query = "UPDATE alumni SET " + ", ".join(update_fields) + " WHERE id = %s"
            values.append(id)

            cursor.execute(query, tuple(values))
            connection.commit()

            logging.info(f"Alumnus with ID {id} updated successfully.")
    except mysql.connector.Error as db_err:
        logging.error(f"Database error fetching all alumni: {db_err}")
        return []
    except Exception as e:
        logging.error(f"Failed to update alumnus: {e}")
        print("An error occurred while updating the alumnus.")

def delete_alumnus(id):
    """Remove an alumnus from the database."""
    try:
        with database_connection() as connection:
            cursor = connection.cursor()
            query = "DELETE FROM alumni WHERE id = %s"
            cursor.execute(query, (id,))
            connection.commit()

            logging.info(f"Alumnus with ID {id} deleted successfully.")
    except mysql.connector.Error as db_err:
        logging.error(f"Database error fetching all alumni: {db_err}")
        return []
    except Exception as e:
        logging.error(f"Failed to delete alumnus with ID {id}: {e}")
        print("An error occurred while deleting the alumnus.")

def add_skill(skill_name):
    """Add a new skill to the skills table."""
    try:
        with database_connection() as connection:
            cursor = connection.cursor()

            query = "INSERT INTO skills (skill_name) VALUES (%s)"
            cursor.execute(query, (skill_name,))

            connection.commit()
            logging.info(f"Skill '{skill_name}' added successfully.")
    except mysql.connector.Error as db_err:
        logging.error(f"Database error fetching all alumni: {db_err}")
        return []
    except Exception as e:
        logging.error(f"Failed to add skill '{skill_name}': {e}")
        print("An error occurred while adding the skill.")

def search_alumni_by_name(name):
    """Search alumni based on name."""
    try:
        with database_connection() as connection:
            cursor = connection.cursor()
            query = "SELECT * FROM alumni WHERE first_name LIKE %s OR last_name LIKE %s"
            cursor.execute(query, ('%' + name + '%', '%' + name + '%'))
            results = cursor.fetchall()

            if len(results) == 0:
                print(f"No alumni found with the name '{name}'.")
                return []

            logging.info(f"Search for alumni by name '{name}' completed successfully.")
            return results
    except mysql.connector.Error as db_err:
        logging.error(f"Database error fetching all alumni: {db_err}")
        return []
    except Exception as e:
        logging.error(f"Failed to search alumni by name '{name}': {e}")
        print("An error occurred during the search.")
        return []



def search_alumni_by_skill(skill_name):
    """Search alumni based on skill."""
    try:
        with database_connection() as connection:
            cursor = connection.cursor()
            query = """
                SELECT alumni.* FROM alumni
                JOIN alumni_skills ON alumni.id = alumni_skills.alumnus_id
                JOIN skills ON skills.skill_id = alumni_skills.skill_id
                WHERE skills.skill_name = %s
            """
            cursor.execute(query, (skill_name,))
            results = cursor.fetchall()

            if len(results) == 0:
                print(f"No alumni found with the skill '{skill_name}'.")
                return []

            logging.info(f"Search for alumni by skill '{skill_name}' completed successfully.")
            return results
    except mysql.connector.Error as db_err:
        logging.error(f"Database error fetching all alumni: {db_err}")
        return []
    except Exception as e:
        logging.error(f"Failed to search alumni by skill '{skill_name}': {e}")
        print("An error occurred during the skill search.")
        return []

def add_event(event_name, event_date, description):
    """Add a new alumni event."""
    if not validate_event_name(event_name):
        logging.error("Invalid event name format.")
        print("Invalid event name format. Please re-enter the event name.")
        return
    if not validate_event_description(description):
        logging.error("Invalid event description.")
        print("Invalid event description. Please re-enter the description.")
        return
    try:
        with database_connection() as connection:
            cursor = connection.cursor()
            query = "INSERT INTO events (event_name, event_date, description) VALUES (%s, %s, %s)"
            cursor.execute(query, (event_name, event_date, description))
            connection.commit()
            logging.info("Event added successfully.")
    except mysql.connector.Error as db_err:
        logging.error(f"Database error fetching all alumni: {db_err}")
        return []
    except Exception as e:
        logging.error(f"Failed to add event: {e}")
        print("An error occurred while adding the event.")

def mark_attendance(alumnus_id, event_id):
    """Mark attendance for an event."""
    try:
        with database_connection() as connection:
            cursor = connection.cursor()
            query = "INSERT INTO event_attendance (alumnus_id, event_id) VALUES (%s, %s)"
            cursor.execute(query, (alumnus_id, event_id))
            connection.commit()
            logging.info("Attendance marked successfully.")
    except mysql.connector.Error as db_err:
        logging.error(f"Database error fetching all alumni: {db_err}")
        return []
    except Exception as e:
        logging.error(f"Failed to mark attendance: {e}")
        print("An error occurred while marking attendance.")

def generate_report():
    try:
        with database_connection() as connection:
            cursor = connection.cursor()

            # Example: Count of registered alumni
            cursor.execute("SELECT COUNT(*) FROM alumni")
            total_alumni = cursor.fetchone()[0]

            # Example: Distribution by graduation year
            cursor.execute("SELECT graduation_year, COUNT(*) FROM alumni GROUP BY graduation_year")
            year_distribution = cursor.fetchall()

            # Format the report
            report = f"Total Alumni: {total_alumni}\n\nGraduation Year Distribution:\n"
            for year, count in year_distribution:
                report += f"Year {year}: {count} alumni\n"

            print(report)
            logging.info("Report generated successfully.")
    except mysql.connector.Error as db_err:
        logging.error(f"Database error fetching all alumni: {db_err}")
        return []
    except Exception as e:
        logging.error(f"Failed to generate report: {e}")
        print("An error occurred during report generation.")

def post_job(user_email, title, description, company, location):
    """
    Post a new job opportunity by an alumnus.

    :param user_email: Email of the alumnus posting the job.
    :param title: Job title.
    :param description: Job description.
    :param company: Company offering the job.
    :param location: Location of the job.
    """
    try:
        with database_connection() as connection:
            cursor = connection.cursor()
            # Retrieve alumnus_id based on email
            cursor.execute("SELECT id FROM alumni WHERE email = %s", (user_email,))
            alumnus_id_result = cursor.fetchone()
            if alumnus_id_result:
                alumnus_id = alumnus_id_result[0]

                # Insert job posting
                job_insert_query = """
                    INSERT INTO job_postings (alumnus_id, title, description, company, location, posted_date)
                    VALUES (%s, %s, %s, %s, %s, NOW())
                """
                cursor.execute(job_insert_query, (alumnus_id, title, description, company, location))

                connection.commit()
                logging.info(f"Job '{title}' posted successfully by alumnus ID {alumnus_id}.")
                print("Job posted successfully.")
            else:
                logging.error("Alumnus not found.")
                print("Error: Alumnus not found.")
    except Exception as e:
        logging.error(f"Failed to post job: {e}")
        print("An error occurred while posting the job.")

def search_jobs(search_term):
    """
    Search for job postings based on a search term.

    :param search_term: The term to search in job titles and descriptions.
    """
    try:
        with database_connection() as connection:
            cursor = connection.cursor()

            # Search for jobs
            search_query = """
                SELECT * FROM job_postings
                WHERE title LIKE %s OR description LIKE %s
            """
            like_term = f'%{search_term}%'
            cursor.execute(search_query, (like_term, like_term))

            jobs = cursor.fetchall()
            for job in jobs:
                print(job)  # Format and display each job as needed

            logging.info(f"Search completed for jobs with term '{search_term}'.")
    except Exception as e:
        logging.error(f"Failed to search jobs: {e}")
        print("An error occurred while searching for jobs.")

    return jobs

def display_achievements():
    """
    Display achievements of alumni.
    """
    try:
        with database_connection() as connection:
            cursor = connection.cursor()

            # Retrieve all achievements
            select_query = "SELECT * FROM alumni_achievements ORDER BY date_posted DESC"
            cursor.execute(select_query)

            achievements = cursor.fetchall()
            for achievement in achievements:
                print(achievement)  # Format and display each achievement as needed

            logging.info("Achievements displayed successfully.")
    except Exception as e:
        logging.error(f"Failed to display achievements: {e}")
        print("An error occurred while displaying achievements.")

    return achievements

def generate_alumni_statistics():
    """
    Generate statistics about alumni.
    """
    try:
        with database_connection() as connection:
            cursor = connection.cursor()

            # Total number of alumni
            cursor.execute("SELECT COUNT(*) FROM alumni")
            total_alumni = cursor.fetchone()[0]

            # Alumni distribution by graduation year
            cursor.execute("SELECT graduation_year, COUNT(*) FROM alumni GROUP BY graduation_year")
            alumni_by_year = cursor.fetchall()

            # Format and display statistics
            print(f"Total Alumni: {total_alumni}\n")
            print("Alumni Distribution by Graduation Year:")
            for year, count in alumni_by_year:
                print(f"Year {year}: {count} alumni")

            logging.info("Alumni statistics generated successfully.")
    except Exception as e:
        logging.error(f"Failed to generate alumni statistics: {e}")
        print("An error occurred while generating alumni statistics.")

def generate_event_participation_report():
    """
    Generate a report on event participation.
    """
    try:
        with database_connection() as connection:
            cursor = connection.cursor()

            # Event participation details
            cursor.execute("""
                SELECT e.event_name, COUNT(a.alumnus_id) AS participants
                FROM events e
                JOIN event_attendance a ON e.event_id = a.event_id
                GROUP BY e.event_name
            """)
            event_participation = cursor.fetchall()

            # Format and display the report
            print("Event Participation Report:")
            for event, participants in event_participation:
                print(f"{event}: {participants} participants")

            logging.info("Event participation report generated successfully.")
    except Exception as e:
        logging.error(f"Failed to generate event participation report: {e}")
        print("An error occurred while generating event participation report.")

def send_message_to_alumnus(sender_email, receiver_email, message):
    """
    Send a message from one alumnus to another.
    """
    try:
        with database_connection() as connection:
            cursor = connection.cursor()
            query = "INSERT INTO alumni_messages (sender_email, receiver_email, message) VALUES (%s, %s, %s)"
            cursor.execute(query, (sender_email, receiver_email, message))
            connection.commit()
            logging.info(f"Message sent from {sender_email} to {receiver_email}")
            print("Message sent successfully.")
    except Exception as e:
        logging.error(f"Failed to send message: {e}")
        print("An error occurred while sending the message.")

def view_received_messages(email):
    """
    View messages received by an alumnus.
    """
    try:
        with database_connection() as connection:
            cursor = connection.cursor()
            query = "SELECT sender_email, message FROM alumni_messages WHERE receiver_email = %s"
            cursor.execute(query, (email,))
            messages = cursor.fetchall()
            print("Received Messages:")
            for sender, message in messages:
                print(f"From {sender}: {message}")
    except Exception as e:
        logging.error(f"Error viewing messages: {e}")
        print("An error occurred while viewing messages.")

def connect_with_alumnus(requester_email, target_email):
    """
    Send a connection request to another alumnus.
    """
    try:
        with database_connection() as connection:
            cursor = connection.cursor()
            query = "INSERT INTO alumni_connections (requester_email, target_email) VALUES (%s, %s)"
            cursor.execute(query, (requester_email, target_email))
            connection.commit()
            logging.info(f"Connection request sent from {requester_email} to {target_email}")
            print("Connection request sent successfully.")
    except Exception as e:
        logging.error(f"Failed to send connection request: {e}")
        print("An error occurred while sending the connection request.")

def create_event(event_name, event_date, description, organizer_email):
    """
    Create a new alumni event.
    """
    try:
        with database_connection() as connection:
            cursor = connection.cursor()
            query = "INSERT INTO events (event_name, event_date, description, organizer_email) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (event_name, event_date, description, organizer_email))
            connection.commit()
            logging.info(f"Event '{event_name}' created successfully")
            print("Event created successfully.")
    except Exception as e:
        logging.error(f"Failed to create event: {e}")
        print("An error occurred while creating the event.")

def send_event_invitations(event_id, attendee_emails):
    """
    Send invitations to a list of attendees for an event.
    """
    for email in attendee_emails:
        try:
            with database_connection() as connection:
                cursor = connection.cursor()
                query = "INSERT INTO event_invitations (event_id, attendee_email) VALUES (%s, %s)"
                cursor.execute(query, (event_id, email))
                connection.commit()
                send_email(email, "Invitation to Alumni Event", f"You're invited to our event! Event ID: {event_id}")
                logging.info(f"Invitation sent for event ID {event_id} to {email}")
        except Exception as e:
            logging.error(f"Failed to send invitation for event ID {event_id} to {email}: {e}")
            print(f"An error occurred while sending invitation to {email}.")

def handle_event_rsvp(event_id, attendee_email, rsvp_status):
    """
    Handle RSVP response for an event.
    """
    try:
        with database_connection() as connection:
            cursor = connection.cursor()
            query = """
                INSERT INTO event_rsvps (event_id, attendee_email, rsvp_status) 
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE rsvp_status = VALUES(rsvp_status);
            """
            cursor.execute(query, (event_id, attendee_email, rsvp_status))
            connection.commit()
            logging.info(f"RSVP status updated for event ID {event_id} by {attendee_email}")
            print("RSVP status updated successfully.")
    except Exception as e:
        logging.error(f"Failed to update RSVP for event ID {event_id}: {e}")
        print("An error occurred while updating the RSVP.")

def get_job_postings():
    """Fetch job postings from the database."""
    try:
        with database_connection() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM job_postings")
            jobs = cursor.fetchall()
            return jobs  # Format as needed, e.g., a list of dictionaries
    except Exception as e:
        logging.error(f"Failed to fetch job postings: {e}")
        return []

roles = {
    "admin": "adminpwd",  
    "student": "studentpwd",
}

current_role = None

def login():
    """Handle user login."""
    global current_role
    while True:
        role_input = input("Are you a 'student' or an 'admin'? ").lower()
        if role_input in roles:
            password = input("Enter password: ")
            if password == roles[role_input]:
                current_role = role_input
                break
            else:
                print("Incorrect password, try again.")
        else:
            print("Invalid role, try again.")

def admin_menu():
    """Display the admin menu."""
    while True:
        print("\nAdmin Menu")
        print("1. Add Alumnus")
        print("2. List All Alumni")
        print("3. Update Alumnus")
        print("4. Delete Alumnus")
        print("5. Add Skill")
        print("6. Search by Name")
        print("7. Search by Skill")
        print("8. Add Event")
        print("9. Mark Attendance")
        print("10. Batch Import Alumni Data")
        print("11. Batch Export Alumni Data")
        print("12. Generate Report")
        print("13. Handle Event RSVP")
        print("14. Exit")

        choice = input("Enter your choice: ")

        if choice == '1':
            first_name = str(input("Enter First Name: "))
            last_name = str(input("Enter Last Name: "))
            email = str(input("Enter Email: "))
            graduation_year = str(int(input("Enter Graduation Year: ")))
            current_job = str(input("Enter Current Job: "))
            add_alumnus(first_name, last_name, email, graduation_year, current_job)
            print("Alumnus added successfully!")

        elif choice == '2':
            records = get_all_alumni()
            for record in records:
                print(record)

        elif choice == '3':
            id = int(input("Enter the ID of the alumnus to update: "))
            first_name = str(input("Enter new First Name (or press Enter to skip): "))
            last_name = str(input("Enter new Last Name (or press Enter to skip): "))
            email = str(input("Enter new Email (or press Enter to skip): "))
            graduation_year = str(input("Enter new Graduation Year (or press Enter to skip): "))
            current_job = str(input("Enter new Current Job (or press Enter to skip): "))

            update_alumnus(id, first_name or None, last_name or None, email or None, int(graduation_year) if graduation_year else None, current_job or None)
            print("Alumnus updated successfully!")

        elif choice == '4':
            id = int(input("Enter the ID of the alumnus to delete: "))
            delete_alumnus(id)
            print("Alumnus deleted successfully!")


        elif choice == '5':
            skill_name = str(input("Enter Skill Name: "))
            add_skill(skill_name)
            print("Skill added successfully!")

        elif choice == '6':
            name = input("Enter Name to Search: ")
            results = search_alumni_by_name(name)
            for result in results:
                print(result)

        elif choice == '7':
            skill_name = str(input("Enter Skill to Search: "))
            results = search_alumni_by_skill(skill_name)
            for result in results:
                print(result)

        elif choice == '8':
            event_name = input("Enter Event Name: ")
            event_date = input("Enter Event Date (YYYY-MM-DD): ")
            description = input("Enter Event Description: ")
            add_event(event_name, event_date, description)
            print("Event added successfully!")

        elif choice == '9':
            alumnus_id = int(input("Enter Alumnus ID: "))
            event_id = int(input("Enter Event ID: "))
            mark_attendance(alumnus_id, event_id)
            print("Attendance marked successfully!")

        elif choice == '10':
            file_path = input("Enter the path of the CSV file to import: ")
            batch_import(file_path)

        elif choice == '11':
            file_path = input("Enter the path to export the CSV file: ")
            batch_export(file_path)
        
        elif choice == '12':
            generate_report()
        
        elif choice == '13':
            event_id = input("Enter Event ID: ")
            attendee_email = input("Enter Attendee Email: ")
            rsvp_status = input("Enter RSVP Status (Yes/No/Maybe): ")
            handle_event_rsvp(event_id, attendee_email, rsvp_status)
        
        elif choice == '14':
            print("Exiting admin menu.")
            break
        
        else:
            print("Invalid choice. Please try again.")

def update_alumnus_profile(user_email):
    """Update an alumnus's profile."""
    connection = connect_to_db()
    cursor = connection.cursor()

    new_first_name = str(input("Enter new first name (or press Enter to skip): "))
    new_last_name = str(input("Enter new last name (or press Enter to skip): "))
    new_graduation_year = str(input("Enter new graduation year (or press Enter to skip): "))
    new_current_job = str(input("Enter your updated job (or press Enter to skip):"))

    update_fields = []
    values = []

    if new_first_name:
        update_fields.append("first_name = %s")
        values.append(new_first_name)
    if new_last_name:
        update_fields.append("last_name = %s")
        values.append(new_last_name)
    if new_graduation_year:
        update_fields.append("graduation_year = %s")
        values.append(new_graduation_year)
    if new_current_job:
        update_fields.append("current_job = %s")
        values.append(new_graduation_year)

    if not update_fields:
        print("No updates made.")
        return

    query = "UPDATE alumni SET " + ", ".join(update_fields) + " WHERE email = %s"
    values.append(user_email)

    cursor.execute(query, tuple(values))
    connection.commit()

    cursor.close()
    connection.close()
    print("Profile updated successfully.")

def admin_login():
    """Handle admin login."""
    global current_role
    while True:
        admin_pwd = input("Enter admin password: ")
        if admin_pwd == roles['admin']:
            current_role = 'admin'
            break
        else:
            print("Incorrect password, try again.")

def add_skill_to_profile(user_email, skill):
    """Add a skill to an alumnus's profile."""
    if not validate_skill_name(skill):
        logging.error("Invalid skill name format.")
        print("Invalid skill name format. Please re-enter the skill name.")
        return
    connection = connect_to_db()
    cursor = connection.cursor()

    # Get alumnus ID based on email
    cursor.execute("SELECT id FROM alumni WHERE email = %s", (user_email,))
    alumnus_id = cursor.fetchone()[0]

    # Insert skill into skills table and get its ID
    cursor.execute("INSERT INTO skills (skill_name) VALUES (%s) ON DUPLICATE KEY UPDATE skill_name = skill_name", (skill,))
    cursor.execute("SELECT skill_id FROM skills WHERE skill_name = %s", (skill,))
    skill_id = cursor.fetchone()[0]

    # Link skill with alumnus
    cursor.execute("INSERT INTO alumni_skills (alumnus_id, skill_id) VALUES (%s, %s)", (alumnus_id, skill_id))

    connection.commit()
    cursor.close()
    connection.close()

def remove_skill_from_profile(user_email, skill):
    """Remove a skill from an alumnus's profile."""
    connection = connect_to_db()
    cursor = connection.cursor()

    # Get alumnus ID based on email
    cursor.execute("SELECT id FROM alumni WHERE email = %s", (user_email,))
    alumnus_id = cursor.fetchone()[0]

    # Get skill ID
    cursor.execute("SELECT skill_id FROM skills WHERE skill_name = %s", (skill,))
    skill_id_result = cursor.fetchone()
    if skill_id_result:
        skill_id = skill_id_result[0]
        # Remove skill link from alumnus
        cursor.execute("DELETE FROM alumni_skills WHERE alumnus_id = %s AND skill_id = %s", (alumnus_id, skill_id))

    connection.commit()
    cursor.close()
    connection.close()

def view_job_history(user_email):
    """View job history of an alumnus."""
    connection = connect_to_db()
    cursor = connection.cursor()

    cursor.execute("SELECT id FROM alumni WHERE email = %s", (user_email,))
    alumnus_id = cursor.fetchone()[0]

    cursor.execute("SELECT * FROM job_history WHERE alumnus_id = %s", (alumnus_id,))
    jobs = cursor.fetchall()

    for job in jobs:
        print(job)  # Format as needed

    cursor.close()
    connection.close()

def update_job_history(user_email):
    """Update an alumnus's job history."""
    connection = connect_to_db()
    cursor = connection.cursor()

    cursor.execute("SELECT id FROM alumni WHERE email = %s", (user_email,))
    alumnus_id = cursor.fetchone()[0]

    # Example: Add a new job record
    # Extend this function to handle different job history updates as per your requirements
    company_name = input("Enter company name: ")
    position = input("Enter position: ")
    start_date = input("Enter start date (YYYY-MM-DD): ")
    end_date = input("Enter end date (YYYY-MM-DD) or leave blank: ")

    cursor.execute("INSERT INTO job_history (alumnus_id, company_name, position, start_date, end_date) VALUES (%s, %s, %s, %s, %s)", (alumnus_id, company_name, position, start_date, end_date or None))

    connection.commit()
    cursor.close()
    connection.close()

def alumni_menu(user_email):
    while True:
        print("\nAlumni Menu")
        print("1. Update Profile Information")
        print("2. Add Skill to Profile")
        print("3. Remove Skill from Profile")
        print("4. View Job History")
        print("5. Update Job History")
        print("6. Post Job Opportunity")
        print("7. Logout")

        choice = input("Enter your choice: ")

        if choice == '1':
            update_alumnus_profile(user_email)
        elif choice == '2':
            skill = input("Enter the skill you want to add: ")
            add_skill_to_profile(user_email, skill)
        elif choice == '3':
            skill = input("Enter the skill you want to remove: ")
            remove_skill_from_profile(user_email, skill)
        elif choice == '4':
            view_job_history(user_email)
        elif choice == '5':
            update_job_history(user_email)
        elif choice == '6':
            job_title = input("Enter job title: ")
            job_description = input("Enter job description: ")
            company_name = input("Enter company name: ")
            job_location = input("Enter job location: ")
            post_job(user_email, job_title, job_description, company_name, job_location)
        elif choice == '7':
            print("Logging out.")
            break
        else:
            print("Invalid choice, please try again.")

def student_menu():
    while True:
        print("\nStudent Menu")
        print("1. List All Alumni")
        print("2. Search by Name")
        print("3. Search by Skill")
        print("4. View Job Postings")
        print("5. Exit")

        choice = input("Enter your choice: ")

        if choice == '1':
            records = get_all_alumni()
            for record in records:
                print(record)

        elif choice == '2':
            name = input("Enter Name to Search: ")
            results = search_alumni_by_name(name)
            for result in results:
                print(result)

        elif choice == '3':
            skill_name = input("Enter Skill to Search: ")
            results = search_alumni_by_skill(skill_name)
            for result in results:
                print(result)

        elif choice == '4':
            print("Job Postings:")
            # Assuming there's a function to fetch job postings
            jobs = get_job_postings()
            for job in jobs:
                print(job)  # Format job posting for display

        elif choice == '5':
            print("Exiting student menu.")
            break
        else:
            print("Invalid choice, please try again.")

def main_menu():
    global db_password
    if db_password is None:
        set_db_password()

    print("\nMain Menu")
    print("1. Admin Login")
    print("2. Student Login")
    print("3. Alumni Registration")
    print("4. Alumni Login")
    print("5. Exit")

    choice = input("Enter your choice: ")

    if choice == '1':
        admin_login()
        admin_menu()  # Assuming admin_menu is defined elsewhere
    elif choice == '2':
        student_menu()  # Assuming student_menu is defined elsewhere
    elif choice == '3':
        register_alumnus()
    elif choice == '4':
        email = input("Enter your email: ")
        if alumnus_login(email):
            alumni_menu(email)  # Pass the logged-in user's email
        else:
            print("Login failed")
    elif choice == '5':
        print("Goodbye!")
        exit()
    else:
        print("Invalid choice, please try again.")

if __name__ == "__main__":
    while True:
        main_menu()