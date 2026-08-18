CREATE DATABASE IF NOT EXISTS smart_wifi;

USE smart_wifi;


-- ------------------------------------
-- USERS
-- ------------------------------------

CREATE TABLE IF NOT EXISTS users (

    user_id INT PRIMARY KEY AUTO_INCREMENT,

    username VARCHAR(100) NOT NULL,

    email VARCHAR(150),

    created_at TIMESTAMP
    DEFAULT CURRENT_TIMESTAMP

);


-- ------------------------------------
-- ALLOCATION HISTORY
-- ------------------------------------

CREATE TABLE IF NOT EXISTS allocation_history (

    allocation_id INT PRIMARY KEY
    AUTO_INCREMENT,

    user_id INT,

    activity VARCHAR(50),

    requested_bandwidth DECIMAL(10,2),

    allocated_bandwidth DECIMAL(10,2),

    utility DECIMAL(10,4),

    fairness_index DECIMAL(10,4),

    created_at TIMESTAMP
    DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id)
    REFERENCES users(user_id)

);