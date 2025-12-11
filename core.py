import os
import random
import re
from typing import Dict, List, Tuple, Optional, Any
import pandas as pd

class PromptGenerator:
    """核心提示词生成器，处理所有业务逻辑"""
    
    DEFAULT_ACTIONS = {
        "裤子": [
            "抬腿拉伸 → 插手裤兜 → 转身体展示大腿剪裁",
            "整理裤腰 → 拉大腿侧布料 → 插手裤袋站立展示",
            "拉裤子大腿部布料 → 踮脚展示裤脚收口 → 自然站立",
            "一只手插口袋 → 一只手拍小腿 → 微笑展示腿部线条",
            "弯腰调整裤脚 → 起身抚摸裤腿 → 转身展示背面",
            "抬腿展示裤子伸展性 → 调整裤脚 → 插口袋定格",
            "侧身站立 → 手指勾起裤腰展示弹性 → 微笑面对镜头",
            "前后踱步 → 展示裤腿垂坠感 → 停下插手展示整体效果",
            "单脚站立 → 展示另一侧裤腿 → 换脚重复动作",
            "坐姿展示 → 起身 → 转身360度展示整体效果"
        ],
        "上衣": [
            "整理衣领 → 抚摸面料质感 → 展示侧面轮廓",
            "拉伸袖口 → 展示手臂活动性 → 自然垂放",
            "整理下摆 → 拍打面料展示弹性 → 微笑面对镜头",
            "转身展示背面设计 → 回头微笑 → 整理领口",
            "抬起手臂 → 展示腋下剪裁 → 放下自然站立",
            "双手抓住下摆两侧 → 拉开展示宽度 → 松手恢复自然状态",
            "手指勾起领口 → 展示领部细节 → 放手整理",
            "轻拉衣角 → 展示下摆设计 → 自然垂放",
            "单手叉腰 → 另一手展示袖口细节 → 换手重复",
            "前后转身 → 展示360度效果 → 定格微笑"
        ],
        "连衣裙": [
            "转圈展示裙摆 → 停下抚摸面料 → 微笑面对镜头",
            "侧身展示剪裁 → 转身正面 → 手轻抚裙摆",
            "提裙角行礼 → 站直展示整体 → 侧身突出腰部设计",
            "自然站立 → 轻提裙摆展示内衬 → 放下整理",
            "双手拉起裙摆两侧 → 展示廓形 → 放下转身",
            "手指轻点肩带 → 展示细节 → 顺着裙摆下滑至脚踝",
            "侧身展示 → 双手向后拢发 → 突出背部设计",
            "轻跳展示裙摆活力 → 站定整理裙褶 → 微笑",
            "单手叉腰 → 另一手展示袖口或领部设计 → 换姿势展示侧面",
            "自然行走 → 停下转身 → 360度展示整体效果"
        ],
        "外套": [
            "穿上外套 → 扣上扣子 → 展示正面效果",
            "打开外套 → 展示内衬和里料 → 扣上展示正面",
            "穿上外套 → 展示袖口细节 → 捏起肩部展示剪裁",
            "侧身站立 → 展示侧面轮廓 → 转身展示背面设计",
            "双手插兜 → 展示整体廓形 → 抬手展示活动性",
            "打开外套 → 随风展示飘逸感 → 扣上展示挺括感",
            "单手系扣 → 展示细节 → 完成后整理领子",
            "穿上外套 → 屈肘展示肩部剪裁 → 放下手自然站立",
            "展示口袋设计 → 插手入袋 → 取出展示口袋容量",
            "前后转身 → 展示360度效果 → 拉起衣领展示细节"
        ]
    }
    
    DEFAULT_ATMOSPHERES = [
        "高能量、高转化力、电影级质感",
        "时尚感、年轻活力、专业质感",
        "轻松自然、生活化、亲和力强",
        "高级感、轻奢调性、精致细节",
        "动感活力、年轻潮流、街拍风格",
        "优雅知性、简约高级、质感突出",
        "休闲舒适、生活场景、真实自然",
        "专业展示、细节放大、品质凸显"
    ]
    
    DEFAULT_TEMPLATE = """主体：一位充满活力的抖音带货达人，镜头全程聚焦，确保【{产品}】是绝对视觉中心。
主体描述：动作连贯有节奏，突出产品核心卖点。面料自然下垂，严禁任何扭曲或拉伸变形，保证结构真实。
动作序列：【{动作}】
镜头语言：动态运镜强化动作细节 —— 推近特写、跟随移动、环绕拍摄。每帧画面变化率 >35%，确保视觉冲击力。
氛围：{氛围}，适合短视频平台快速种草。"""
    
    def __init__(self) -> None:
        self.action_library: Dict[str, List[str]] = {}
        self.value_library: Dict[str, List[str]] = {}
        self.template: str = self.DEFAULT_TEMPLATE
        self.load_default_actions()
    
    def load_default_actions(self) -> None:
        """加载默认动作库"""
        self.action_library = self.DEFAULT_ACTIONS.copy()
        self.value_library = {}
    
    def load_action_library_from_file(self, file_path: str) -> Tuple[bool, str]:
        """从Excel文件加载动作库"""
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
            
            # 识别产品类型列
            action_library: Dict[str, List[str]] = {}
            value_library: Dict[str, List[str]] = {}
            for col in df.columns:
                col_name = str(col).strip()
                values = [str(v).strip() for v in df[col].dropna().tolist() if str(v).strip()]
                if values:
                    value_library[col_name] = values
                # 智能识别产品类型列用于动作库
                if any(keyword in col_name.lower() for keyword in ['裤', '衣', '衫', '裙', '外套', '夹克']):
                    if values:
                        action_library[col_name] = values
            
            if not action_library:
                self.action_library = self.DEFAULT_ACTIONS.copy()
                self.value_library = value_library
                return True, f"成功加载占位符字段 {len(value_library)} 个；未检测到产品列，已使用默认产品类型"
            self.action_library = action_library
            self.value_library = value_library
            return True, f"成功加载 {len(action_library)} 个产品类型，可用占位符字段 {len(value_library)} 个"
            
        except Exception as e:
            return False, f"解析文件时出错: {str(e)}"
    
    def get_product_types(self) -> List[str]:
        types = list(self.action_library.keys())
        if types:
            return types
        return list(self.DEFAULT_ACTIONS.keys())
    
    def get_actions_for_product(self, product_type: str) -> List[str]:
        actions = self.action_library.get(product_type, [])
        if actions:
            return actions
        return self.DEFAULT_ACTIONS.get(product_type, [])
    
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
            selected_action = actions[0] if not actions else random.choice(actions)

        if not atmosphere:
            atmosphere = random.choice(self.DEFAULT_ATMOSPHERES)

        template = self.template
        spans: List[Dict[str, Any]] = []
        output_parts: List[str] = []
        idx = 0
        for m in re.finditer(r"\{([^}]*)\}", template):
            start, end = m.span()
            marker = m.group(1)
            # 先添加占位符前的文本
            output_parts.append(template[idx:start])
            # 计算替换值
            # 优先使用变量库
            if marker in self.value_library and self.value_library[marker]:
                rep = random.choice(self.value_library[marker])
            elif marker == "产品":
                rep = product_type
            elif marker == "动作":
                rep = selected_action
            elif marker == "氛围":
                rep = atmosphere
            elif selected_marker_values and marker in selected_marker_values:
                rep = selected_marker_values[marker]
            else:
                rep = f"[自定义:{marker}]"
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
        """设置模板"""
        self.template = template
    
    def get_template(self) -> str:
        """获取当前模板"""
        return self.template
