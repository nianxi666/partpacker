import subprocess
import modal

# --- 配置 ---
VOLUME_NAME = "my-notebook-volume"
APP_NAME = "interactive-app"
APP_DIR = "/app"

# --- Modal App 设置 ---
app = modal.App(APP_NAME)

# 定义环境镜像，并安装所有指定的依赖
image = (
    modal.Image.debian_slim(python_version="3.10")
    .apt_install("git", "curl", "ffmpeg", "python3-tk")  # 保留这些通用的系统依赖
    .pip_install(
        "torch==2.5.1",
        "torchvision==0.20.1",
        "numpy",
        "trimesh",
        "fpsample",
        "einops",
        "onnxruntime",
        "rembg",
        "kiui",
        "pymcubes",
        "tqdm",
        "opencv-python",
        "ninja",
        "pymeshlab",
        "transformers",
    )
)

# 从统一名称创建或获取持久化存储卷
volume = modal.Volume.from_name(VOLUME_NAME, create_if_missing=True)

# --- Modal 函数定义 ---

@app.function(
    image=image,
    volumes={APP_DIR: volume},
    gpu="H100", # GPU 已更新为 H100
    timeout=3600,
)
def run_command_in_container(command: str):
    """在 Modal 容器内执行指定的 shell 命令。"""
    print(f"准备执行命令: '{command}'")
    try:
        # 使用 subprocess.run 执行命令，并设置工作目录
        process = subprocess.run(
            command,
            shell=True,
            check=True,
            cwd=APP_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        print("--- 命令输出 ---")
        print(process.stdout)
        if process.stderr:
            print("--- 错误输出 ---")
            print(process.stderr)
        print("\n命令执行成功。")
    except subprocess.CalledProcessError as e:
        print(f"\n命令执行失败，返回码: {e.returncode}")
        print("--- 命令输出 ---")
        print(e.stdout)
        print("--- 错误输出 ---")
        print(e.stderr)


# --- CLI 入口点 ---

@app.local_entrypoint()
def main(command: str):
    """本地入口点，用于触发远程 Modal 函数执行命令。"""
    print(f"正在通过 Modal 远程执行命令: '{command}'")
    run_command_in_container.remote(command)

