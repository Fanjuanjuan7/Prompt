import customtkinter as ctk
from gui import PromptGeneratorGUI
import os
import sys

def main() -> None:
    """程序主入口"""
    try:
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
    except Exception as e:
        try:
            import tkinter as tk
            from tkinter import messagebox
            tmp = tk.Tk()
            tmp.withdraw()
            messagebox.showerror("程序异常", f"运行过程中发生错误：\n{str(e)}")
            tmp.destroy()
        except:
            pass

if __name__ == "__main__":
    main()
