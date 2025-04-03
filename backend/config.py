# uvicorn_config.py
import uvicorn

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)
    # Use the following command to run the server with the specified host and port: python uvicorn-config.py
