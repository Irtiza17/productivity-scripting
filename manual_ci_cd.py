from fabric import task, Connection
import os
from invoke import Responder
VPS_HOST = ""
VPS_USER = ""
VPS_PASSWORD = ""  # ⚠️ Warning: Don't commit this to version control
REMOTE_DIR = ""
VENV_PIP = ""
SERVICE_NAME = ""

@task
def deploy(c):

    conn = Connection(
        host=VPS_HOST,
        user=VPS_USER,
        connect_kwargs={"password": VPS_PASSWORD}
    )

    # Step 0: Run the build script
    print("Running pre_build.py to obfuscate and build the wheel...")
    result = os.system("python pre_build.py")
    if result != 0:
        print("pre_build.py failed. Aborting deployment.")
        return
    
    # Set up sudo responder
    sudo_pass = Responder(
        pattern=r"\[sudo\] password:",
        response="" + "\n",
    )

    # Step 1: Find the wheel file
    dist_dir = "dist"
    wheel_file = next((f for f in os.listdir(dist_dir) if f.endswith(".whl")), None)
    if not wheel_file:
        print("No wheel file found.")
        return

    local_path = os.path.join(dist_dir, wheel_file)
    remote_path = f"{REMOTE_DIR}/{wheel_file}"

    # Step 2: Copy the file using SCP (put)
    print(f"Uploading {local_path} to {remote_path}")
    conn.put(local_path, remote_path)

    # Step 3: Install the wheel and restart service
    print("Installing wheel and restarting service...")
    conn.run(f"{VENV_PIP} install --force-reinstall {remote_path}")
    # conn.sudo(f"systemctl restart {SERVICE_NAME}")
     # Restart with sudo and responder
    conn.sudo(f"systemctl restart {SERVICE_NAME}", watchers=[sudo_pass])