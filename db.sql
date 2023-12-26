-- Active: 1703509556837@@localhost@3306@alumnidb
CREATE DATABASE IF NOT EXISTS AlumniDB;
USE AlumniDB;

CREATE TABLE alumni (
    id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    graduation_year VARCHAR(10),
    current_job VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS email_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    host VARCHAR(255) NOT NULL,
    port INT NOT NULL,
    email_address VARCHAR(255) NOT NULL,
    email_password VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS skills (
    skill_id INT AUTO_INCREMENT PRIMARY KEY,
    skill_name VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS alumni_skills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    alumnus_id INT,
    skill_id INT,
    FOREIGN KEY (alumnus_id) REFERENCES alumni(id),
    FOREIGN KEY (skill_id) REFERENCES skills(skill_id)
);

CREATE TABLE IF NOT EXISTS events (
    event_id INT AUTO_INCREMENT PRIMARY KEY,
    event_name VARCHAR(255) NOT NULL,
    event_date DATE NOT NULL,
    description TEXT,
    organizer_email VARCHAR(100),
    FOREIGN KEY (organizer_email) REFERENCES alumni(email)
);

CREATE TABLE IF NOT EXISTS job_postings (
    job_id INT AUTO_INCREMENT PRIMARY KEY,
    alumnus_id INT,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    company VARCHAR(255),
    location VARCHAR(255),
    posted_date DATE,
    FOREIGN KEY (alumnus_id) REFERENCES alumni(id)
);

CREATE TABLE IF NOT EXISTS alumni_achievements (
    achievement_id INT AUTO_INCREMENT PRIMARY KEY,
    alumnus_id INT,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    date_posted DATE,
    FOREIGN KEY (alumnus_id) REFERENCES alumni(id)
);

CREATE TABLE IF NOT EXISTS alumni_messages (
    message_id INT AUTO_INCREMENT PRIMARY KEY,
    sender_email VARCHAR(100),
    receiver_email VARCHAR(100),
    message TEXT,
    FOREIGN KEY (sender_email) REFERENCES alumni(email),
    FOREIGN KEY (receiver_email) REFERENCES alumni(email)
);

CREATE TABLE IF NOT EXISTS alumni_connections (
    connection_id INT AUTO_INCREMENT PRIMARY KEY,
    requester_email VARCHAR(100),
    target_email VARCHAR(100),
    FOREIGN KEY (requester_email) REFERENCES alumni(email),
    FOREIGN KEY (target_email) REFERENCES alumni(email)
);

CREATE TABLE IF NOT EXISTS job_history (
    history_id INT AUTO_INCREMENT PRIMARY KEY,
    alumnus_id INT,
    company_name VARCHAR(255),
    position VARCHAR(255),
    start_date DATE,
    end_date DATE,
    FOREIGN KEY (alumnus_id) REFERENCES alumni(id)
);

CREATE TABLE IF NOT EXISTS event_attendance (
    attendance_id INT AUTO_INCREMENT PRIMARY KEY,
    event_id INT,
    alumnus_id INT,
    FOREIGN KEY (event_id) REFERENCES events(event_id),
    FOREIGN KEY (alumnus_id) REFERENCES alumni(id)
);

CREATE TABLE IF NOT EXISTS event_invitations (
    invitation_id INT AUTO_INCREMENT PRIMARY KEY,
    event_id INT,
    attendee_email VARCHAR(100),
    FOREIGN KEY (event_id) REFERENCES events(event_id),
    FOREIGN KEY (attendee_email) REFERENCES alumni(email)
);

CREATE TABLE IF NOT EXISTS event_rsvps (
    rsvp_id INT AUTO_INCREMENT PRIMARY KEY,
    event_id INT,
    attendee_email VARCHAR(100),
    rsvp_status VARCHAR(50),
    FOREIGN KEY (event_id) REFERENCES events(event_id),
    FOREIGN KEY (attendee_email) REFERENCES alumni(email)
);

select * from alumni

INSERT INTO alumni (first_name, last_name, email, graduation_year, current_job) 
VALUES ('Amit', 'Jha', 'amitkjha2403@gmail.com', '2025', 'Junior Editor');
