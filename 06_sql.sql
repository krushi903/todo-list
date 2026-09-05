USE ecom;

-- CREATE VIEW delivered_orders AS
-- SELECT order_id,
--        customer_name,
--        city,
--        product,
--        price_per_unit,
--        order_date
-- FROM orders
-- WHERE order_status = 'Delivered';

-- CREATE VIEW del_mum_clients AS 
-- SELECT * FROM orders
-- WHERE (city= "Delhi" AND order_status = "Delivered") 
-- OR city = "Mumbai";
-- UPDATE orders SET customer_name = "Dr Amit" WHERE order_id = 1;

-- UPDATE delivered_orders
-- SET price_per_unit = price_per_unit + 101
-- WHERE order_id = 1;
DROP VIEW delivered_orders;
-- SELECT * FROM delivered_orders;
