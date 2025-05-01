import os
import sys
import uvicorn

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    # Use the correct import path based on your project structure
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
    