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
        try:
            self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        except Exception:
            pass
        
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

        # 检查持久化文件
        missing_files = self.generator.check_persistence_files()
        if missing_files:
            msg = "检测到以下持久化文件缺失，可能导致配置丢失：\n\n" + "\n".join(missing_files) + "\n\n是否自动创建默认文件？"
            if messagebox.askyesno("文件缺失提示", msg):
                self.generator.create_persistence_files(missing_files)
                # 重新加载以应用默认值
                self.generator.load_settings()
                self.generator.load_template_presets()
                self.generator.load_used_values()
        
        # 创建UI
        self.create_widgets()
        
        # 加载初始数据
        self.load_initial_data()
    
    def _create_section(self, parent, index):
        """创建单个生成区域"""
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="both", expand=True, pady=5)
        
        # 顶部控制行：模板选择
        ctrl_frame = ctk.CTkFrame(frame, fg_color="transparent")
        ctrl_frame.pack(fill="x", padx=10, pady=(5, 2))
        
        ctk.CTkLabel(ctrl_frame, text=f"窗口 {index} 模板:").pack(side="left", padx=(0, 5))
        
        # 获取上次记忆的模板
        last_preset = self.generator.get_last_preset(index)
        
        preset_var = ctk.StringVar(value=last_preset)
        preset_combo = ctk.CTkComboBox(ctrl_frame, variable=preset_var, state="readonly", width=200)
        preset_combo.pack(side="left", fill="x", expand=True)
        
        # 结果文本框
        text_widget = tk.Text(
            frame,
            wrap="word",
            font=self.font_normal,
            height=10
        )
        text_widget.pack(fill="both", expand=True, padx=10, pady=5)
        text_widget.tag_config("placeholder", foreground="#e74c3c", font=self.font_placeholder)
        
        # 底部操作行
        action_frame = ctk.CTkFrame(frame, fg_color="transparent")
        action_frame.pack(fill="x", padx=10, pady=(0, 5))
        
        char_count_lbl = ctk.CTkLabel(action_frame, text="0 字符", font=("Arial", 12))
        char_count_lbl.pack(side="left")
        
        copy_btn = ctk.CTkButton(
            action_frame,
            text="📋 复制",
            width=80,
            height=28,
            command=lambda: self.copy_to_clipboard(index-1)
        )
        copy_btn.pack(side="right", padx=(5, 0))
        
        gen_btn = ctk.CTkButton(
            action_frame,
            text="🎲 一键生成",
            width=100,
            height=28,
            font=("Arial", 12, "bold"),
            command=lambda: self.generate_prompt(index-1)
        )
        gen_btn.pack(side="right")

        # 字符统计
        def _update_count(e=None):
            try:
                content = text_widget.get("1.0", "end-1c")
                n = len(content)
                char_count_lbl.configure(text=f"{n} 字符")
                if n > 780:
                    char_count_lbl.configure(text_color="#e74c3c")
                else:
                    char_count_lbl.configure(text_color="#2ecc71")
            except Exception:
                pass
        
        text_widget.bind("<KeyRelease>", _update_count)

        # 预设切换回调 (预览)
        def on_preset_change(choice=None):
            name = preset_var.get()
            # 记忆当前选择
            self.generator.set_last_preset(index, name)
            
            tpl = self.generator.get_template_by_name(name)
            if tpl:
                try:
                    text, spans = self.generator.generate_preview_with_spans(
                        product_type="",
                        selected_marker_values=None,
                        template_str=tpl
                    )
                    text_widget.delete("1.0", "end")
                    text_widget.insert("1.0", text)
                    for s in spans:
                        text_widget.tag_add("placeholder", f"1.0+{s['start']}c", f"1.0+{s['end']}c")
                    _update_count()
                except Exception as e:
                    pass

        preset_combo.configure(command=on_preset_change)

        return {
            "frame": frame,
            "preset_var": preset_var,
            "preset_combo": preset_combo,
            "text": text_widget,
            "gen_btn": gen_btn,
            "copy_btn": copy_btn,
            "char_count_lbl": char_count_lbl,
            "last_spans": [],
            "on_preset_change": on_preset_change
        }

    def _apply_font_size(self, sz):
        try:
            self.font_normal.configure(size=sz)
            self.font_placeholder.configure(size=sz+2)
            self.generator.set_result_font_size(sz)
        except Exception:
            pass

    def _on_font_change(self, value):
        if self._font_update_job:
            try:
                self.root.after_cancel(self._font_update_job)
            except Exception:
                pass
        sz = int(float(value))
        self._font_update_job = self.root.after(120, lambda: self._apply_font_size(sz))

    def create_widgets(self):
        """创建所有UI组件"""
        # 字体初始化
        sysname = platform.system()
        if sysname == "Windows":
            family = "Consolas"
        elif sysname == "Darwin":
            family = "Menlo"
        else:
            family = "DejaVu Sans Mono"
        initial_size = getattr(self.generator, 'get_result_font_size')()
        self.font_normal = tkfont.Font(family=family, size=initial_size)
        self.font_placeholder = tkfont.Font(family=family, size=initial_size+2, weight="bold")

        # 主框架
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 标题区域
        title_frame = ctk.CTkFrame(main_frame)
        title_frame.pack(fill="x", pady=(0, 10))
        
        title_label = ctk.CTkLabel(
            title_frame, 
            text="👗 服装展示提示词生成器", 
            font=("Arial", 24, "bold"),
            text_color="#4a6fa5"
        )
        title_label.pack(pady=5)
        
        # 全局控制区域
        global_ctrl = ctk.CTkFrame(main_frame)
        global_ctrl.pack(fill="x", pady=(0, 10))
        
        match_label = ctk.CTkLabel(global_ctrl, text="匹配原则:")
        match_label.pack(side="left", padx=(10, 5))
        
        self.match_var = ctk.StringVar(value="随机")
        self.match_combo = ctk.CTkComboBox(
            global_ctrl, 
            variable=self.match_var, 
            state="readonly", 
            values=["随机", "顺序"], 
            width=100,
            command=lambda v=None: self.generator.set_matching_mode("sequential" if self.match_var.get()=="顺序" else "random")
        )
        self.match_combo.pack(side="left", padx=5)
        if getattr(self.generator, 'matching_mode', 'random') == 'sequential':
            self.match_var.set("顺序")
        else:
            self.match_var.set("随机")

        self.configure_custom_btn = ctk.CTkButton(global_ctrl, text="⚙️ 设置自定义参数", command=self.configure_custom_params, width=140)
        self.configure_custom_btn.pack(side="right", padx=10)

        # 初始化 section 列表
        self.sections = []
        
        # 创建两个生成窗口
        self.sections.append(self._create_section(main_frame, 1))
        self.sections.append(self._create_section(main_frame, 2))
        
        # 底部设置区域
        settings_frame = ctk.CTkFrame(main_frame)
        settings_frame.pack(fill="x", pady=(6, 6))
        
        self.upload_btn = ctk.CTkButton(settings_frame, text="📁 上传变量库", command=self.upload_action_library, width=100)
        self.upload_btn.pack(side="left", padx=5, pady=6)
        
        self.reload_btn = ctk.CTkButton(settings_frame, text="🧹 清空", command=self.clear_value_library, width=80)
        self.reload_btn.pack(side="left", padx=5, pady=6)
        
        self.delete_fields_btn = ctk.CTkButton(settings_frame, text="⚙️ 用完即删", command=self.configure_delete_fields, width=100)
        self.delete_fields_btn.pack(side="left", padx=5, pady=6)
        
        self.template_btn = ctk.CTkButton(settings_frame, text="✏️ 编辑模板", command=self.edit_template, width=100)
        self.template_btn.pack(side="left", padx=5, pady=6)
        
        # 字体大小
        font_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        font_frame.pack(side="right", padx=5)
        ctk.CTkLabel(font_frame, text="字体").pack(side="left", padx=2)
        
        self._font_update_job = None
        self.font_size_var = tk.IntVar(value=getattr(self.generator, 'get_result_font_size')())
        
        self.font_slider = ctk.CTkSlider(font_frame, from_=6, to=22, number_of_steps=16, width=100, command=self._on_font_change)
        self.font_slider.set(self.font_size_var.get())
        self.font_slider.pack(side="left", padx=2)
        
        # 状态栏
        self.status_var = ctk.StringVar()
        self.status_var.set("就绪 | 使用内置默认动作库")
        self.status_bar = ctk.CTkLabel(
            self.root,
            textvariable=self.status_var,
            font=("Arial", 10),
            text_color="#666666",
            anchor="w"
        )
        self.status_bar.pack(side="bottom", fill="x", padx=20, pady=5)
    
    def load_initial_data(self):
        """加载初始数据"""
        # 自动加载上次变量库
        if hasattr(self.generator, 'last_library_path') and self.generator.last_library_path and os.path.exists(self.generator.last_library_path):
            self.generator.load_action_library_from_file(self.generator.last_library_path)
            self.status_var.set(f"✓ 已加载上次变量库: {os.path.basename(self.generator.last_library_path)}")
        
        names = self.generator.list_template_names()
        
        for i, section in enumerate(self.sections):
            if names:
                section['preset_combo'].configure(values=names)
                # 尝试恢复之前的选择或默认
                last = self.generator.get_last_preset(i + 1)
                if last and last in names:
                    section['preset_var'].set(last)
                else:
                    section['preset_var'].set(names[0] if names else "")
                
                # 触发更新预览
                if section.get('on_preset_change'):
                    section['on_preset_change']()
            else:
                 section['preset_combo'].configure(values=[])
                 section['preset_var'].set("")

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
            self.generator.set_last_library_path(file_path)
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
        preset_label.pack(anchor="w", padx=0)
        list_frame = ctk.CTkScrollableFrame(preset_frame, height=120)
        list_frame.pack(fill="x", padx=0, pady=5)
        preset_names = self.generator.list_template_names()
        preset_var = ctk.StringVar(value=preset_names[0] if preset_names else "")
        rows = []
        def refresh_list():
            for r in rows:
                try:
                    r.destroy()
                except Exception:
                    pass
            rows.clear()
            names = self.generator.list_template_names()
            for n in names:
                row = ctk.CTkFrame(list_frame)
                row.pack(fill="x", pady=3)
                rb = ctk.CTkRadioButton(row, text=n, variable=preset_var, value=n)
                rb.pack(side="left", padx=4)
                def on_delete(name=n, fr=row):
                    ok = self.generator.delete_template_preset(name)
                    if ok:
                        self.status_var.set("✓ 已删除预设")
                        messagebox.showinfo("成功", "预设已删除")
                        refresh_list()
                        self._refresh_all_combos()
                del_btn = ctk.CTkButton(row, text="×", width=28, command=on_delete, fg_color="#e74c3c", hover_color="#c0392b")
                del_btn.pack(side="right", padx=4)
                rows.append(row)
        refresh_list()
        def apply_preset():
            name = preset_var.get()
            tpl = self.generator.get_template_by_name(name)
            if tpl:
                template_text.delete("1.0", "end")
                template_text.insert("1.0", tpl)
                # self.generator.set_current_preset(name) # 编辑时不强制应用到主窗口
                self.status_var.set(f"✓ 已加载预设内容: {name}")
        apply_btn = ctk.CTkButton(preset_frame, text="加载预设内容", command=apply_preset, width=100)
        apply_btn.pack(padx=0, pady=5)

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
            target = preset_var.get().strip()
            ok = False
            if target and self.generator.preset_name_exists(target):
                ok = self.generator.update_template_preset(target, new_template)
                if ok:
                    self.status_var.set(f"✓ 预设已更新: {target}")
                    messagebox.showinfo("成功", f"预设‘{target}’已更新并保存")
                    self._refresh_all_combos()
            if not ok:
                # 只是保存为当前临时模板，不影响预设库
                self.generator.set_template(new_template)
                self.status_var.set("✓ 模板已更新")
                messagebox.showinfo("成功", "当前模板已更新并保存")
            template_window.destroy()

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
            self._refresh_all_combos()
            refresh_list()
            self.status_var.set(f"✓ 已保存预设: {base}")
            messagebox.showinfo("成功", "预设已保存")
            # template_window.destroy() # 可以不关闭，方便继续编辑
        
        def cancel_edit():
            template_window.destroy()
        
        # 保存按钮
        save_btn = ctk.CTkButton(
            btn_frame,
            text="💾 更新选中预设",
            command=save_template,
            width=120
        )
        save_btn.pack(side="right", padx=5)

        save_preset_btn = ctk.CTkButton(
            btn_frame,
            text="⭐ 新存为预设",
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

    def _refresh_all_combos(self):
        names = self.generator.list_template_names()
        for section in self.sections:
            section['preset_combo'].configure(values=names)

    def generate_prompt(self, index=0):
        """生成提示词"""
        try:
            if index < 0 or index >= len(self.sections):
                return
            section = self.sections[index]
            
            # 获取当前选择的模板
            template_name = section['preset_var'].get()
            template_str = self.generator.get_template_by_name(template_name)
            if not template_str:
                template_str = self.generator.get_template()

            markers = set(self.generator.extract_markers(template_str))
            sel = {}
            custom_map = getattr(self.generator, 'custom_params_map', {}) or {}
            for k, v in custom_map.items():
                if k in markers:
                    sel[k] = v
            
            text, spans = self.generator.generate_prompt_with_spans(
                product_type="",
                selected_marker_values=sel or None,
                template_str=template_str
            )
            
            section['text'].delete("1.0", "end")
            section['text'].insert("1.0", text)
            for s in spans:
                section['text'].tag_add("placeholder", f"1.0+{s['start']}c", f"1.0+{s['end']}c")
            section['last_spans'] = spans
            
            if section.get('update_count_func'):
                section['update_count_func']()
                
            self.status_var.set(f"✓ 窗口 {index+1} 已生成提示词")
            
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
        win.geometry("500x600")
        win.grab_set()
        
        # 说明标签
        ctk.CTkLabel(win, text="勾选的字段在生成提示词后，其值会被记录并在下次生成时剔除，直到所有值用完。", wraplength=460).pack(pady=10)

        frame = ctk.CTkScrollableFrame(win)
        frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        checks = {}
        current = set(self.generator.delete_on_use_fields)
        
        for k in keys:
            row = ctk.CTkFrame(frame)
            row.pack(fill="x", pady=2)
            
            var = tk.BooleanVar(value=k in current)
            cb = ctk.CTkCheckBox(row, text=k, variable=var)
            cb.pack(side="left", padx=8, pady=4)
            checks[k] = var
            
            # 清除记录按钮
            def clear_record(field=k):
                if messagebox.askyesno("确认", f"确定要清除字段 '{field}' 的已用记录吗？\n清除后该字段的所有值将重新变为可用。"):
                    self.generator.clear_used_values(field)
                    messagebox.showinfo("成功", f"已清除 '{field}' 的使用记录")
            
            btn_clear = ctk.CTkButton(row, text="清除记录", width=80, height=24, fg_color="#e74c3c", hover_color="#c0392b", command=clear_record)
            btn_clear.pack(side="right", padx=8)

        btn = ctk.CTkButton(win, text="保存设置", command=lambda: self._save_delete_fields(win, checks))
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
        self.generate_prompt(0)
    
    def copy_to_clipboard(self, index=0):
        """复制到剪贴板"""
        try:
            if index < 0 or index >= len(self.sections):
                return
            section = self.sections[index]
            prompt = section['text'].get("1.0", "end-1c")
            if not prompt.strip():
                messagebox.showwarning("警告", "没有内容可复制")
                return
            
            self.root.clipboard_clear()
            self.root.clipboard_append(prompt)
            self.root.update()  # 确保剪贴板更新
            
            try:
                spans = section.get('last_spans', []) or []
                self.generator.mark_used_from_spans(prompt, spans)
            except Exception:
                pass
            self.status_var.set(f"✓ 窗口 {index+1} 内容已复制")
            try:
                self.status_bar.configure(text_color="#2ecc71")
            except Exception:
                pass
        except Exception as e:
            self.status_var.set(f"✗ 复制失败: {str(e)}")
            messagebox.showerror("错误", f"复制到剪贴板失败:\n{str(e)}")

    def configure_custom_params(self):
        """
        设置自定义参数
        用法说明：
        1. 在列表中找到您想要固定的字段（例如 '品牌'）。
        2. 在右侧下拉框选择您想要锁定的值（例如 'Nike'）。
        3. 勾选 '激活' 复选框。
        4. 点击 '保存设置'。
        激活后，无论匹配原则是随机还是顺序，该字段都将始终使用您指定的值。
        """
        keys = sorted([k for k in self.generator.value_library.keys()])
        if not keys:
            messagebox.showinfo("提示", "请先上传变量库文档")
            return
        win = ctk.CTkToplevel(self.root)
        win.title("设置自定义参数")
        win.geometry("560x700")
        win.grab_set()
        
        # 说明区域
        info_frame = ctk.CTkFrame(win, fg_color="transparent")
        info_frame.pack(fill="x", padx=15, pady=(10, 5))
        ctk.CTkLabel(info_frame, text="💡 说明：在此处激活的参数将覆盖随机生成逻辑，\n强制生成指定的值（适用于固定品牌、季节等场景）。", 
                     text_color="gray", justify="left").pack(anchor="w")

        frame = ctk.CTkScrollableFrame(win)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        rows = []
        existing = getattr(self.generator, 'custom_params_map', {}) or {}
        for i in range(5):
            row = ctk.CTkFrame(frame)
            row.pack(fill="x", pady=6)
            name_cb = ctk.CTkComboBox(row, values=keys, state="readonly", width=160)
            name_cb.pack(side="left", padx=6)
            val_cb = ctk.CTkComboBox(row, values=[], state="readonly")
            val_cb.pack(side="left", padx=6, fill="x", expand=True)
            act_var = tk.BooleanVar(value=False)
            act_cb = ctk.CTkCheckBox(row, text="激活", variable=act_var)
            act_cb.pack(side="left", padx=6)
            def on_name_change(cb=name_cb, vcb=val_cb, a=act_var):
                name = cb.get()
                vals = [v for v in self.generator.value_library.get(name, []) if str(v).strip()]
                vcb.configure(values=vals)
                if name in existing and existing[name] in vals:
                    vcb.set(existing[name])
                    a.set(True)
                elif vals:
                    vcb.set(vals[0])
            name_cb.configure(command=lambda v=None, f=on_name_change: f())
            if i < len(existing):
                pre_name = list(existing.keys())[i]
                if pre_name in keys:
                    name_cb.set(pre_name)
                    on_name_change()
            rows.append((name_cb, val_cb, act_var))
        # 持久化文件路径配置区域
        path_area = ctk.CTkFrame(frame)
        path_area.pack(fill="x", padx=4, pady=10)
        path_title = ctk.CTkLabel(path_area, text="持久化文件路径（settings/templates/used_values）")
        path_title.pack(anchor="w", padx=6, pady=(4,6))
        # 当前路径预填
        cur_settings = getattr(self.generator, "custom_settings_file_path", None) or getattr(self.generator, "settings_file")
        cur_templates = getattr(self.generator, "custom_templates_file_path", None) or getattr(self.generator, "templates_file")
        cur_used = getattr(self.generator, "custom_used_values_file_path", None) or getattr(self.generator, "used_values_file")
        # settings.json
        row_settings = ctk.CTkFrame(path_area)
        row_settings.pack(fill="x", pady=6)
        lbl_settings = ctk.CTkLabel(row_settings, text="Settings文件路径:")
        lbl_settings.pack(side="left", padx=6)
        ent_settings = ctk.CTkEntry(row_settings, width=320)
        ent_settings.pack(side="left", padx=6, fill="x", expand=True)
        try:
            ent_settings.insert(0, cur_settings or "")
        except Exception:
            pass
        def pick_settings():
            p = filedialog.asksaveasfilename(title="选择或创建 settings.json", defaultextension=".json", filetypes=[("JSON Files", "*.json")])
            if p:
                ent_settings.delete(0, "end")
                ent_settings.insert(0, p)
        btn_settings = ctk.CTkButton(row_settings, text="浏览", width=80, command=pick_settings)
        btn_settings.pack(side="left", padx=6)
        # templates.json
        row_templates = ctk.CTkFrame(path_area)
        row_templates.pack(fill="x", pady=6)
        lbl_templates = ctk.CTkLabel(row_templates, text="Templates文件路径:")
        lbl_templates.pack(side="left", padx=6)
        ent_templates = ctk.CTkEntry(row_templates, width=320)
        ent_templates.pack(side="left", padx=6, fill="x", expand=True)
        try:
            ent_templates.insert(0, cur_templates or "")
        except Exception:
            pass
        def pick_templates():
            p = filedialog.asksaveasfilename(title="选择或创建 templates.json", defaultextension=".json", filetypes=[("JSON Files", "*.json")])
            if p:
                ent_templates.delete(0, "end")
                ent_templates.insert(0, p)
        btn_templates = ctk.CTkButton(row_templates, text="浏览", width=80, command=pick_templates)
        btn_templates.pack(side="left", padx=6)
        # used_values.json
        row_used = ctk.CTkFrame(path_area)
        row_used.pack(fill="x", pady=6)
        lbl_used = ctk.CTkLabel(row_used, text="UsedValues文件路径:")
        lbl_used.pack(side="left", padx=6)
        ent_used = ctk.CTkEntry(row_used, width=320)
        ent_used.pack(side="left", padx=6, fill="x", expand=True)
        try:
            ent_used.insert(0, cur_used or "")
        except Exception:
            pass
        def pick_used():
            p = filedialog.asksaveasfilename(title="选择或创建 used_values.json", defaultextension=".json", filetypes=[("JSON Files", "*.json")])
            if p:
                ent_used.delete(0, "end")
                ent_used.insert(0, p)
        btn_used = ctk.CTkButton(row_used, text="浏览", width=80, command=pick_used)
        btn_used.pack(side="left", padx=6)
        def save():
            m = {}
            for name_cb, val_cb, act_var in rows:
                if act_var.get():
                    name = name_cb.get()
                    val = val_cb.get()
                    if name and val:
                        m[name] = val
            self.generator.set_custom_params_map(m)
            spath = ent_settings.get().strip()
            tpath = ent_templates.get().strip()
            upath = ent_used.get().strip()
            try:
                self.generator.set_data_file_paths(
                    templates_path=tpath or None,
                    settings_path=spath or None,
                    used_values_path=upath or None
                )
                try:
                    self._refresh_all_combos()
                except Exception:
                    pass
            except Exception:
                pass
            self.status_var.set("✓ 已更新自定义参数与文件路径")
            win.destroy()
        btn = ctk.CTkButton(win, text="保存", command=save)
        btn.pack(pady=8)

    def _on_close(self):
        try:
            self.generator.save_settings()
        except Exception:
            pass
        try:
            self.root.destroy()
        except Exception:
            pass
    
    def save_to_file(self):
        """保存到文件"""
        # 默认保存第一个窗口的内容
        if not self.sections:
             return
        prompt = self.sections[0]['text'].get("1.0", "end-1c")
        if not prompt.strip():
            messagebox.showwarning("警告", "没有内容可保存")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="保存提示词",
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            initialfile="提示词.txt"
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
