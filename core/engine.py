"""
Pluggable Skills Core Orchestration Engine.
遵循 KISS 原则：单文件、零重型依赖、极简易读、高扩展性。
"""

import os
import re
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from .validator import ContractValidator


@dataclass
class Plugin:
    """槽位插件元数据与提示词内容"""
    slot: str
    id: str
    name: str
    version: str
    description: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SlotDefinition:
    """槽位定义规范"""
    slot_id: str
    name: str
    description: str
    expected_output_fields: List[str]
    default_fallback: Dict[str, Any] = field(default_factory=dict)


def parse_plugin_markdown(file_path: str) -> Plugin:
    """
    轻量解析 Markdown FrontMatter 与正文。
    无需安装 PyYAML 外部依赖，利用纯正则解析常用键值对。
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"找不到插件文件: {file_path}")

    text = path.read_text(encoding="utf-8")
    frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.DOTALL)

    meta = {}
    content = text
    if frontmatter_match:
        raw_meta = frontmatter_match.group(1)
        content = frontmatter_match.group(2).strip()

        # 简单逐行解析 yaml 键值对
        for line in raw_meta.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                k, v = line.split(":", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                meta[k] = v

    return Plugin(
        slot=meta.get("slot", "unknown"),
        id=meta.get("id", path.stem),
        name=meta.get("name", path.stem),
        version=meta.get("version", "1.0.0"),
        description=meta.get("description", ""),
        content=content,
        metadata=meta
    )


class PluggableSkillEngine:
    """
    可插拔技能流水线编排微内核。
    负责插槽生命周期调度、单步沙箱组装、防污染上下文隔离及契约校验。
    """

    def __init__(self, pipeline_config_path: Optional[str] = None):
        self.slots: Dict[str, SlotDefinition] = {}
        self.mounted_plugins: Dict[str, Plugin] = {}
        self.execution_log: List[str] = []

        if pipeline_config_path:
            self.load_pipeline_config(pipeline_config_path)

    def load_pipeline_config(self, config_path: str):
        """加载流水线槽位配置 (JSON)"""
        p = Path(config_path)
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)

        for slot_info in data.get("slots", []):
            slot_def = SlotDefinition(
                slot_id=slot_info["slot_id"],
                name=slot_info.get("name", slot_info["slot_id"]),
                description=slot_info.get("description", ""),
                expected_output_fields=slot_info.get("expected_output_fields", []),
                default_fallback=slot_info.get("default_fallback", {})
            )
            self.slots[slot_def.slot_id] = slot_def

    def mount_plugin(self, plugin_path: str):
        """挂载一个单文件 Markdown 插件"""
        plugin = parse_plugin_markdown(plugin_path)
        if plugin.slot not in self.slots:
            self.execution_log.append(
                f"[提示] 插件 '{plugin.name}' 挂载到动态槽位: {plugin.slot}"
            )
        self.mounted_plugins[plugin.slot] = plugin
        self.execution_log.append(
            f"成功挂载插件: [{plugin.name}] -> [槽位: {plugin.slot}]"
        )

    def assemble_step_prompt(
        self,
        slot_id: str,
        topic: str,
        previous_clean_data: Dict[str, Any]
    ) -> str:
        """
        核心隔离机制：单步组装 Prompt。
        只引入：
        1. 核心契约与指令 (Core Contract)
        2. 上一步清洗后的干净数据 (Clean Input Data)
        3. 当前挂载插件的局部风格约束 (Ephemeral Plugin Directives)
        【绝对不携带上一插件的 Prompt 历史，杜绝交叉污染】
        """
        slot_def = self.slots.get(slot_id)
        plugin = self.mounted_plugins.get(slot_id)

        prompt_parts = [
            f"# 任务节点：{slot_def.name if slot_def else slot_id}",
            f"全局主题：{topic}",
            f"\n## 上游环节已完成的干净数据输入：",
            json.dumps(previous_clean_data, ensure_ascii=False, indent=2)
        ]

        if plugin:
            prompt_parts.extend([
                f"\n## 【已激活插件风格】：{plugin.name}",
                f"{plugin.content}"
            ])
        else:
            prompt_parts.extend([
                "\n## 【默认系统规则】：",
                "请使用客观、清晰、结构化的方式输出该环节结果。"
            ])

        expected_fields = slot_def.expected_output_fields if slot_def else ["content"]
        prompt_parts.extend([
            f"\n## 输出契约（必须以纯 JSON 格式输出，且必须包含以下字段）：",
            f"字段列表: {json.dumps(expected_fields, ensure_ascii=False)}"
        ])

        return "\n".join(prompt_parts)

    def run_pipeline(
        self,
        topic: str,
        llm_caller: Optional[Callable[[str], Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        端到端按槽位顺序执行流水线。
        llm_caller 为实际调用 LLM 的函数适配器；若为 None 则走预置 Mock 演示。
        """
        accumulated_data: Dict[str, Any] = {"topic": topic}

        for slot_id, slot_def in self.slots.items():
            self.execution_log.append(f"正在执行槽位: [{slot_def.name}] ({slot_id})...")

            # 1. 组装单步沙箱 Prompt
            step_prompt = self.assemble_step_prompt(slot_id, topic, accumulated_data)

            # 2. 执行模型推理 (支持外部适配器或模拟推理)
            if llm_caller:
                raw_output = llm_caller(step_prompt)
            else:
                raw_output = self._mock_llm_execution(slot_id, topic, self.mounted_plugins.get(slot_id))

            # 3. 契约校验与自愈补齐 (保证系统稳定)
            cleaned_step_output, warnings = ContractValidator.validate_and_repair(
                slot_id=slot_id,
                output_data=raw_output,
                expected_fields=slot_def.expected_output_fields,
                default_fallback=slot_def.default_fallback
            )
            self.execution_log.extend(warnings)

            # 4. 数据合并传递（不传递插件自身的提示词环境）
            accumulated_data[slot_id] = cleaned_step_output

        return accumulated_data

    def _mock_llm_execution(
        self,
        slot_id: str,
        topic: str,
        plugin: Optional[Plugin]
    ) -> Dict[str, Any]:
        """用于脱机演示与测试的模拟 LLM 生成逻辑"""
        plugin_name = plugin.name if plugin else "内置默认"
        if "script" in slot_id or "concept" in slot_id:
            return {
                "headline": f"【{plugin_name}风格】{topic}的惊人内幕",
                "body_content": f"根据{plugin_name}的指导，这里以极具特色的口吻深入剖析了关于{topic}的核心本质。",
                "tone_used": plugin_name
            }
        elif "visual" in slot_id or "storyboard" in slot_id:
            return {
                "scenes": [
                    {"scene_id": 1, "prompt": f"特写镜头，{plugin_name}艺术风格呈现的{topic}"},
                    {"scene_id": 2, "prompt": f"全景渲染，符合{plugin_name}色彩倾向的戏剧性画面"}
                ],
                "render_style": plugin_name
            }
        else:
            return {
                "output": f"节点 {slot_id} 由 [{plugin_name}] 处理完成。",
                "summary": f"针对 {topic} 的针对性输出"
            }
