import pandas as pd
#create a DataFrame of ecommerce orders
df = pd.DataFrame({
    'order_id': [1001, 1002, 1003, 1004],
    'customer_id': [501, 502,503, 504],
    'order_amount': [250.0, 150.0, 300.0, 200.0],
    'order_date': ['2024-01-15', '2024-01-16', '2024-01-17', '2024-01-18'],
    'customer_name': ['Alice', 'Bob', 'Charlie', 'David'],
    'customer_cuuntry': ['USA', 'Canada', 'USA', 'UK']
})
#Create a DataFrame for products
df2 = pd.DataFrame({
    'product_id': [101, 102, 103, 104],
    'product_name': ['Laptop', 'Smartphone', 'Headphones', 'Monitor'],
    'price': [1000.0, 500.0, 150.0, 300.0]
})

print(df)

#df.to_csv('ecommerce_orders.csv', index=False)
with pd.ExcelWriter('ecommerce_orders.xlsx') as writer:
    df.to_excel(writer, sheet_name='Orders', index=False)
    df2.to_excel(writer, sheet_name='Products', index=False)