from pyngrok import ngrok
import time

def start_ngrok():
    try:
        # Open a HTTP tunnel on port 8000
        public_url = ngrok.connect(8000)
        print("NGROK_URL___ " + public_url.public_url + " ___")
        print("Running ngrok. Keep this terminal open...")
        while True:
            time.sleep(1)
    except Exception as e:
        print(f"Error starting ngrok: {e}")

if __name__ == "__main__":
    start_ngrok()
