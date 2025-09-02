-- analysis.sql
-- Example SQL queries for Exploratory Data Analysis in AWS Athena.
-- Replace `nyc_taxi_db.processed_data_table` with your actual database and table name.

-- Query 1: Average Trip Duration by Hour of Day
-- Find the busiest and slowest times for taxi trips.
SELECT
    pickup_hour,
    AVG(trip_duration_minutes) AS average_duration
FROM
    "nyc_taxi_db"."processed_data_table"
GROUP BY
    pickup_hour
ORDER BY
    pickup_hour;


-- Query 2: Top 10 Busiest Pickup Locations
-- Identify rider demand hotspots.
-- Note: This requires PULocationID to be mapped to actual borough/neighborhood names,
-- which can be done by joining with a location lookup table.
SELECT
    "PULocationID",
    COUNT(*) as trip_count
FROM
    "nyc_taxi_db"."processed_data_table"
GROUP BY
    "PULocationID"
ORDER BY
    trip_count DESC
LIMIT 10;


-- Query 3: Tipping Behavior by Payment Type
-- Analyze how tipping percentage varies between cash and credit card payments.
-- (Assuming 1=Credit card, 2=Cash from data dictionary)
SELECT
    CASE
        WHEN payment_type = 1 THEN 'Credit Card'
        WHEN payment_type = 2 THEN 'Cash'
        ELSE 'Other'
    END as payment_method,
    COUNT(*) as number_of_trips,
    AVG(tip_percentage) as avg_tip_percentage
FROM
    "nyc_taxi_db"."processed_data_table"
WHERE
    payment_type IN (1, 2)
GROUP BY
    payment_type;


-- Query 4: Fare and Distance Distribution
-- Get basic statistics on core financial metrics.
SELECT
    APPROX_PERCENTILE(total_amount, 0.5) as median_fare,
    AVG(total_amount) as average_fare,
    MAX(total_amount) as max_fare,
    AVG(trip_distance) as average_distance
FROM
    "nyc_taxi_db"."processed_data_table"
WHERE
    total_amount > 0 AND total_amount < 500; -- Filter outliers
