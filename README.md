# Alumni-Management-System
This was the project created by me in class 12th as the final CBSE project. I am uploading it here because why not (-:


## Description
The Alumni Management System is a comprehensive solution for managing alumni data, events, job postings, and more. It is built with Python and uses a MySQL database for data storage.

## Features
- Alumni registration and login
- Email notifications
- Batch import and export of alumni data
- Job postings by alumni
- Event management with RSVP functionality
- Skills management for alumni profiles
- Database management for storing alumni information, events, skills, and job postings

## Installation
1. Clone the repository:
```bash
git clone AmitJha2403/Alumni-Management-System
```
2. Install required Python packages:
```bash
pip install mysql-connector-python
```

## Configuration
1. Set up a MySQL database using the provided `db.sql` script.
2. Update the database connection details in `main.py` to match your database configuration.
3. Set up an email server configuration for sending notifications.

## Usage
Run the `main.py` script:
```bash
python main.py
```
Follow the on-screen prompts to interact with the system.

### Admin Functions
- Add, list, update, and delete alumni
- Manage events and job postings
- Generate reports

### Alumni Functions
- Update profile information
- Add or remove skills
- View and update job history
- Post job opportunities

### Student Functions
- View alumni information
- Search alumni by name or skill
- View job postings

## Database Schema
The system uses the following database tables:
- `alumni`: Stores personal and professional details of the alumni.
- `email_config`: Contains email server configuration for sending notifications.
- `skills`, `alumni_skills`: Manage skills associated with alumni.
- `events`, `event_attendance`, `event_invitations`, `event_rsvps`: Manage events and track attendance and invitations.
- `job_postings`: Store job opportunities posted by alumni.
- `alumni_achievements`: Record achievements of alumni.
- `alumni_messages`, `alumni_connections`: Handle communication and connections between alumni.
- `job_history`: Track job history of alumni.

Refer to `db.sql` for the complete schema.
