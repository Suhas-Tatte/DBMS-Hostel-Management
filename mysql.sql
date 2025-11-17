CREATE DATABASE hostel_management;
USE hostel_management;


CREATE TABLE student (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    f_name VARCHAR(50) NOT NULL,
    l_name VARCHAR(50) NOT NULL,
    age INT CHECK (age > 0),
    age_group VARCHAR(20)
);

CREATE TABLE visitor (
    visitor_id INT AUTO_INCREMENT PRIMARY KEY,
    f_name VARCHAR(50) NOT NULL,
    l_name VARCHAR(50) NOT NULL
);


CREATE TABLE visits (
    student_id INT NOT NULL,
    visitor_id INT NOT NULL,
    visit_date DATE NOT NULL,
    PRIMARY KEY (student_id, visitor_id, visit_date),
    FOREIGN KEY (student_id) REFERENCES student(student_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (visitor_id) REFERENCES visitor(visitor_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);


CREATE TABLE fees (
    receipt_no INT AUTO_INCREMENT PRIMARY KEY,
    due_date DATE NOT NULL,
    amount DECIMAL(10,2) NOT NULL CHECK (amount >= 0),
    date_paid DATE,
    student_id INT NOT NULL,
    FOREIGN KEY (student_id) REFERENCES student(student_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);


CREATE TABLE phone_student (
    student_id INT NOT NULL,
    phone_no VARCHAR(15) NOT NULL,
    PRIMARY KEY (student_id, phone_no),
    FOREIGN KEY (student_id) REFERENCES student(student_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);


CREATE TABLE phone_visitor (
    visitor_id INT NOT NULL,
    phone_no VARCHAR(15) NOT NULL,
    PRIMARY KEY (visitor_id, phone_no),
    FOREIGN KEY (visitor_id) REFERENCES visitor(visitor_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);


CREATE TABLE warden (
    warden_id INT AUTO_INCREMENT PRIMARY KEY,
    f_name VARCHAR(50) NOT NULL,
    l_name VARCHAR(50) NOT NULL,
    phone_no VARCHAR(15),
    salary DECIMAL(10,2) CHECK (salary >= 0)
);


CREATE TABLE phone_warden (
    warden_id INT NOT NULL,
    phone_no VARCHAR(15) NOT NULL,
    PRIMARY KEY (warden_id, phone_no),
    FOREIGN KEY (warden_id) REFERENCES warden(warden_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);


CREATE TABLE hostel (
    hostel_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    total_room INT CHECK (total_room >= 0),
    street VARCHAR(100),
    city VARCHAR(50),
    pincode VARCHAR(10),
    warden_id INT,
    FOREIGN KEY (warden_id) REFERENCES warden(warden_id)
        ON DELETE SET NULL ON UPDATE CASCADE
);


CREATE TABLE room (
    room_id INT AUTO_INCREMENT PRIMARY KEY,
    type VARCHAR(20),
    capacity INT CHECK (capacity > 0),
    hostel_id INT NOT NULL,
    FOREIGN KEY (hostel_id) REFERENCES hostel(hostel_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);


CREATE TABLE allocated (
    student_id INT NOT NULL,
    room_id INT NOT NULL,
    PRIMARY KEY (student_id, room_id),
    FOREIGN KEY (student_id) REFERENCES student(student_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (room_id) REFERENCES room(room_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);



INSERT INTO student (f_name, l_name, age, age_group) VALUES
('Arjun', 'Reddy', 20, '18-22'),
('Sneha', 'Patil', 21, '18-22'),
('Karthik', 'Prasad', 22, '18-22'),
('Priya', 'Menon', 19, '18-22');

INSERT INTO visitor (f_name, l_name) VALUES
('Ramesh', 'Reddy'),
('Anita', 'Patil'),
('Rajesh', 'Menon');

INSERT INTO visits (student_id, visitor_id, visit_date) VALUES
(1, 1, '2025-09-15'),
(2, 2, '2025-09-18'),
(4, 3, '2025-09-20');

INSERT INTO fees (due_date, amount, date_paid, student_id) VALUES
('2025-07-01', 15000.00, '2025-07-02', 1),
('2025-07-01', 15000.00, '2025-07-03', 2),
('2025-07-01', 15000.00, NULL, 3),
('2025-07-01', 15000.00, '2025-07-05', 4);

INSERT INTO phone_student (student_id, phone_no) VALUES
(1, '9876543210'),
(2, '9876501234'),
(3, '9001234567'),
(4, '9123456789');

INSERT INTO phone_visitor (visitor_id, phone_no) VALUES
(1, '9822012345'),
(2, '9822045678'),
(3, '9822099999');

INSERT INTO warden (f_name, l_name, phone_no, salary) VALUES
('Manoj', 'Kumar', '9800012345', 35000.00),
('Sujatha', 'Rao', '9800023456', 36000.00);

INSERT INTO phone_warden (warden_id, phone_no) VALUES
(1, '9800012345'),
(1, '9800011111'),
(2, '9800023456');

INSERT INTO hostel (name, total_room, street, city, pincode, warden_id) VALUES
('A Block', 20, 'MG Road', 'Bangalore', '560001', 1),
('B Block', 25, 'Church Street', 'Bangalore', '560002', 2);

INSERT INTO room (type, capacity, hostel_id) VALUES
('Single', 1, 1),
('Double', 2, 1),
('Double', 2, 2),
('Triple', 3, 2);

INSERT INTO allocated (student_id, room_id) VALUES
(1, 1),
(2, 2),
(3, 3),
(4, 4);

SHOW TABLES;

USE hostel_management;

-- DELETE FROM allocated WHERE student_id = 1;
-- Trigger after allocate
SELECT * FROM room WHERE room_id = 2;
INSERT INTO allocated(student_id, room_id) VALUES (4, 2);
INSERT INTO allocated(student_id, room_id) VALUES (1, 2);
SELECT * FROM room WHERE room_id = 2;

-- Trigger after deallocate
DELETE FROM allocated WHERE student_id = 4 AND room_id = 2;
SELECT * FROM room WHERE room_id = 2;

-- delete from fees where receipt_no = 5;
-- Trigger for fee status insert
INSERT INTO fees(receipt_no, due_date, amount, date_paid, student_id)
VALUES (5, '2025-08-01', 15000, NULL, 3);
SELECT * FROM fees WHERE receipt_no = 5;

-- Trigger for fee paid
UPDATE fees
SET date_paid = '2025-08-05'
WHERE receipt_no = 5;
SELECT * FROM fees WHERE receipt_no = 5;

-- delete from visits where student_id = 1;
-- Trigger for duplicate visits
INSERT INTO visits(student_id, visitor_id, visit_date) VALUES (1, 1, CURDATE());
-- Second insert
INSERT INTO visits(student_id, visitor_id, visit_date) VALUES (1, 1, CURDATE());

-- delete from allocated where student_id = 2;
-- Procedure to allocate room
SELECT * FROM room WHERE room_id = 2;
CALL allocate_room(2, 2);
SELECT * FROM allocated WHERE room_id = 2;
SELECT * FROM room WHERE room_id = 2;

-- delete from visits where student_id = 2 and visitor_id = 3;
-- Procedure to log a visit with today's date
CALL record_visit(2, 3);
SELECT * FROM visits WHERE student_id = 2 AND visitor_id = 3;


-- Procedure for fee payment
SELECT * FROM fees WHERE receipt_no = 1;
-- Call procedure
CALL record_payment(1, 2, '2025-07-10');
SELECT * FROM fees WHERE receipt_no = 1;

-- Function to check how many student's fee is still pending
SELECT total_pending_fees(3) AS Pending_Amount;

-- Function to check how many students in hostel
SELECT student_count_in_hostel(1) AS Hostel1_Students;

-- Function to check number of visits of student
SELECT total_visits(1) AS Visits_By_Student1;
