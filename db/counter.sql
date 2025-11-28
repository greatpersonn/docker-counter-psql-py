CREATE TABLE user_counters (
    user_id INT PRIMARY KEY,
    counter INT NOT NULL,
    version INT NOT NULL
);

INSERT INTO user_counters (user_id, counter, version) VALUES (1, 0, 0);