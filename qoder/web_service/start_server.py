import subprocess
import sys
import os
from pathlib import Path

def install_dependencies():
    """安装必要的依赖"""
    print("正在安装依赖...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("依赖安装完成!")
        return True
    except subprocess.CalledProcessError:
        print("依赖安装失败，请手动安装Flask: pip install Flask")
        return False

def start_server():
    """启动Web服务器"""
    print("正在启动Qoder历史记录查看器...")
    print("服务器将在 http://127.0.0.1:5000 上运行")
    print("按 Ctrl+C 停止服务器")
    
    try:
        # 使用Flask内置服务器启动
        os.system("python app.py")
    except KeyboardInterrupt:
        print("\n服务器已停止")

def main():
    print("Qoder 历史记录查看器启动器")
    print("="*40)
    
    # 检查是否已安装依赖
    req_file = Path("requirements.txt")
    if req_file.exists():
        install_dependencies()
    
    start_server()

if __name__ == "__main__":
    main()