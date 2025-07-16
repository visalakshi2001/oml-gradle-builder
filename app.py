import os
import shutil
import subprocess
from pathlib import Path
from fastapi import FastAPI, UploadFile, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates


app = FastAPI()

# Path to your project root (adjust if app.py lives elsewhere)
PROJECT_ROOT = Path(__file__).parent.resolve()
BUNDLE_PATH = PROJECT_ROOT / "src" / "oml" / "example.com" / "project" / "bundle.oml"
BUILD_DIR   = PROJECT_ROOT / "build"
LOG_DIR     = BUILD_DIR / "logs"


@app.get("/")
def read_root():
    return {"message": "Welcome to the OML Build Service! POST request at /build with a .oml file to build. Files can be seen at /browse"}

@app.post("/buildomlfile")
async def build(bundle: UploadFile, request: Request):
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
    
    browse_url = str(request.base_url) + "browse"

    # 7. Return JSON with status, code, and browse URL
    return JSONResponse({
        "exit_code": proc.returncode,
        "log_path": str(log_file.relative_to(PROJECT_ROOT)),
        "browse_url": browse_url
    })


# app.mount("/browse", StaticFiles(directory=PROJECT_ROOT, follow_symlink=True), name="browse")
templates = Jinja2Templates(directory=PROJECT_ROOT / "templates")

@app.get("/browse/", response_class=HTMLResponse)
@app.get("/browse", response_class=HTMLResponse)
def browse(request: Request):
    request_url = request.url._url
    if request_url.endswith("/"):
        request_url = request_url[:-1]

    files = os.listdir("./")
    files = [f'{f}/' if os.path.isdir(f) else f for f in files]
    files_paths = [f'{request_url}/{f}' for f in files]
    return templates.TemplateResponse(
        "index.html", {"request": request, "cur_dir": "", "files_paths": files_paths, "files": files, "enumerate": enumerate}
    )

# Also handle all the subdirectories under /browse using path parameters
@app.get("/browse/{subpath:path}")
def browse_subpath(request: Request, subpath: str):
    request_url = request.url._url
    print("Request URL:", request_url)
    
    if request_url.endswith("/"):
        print("Yes")
        request_url = request_url[:-1]
        print("Updated Request URL:", request_url)
    else:
        print("No")
        

    full_path = PROJECT_ROOT / subpath
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="Path not found")
        
    if full_path.is_dir():
        files = os.listdir(full_path)
        print(files)
        print(subpath)
        files = [f'{f}/' if os.path.isdir(full_path / f) else f'{f}' for f in files]
        files_paths = [f'{request_url}/{f}' for f in files]
        print(files_paths)
        return templates.TemplateResponse(
            "index.html", {"request": request, "cur_dir": subpath, "files_paths": files_paths, "files": files, "enumerate": enumerate}
        )
    else:
        # If it's a file, just return the file path
        return FileResponse(full_path)

