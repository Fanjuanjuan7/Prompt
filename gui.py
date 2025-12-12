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
        self.root.geometry("480x780")
        self.root.minsize(420, 700)
        
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
        
        # 控制区域（横向排列：模板预设 / 产品类型 / 匹配原则）
        control_frame = ctk.CTkFrame(main_frame)
        control_frame.pack(fill="x", pady=(0, 12))
        control_frame.grid_columnconfigure(0, weight=1)
        control_frame.grid_columnconfigure(1, weight=1)
        control_frame.grid_columnconfigure(2, weight=1)
        
        # 产品类型选择
        preset_label = ctk.CTkLabel(control_frame, text="模板预设")
        preset_label.grid(row=0, column=0, padx=10, pady=(10, 2), sticky="w")
        self.preset_var = ctk.StringVar()
        self.preset_combo = ctk.CTkComboBox(control_frame, variable=self.preset_var, state="readonly")
        self.preset_combo.grid(row=1, column=0, padx=10, pady=(0, 8), sticky="ew")

        product_label = ctk.CTkLabel(control_frame, text="产品类型")
        product_label.grid(row=0, column=1, padx=10, pady=(10, 2), sticky="w")
        self.product_var = ctk.StringVar()
        self.product_combo = ctk.CTkComboBox(control_frame, variable=self.product_var, state="readonly", command=lambda v=None: self.generator.set_current_product_type(self.product_var.get()))
        self.product_combo.grid(row=1, column=1, padx=10, pady=(0, 8), sticky="ew")

        match_label = ctk.CTkLabel(control_frame, text="匹配原则")
        match_label.grid(row=0, column=2, padx=10, pady=(10, 2), sticky="w")
        self.match_var = ctk.StringVar(value="随机")
        self.match_combo = ctk.CTkComboBox(control_frame, variable=self.match_var, state="readonly", values=["随机", "顺序"], command=lambda v=None: self.generator.set_matching_mode("sequential" if self.match_var.get()=="顺序" else "random"))
        self.match_combo.grid(row=1, column=2, padx=10, pady=(0, 8), sticky="ew")
        if getattr(self.generator, 'matching_mode', 'random') == 'sequential':
            self.match_var.set("顺序")
        else:
            self.match_var.set("随机")
        
        # 顶部右侧操作（放在编辑框上方靠右）：生成 / 复制
        actions_top = ctk.CTkFrame(main_frame)
        actions_top.pack(fill="x", pady=(0, 6))
        actions_container = ctk.CTkFrame(actions_top)
        actions_container.pack(anchor="e", padx=10)
        self.generate_btn = ctk.CTkButton(
            actions_container,
            text="🎲 一键生成提示词",
            command=self.generate_prompt,
            width=160,
            height=36,
            font=("Arial", 14, "bold"),
            fg_color="#4a6fa5",
            hover_color="#3a5a80"
        )
        self.generate_btn.pack(side="right", padx=8)
        self.copy_btn = ctk.CTkButton(
            actions_container,
            text="📋 复制到剪贴板",
            command=self.copy_to_clipboard,
            width=140,
            height=36
        )
        self.copy_btn.pack(side="right", padx=8)
        
        # 结果区域
        result_frame = ctk.CTkFrame(main_frame)
        result_frame.pack(fill="both", expand=True)
        
        # 结果标签
        result_label = ctk.CTkLabel(result_frame, text="生成结果", font=("Arial", 13, "bold"))
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
            height=20
        )
        self.result_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.result_text.tag_config("placeholder", foreground="#e74c3c", font=self.font_placeholder)
        
        # 编辑框下方一行设置按钮：上传变量库 / 清空变量库 / 用完即删字段 / 编辑模板
        settings_frame = ctk.CTkFrame(main_frame)
        settings_frame.pack(fill="x", pady=(6, 6))
        self.upload_btn = ctk.CTkButton(settings_frame, text="📁 上传变量库", command=self.upload_action_library, width=140)
        self.upload_btn.pack(side="left", padx=10, pady=6)
        self.reload_btn = ctk.CTkButton(settings_frame, text="🧹 清空变量库", command=self.clear_value_library, width=140)
        self.reload_btn.pack(side="left", padx=6, pady=6)
        self.delete_fields_btn = ctk.CTkButton(settings_frame, text="⚙️ 设置用完即删字段", command=self.configure_delete_fields, width=180)
        self.delete_fields_btn.pack(side="left", padx=6, pady=6)
        self.template_btn = ctk.CTkButton(settings_frame, text="✏️ 编辑模板", command=self.edit_template, width=120)
        self.template_btn.pack(side="left", padx=6, pady=6)
        font_frame = ctk.CTkFrame(settings_frame)
        font_frame.pack(side="right", padx=10, pady=6)
        font_label = ctk.CTkLabel(font_frame, text="字体大小")
        font_label.pack(side="left", padx=(0,6))
        self.font_size_var = tk.IntVar(value=getattr(self.generator, 'get_result_font_size')())
        def on_font_change(value):
            sz = int(float(value))
            self.font_normal.configure(size=sz)
            self.font_placeholder.configure(size=sz+2)
            self.generator.set_result_font_size(sz)
        self.font_slider = ctk.CTkSlider(font_frame, from_=10, to=22, number_of_steps=12, command=on_font_change)
        self.font_slider.set(self.font_size_var.get())
        self.font_slider.pack(side="left", padx=6)
        
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
        names = self.generator.list_template_names()
        if names:
            self.preset_combo.configure(values=names)
            self.preset_var.set(names[0])
        def on_preset_change(choice=None):
            name = self.preset_var.get()
            self.generator.set_current_preset(name)
            t = self.generator.get_template()
            self.status_var.set(f"✓ 已应用预设: {name}")
            text, spans = self.generator.generate_preview_with_spans(
                product_type=self.product_var.get() if self.product_var.get() else "",
                selected_marker_values={'产品类型': self.product_var.get()} if self.product_var.get() else None
            )
            self.result_text.delete("1.0", "end")
            self.result_text.insert("1.0", text)
            for s in spans:
                self.result_text.tag_add("placeholder", f"1.0+{s['start']}c", f"1.0+{s['end']}c")
        self.preset_combo.configure(command=lambda v=None: on_preset_change())
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
        try:
            text, spans = self.generator.generate_preview_with_spans(
                product_type=self.product_var.get() if self.product_var.get() else "",
                selected_marker_values={'产品类型': self.product_var.get()} if self.product_var.get() else None
            )
            self.result_text.delete("1.0", "end")
            self.result_text.insert("1.0", text)
            for s in spans:
                self.result_text.tag_add("placeholder", f"1.0+{s['start']}c", f"1.0+{s['end']}c")
        except Exception as e:
            self.status_var.set(f"✗ 初始化生成失败: {str(e)}")
    
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
    
    def clear_value_library(self):
        self.generator.load_default_actions()
        self.status_var.set("✓ 已清空变量库")
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
        
        preset_frame = ctk.CTkFrame(template_window)
        preset_frame.pack(fill="x", padx=10, pady=5)
        preset_label = ctk.CTkLabel(preset_frame, text="模板预设:")
        preset_label.pack(side="left")
        preset_names = self.generator.list_template_names()
        preset_var = ctk.StringVar(value=preset_names[0] if preset_names else "")
        preset_combo = ctk.CTkComboBox(preset_frame, variable=preset_var, values=preset_names, state="readonly", width=250)
        preset_combo.pack(side="left", padx=10)
        def apply_preset():
            name = preset_var.get()
            tpl = self.generator.get_template_by_name(name)
            if tpl:
                template_text.delete("1.0", "end")
                template_text.insert("1.0", tpl)
                self.generator.set_template(tpl)
                self.status_var.set(f"✓ 已应用预设: {name}")
        apply_btn = ctk.CTkButton(preset_frame, text="应用预设", command=apply_preset, width=100)
        apply_btn.pack(side="left", padx=5)
        def delete_preset():
            name = preset_var.get().strip()
            if not name:
                return
            ok = self.generator.delete_template_preset(name)
            if ok:
                names = self.generator.list_template_names()
                preset_combo.configure(values=names)
                preset_var.set(names[0] if names else "")
                self.preset_combo.configure(values=names)
                if names:
                    self.preset_var.set(names[0])
                self.status_var.set("✓ 已删除预设")
                messagebox.showinfo("成功", "预设已删除")
            else:
                messagebox.showerror("错误", "预设不存在")
        delete_btn = ctk.CTkButton(preset_frame, text="删除预设", command=delete_preset, width=100)
        delete_btn.pack(side="left", padx=5)

        name_frame = ctk.CTkFrame(template_window)
        name_frame.pack(fill="x", padx=10, pady=5)
        name_label = ctk.CTkLabel(name_frame, text="预设名称:")
        name_label.pack(side="left")
        name_entry = ctk.CTkEntry(name_frame, width=250)
        name_entry.pack(side="left", padx=10)

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

        def save_preset():
            new_template = template_text.get("1.0", "end-1c")
            base = name_entry.get().strip()
            if not base:
                messagebox.showerror("错误", "请输入预设名称")
                return
            if self.generator.preset_name_exists(base):
                messagebox.showerror("错误", "预设名不能重复")
                return
            self.generator.save_template_preset(base, new_template)
            names = self.generator.list_template_names()
            self.preset_combo.configure(values=names)
            self.preset_var.set(base)
            self.status_var.set(f"✓ 已保存预设: {base}")
            messagebox.showinfo("成功", "预设已保存")
            template_window.destroy()
        
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

        save_preset_btn = ctk.CTkButton(
            btn_frame,
            text="⭐ 保存为预设",
            command=save_preset,
            width=120
        )
        save_preset_btn.pack(side="right", padx=5)
        
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
            empties = self.generator.get_empty_selected_fields()
            if empties:
                messagebox.showwarning("警告", "字段下没有值，请添加变量值: " + ", ".join(empties))
        except Exception as e:
            self.status_var.set(f"✗ 生成失败: {str(e)}")
            messagebox.showerror("错误", f"生成提示词时出错:\n{str(e)}")

    def configure_delete_fields(self):
        keys = sorted(list(self.generator.value_library.keys()))
        if not keys:
            messagebox.showinfo("提示", "请先上传变量库文档")
            return
        win = ctk.CTkToplevel(self.root)
        win.title("设置用完即删字段")
        win.geometry("400x500")
        win.grab_set()
        frame = ctk.CTkScrollableFrame(win)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        checks = {}
        current = set(self.generator.delete_on_use_fields)
        for k in keys:
            var = tk.BooleanVar(value=k in current)
            cb = ctk.CTkCheckBox(frame, text=k, variable=var)
            cb.pack(anchor="w", padx=8, pady=4)
            checks[k] = var
        btn = ctk.CTkButton(win, text="保存", command=lambda: self._save_delete_fields(win, checks))
        btn.pack(pady=10)

    def _save_delete_fields(self, win, checks):
        selected = [k for k, v in checks.items() if v.get()]
        self.generator.set_delete_on_use_fields(selected)
        self.status_var.set("✓ 已更新用完即删字段")
        win.destroy()

    def _now_str(self):
        import datetime
        return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
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
