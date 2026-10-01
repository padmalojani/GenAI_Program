from fastapi import FastAPI

# Initialize the FastAPI application instance
app = FastAPI()

# 1. Root endpoint returning a welcome JSON response
@app.get("/")
def read_root():
    return {"message": "Welcome to my FastAPI application!"}

# 2. Parameterized endpoint taking a path parameter
@app.get("/greet/{name}")
def greet_user(name: str):
    return {"message": f"Hello, {name}!", "input_received": name}
