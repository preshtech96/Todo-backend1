from fastapi import FastAPI,status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from fastapi import HTTPException
from Schema import User,Login,Secret,Todo
from private import hash_password
import os
from dotenv import load_dotenv




app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
    )


client = AsyncIOMotorClient(os.getenv("MONGO_URI"))
db = client["mydatabase"]
collection = db["mycollection"]
userdata = db["Todolist"]

@app.post("/Register")
async def register_user(user: User):
    try:
        user=dict(user) 
        dataexists = await collection.find_one({"email": user["email"]})
        if dataexists:
            return HTTPException(status_code=400, detail="Email already exists")
        if user["password"] =="" or user["confirmPassword"] == "":
            return HTTPException(status_code=400, detail="Password and Confirm Password cannot be empty")
        if user["password"] != user["confirmPassword"] :
            return HTTPException(status_code=400, detail="Passwords do not match")
        if not user["secretpin"]:
            return HTTPException(status_code=400, detail="Secret PIN is required")
        user["password"] = hash_password(user["password"])
        user["confirmPassword"] = hash_password(user["confirmPassword"])
        user["secretpin"] = hash_password(user["secretpin"])
        user = await collection.insert_one(user)
        return JSONResponse({"Messge":"Account Created Successfully","status":status.HTTP_201_CREATED})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/Login")
async def get_user(user: Login):
    try:
        data=dict(user)
        user = await collection.find_one({"email": data["email"] })
        if user:
            if user["password"] == hash_password(data["password"]):
                del user["password"]
                del user["confirmPassword"]
                user["_id"] = str(user["_id"])
                return JSONResponse({"Message": "Login Successful", "status": status.HTTP_200_OK, "user1": user})
            else:
                return HTTPException(status_code=400, detail="Invalid Password")
        else:
            return HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e)) 



@app.post("/Secret")
async def get_secret(pin: Secret):
      data = dict(pin)
      try:
        user = await collection.find_one({"_id": ObjectId(data["id"])})
        user["_id"] = str(user["_id"]) 
        print(data)
        if user:
            if user["secretpin"] == hash_password(data["secretpin"]):
                del user["secretpin"]
                return JSONResponse({"Message": "Secret PIN Accepted", "status": status.HTTP_200_OK})
            else:
                return HTTPException(status_code=400, detail="Invalid Secret PIN")
        else:
            return HTTPException(status_code=404, detail="User not found")
      except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
      


@app.post("/Todolist")
async def Todo(todo: Todo):
    todo = dict(todo)
    
    try:
        if todo["userId"]:
            user=await collection.find_one({"_id": ObjectId(todo["userId"])})
            if not user:
                return JSONResponse({"Message":"User Not Found","status":status.HTTP_404_NOT_FOUND})
            else:
                data=await userdata.insert_one(todo)
                print(data.inserted_id)
                if "todo" not in user:
                    await collection.update_one({"_id": ObjectId(todo["userId"])}, {"$set": {"todo": [str(data.inserted_id)]}})
                else:
                    await collection.update_one({"_id": ObjectId(todo["userId"])}, {"$push": {"todo": str(data.inserted_id)}})
    except:
        return JSONResponse({"Message":"Error","status":status.HTTP_500_INTERNAL_SERVER_ERROR})


@app.get("/Todolist/{userId}")
async def GetTodo(userId: str):
    try:
        data = await collection.find_one({"_id": ObjectId(userId)})
        if not data:
            return JSONResponse(
                {"message": "User Not Found", "status": status.HTTP_404_NOT_FOUND}
            )

        todo_list = []
        if "todo" in data:
            for todo_id in data["todo"]:
                todo_data = await userdata.find_one({"_id": ObjectId(todo_id)})
                if todo_data:
                    todo_data["_id"] = str(todo_data["_id"])
                    todo_list.append(todo_data)

        return JSONResponse({
            "message": "Todo List Fetched",
            "status": status.HTTP_200_OK,
            "payload": todo_list
        })

    except Exception as e:
        return JSONResponse(
            {
                "message": "Error retrieving todos",
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": str(e)
            }
        )
    
    

@app.delete("/Todolist/{todoId}")
async def DeleteTodo(todoId: str):
    try:
        result = await userdata.delete_one({"_id": ObjectId(todoId)})
        await collection.update_many({}, {"$pull": {"todo": todoId}})
        if result.deleted_count == 0:
            return JSONResponse(
                {"Message": "Todo not found", "status": status.HTTP_404_NOT_FOUND},
                status_code=status.HTTP_404_NOT_FOUND
            )
        return JSONResponse(
            {"Message": "Todo Deleted Successfully", "status": status.HTTP_200_OK},
            status_code=status.HTTP_200_OK
        )
    except Exception as e:
        print("Error deleting todo:", e)
        return JSONResponse(
            {"Message": "Internal Server Error", "status": status.HTTP_500_INTERNAL_SERVER_ERROR},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    
@app.put("/todo/status/{todoId}/{status1}")
async def UpdateTodoStatus(todoId: str, status1: bool):
    try:
        await userdata.update_one({"_id": ObjectId(todoId)}, {"$set": {"status": status1}})
        return JSONResponse({"Message": "Todo Status Updated Successfully", "status": status.HTTP_200_OK})
    except:
        return JSONResponse({"Message": "Error", "status": status.HTTP_500_INTERNAL_SERVER_ERROR})






@app.delete("/DeleteAccount/{userId}")
async def DeleteAccount(userId: str):
    try:
        user = await collection.find_one({"_id": ObjectId(userId)})
        if not user:
            return JSONResponse(
                {"Message": "User Not Found", "status": status.HTTP_404_NOT_FOUND},
                status_code=status.HTTP_404_NOT_FOUND
            )

        await collection.delete_one({"_id": ObjectId(userId)})
        await userdata.delete_many({"userId": userId})  

        return JSONResponse(
            {"Message": "Account Deleted Successfully", "status": status.HTTP_200_OK},
            status_code=status.HTTP_200_OK
        )
    except Exception as e:
        return JSONResponse(
            {
                "Message": "Error Deleting Account",
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": str(e)
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
