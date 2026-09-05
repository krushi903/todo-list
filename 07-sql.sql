USE ecom;
-- SELECT AVG(price_er_unit) FROM orders;
-- SELECT *,
-- (SELECT AVG(price_per_unit) FROM orders) AS average FROM orders;
SELECT * FROM orders o
WHERE EXISTS (
SELECT 1
FROM orders
WHERE city = o.city
AND category = "Furniture"
);




-- WHERE city IN (
-- SELECT city FROM ORDERS WHERE category = "Electronics"
-- );
-- WHERE price_per_unit > (
-- SELECT AVG (price_per_unit) FROM orders
-- );