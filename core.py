import os
import random
import re
import json
import sys
import platform
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
import pandas as pd

class PromptGenerator:
    """核心提示词生成器，处理所有业务逻辑"""
    
    DEFAULT_ACTIONS: Dict[str, List[str]] = {}
    DEFAULT_ATMOSPHERES: List[str] = []
    
    DEFAULT_TEMPLATE = """主体：一位充满活力的抖音带货达人，镜头全程聚焦，确保【{产品}】是绝对视觉中心。
主体描述：动作连贯有节奏，突出产品核心卖点。面料自然下垂，严禁任何扭曲或拉伸变形，保证结构真实。
动作序列：【{动作}】
镜头语言：动态运镜强化动作细节 —— 推近特写、跟随移动、环绕拍摄。每帧画面变化率 >35%，确保视觉冲击力。
氛围：{氛围}，适合短视频平台快速种草。"""
    
    def __init__(self) -> None:
        self.action_library: Dict[str, List[str]] = {}
        self.value_library: Dict[str, List[str]] = {}
        self.template: str = self.DEFAULT_TEMPLATE
        self.matching_mode: str = "random"
        self.field_indices: Dict[str, int] = {}
        self.delete_on_use_fields: List[str] = []
        self.template_presets: List[Dict[str, Any]] = []
        base_dir = os.path.dirname(__file__)
        # 计算持久化目录（跨平台）
        def _data_dir() -> str:
            app_name = "Prompt"
            sysname = platform.system()
            if sysname == "Windows":
                root = os.environ.get("APPDATA") or os.path.expanduser("~")
                return os.path.join(root, app_name)
            elif sysname == "Darwin":
                return os.path.join(os.path.expanduser("~"), "Library", "Application Support", app_name)
            else:
                return os.path.join(os.path.expanduser("~"), ".config", app_name)
        self.data_dir: str = _data_dir()
        try:
            os.makedirs(self.data_dir, exist_ok=True)
        except Exception:
            pass
        old_templates = os.path.join(base_dir, "templates.json")
        old_settings = os.path.join(base_dir, "settings.json")
        old_used = os.path.join(base_dir, "used_values.json")
        self.templates_file: str = os.path.join(self.data_dir, "templates.json")
        self.settings_file: str = os.path.join(self.data_dir, "settings.json")
        self.current_product_type: Optional[str] = None
        self.used_values_file: str = os.path.join(self.data_dir, "used_values.json")
        self.used_values: Dict[str, List[str]] = {}
        self.result_font_size: int = 14
        self.current_template_override: Optional[str] = None
        self.current_preset_name: Optional[str] = None
        self.last_library_path: Optional[str] = None
        self.selected_custom_param: Optional[str] = None
        self.selected_custom_value: Optional[str] = None
        self.custom_params_map: Dict[str, str] = {}
        self.custom_settings_file_path: Optional[str] = None
        self.custom_templates_file_path: Optional[str] = None
        self.custom_used_values_file_path: Optional[str] = None
        self.load_default_actions()
        self.load_template_presets()
        self.load_settings()
        self.load_used_values()
        # 迁移旧文件至持久化目录（仅在新路径不存在且旧路径存在时）
        try:
            if (not os.path.exists(self.templates_file)) and os.path.exists(old_templates):
                with open(old_templates, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                with open(self.templates_file, "w", encoding="utf-8") as fp:
                    json.dump(data, fp, ensure_ascii=False, indent=2)
            if (not os.path.exists(self.settings_file)) and os.path.exists(old_settings):
                with open(old_settings, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                with open(self.settings_file, "w", encoding="utf-8") as fp:
                    json.dump(data, fp, ensure_ascii=False, indent=2)
            if (not os.path.exists(self.used_values_file)) and os.path.exists(old_used):
                with open(old_used, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                with open(self.used_values_file, "w", encoding="utf-8") as fp:
                    json.dump(data, fp, ensure_ascii=False, indent=2)
        except Exception:
            pass
        if self.last_library_path and os.path.exists(self.last_library_path):
            try:
                self.load_action_library_from_file(self.last_library_path)
            except Exception:
                pass
    
    def load_default_actions(self) -> None:
        self.action_library = {}
        self.value_library = {}
    
    def load_action_library_from_file(self, file_path: str) -> Tuple[bool, str]:
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            ext = os.path.splitext(file_path)[1].lower()
            if ext == ".xlsx":
                df = pd.read_excel(file_path, engine="openpyxl")
            elif ext == ".xls":
                df = pd.read_excel(file_path, engine="xlrd")
            else:
                df = pd.read_excel(file_path)
            
            value_library: Dict[str, List[str]] = {}
            for col in df.columns:
                col_name = str(col).strip()
                values = [str(v).strip() for v in df[col].dropna().tolist() if str(v).strip()]
                if values:
                    value_library[col_name] = values
            
            self.value_library = value_library
            return True, f"成功加载占位符字段 {len(value_library)} 个"
            
        except Exception as e:
            return False, f"解析文件时出错: {str(e)}"
    
    def get_product_types(self) -> List[str]:
        values = self.value_library.get("产品类型", [])
        return [v for v in values if str(v).strip()]
    
    def get_actions_for_product(self, product_type: str) -> List[str]:
        return [v for v in self.value_library.get("动作", []) if str(v).strip()]
    
    def generate_prompt(self, product_type: str, atmosphere: Optional[str] = None, custom_action: Optional[str] = None, selected_marker_values: Optional[Dict[str, str]] = None) -> str:
        """生成提示词"""
        text, _ = self.generate_prompt_with_spans(product_type, atmosphere, custom_action, selected_marker_values)
        return text

    def generate_prompt_with_spans(self, product_type: str, atmosphere: Optional[str] = None, custom_action: Optional[str] = None, selected_marker_values: Optional[Dict[str, str]] = None) -> Tuple[str, List[Dict[str, Any]]]:
        """生成提示词，并返回替换片段区间用于高亮显示
        返回: (文本, spans)，其中 spans 每项包含 {start, end, marker}
        """
        actions = self.get_actions_for_product(product_type)
        if custom_action:
            selected_action = custom_action
        else:
            selected_action = actions[0] if actions else ""

        template = self.template
        current_product_value = None
        if selected_marker_values:
            current_product_value = selected_marker_values.get("产品") or selected_marker_values.get("产品类型")
        if not current_product_value:
            current_product_value = self.current_product_type
        spans: List[Dict[str, Any]] = []
        output_parts: List[str] = []
        idx = 0
        for m in re.finditer(r"\{([^}]*)\}", template):
            start, end = m.span()
            marker = m.group(1)
            # 先添加占位符前的文本
            output_parts.append(template[idx:start])
            # 计算替换值（优先使用外部指定 selected_marker_values）
            if selected_marker_values and marker in selected_marker_values:
                rep = selected_marker_values[marker]
            elif marker in self.value_library:
                values = self.value_library.get(marker, [])
                if not values:
                    rep = m.group(0)
                used = set(self.used_values.get(marker, []))
                if self.matching_mode == "sequential":
                    idx_cur = self.field_indices.get(marker, 0)
                    if idx_cur >= len(values):
                        idx_cur = 0
                    start_idx = idx_cur
                    rep = None
                    while True:
                        v = values[idx_cur]
                        if v not in used:
                            rep = v
                            break
                        idx_cur = idx_cur + 1 if idx_cur + 1 < len(values) else 0
                        if idx_cur == start_idx:
                            self.used_values[marker] = []
                            used = set()
                            rep = values[start_idx]
                            break
                    self.field_indices[marker] = idx_cur + 1 if idx_cur + 1 < len(values) else 0
                else:
                    attempts = 0
                    rep = None
                    while attempts < 3:
                        candidate = random.choice(values)
                        if candidate not in used:
                            rep = candidate
                            break
                        attempts += 1
                    if rep is None:
                        self.used_values[marker] = []
                        rep = random.choice(values)
            elif marker == "产品类型":
                if current_product_value and str(current_product_value).strip():
                    rep = str(current_product_value).strip()
                else:
                    rep = m.group(0)
            elif marker == "动作":
                if selected_action:
                    used = set(self.used_values.get("动作", []))
                    if selected_action in used and "动作" in self.delete_on_use_fields:
                        actions_pool = [a for a in actions if a not in used] or actions
                        rep = random.choice(actions_pool) if self.matching_mode == "random" else actions_pool[0]
                    else:
                        rep = selected_action
                else:
                    rep = m.group(0)
            elif marker == "氛围":
                if (selected_marker_values and selected_marker_values.get("氛围")):
                    rep = selected_marker_values.get("氛围")
                elif "氛围" in self.value_library:
                    vals = self.value_library.get("氛围", [])
                    if not vals:
                        rep = m.group(0)
                    used = set(self.used_values.get("氛围", []))
                    pool = [v for v in vals if v not in used] or vals
                    rep = random.choice(pool) if self.matching_mode == "random" else pool[0]
                else:
                    rep = m.group(0)
            else:
                rep = m.group(0)
            # 记录替换片段的区间（基于输出文本的字符位置）
            replaced_start_pos = sum(len(p) for p in output_parts)
            output_parts.append(rep)
            replaced_end_pos = replaced_start_pos + len(rep)
            spans.append({"start": replaced_start_pos, "end": replaced_end_pos, "marker": marker})
            # 移动模板索引
            idx = end
        # 追加模板剩余部分
        output_parts.append(template[idx:])
        text = "".join(output_parts)
        return text, spans

    def generate_preview_with_spans(self, product_type: Optional[str] = None, selected_marker_values: Optional[Dict[str, str]] = None) -> Tuple[str, List[Dict[str, Any]]]:
        template = self.template
        current_product_value = None
        if selected_marker_values:
            current_product_value = selected_marker_values.get("产品") or selected_marker_values.get("产品类型")
        if not current_product_value:
            current_product_value = product_type or self.current_product_type
        spans: List[Dict[str, Any]] = []
        output_parts: List[str] = []
        idx = 0
        for m in re.finditer(r"\{([^}]*)\}", template):
            start, end = m.span()
            marker = m.group(1)
            output_parts.append(template[idx:start])
            rep: Optional[str] = None
            if marker in self.value_library:
                values = self.value_library.get(marker, [])
                if values:
                    if self.matching_mode == "sequential":
                        i = self.field_indices.get(marker, 0)
                        if i >= len(values):
                            i = 0
                        rep = values[i]
                    else:
                        rep = random.choice(values)
            elif marker in ("产品", "产品类型"):
                if current_product_value and str(current_product_value).strip():
                    rep = str(current_product_value).strip()
            elif marker == "动作":
                actions = self.get_actions_for_product(current_product_value or "")
                if actions:
                    if self.matching_mode == "sequential":
                        rep = actions[0]
                    else:
                        rep = random.choice(actions)
            elif selected_marker_values and marker in selected_marker_values:
                val = selected_marker_values.get(marker)
                if val:
                    rep = val
            replaced_start_pos = sum(len(p) for p in output_parts)
            if rep is None:
                output_parts.append(m.group(0))
                replaced_end_pos = replaced_start_pos + len(m.group(0))
            else:
                output_parts.append(rep)
                replaced_end_pos = replaced_start_pos + len(rep)
                spans.append({"start": replaced_start_pos, "end": replaced_end_pos, "marker": marker})
            idx = end
        output_parts.append(template[idx:])
        text = "".join(output_parts)
        return text, spans
    
    def extract_markers(self, template: str) -> List[str]:
        """从模板中提取所有标记，如 {产品}、{动作} 等"""
        return list(set(re.findall(r'\{([^}]*)\}', template)))
    
    def save_prompt_to_file(self, prompt: str, file_path: str) -> Tuple[bool, str]:
        """保存提示词到文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(prompt)
            return True, "文件保存成功"
        except Exception as e:
            return False, f"保存文件失败: {str(e)}"
    
    def set_template(self, template: str) -> None:
        self.template = template
        self.current_template_override = template
        self.save_settings()
    
    def get_template(self) -> str:
        """获取当前模板"""
        return self.template

    def set_matching_mode(self, mode: str) -> None:
        self.matching_mode = mode if mode in ("random", "sequential") else "random"
        self.save_settings()

    def set_delete_on_use_fields(self, fields: List[str]) -> None:
        self.delete_on_use_fields = list(set(fields or []))
        self.save_settings()

    def get_empty_selected_fields(self) -> List[str]:
        empty = []
        for f in self.delete_on_use_fields:
            if not self.value_library.get(f):
                empty.append(f)
        return empty

    def load_template_presets(self) -> None:
        try:
            if os.path.exists(self.templates_file):
                with open(self.templates_file, "r", encoding="utf-8") as fp:
                    self.template_presets = json.load(fp) or []
            if not self.template_presets:
                self.template_presets = [{"name": "默认模板", "template": self.DEFAULT_TEMPLATE, "time": datetime.now().isoformat()}]
        except Exception:
            self.template_presets = [{"name": "默认模板", "template": self.DEFAULT_TEMPLATE, "time": datetime.now().isoformat()}]

    def save_template_preset(self, name: str, template: str) -> None:
        preset = {"name": name, "template": template, "time": datetime.now().isoformat()}
        self.template_presets.append(preset)
        try:
            with open(self.templates_file, "w", encoding="utf-8") as fp:
                json.dump(self.template_presets, fp, ensure_ascii=False, indent=2)
        except Exception:
            pass
        self.save_settings(current_preset=name)

    def list_template_names(self) -> List[str]:
        return [p.get("name", "") for p in self.template_presets]

    def get_template_by_name(self, name: str) -> Optional[str]:
        for p in self.template_presets:
            if p.get("name") == name:
                return p.get("template")
        return None

    def set_current_preset(self, name: str) -> None:
        tpl = self.get_template_by_name(name)
        if tpl:
            self.set_template(tpl)
            self.save_settings(current_preset=name)
            self.current_preset_name = name

    def preset_name_exists(self, name: str) -> bool:
        for p in self.template_presets:
            if p.get("name") == name:
                return True
        return False

    def get_current_preset_name(self) -> Optional[str]:
        return self.current_preset_name

    def update_template_preset(self, name: str, template: str) -> bool:
        updated = False
        for p in self.template_presets:
            if p.get("name") == name:
                p["template"] = template
                p["time"] = datetime.now().isoformat()
                updated = True
                break
        if updated:
            try:
                with open(self.templates_file, "w", encoding="utf-8") as fp:
                    json.dump(self.template_presets, fp, ensure_ascii=False, indent=2)
            except Exception:
                pass
            self.set_current_preset(name)
        return updated

    def set_data_file_paths(self, templates_path: Optional[str] = None, settings_path: Optional[str] = None, used_values_path: Optional[str] = None) -> None:
        if templates_path:
            self.templates_file = templates_path
            self.custom_templates_file_path = templates_path
            self.load_template_presets()
        if settings_path:
            self.settings_file = settings_path
            self.custom_settings_file_path = settings_path
        if used_values_path:
            self.used_values_file = used_values_path
            self.custom_used_values_file_path = used_values_path
            self.load_used_values()
        self.save_settings()

    def delete_template_preset(self, name: str) -> bool:
        idx = None
        for i, p in enumerate(self.template_presets):
            if p.get("name") == name:
                idx = i
                break
        if idx is None:
            return False
        self.template_presets.pop(idx)
        try:
            with open(self.templates_file, "w", encoding="utf-8") as fp:
                json.dump(self.template_presets, fp, ensure_ascii=False, indent=2)
        except Exception:
            pass
        return True

    def load_settings(self) -> None:
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                self.matching_mode = data.get("matching_mode", self.matching_mode)
                self.delete_on_use_fields = data.get("delete_on_use_fields", self.delete_on_use_fields)
                current_preset = data.get("current_preset")
                self.current_template_override = data.get("current_template_override", self.current_template_override)
                self.current_preset_name = current_preset
                paths = data.get("data_file_paths") or {}
                if isinstance(paths, dict):
                    tpath = paths.get("templates_file")
                    spath = paths.get("settings_file")
                    upath = paths.get("used_values_file")
                    if tpath:
                        self.templates_file = tpath
                        self.custom_templates_file_path = tpath
                    if spath:
                        self.settings_file = spath
                        self.custom_settings_file_path = spath
                    if upath:
                        self.used_values_file = upath
                        self.custom_used_values_file_path = upath
                if self.current_template_override:
                    self.set_template(self.current_template_override)
                elif current_preset:
                    self.set_current_preset(current_preset)
                self.current_product_type = data.get("current_product_type", self.current_product_type)
                self.result_font_size = int(data.get("result_font_size", self.result_font_size))
                self.last_library_path = data.get("last_library_path", self.last_library_path)
                self.selected_custom_param = data.get("selected_custom_param", self.selected_custom_param)
                self.selected_custom_value = data.get("selected_custom_value", self.selected_custom_value)
                self.custom_params_map = data.get("custom_params_map", self.custom_params_map) or {}
        except Exception:
            pass

    def save_settings(self, current_preset: Optional[str] = None) -> None:
        data = {
            "matching_mode": self.matching_mode,
            "delete_on_use_fields": self.delete_on_use_fields,
            "current_product_type": self.current_product_type,
            "result_font_size": self.result_font_size,
            "last_library_path": self.last_library_path,
            "selected_custom_param": self.selected_custom_param,
            "selected_custom_value": self.selected_custom_value,
            "custom_params_map": self.custom_params_map,
            "current_template_override": self.current_template_override,
            "data_file_paths": {
                "templates_file": self.templates_file,
                "settings_file": self.settings_file,
                "used_values_file": self.used_values_file,
            },
        }
        if current_preset:
            data["current_preset"] = current_preset
        try:
            with open(self.settings_file, "w", encoding="utf-8") as fp:
                json.dump(data, fp, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def set_current_product_type(self, value: Optional[str]) -> None:
        self.current_product_type = value
        self.save_settings()

    def set_result_font_size(self, size: int) -> None:
        self.result_font_size = int(size)
        self.save_settings()

    def get_result_font_size(self) -> int:
        return int(self.result_font_size)

    def load_used_values(self) -> None:
        try:
            if os.path.exists(self.used_values_file):
                with open(self.used_values_file, "r", encoding="utf-8") as fp:
                    self.used_values = json.load(fp) or {}
        except Exception:
            self.used_values = {}

    def save_used_values(self) -> None:
        try:
            with open(self.used_values_file, "w", encoding="utf-8") as fp:
                json.dump(self.used_values, fp, ensure_ascii=False, indent=2)
        except Exception:
            pass
    def set_last_library_path(self, path: Optional[str]) -> None:
        self.last_library_path = path
        self.save_settings()

    def set_selected_custom_param(self, name: Optional[str], value: Optional[str]) -> None:
        self.selected_custom_param = name
        self.selected_custom_value = value
        self.save_settings()

    def set_custom_params_map(self, m: Dict[str, str]) -> None:
        self.custom_params_map = dict(m or {})
        self.save_settings()

    def mark_used_from_spans(self, text: str, spans: List[Dict[str, Any]]) -> None:
        try:
            for s in spans:
                marker = s.get("marker")
                if marker in self.delete_on_use_fields:
                    start = int(s.get("start", 0))
                    end = int(s.get("end", start))
                    val = text[start:end]
                    arr = self.used_values.get(marker, [])
                    if val and val not in arr:
                        arr.append(val)
                        self.used_values[marker] = arr
            self.save_used_values()
        except Exception:
            pass
