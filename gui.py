import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog, messagebox
import tkinter.font as tkfont
import os
import platform
import webbrowser
from core import PromptGenerator

class PromptGeneratorGUI:
    """GUI界面实现，使用CustomTkinter"""
    
    def __init__(self, root: ctk.CTk):
        self.root = root
        self.root.title("服装展示提示词生成器")
        self.root.geometry("1200x800")
        self.root.minsize(1100, 800)
        
        # 设置主题
        ctk.set_appearance_mode("system")  # 可选: "light", "dark", "system"
        ctk.set_default_color_theme("blue")  # 可选: "blue", "green", "dark-blue"
        
        # 加载图标
        try:
            if os.name == 'nt':  # Windows
                icon_path = os.path.join(os.path.dirname(__file__), "assets", "app_icon.ico")
                if os.path.exists(icon_path):
                    self.root.iconbitmap(icon_path)
            else:  # macOS/Linux
                icon_path = os.path.join(os.path.dirname(__file__), "assets", "app_icon.png")
                if os.path.exists(icon_path):
                    img = tk.PhotoImage(file=icon_path)
                    self.root.tk.call('wm', 'iconphoto', self.root._w, img)
        except Exception as e:
            print(f"加载图标失败: {e}")
        
        # 初始化核心生成器
        self.generator = PromptGenerator()
        
        # 创建UI
        self.create_widgets()
        
        # 加载初始数据
        self.load_initial_data()
    
    def create_widgets(self):
        """创建所有UI组件"""
        # 主框架
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 标题区域
        title_frame = ctk.CTkFrame(main_frame)
        title_frame.pack(fill="x", pady=(0, 15))
        
        title_label = ctk.CTkLabel(
            title_frame, 
            text="👗 服装展示提示词生成器", 
            font=("Arial", 24, "bold"),
            text_color="#4a6fa5"
        )
        title_label.pack(pady=10)
        
        subtitle_label = ctk.CTkLabel(
            title_frame,
            text="一键生成高转化率短视频拍摄脚本",
            font=("Arial", 14),
            text_color="#666666"
        )
        subtitle_label.pack(pady=(0, 5))
        
        # 控制区域
        control_frame = ctk.CTkFrame(main_frame)
        control_frame.pack(fill="x", pady=(0, 15))
        
        # 产品类型选择
        product_label = ctk.CTkLabel(control_frame, text="产品类型:")
        product_label.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="e")
        
        self.product_var = ctk.StringVar()
        self.product_combo = ctk.CTkComboBox(
            control_frame,
            variable=self.product_var,
            width=200,
            state="readonly"
        )
        self.product_combo.grid(row=0, column=1, padx=5, pady=10, sticky="w")
        
        # 已移除氛围选择控件
        
        # 操作按钮
        btn_frame = ctk.CTkFrame(main_frame)
        btn_frame.pack(fill="x", pady=(0, 15))
        
        # 上传按钮
        self.upload_btn = ctk.CTkButton(
            btn_frame,
            text="📁 上传变量库",
            command=self.upload_action_library,
            width=120
        )
        self.upload_btn.pack(side="left", padx=10)
        
        # 重载按钮
        self.reload_btn = ctk.CTkButton(
            btn_frame,
            text="🔄 重载动作库",
            command=self.reload_action_library,
            width=120
        )
        self.reload_btn.pack(side="left", padx=5)
        
        # 复制按钮 (位置与“编辑模板”调换为顶部右侧)
        self.copy_btn = ctk.CTkButton(
            btn_frame,
            text="📋 复制到剪贴板",
            command=self.copy_to_clipboard,
            width=150
        )
        self.copy_btn.pack(side="right", padx=10)
        
        # 随机生成按钮 (大按钮)
        self.generate_btn = ctk.CTkButton(
            btn_frame,
            text="🎲 一键生成提示词",
            command=self.generate_prompt,
            width=200,
            height=50,
            font=("Arial", 16, "bold"),
            fg_color="#4a6fa5",
            hover_color="#3a5a80"
        )
        self.generate_btn.pack(side="right", padx=20, ipadx=20, ipady=5)
        
        # 结果区域
        result_frame = ctk.CTkFrame(main_frame)
        result_frame.pack(fill="both", expand=True)
        
        # 结果标签
        result_label = ctk.CTkLabel(result_frame, text="生成结果:", font=("Arial", 14, "bold"))
        result_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        # 结果文本框（使用 tk.Text 以支持片段高亮）
        sysname = platform.system()
        if sysname == "Windows":
            family = "Consolas"
        elif sysname == "Darwin":
            family = "Menlo"
        else:
            family = "DejaVu Sans Mono"
        self.font_normal = tkfont.Font(family=family, size=14)
        self.font_placeholder = tkfont.Font(family=family, size=16, weight="bold")
        self.result_text = tk.Text(
            result_frame,
            wrap="word",
            font=self.font_normal,
            height=16
        )
        self.result_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.result_text.tag_config("placeholder", foreground="#e74c3c", font=self.font_placeholder)
        
        # 底部按钮
        bottom_frame = ctk.CTkFrame(main_frame)
        bottom_frame.pack(fill="x", pady=(10, 0))
        
        # 模板编辑按钮（移动到底部左侧）
        self.template_btn = ctk.CTkButton(
            bottom_frame,
            text="✏️ 编辑模板",
            command=self.edit_template,
            width=120
        )
        self.template_btn.pack(side="left", padx=10, pady=5)
        
        # 保存按钮
        self.save_btn = ctk.CTkButton(
            bottom_frame,
            text="💾 保存为文件",
            command=self.save_to_file,
            width=150
        )
        self.save_btn.pack(side="left", padx=5, pady=5)
        
        # 重新生成按钮
        self.regenerate_btn = ctk.CTkButton(
            bottom_frame,
            text="🔄 重新生成 (同类型)",
            command=self.regenerate_same_type,
            width=150
        )
        self.regenerate_btn.pack(side="right", padx=10, pady=5)
        
        # 状态栏
        self.status_var = ctk.StringVar()
        self.status_var.set("就绪 | 使用内置默认动作库")
        status_bar = ctk.CTkLabel(
            self.root,
            textvariable=self.status_var,
            font=("Arial", 10),
            text_color="#666666",
            anchor="w"
        )
        status_bar.pack(side="bottom", fill="x", padx=20, pady=5)
    
    def load_initial_data(self):
        """加载初始数据"""
        # 加载产品类型（优先来自变量库的“产品类型”列）
        values = []
        if hasattr(self.generator, 'value_library') and '产品类型' in self.generator.value_library:
            values = [v for v in self.generator.value_library['产品类型'] if str(v).strip()]
        if not values:
            values = self.generator.get_product_types()
        if values:
            self.product_combo.configure(values=values)
            self.product_var.set(values[0])
        
        # 已移除氛围类型加载
        
        # 设置初始结果并高亮占位符
        text, spans = self.generator.generate_prompt_with_spans(
            product_type=self.product_var.get(),
            selected_marker_values={'产品类型': self.product_var.get()}
        )
        self.result_text.delete("1.0", "end")
        self.result_text.insert("1.0", text)
        for s in spans:
            self.result_text.tag_add("placeholder", f"1.0+{s['start']}c", f"1.0+{s['end']}c")
    
    def upload_action_library(self):
        """上传动作库文件"""
        file_path = filedialog.askopenfilename(
            title="选择动作库文件",
            filetypes=[("Excel Files", "*.xlsx *.xls"), ("All Files", "*.*")]
        )
        
        if not file_path:
            return
        
        success, message = self.generator.load_action_library_from_file(file_path)
        if success:
            self.status_var.set(f"✓ {message} | 文件: {os.path.basename(file_path)}")
            messagebox.showinfo("成功", message)
            self.load_initial_data()
        else:
            self.status_var.set(f"✗ {message}")
            messagebox.showerror("错误", message)
    
    def reload_action_library(self):
        """重载动作库 (恢复默认)"""
        self.generator.load_default_actions()
        self.status_var.set("✓ 已重载默认动作库")
        messagebox.showinfo("成功", "已重载默认动作库")
        self.load_initial_data()
    
    def edit_template(self):
        """编辑模板"""
        # 创建模板编辑窗口
        template_window = ctk.CTkToplevel(self.root)
        template_window.title("编辑模板")
        template_window.geometry("700x500")
        template_window.grab_set()  # 模态窗口
        
        # 模板说明
        info_label = ctk.CTkLabel(
            template_window,
            text="可使用任意占位符，如 {产品}、{动作}、{氛围}、{品牌}、{材质} 等\n只要与上传Excel中的列名一致，将随机抽取该列的值进行替换",
            justify="left"
        )
        info_label.pack(pady=(10, 5), padx=10, anchor="w")
        
        # 模板文本框
        template_text = ctk.CTkTextbox(
            template_window,
            wrap="word",
            font=("Consolas", 12),
            height=300
        )
        template_text.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 加载当前模板
        current_template = self.generator.get_template()
        template_text.insert("1.0", current_template)
        
        # 按钮框架
        btn_frame = ctk.CTkFrame(template_window)
        btn_frame.pack(fill="x", pady=10, padx=10)
        
        def save_template():
            new_template = template_text.get("1.0", "end-1c")
            self.generator.set_template(new_template)
            self.status_var.set("✓ 模板已更新")
            template_window.destroy()
            messagebox.showinfo("成功", "模板已更新")
        
        def cancel_edit():
            template_window.destroy()
        
        # 保存按钮
        save_btn = ctk.CTkButton(
            btn_frame,
            text="💾 保存模板",
            command=save_template,
            width=120
        )
        save_btn.pack(side="right", padx=5)
        
        # 取消按钮
        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="❌ 取消",
            command=cancel_edit,
            width=120,
            fg_color="#e74c3c",
            hover_color="#c0392b"
        )
        cancel_btn.pack(side="right", padx=5)
        
        # 帮助按钮
        help_btn = ctk.CTkButton(
            btn_frame,
            text="❓ 帮助",
            command=lambda: webbrowser.open("https://example.com/template-help"),
            width=100
        )
        help_btn.pack(side="left", padx=5)
    
    def generate_prompt(self):
        """生成提示词"""
        if not self.product_var.get():
            messagebox.showwarning("警告", "请选择产品类型")
            return
        
        try:
            text, spans = self.generator.generate_prompt_with_spans(
                product_type=self.product_var.get(),
                selected_marker_values={'产品类型': self.product_var.get()}
            )
            self.result_text.delete("1.0", "end")
            self.result_text.insert("1.0", text)
            for s in spans:
                self.result_text.tag_add("placeholder", f"1.0+{s['start']}c", f"1.0+{s['end']}c")
            self.status_var.set(f"✓ 已生成 {self.product_var.get()} 的提示词")
        except Exception as e:
            self.status_var.set(f"✗ 生成失败: {str(e)}")
            messagebox.showerror("错误", f"生成提示词时出错:\n{str(e)}")
    
    def regenerate_same_type(self):
        """重新生成同类型提示词"""
        self.generate_prompt()
    
    def copy_to_clipboard(self):
        """复制到剪贴板"""
        try:
            prompt = self.result_text.get("1.0", "end-1c")
            if not prompt.strip():
                messagebox.showwarning("警告", "没有内容可复制")
                return
            
            self.root.clipboard_clear()
            self.root.clipboard_append(prompt)
            self.root.update()  # 确保剪贴板更新
            
            self.status_var.set("✓ 已复制到剪贴板")
        except Exception as e:
            self.status_var.set(f"✗ 复制失败: {str(e)}")
            messagebox.showerror("错误", f"复制到剪贴板失败:\n{str(e)}")
    
    def save_to_file(self):
        """保存到文件"""
        prompt = self.result_text.get("1.0", "end-1c")
        if not prompt.strip():
            messagebox.showwarning("警告", "没有内容可保存")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="保存提示词",
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            initialfile=f"{self.product_var.get()}_提示词.txt"
        )
        
        if not file_path:
            return
        
        success, message = self.generator.save_prompt_to_file(prompt, file_path)
        if success:
            self.status_var.set(f"✓ {message} | 位置: {file_path}")
            messagebox.showinfo("成功", f"文件已保存到:\n{file_path}")
        else:
            self.status_var.set(f"✗ {message}")
            messagebox.showerror("错误", message)

if __name__ == "__main__":
    pass
