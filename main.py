import customtkinter as ctk
from gui import PromptGeneratorGUI
import os
import sys

def main() -> None:
    """程序主入口"""
    # 设置高DPI支持
    if os.name == 'nt':  # Windows
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
    
    # 创建主窗口
    root = ctk.CTk()
    
    # 设置窗口最小大小
    root.minsize(800, 600)
    
    # 创建应用
    app = PromptGeneratorGUI(root)
    
    # 运行主循环
    root.mainloop()

if __name__ == "__main__":
    main()
