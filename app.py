import os
import shutil
import subprocess
from pathlib import Path
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

app = FastAPI()

# Path to your project root (adjust if app.py lives elsewhere)
PROJECT_ROOT = Path(__file__).parent.resolve()
BUNDLE_PATH = PROJECT_ROOT / "src" / "oml" / "example.com" / "project" / "bundle.oml"
BUILD_DIR   = PROJECT_ROOT / "build"
LOG_DIR     = BUILD_DIR / "logs"

@app.get("/")
def read_root():
    return {"message": "Welcome to the OML Build Service! POST request at /build with a .oml file to build. Files can be seen at /browse"}

@app.post("/build")
async def build(bundle: UploadFile):
    print("Received bundle upload:", bundle.filename)
    print(bundle)
    # 1. Validate upload
    if not bundle.filename.endswith(".oml"):
        raise HTTPException(status_code=400, detail="Must upload a .oml file")
    
    # 2. Ensure directories exist
    BUNDLE_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    # 3. Save uploaded bundle.oml (overwrite any existing)
    with BUNDLE_PATH.open("wb") as f_out:
        contents = await bundle.read()
        f_out.write(contents)
    
    # 4. Run Gradle build
    # Determine which Gradle wrapper to invoke
    if os.name == "nt":  # Windows
        wrapper = "gradlew.bat"
        # On Windows it’s often simpler to run under shell so the .bat is recognized
        shell_flag = True
    else:
        wrapper = "./gradlew"
        shell_flag = False
    cmd = [wrapper, "clean", "downloadDependencies", "build"]
    proc = subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        shell=shell_flag
    )
    
    
    # 5. Persist logs
    log_file = LOG_DIR / f"buildlogs_code{proc.returncode}.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with log_file.open("w") as log_file_f:
        log_file_f.write(proc.stdout)
        
    # 6. Prepare response URL
    #    We’ll serve BUILD_DIR on port 8080 (see next steps),
    #    so we just point clients there under /browse/
    host = os.getenv("HOSTNAME", "localhost")
    port = os.getenv("PORT", "8080")
    browse_url = f"http://{host}:{port}"

    # 7. Return JSON with status, code, and browse URL
    return JSONResponse({
        "exit_code": proc.returncode,
        "log_path": str(log_file.relative_to(PROJECT_ROOT)),
        "browse_url": browse_url
    })

# can try https://stackoverflow.com/questions/71276790/list-files-from-a-static-folder-in-fastapi