"""
# NUMPY
# Thư viện để tính toán
N-D array: là 1 cách tính toán có thể thực hiện được nhiều chiều
1 chiều là vecotr
2 chiều là matrix

Tại sao phải sự dụng numpy
speed: các toán tử được thực thi được ngôn ngữ C, nhanh hơn rất nhiều do với vòng lăp python
vector hóa các phép tính -> ko dùng vòng lặp
memory: lưu dữ liệu hiệu quả hơn đặc biệt với dữ liệu lớn


ndarray = N-Dimentional aray
tất cả các phần tử trong ndarray đều cùng kiểu dữ liệu


.shape: Thể hiện bao nhiêu dòng và bao nhiêu cột #(2 , 3)
.size: số lượng phần tử trong array


import numpy as np
arr = np.array([1.0,2.0],[3.0,4.0],dtype=np.float32)
print(f"Shape: {arr.shape}")
print(f"Dimentions: {arr.ndim}")
print(f"Data Type: {arr.dtype}")
shape: (2,2)
dimension:2
data type: float32

list_1d = [1,2,3]
arr_1d

.zeros(shape) => khởi tạo 1 ma trận với giá trị bằng 0
np.zeros(2,3) = 2 dòng 3 cột
.ones(4)
.full((),7)

.arange(0,10,2) -> range là từ 0-9, bước nhảy là 2
.linspace(0,1,5) -> tạo ra 1 list có 5 số cách đều nhau từ 0-1
"""


#### DEMO #####
#pip install numpy
import numpy as np

#array 1 chiều
students = np.array(["An","Binh","Nhi","Tuan","Khoa"])
subjects = np.array(["Python","Math","Machine Learning","AI"])

# array 2 chiều
scores = np.array([
	[8,9,5,7],
	[6,5,7,5],
	[8,9,5,9],
	[10,7,5,8],
	[7,8,6,9]
])
"""
print(students)
print(subjects)
print(scores)

# Attribute: shape, dtype, size, ndim

# Hiển thị số dòng và số cột:
print("Row and Column: ",scores.shape)

# Số chiều của mảng
print("Number of dimension: ",scores.ndim)

# Tổng số phần tử:
print("Number of elements:",scores.size)

# Kiểu dữ liệu của các phần tử
print("Data Type: ",scores.dtype)
"""

"""
### INDEXING
import numpy as np
arr_1d = np.array([10,20,30,40])
arr_2d = np.array([[1,2],[3,4]])


import numpy as np
arr =np.array([0,1,2,3,4,5,6,])
print(f"arr[1:4]: {arr[1:4]}") #[1 2 3]
print(f"arr[::2]: {arr[::2]}") #[0 2 4 6]
#arr[1:4]: [1 2 3]
#arr[::2]: [0 2 4 6]

import numpy as np
matrix = np.array([[1,2,3],[4,5,6],[7,8,9]])
matrix[0:2,:] #[[1 2 3][4 5 6]]
matrix[:,1] #[2 5 8]
"""

# Lấy điểm python của ân
scores[0,0]

# Lấy toàn bộ điểm của anh tuấn
scores[3]

# Lấy điểm AI của Nhi
scores[2,3] #hoặc scores[2,-1]

# Lấy toàn bộ điểm của sinh viên cuối cùng
scores[4] #hoặc scores[-1]


"""
# Hiển thị điểm của 3 sinh viên đầu tiên
print(scores[:3,:]) # [0:3] , [:3]

# Hiển thị điểm của 2 môn đầu tiên của tất cả sinh viên
print(scores[:,:2])

# Hiển thị điểm python và AI của tất cả sinh viên
print(scores[:,0:-2])

#[-3:-1]
"""


# BOOLEAN INDEXING
# Hiển thị sinh viên có điểm Python nhỏ hơn 8
python_scores = scores[:,0]
print("Diem python < 8: \n",python_scores[python_scores<8])
print("SV có điểm python nhỏ hơn 8:",students[python_scores<8])

#Reshaping lại mảng:


#reshape(): Chuyển mảng 1 chiều thành 2 chiều
#python_reshape = python_scores.reshape(2,3)

#flattern(): Chuyển trả ngược lại 2 chiều thành 1 chiều
#python_flatten = python_reshape.flatten()

import numpy as np
matrix = np.array([
	[1,2,3],
	[4,5,6]
])
print("matrix: ",matrix)
print("matrixT: ",matrix.T)

# .copy() Tạo ra 1 mảng ko ảnh hưởng đến dữ liệu cũ
# view

# +,*,**,/,-
# .sqrt() -> Căn bậc 2
# .exp() ->
#.sum()
#.mean() = trung bình
#.min()
#.max()
#.std() độ lệch chuẩn

### ALONG AXES:
#np.sum(matrix,axis=0)
#np.sum(matrix,axis=1)


#Tinh điểm trung bình của từng sinh viên
student_avg = np.mean(scores,axis=1)
print("student_avg",student_avg)
for i in range(len(students)):
	print(students[i],":",student_avg[i])


# diem cao nhat của toan bộ
print("Diem cao nhat: ",np.max(scores))
# Điểm thấp nhất của toàn bộ
print("Điểm thấp nhất: ",np.min(scores))
# Điểm cao nhất của từng môn học
print("Điểm cao nhất của từng môn học:",np.max(scores,axis=0))


### Broadcasting: Mở rộng thêm dữ liệu
# Do đi học đầy đủ nên mỗi người +1
bonus = 1
new_scores = scores + bonus
#print("Điểm sau khi cộng: \n"+new_scores)

### ĐẠI SỐ TUYẾN TÍNH CƠ BẢN
"""
số cột của ma trận thứ nhất = số dòng của ma trận thứ 2
(m,n) x (n,p) => (m,p)
dòng thứ 1 của ma trận 1 * cột 1 của ma trận 2
[1,2][3,4] x [5,6][7,8]
1 x 5 + 2 x 7 
Nhân ma trận
"""

# np.dot() hoặc @: nhan ma tran
#Tinh điểm tổng kết có trọng số
"""
Python = 20%
Math = 20%
ML = 35%
AI = 25%
"""
w = np.array([0.2,0.2,0.35,0.25])
final_scores = scores @ w
print("final_scores: ",final_scores)

### np.concatenate((arr1,att2),axis=) join array not add
### np.vstack((arr1,arr2))
### np.hstack

np.random.seed(42)
np.random.rand(d0,d1) #(2,2) trả về 1 mản g
np.random.randint(low,high,size)

# random(): mô phỏng dữ liệu
np.random.seed(10)
print("Random 0-1: ",np.random.rand()) #[0,1)
print("Random (2x2):n/",np.random.rand(2,2))
print("Random (0,9) lay 3 so:" np.random.randint(0,10,3)) # lấy ngẫu nhiên 3 số từ 0-9

### Fancy indexing: Advanced selection
data = np.array([10,20,30,40,50,60])
indices = np.array([0,3,5]) #10,40,60
matrix = np.array([[1,2,3],[4,5,6],[7,8,9]])
matrix[[0,2],[1,3]] # 0,2 là dòng, 1.3 là cột

scores[:,[1,3]] # tất cả dòng, cột 1,3

np.save()
np.savetxt()
np.load()
np.loadtxt()

# Luu và doc file array
np.save("students.npy",students)
# doc du lieu tu file binary
students_load = np.load("students.npy")
print("students_load: ",students_load)
#Luu du lieu file text
np.savetxt("scores.txt",scores,delimiter=",")
scores_load = np.loadtxt("scores.txt")
print("scores_load:",scores_load,delimiter=",")
