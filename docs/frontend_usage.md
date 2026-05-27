# LoopDrive Frontend

The project now includes a Streamlit frontend for prompt-driven driving-video generation.
The page talks to the FastAPI backend service instead of running the heavy pipeline inline.

## Features

- text prompt input
- browser microphone capture
- audio file upload
- reference image, video, and sketch upload
- optional long-tail scenario control
- backend health check
- environment check for the selected scene/backend
- native ChatSim or MagicDrive-V2 backend selection
- rendered video preview and download

The browser microphone path uploads the recording to the backend service as an audio file and then reuses the existing audio-to-text prompt-conditioning flow.

## Run

Start the backend service first:

```bash
uvicorn service.api:app --host 0.0.0.0 --port 8000
```

Then, in a second terminal, start Streamlit from the project root:

```bash
streamlit run frontend/app.py
```

By default, the page will be available at:

```text
http://localhost:8501
```

## Notes

- The frontend expects the FastAPI service to be reachable at `http://localhost:8000` by default. You can change this from the sidebar.
- If you deploy on a remote server, browser microphone capture still works because the recording happens in the browser and then uploads to the backend service.
- If you use `magicdrive_v2`, provide a valid backend command and working directory in the sidebar.
