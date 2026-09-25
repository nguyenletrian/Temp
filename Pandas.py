import sys

path = r"C:\Users\an.nguyen_g\MayaPackages"

if path not in sys.path:
    sys.path.insert(0, path)

import pandas as pd
import numpy as np

"""
s1 = pd.Series([10,20,30]) # Series có thêm cột và data type
print(s1)
print("index: ",s1.index)
print("value: ",s1.values)



# TẠO DATA FRAME TỪ DICTIONARY
data = {
    "Product":["Laptop","Phone","Tablet"],
    "Price":[1000,800,500],
    "Quantity":[2,3,1]
}
df = pd.DataFrame(data)
print(df)


# TẠO DATA FRAME TỪ LIST
data = [
    {'Name':'Alice','Age':25},
    {'Name':'Bob','Age':3}
]
df = pd.DataFrame(data)
print(df)


# CSV Comma seperated value
# DOC DU LIEU TU FILE CSV
df = pd.read_csv("D:\code\PythonClass\data.csv")
print(df)


df.head(n) -> Show n dòng đầu tiên
df.tail(n) -> Show n dòng cuối cùng
df.shape() -> trả về cột và dòng


# Hiển thị 3 dòng dầu tiên
print(df.head(3))
# Hiển thị 3 dòng cuối cùng
print(df.tail(3))
print("Hiện thị kích thước:")
print(df.shape)
# Xem thông tin của dữ liệu
print(df.info())
print("Thống kê cơ bản của df")
print(df.describe())
# std đã là độ lệch chuẩn
"""


df = pd.read_csv("D:\code\PythonClass\data.csv")
df["Subtotal"] = df["Price"] * df["Quantity"]

"""
print(df)
# Kiểm tra missing value
print(df.isnull())

print("Đếm số lượng missing của từng cột")
print(df.isnull().sum())

dfDrop = df.dropna() # Xóa toàn bộ những dòng có dữ liệu có missing


# Fill missing valu
dfFill = df.copy()
dfFill["Price"] = dfFill["Price"].fillna(df["Price"].mean()) # mean = Trung bìn, min(), max()
dfFill["City"] = dfFill["City"].fillna("Unknown")
print(dfFill)





# Lấy theo cột
print(df["City"])
print(df[["Product","Price"]])
# Lấy dữ liệu theo lable hoặc index
data = {
    "Product":["Laptop","Phone","Tablet"],
    "Price":[1000,800,500],
    "Quantity":[2,3,1]
}
df_loc = pd.DataFrame(data,index=["A","B","C"])
print(df_loc)

# Hien thi dòng 'B'
print(df_loc.loc["B"])
# Hien thi dòng từ "A"->"C"
print(df_loc.loc["A":"C"])
# Thêm 1 dòng dữ liệu
df_loc.loc["D"] = {"Product":"Tablet","Price":500}
print(df_loc)

#Thêm 1 dòng dữ liệu theo index number
df_loc.loc[len(df_loc)] = {"Product":"Mouse","Price":20}
print(df_loc)

#iloc là theo index
# Lấy dòng thứ 2
#print(df.iloc[1])


# chon dong index 0 va dong index 2
print(df.iloc[[0,2]])

# chọn 1 cell
print(df.iloc[0,2])

# Chọn nhiều dòng
print(df.iloc[0:2])


#### BOOLEAN INDEXING lọc dòng dữ liệu
# Lọc sản phẩm có giá >= 800
print(df[df["Price"]>=800])
print(df[(df["Price"]>=50) & (df["Price"]<=1500)])


### groupby (nhóm lại các dòng dựa trên cột) kết hợp với sum(), mean(), count()
#dataframe.groupby(by=['age','output'],axis=0,sort=True,dropna=True).count()

# City nào có doanh thu nhiều nhất
dfClean =  df.drop_duplicates()
print(dfClean.groupby("City")["Subtotal"].sum())

# Tính tổng số lượng đã bán và tổng doanh thủ
result = dfClean[["Quantity","Subtotal"]].sum() #mặc định là axis = 0 theo cột, tính trung bình điểm sẽ dùng axis = 1
print(result)

# Sắp xếp danh sách đơn hàng theo doanh thu từ cao xuống thấp

dfSorted = dfClean.sort_values(by="Subtotal")
print(dfSorted)
dfSorted = dfClean.sort_values(by="Subtotal",ascending=False)
print(dfSorted)

# Hiển thị 3 đơn hàng có doanh thu cao nhất
print(dfSorted.head(3))
"""

#Merge
#pd.merge(left_df,right_df,on="key_column",how="join_type") #mặc định là innerjoin
#inner joint: giao 2 df
#left join: toàn bộ
#right join:
#outer join

#Tạo bảng customer
customer_data = {
    "CustomerID":["C001","C002","C003","C004"],
    "CustomerName":["Tuan","Khoa","Nhi","Diem"],
}
df_customer =pd.DataFrame(customer_data)

print(df_customer)
merge_df = pd.merge(df,df_customer,on="CustomerID")
print(merge_df)
print(merge_df["City"])


df1 = pd.DataFrame({
    "ID":[1,2,3],
    "Category":['Laptop','Phone','Mouse']
})
df2 = pd.DataFrame({
    "ID":[2,3,4],
    "Product":["Cat1","Cat2","Cat3"]
})
inner_join = pd.merge(df1,df2,on="ID",how="inner")
print(inner_join)
left_join = pd.merge(df1,df2,on="ID",how="left")
print(left_join)
right_join = pd.merge(df1,df2,on="ID",how="right")
print(right_join)
outer_join = pd.merge(df1,df2,on="ID",how="outer")
print(outer_join)