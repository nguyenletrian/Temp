from abc import ABC, abstractmethod

class Product(ABC):
    product_id = None
    name = None
    price = None

    @abstractmethod
    def addProduct(self):
        pass

class ElectronicProduct(Product):
    brand = None
    warranty = None
            
    def addProduct(self,product_id,name,price):
        self.product_id = product_id
        self.name = name
        self.price = price
        print(self.product_id,self.name,self.price)

class ClothingProduct(Product):
    size = None
    material = None
    
    def addProduct(self,product_id,name,price):
        self.product_id = product_id
        self.name = name
        self.price = price
        print(self.product_id,self.name,self.price)
        
class ProductManager():
    products = {}
    def newInput(self,data):
        block = data["block"]
        formats = data["format"]
        function = data["function"]        
        inputData = None 
        inputData = input(data["text"])
        if inputData == "":
            return()        

        inputBlocks = inputData.split(";") 
        if len(inputBlocks)!= block:
            print("So luong truong nhap vao khong dung")
        inputClears = []
        for inputBlock in inputBlocks:
            try:
                inputClears.append(int(inputBlock))
                continue
            except:pass
            try:
                inputClears.append(float(inputBlock))
                continue
            except:pass
            try:
                inputClears.append(str(inputBlock))
                continue
            except:pass
        for i in range(len(inputClears)):
            if type(inputClears[i]).__name__ != formats[i]:
                print(f"Du lieu thu {inputClears[i]} phai la {formats[i]}")
                if function:
                    function()
                break;
        return(inputClears)
                
        
    def addProduct(self):
        addData = self.newInput({
            "text":"Vui long nhap thong tin san pham, cach nhau bang dau ';', vi du SP01;Ten san pham;1000000",
            "block":3,
            "format":["str","str","int"],
            "function":self.addProduct,
        })
        if addData[0] not in self.products:
            self.products[addData[0]] = {"name":addData[1],"price":addData[2]}
        else:
            print("Da ton tai ma san pham")

    def showProducts(self):
        for key,val in self.products.items():
            print(f"Ma san pham {key}: Ten {val['name]}, gia tien {val['price']}")

    def updateProduct(self):
        updateData = self.newInput({
            "text":"Vui long nhap thong tin can cap nhat, cach nhau bang dau ';', vi du SP01;Ten san pham;1000000",
            "block":3,
            "format":["str","str","int"],
            "function":self.updateProduct,
        })
        if addData[0] in self.products:
            self.products[addData[0]] = {"name":addData[1],"price":addData[2]}
        else:
            print("Khong ton tai ma san pham")
            
    def deleteProduct(self):
        deleteData = self.newInput({
            "text":"Vui long nhap ma san pham can xoa!",
            "block":1,
            "format":["str"],
            "function":self.deleteProduct,
        })
        if deleteData[0] in self.products:
            confirmData = self.newInput({
                "text":"Xac nhan xoa!? Y/N",
                "block":1,
                "format":["str"],
            })
            if confirmData.lower() == "y":        
                del self.products[deleteData[0]]
        else:
            print("Ma san pham khong ton tai")
        
        
manager = ProductManager()