import datetime
import json
import os
import time
import traceback
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]

PAGE_TITLE = "LoopDrive Studio"
ACCENT = "#19c2b7"
SECONDARY = "#ff7a59"
WARM = "#f5c451"
DEFAULT_SERVICE_URL = "http://localhost:8000"


def configure_page():
    st.set_page_config(
        page_title=PAGE_TITLE,
        page_icon="🎬",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(
        f"""
        <style>
        :root {{
            --bg: #0d1117;
            --panel: #161b22;
            --panel-soft: #11161d;
            --border: #2b3440;
            --text: #f3f6fb;
            --muted: #99a6b5;
            --accent: {ACCENT};
            --secondary: {SECONDARY};
            --warm: {WARM};
        }}
        .stApp {{
            background:
                radial-gradient(circle at top left, rgba(25,194,183,0.08), transparent 22%),
                radial-gradient(circle at top right, rgba(255,122,89,0.08), transparent 22%),
                var(--bg);
            color: var(--text);
        }}
        [data-testid="stSidebar"] {{
            background: #0f141b;
            border-right: 1px solid var(--border);
        }}
        [data-testid="stSidebar"] * {{
            color: var(--text);
        }}
        .block-container {{
            max-width: 1280px;
            padding-top: 1.4rem;
            padding-bottom: 2rem;
        }}
        .hero {{
            padding: 1rem 0 1.25rem 0;
        }}
        .eyebrow {{
            display: inline-block;
            padding: 0.28rem 0.58rem;
            border: 1px solid rgba(25,194,183,0.35);
            border-radius: 8px;
            color: var(--accent);
            background: rgba(25,194,183,0.08);
            font-size: 0.82rem;
            margin-bottom: 0.85rem;
        }}
        .hero h1 {{
            font-size: 2.25rem;
            line-height: 1.08;
            margin: 0 0 0.55rem 0;
            letter-spacing: 0;
            color: var(--text);
        }}
        .hero p {{
            margin: 0;
            max-width: 760px;
            color: var(--muted);
            font-size: 1rem;
            line-height: 1.6;
        }}
        .surface {{
            background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1rem;
        }}
        .section-title {{
            font-size: 0.95rem;
            color: var(--muted);
            margin-bottom: 0.6rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }}
        .bubble-user, .bubble-assistant {{
            border-radius: 8px;
            padding: 0.9rem 1rem;
            margin-bottom: 0.9rem;
            border: 1px solid var(--border);
        }}
        .bubble-user {{
            background: rgba(25,194,183,0.08);
        }}
        .bubble-assistant {{
            background: rgba(255,255,255,0.02);
        }}
        .bubble-label {{
            font-size: 0.78rem;
            color: var(--muted);
            margin-bottom: 0.35rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }}
        .metric-row {{
            display: flex;
            gap: 0.8rem;
            flex-wrap: wrap;
            margin-top: 0.4rem;
            margin-bottom: 0.4rem;
        }}
        .metric-chip {{
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 0.55rem 0.7rem;
            background: rgba(255,255,255,0.02);
            min-width: 150px;
        }}
        .metric-chip strong {{
            display: block;
            color: var(--text);
            font-size: 0.96rem;
            margin-top: 0.15rem;
        }}
        .subtle {{
            color: var(--muted);
            font-size: 0.92rem;
        }}
        .stButton > button {{
            background: var(--text);
            color: #0d1117;
            border: none;
            border-radius: 8px;
            padding: 0.7rem 1rem;
            font-weight: 600;
        }}
        .stDownloadButton > button {{
            border-radius: 8px;
        }}
        .stTextArea textarea,
        .stTextInput input,
        .stSelectbox div[data-baseweb="select"] > div,
        .stMultiSelect div[data-baseweb="select"] > div,
        .stNumberInput input {{
            background: #0f141b !important;
            color: var(--text) !important;
            border-radius: 8px !important;
            border: 1px solid var(--border) !important;
        }}
        [data-testid="stFileUploader"] {{
            background: rgba(255,255,255,0.02);
            border: 1px dashed var(--border);
            border-radius: 8px;
            padding: 0.35rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def ensure_session():
    if "frontend_session_id" not in st.session_state:
        st.session_state.frontend_session_id = uuid.uuid4().hex[:10]
    if "run_history" not in st.session_state:
        st.session_state.run_history = load_run_history()
    if "active_result" not in st.session_state:
        st.session_state.active_result = None
    if "service_url" not in st.session_state:
        st.session_state.service_url = DEFAULT_SERVICE_URL


def history_path() -> Path:
    path = ROOT / "results" / "frontend_history"
    path.mkdir(parents=True, exist_ok=True)
    return path / f"{st.session_state.frontend_session_id}.json"


def load_run_history():
    path = history_path()
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def persist_run_history():
    path = history_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(st.session_state.run_history[-20:], f, ensure_ascii=False, indent=2)


def load_config_options():
    config_dir = ROOT / "config"
    options = sorted(path.name for path in config_dir.glob("*.yaml"))
    preferred = "3dgs-waymo-1137.yaml"
    if preferred in options:
        options.remove(preferred)
        options.insert(0, preferred)
    return options


def render_header():
    left, right = st.columns([1.35, 0.85], gap="large")
    with left:
        st.markdown(
            """
            <div class="hero">
              <div class="eyebrow">Prompt-driven driving video generation</div>
              <h1>Talk to the simulator, then watch the scene come alive.</h1>
              <p>
                Use text, microphone input, reference files, and long-tail controls in one workspace.
                The page records speech in the browser, uploads the audio to the backend service, and
                sends the fused prompt into the generation pipeline.
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right:
        teaser = ROOT / "img" / "teaser.jpg"
        if teaser.exists():
            st.image(str(teaser))


def render_env_summary(check_payload: Dict[str, object]):
    summary = check_payload.get("summary", {}) or {}
    checks = check_payload.get("checks", []) or []
    failed = [item for item in checks if item.get("status") == "fail"]
    warned = [item for item in checks if item.get("status") == "warn"]

    st.markdown(
        f"""
        <div class="metric-row">
          <div class="metric-chip"><span class="subtle">Passed</span><strong>{summary.get('passed', 0)}</strong></div>
          <div class="metric-chip"><span class="subtle">Warnings</span><strong>{summary.get('warnings', 0)}</strong></div>
          <div class="metric-chip"><span class="subtle">Failed</span><strong>{summary.get('failed', 0)}</strong></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if failed:
        st.markdown("**Needs attention**")
        for item in failed[:6]:
            st.caption(f"- {item.get('name')}: {item.get('detail')}")

    if warned:
        st.markdown("**Worth checking**")
        for item in warned[:4]:
            st.caption(f"- {item.get('name')}: {item.get('detail')}")


def fetch_service_health(service_url: str) -> Tuple[bool, Dict[str, object]]:
    try:
        response = requests.get(_join_url(service_url, "/health"), timeout=2.5)
        response.raise_for_status()
        return True, response.json()
    except Exception as exc:
        return False, {"error": str(exc)}


def fetch_system_check(
    service_url: str,
    config_yaml: str,
    generation_backend: str,
    backend_workdir: Optional[str],
    backend_command: Optional[str],
) -> Tuple[bool, Dict[str, object]]:
    try:
        response = requests.get(
            _join_url(service_url, "/system/check"),
            params={
                "config_yaml": config_yaml,
                "generation_backend": generation_backend,
                "backend_workdir": backend_workdir or "",
                "backend_command": backend_command or "",
            },
            timeout=8,
        )
        response.raise_for_status()
        return True, response.json()
    except Exception as exc:
        return False, {"error": str(exc)}


def render_sidebar():
    config_options = load_config_options()
    with st.sidebar:
        st.markdown("## Service")
        service_url = st.text_input("Service URL", value=st.session_state.service_url)
        st.session_state.service_url = service_url.strip() or DEFAULT_SERVICE_URL
        health_ok, health_payload = fetch_service_health(st.session_state.service_url)
        if health_ok:
            st.success(f"Connected to backend · {health_payload.get('task_count', 0)} tracked tasks")
        else:
            st.warning("Backend service is not reachable right now.")
            st.caption(health_payload.get("error", "Unknown connection error"))

        st.markdown("## Run Settings")
        config_name = st.selectbox("Scene config", options=config_options, index=0)
        simulation_name = st.text_input("Simulation name", value="frontend_demo")
        generation_backend = st.selectbox(
            "Generation backend",
            options=["native_chatsim", "magicdrive_v2"],
            index=0,
        )
        backend_command = None
        backend_workdir = None
        if generation_backend == "magicdrive_v2":
            backend_workdir = st.text_input("MagicDrive-V2 workdir", value="")
            backend_command = st.text_input(
                "MagicDrive-V2 command",
                value="python infer.py --prompt {prompt} --output_video {video_path}",
            )

        if health_ok:
            check_ok, check_payload = fetch_system_check(
                st.session_state.service_url,
                config_yaml=f"config/{config_name}",
                generation_backend=generation_backend,
                backend_workdir=backend_workdir,
                backend_command=backend_command,
            )
            if check_ok:
                summary = check_payload.get("summary", {})
                overall = check_payload.get("status", "unknown").upper()
                if check_payload.get("status") == "ok":
                    st.success(
                        f"Environment check: {overall} · "
                        f"{summary.get('passed', 0)} pass / "
                        f"{summary.get('warnings', 0)} warn / "
                        f"{summary.get('failed', 0)} fail"
                    )
                elif check_payload.get("status") == "warn":
                    st.warning(
                        f"Environment check: {overall} · "
                        f"{summary.get('passed', 0)} pass / "
                        f"{summary.get('warnings', 0)} warn / "
                        f"{summary.get('failed', 0)} fail"
                    )
                else:
                    st.error(
                        f"Environment check: {overall} · "
                        f"{summary.get('passed', 0)} pass / "
                        f"{summary.get('warnings', 0)} warn / "
                        f"{summary.get('failed', 0)} fail"
                    )
                with st.expander("Environment details", expanded=False):
                    render_env_summary(check_payload)
                    st.json(check_payload)
            else:
                st.caption(f"Environment check unavailable: {check_payload.get('error', 'unknown error')}")

        st.markdown("## Evaluation")
        closed_loop = st.checkbox("Closed-loop refinement", value=False)
        target_score = st.slider("Target score", min_value=0.1, max_value=1.0, value=0.8, step=0.05)
        max_attempts = st.slider("Max attempts", min_value=1, max_value=5, value=3, step=1)
        evaluator_type = st.selectbox(
            "Evaluator",
            options=["shell", "python", "json", "perception"],
            index=3 if closed_loop else 0,
        )

        st.markdown("## Prompt Conditioning")
        long_tail_tags = st.multiselect(
            "Long-tail controls",
            options=["animal_crossing", "traffic_accident", "heavy_rain", "fog", "snow"],
            default=[],
        )
        weather_strength = st.slider("Weather strength", min_value=0.0, max_value=1.0, value=0.45, step=0.05)
        openai_key = st.text_input("OpenAI API key", type="password", value="")
        st.caption("Leave the key blank to use OPENAI_API_KEY from the backend environment.")

        if st.session_state.run_history:
            st.markdown("## Recent sessions")
            for item in reversed(st.session_state.run_history[-4:]):
                label = f"{item['simulation_name']} · {item['backend_name']}"
                if st.button(label, key=f"history-{item['run_id']}"):
                    st.session_state.active_result = item
                    st.rerun()

    return {
        "service_url": st.session_state.service_url,
        "service_health_ok": health_ok,
        "config_yaml": f"config/{config_name}",
        "config_name": config_name,
        "simulation_name": simulation_name,
        "generation_backend": generation_backend,
        "backend_command": backend_command,
        "backend_workdir": backend_workdir or None,
        "closed_loop": closed_loop,
        "target_score": target_score,
        "max_attempts": max_attempts,
        "evaluator_type": evaluator_type,
        "long_tail_tags": long_tail_tags,
        "weather_strength": weather_strength,
        "openai_key": openai_key.strip(),
    }


def render_inputs():
    st.markdown('<div class="surface">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Instruction Workspace</div>', unsafe_allow_html=True)
    prompt = st.text_area(
        "Prompt",
        value="Add a clear vehicle in front of me and make the motion smooth.",
        height=150,
        placeholder="Describe the scene you want to generate.",
    )

    audio_input_widget = None
    if hasattr(st, "audio_input"):
        audio_input_widget = st.audio_input("Microphone", help="Record a spoken instruction in the browser.")
    else:
        st.info("This Streamlit version does not expose browser microphone capture. Upload an audio file instead.")

    uploaded_audio = st.file_uploader(
        "Audio files",
        type=["wav", "mp3", "m4a", "ogg", "flac"],
        accept_multiple_files=True,
    )
    uploaded_images = st.file_uploader(
        "Reference images",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
    )
    uploaded_videos = st.file_uploader(
        "Reference videos",
        type=["mp4", "mov", "avi", "mkv"],
        accept_multiple_files=True,
    )
    uploaded_sketches = st.file_uploader(
        "Sketches",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)
    return {
        "prompt": prompt,
        "audio_input_widget": audio_input_widget,
        "uploaded_audio": uploaded_audio or [],
        "uploaded_images": uploaded_images or [],
        "uploaded_videos": uploaded_videos or [],
        "uploaded_sketches": uploaded_sketches or [],
    }


def _join_url(base: str, path: str) -> str:
    return base.rstrip("/") + path


def _uploaded_file_tuple(file_obj, fallback_name: str, fallback_mime: str):
    if file_obj is None:
        return None
    raw_name = getattr(file_obj, "name", "") or fallback_name
    mime = getattr(file_obj, "type", None) or fallback_mime
    data = file_obj.getvalue() if hasattr(file_obj, "getvalue") else file_obj.read()
    return raw_name, data, mime


def build_task_payload(sidebar_state, input_state):
    form_data = {
        "prompt": input_state["prompt"].strip(),
        "config_yaml": sidebar_state["config_yaml"],
        "simulation_name": sidebar_state["simulation_name"],
        "generation_backend": sidebar_state["generation_backend"],
        "backend_command": sidebar_state["backend_command"] or "",
        "backend_workdir": sidebar_state["backend_workdir"] or "",
        "closed_loop": str(sidebar_state["closed_loop"]).lower(),
        "target_score": str(sidebar_state["target_score"]),
        "max_attempts": str(sidebar_state["max_attempts"]),
        "evaluator_type": sidebar_state["evaluator_type"],
        "long_tail_scenarios": ",".join(sidebar_state["long_tail_tags"]),
        "weather_strength": str(sidebar_state["weather_strength"]),
        "openai_api_key": sidebar_state["openai_key"],
    }

    files: List[Tuple[str, Tuple[str, bytes, str]]] = []

    if input_state["audio_input_widget"] is not None:
        record = _uploaded_file_tuple(
            input_state["audio_input_widget"],
            fallback_name="microphone_prompt.wav",
            fallback_mime="audio/wav",
        )
        if record:
            files.append(("audio_files", record))

    for audio_file in input_state["uploaded_audio"]:
        record = _uploaded_file_tuple(audio_file, fallback_name="audio.wav", fallback_mime="audio/wav")
        if record:
            files.append(("audio_files", record))
    for image_file in input_state["uploaded_images"]:
        record = _uploaded_file_tuple(image_file, fallback_name="image.png", fallback_mime="image/png")
        if record:
            files.append(("reference_images", record))
    for video_file in input_state["uploaded_videos"]:
        record = _uploaded_file_tuple(video_file, fallback_name="reference.mp4", fallback_mime="video/mp4")
        if record:
            files.append(("reference_videos", record))
    for sketch_file in input_state["uploaded_sketches"]:
        record = _uploaded_file_tuple(sketch_file, fallback_name="sketch.png", fallback_mime="image/png")
        if record:
            files.append(("reference_sketches", record))

    return form_data, files


def submit_task(sidebar_state, input_state):
    form_data, files = build_task_payload(sidebar_state, input_state)
    response = requests.post(
        _join_url(sidebar_state["service_url"], "/tasks"),
        data=form_data,
        files=files,
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def poll_task(service_url: str, task_id: str, status_placeholder, log_placeholder):
    last_logs = ""
    while True:
        response = requests.get(_join_url(service_url, f"/tasks/{task_id}"), timeout=20)
        response.raise_for_status()
        task = response.json()

        phase = task.get("status", "unknown").upper()
        status_placeholder.markdown(
            f"""
            <div class="surface">
              <div class="section-title">Live Status</div>
              <div class="subtle">Task <strong>{task_id}</strong> is currently <strong>{phase}</strong>.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        logs = task.get("logs", "") or ""
        if logs != last_logs:
            log_placeholder.code(logs[-12000:] if logs else "Waiting for backend logs...")
            last_logs = logs

        if task.get("status") in {"succeeded", "failed"}:
            if not logs:
                log_placeholder.code("No backend logs were emitted.")
            return task
        time.sleep(1.0)


def _extract_result_payload(bundle: Dict) -> Tuple[Dict, str, str]:
    if "task" in bundle:
        task = bundle["task"] or {}
        result = task.get("result") or {}
        logs = task.get("logs", "") or ""
        return result, logs, ""
    result = bundle.get("result") or {}
    return result, bundle.get("stdout", "") or "", bundle.get("stderr", "") or ""


def render_result(result_bundle):
    result, stdout_text, stderr_text = _extract_result_payload(result_bundle)
    prompt_conditioning = result.get("prompt_conditioning") or {}
    transcripts = prompt_conditioning.get("audio_transcripts") or []

    st.markdown('<div class="surface">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Run Summary</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="metric-row">
          <div class="metric-chip"><span class="subtle">Mode</span><strong>{result.get("mode", "-")}</strong></div>
          <div class="metric-chip"><span class="subtle">Backend</span><strong>{result_bundle["backend_name"]}</strong></div>
          <div class="metric-chip"><span class="subtle">Config</span><strong>{result_bundle["config_name"]}</strong></div>
          <div class="metric-chip"><span class="subtle">Status</span><strong>{result_bundle.get("status", "done")}</strong></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="bubble-user">
          <div class="bubble-label">User request</div>
          <div>{result.get("prompt_raw") or result_bundle.get("prompt_raw") or "No text prompt provided."}</div>
        </div>
        <div class="bubble-assistant">
          <div class="bubble-label">Fused prompt</div>
          <div>{result.get("prompt_semantic") or result_bundle.get("prompt_semantic") or "No fused prompt available."}</div>
        </div>
        <div class="bubble-assistant">
          <div class="bubble-label">Render prompt</div>
          <div>{result.get("prompt_render") or result_bundle.get("prompt_render") or "No render prompt available."}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if transcripts:
        st.markdown("**Speech transcripts**")
        for item in transcripts:
            st.write(f"- `{Path(item.get('path', '')).name}`: {item.get('text', '')}")

    video_path = result.get("video_path") or result_bundle.get("video_path")
    if video_path and os.path.exists(video_path):
        st.video(video_path)
        with open(video_path, "rb") as f:
            st.download_button(
                label="Download video",
                data=f.read(),
                file_name=Path(video_path).name,
                mime="video/mp4",
            )
    else:
        st.warning("The run completed but no video file was found.")

    with st.expander("Prompt conditioning details"):
        st.json(prompt_conditioning)

    if result.get("mode") == "closed_loop" and result.get("attempt_record"):
        with st.expander("Closed-loop attempt record"):
            st.json(result["attempt_record"])

    with st.expander("Backend logs", expanded=False):
        combined_logs = stdout_text + ("\n" + stderr_text if stderr_text.strip() else "")
        st.code(combined_logs if combined_logs.strip() else "No backend logs were emitted.")
    st.markdown("</div>", unsafe_allow_html=True)


def _history_status_badge(status: str) -> str:
    status = (status or "unknown").lower()
    if status == "succeeded":
        color = "rgba(25,194,183,0.14)"
        border = "rgba(25,194,183,0.35)"
        text = "#7fe3dc"
    elif status == "failed":
        color = "rgba(255,122,89,0.14)"
        border = "rgba(255,122,89,0.35)"
        text = "#ff9e86"
    else:
        color = "rgba(245,196,81,0.12)"
        border = "rgba(245,196,81,0.35)"
        text = "#f5c451"
    return (
        f"display:inline-block;padding:0.22rem 0.5rem;border-radius:8px;"
        f"background:{color};border:1px solid {border};color:{text};font-size:0.78rem;"
    )


def _render_history_card(item: Dict, index: int):
    result = (item.get("task") or {}).get("result") or {}
    preview_prompt = item.get("prompt_raw") or "No prompt recorded."
    preview_prompt = preview_prompt[:120] + ("..." if len(preview_prompt) > 120 else "")
    timestamp = item.get("timestamp", "")
    status = item.get("status", "unknown")
    mode = result.get("mode", "-")
    video_path = item.get("video_path")

    st.markdown(
        f"""
        <div class="surface" style="min-height: 168px;">
          <div style="display:flex;justify-content:space-between;gap:0.6rem;align-items:flex-start;">
            <div>
              <div style="font-weight:600;color:var(--text);margin-bottom:0.2rem;">{item.get('simulation_name', 'Run')}</div>
              <div class="subtle" style="font-size:0.82rem;">{timestamp}</div>
            </div>
            <div style="{_history_status_badge(status)}">{status}</div>
          </div>
          <div style="margin-top:0.75rem;color:var(--text);line-height:1.5;">{preview_prompt}</div>
          <div style="margin-top:0.85rem;display:flex;gap:0.45rem;flex-wrap:wrap;">
            <span style="{_history_status_badge(item.get('backend_name', 'backend'))}">{item.get('backend_name', '-')}</span>
            <span style="{_history_status_badge(mode)}">{mode}</span>
            <span style="{_history_status_badge(item.get('config_name', 'config'))}">{item.get('config_name', '-')}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    button_cols = st.columns([1, 1])
    with button_cols[0]:
        if st.button("Open", key=f"open-history-{item['run_id']}"):
            st.session_state.active_result = item
            st.rerun()
    with button_cols[1]:
        if video_path and os.path.exists(video_path):
            with open(video_path, "rb") as f:
                st.download_button(
                    "Video",
                    data=f.read(),
                    file_name=Path(video_path).name,
                    mime="video/mp4",
                    key=f"download-history-{item['run_id']}",
                    use_column_width=True,
                )
        else:
            st.button("No video", key=f"no-video-{index}", disabled=True)


def render_history():
    if not st.session_state.run_history:
        return
    st.markdown("### Recent runs")
    st.caption("A quick gallery of the latest generations, with one-click reopen and download.")
    recent_items = list(reversed(st.session_state.run_history[-6:]))
    columns = st.columns(3, gap="large")
    for index, item in enumerate(recent_items):
        with columns[index % 3]:
            _render_history_card(item, index)


def make_history_entry(task: Dict, sidebar_state: Dict):
    result = task.get("result") or {}
    return {
        "run_id": uuid.uuid4().hex,
        "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
        "task": task,
        "backend_name": sidebar_state["generation_backend"],
        "config_name": sidebar_state["config_name"],
        "simulation_name": sidebar_state["simulation_name"],
        "prompt_raw": result.get("prompt_raw") or task.get("request", {}).get("prompt"),
        "prompt_semantic": result.get("prompt_semantic"),
        "prompt_render": result.get("prompt_render"),
        "video_path": result.get("video_path") or (task.get("artifacts") or {}).get("video_path"),
        "status": task.get("status"),
    }


def main():
    configure_page()
    ensure_session()
    render_header()
    sidebar_state = render_sidebar()
    input_state = render_inputs()

    col_action, col_note = st.columns([0.26, 0.74], gap="large")
    with col_action:
        run_clicked = st.button("Generate video", type="primary")
    with col_note:
        st.caption("Browser microphone capture is uploaded as a WAV-style audio input so the backend can transcribe it without an extra conversion hop.")

    if st.session_state.active_result:
        st.markdown("### Selected run")
        render_result(st.session_state.active_result)

    if run_clicked:
        if not sidebar_state["service_health_ok"]:
            st.error("The backend service is not reachable. Start the FastAPI service first, then try again.")
            return
        if not input_state["prompt"].strip() and not input_state["uploaded_audio"] and input_state["audio_input_widget"] is None:
            st.error("Give the system either a text prompt, a microphone recording, or an uploaded audio file.")
            return
        if sidebar_state["generation_backend"] == "magicdrive_v2" and not sidebar_state["backend_command"]:
            st.error("MagicDrive-V2 needs a backend command before it can run.")
            return

        try:
            status_placeholder = st.empty()
            log_placeholder = st.empty()
            submitted_task = submit_task(sidebar_state, input_state)
            task = poll_task(
                service_url=sidebar_state["service_url"],
                task_id=submitted_task["task_id"],
                status_placeholder=status_placeholder,
                log_placeholder=log_placeholder,
            )
            if task.get("status") == "failed":
                raise RuntimeError(task.get("error") or task.get("traceback") or "The backend task failed.")
            bundle = make_history_entry(task, sidebar_state)
            st.session_state.run_history.append(bundle)
            persist_run_history()
            st.session_state.active_result = bundle
            status_placeholder.empty()
            log_placeholder.empty()
            render_result(bundle)
        except Exception as exc:
            st.error("The generation run failed.")
            st.code("".join(traceback.format_exception(exc)))

    render_history()


if __name__ == "__main__":
    main()
