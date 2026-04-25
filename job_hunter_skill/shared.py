"""Job Hunter 公共模块：配置、日志、LLM 接口、评分逻辑、浏览器接管。"""

from __future__ import annotations

import copy
import json
import logging
import os
import random
import re
import socket
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


CODE_DIR = Path(__file__).resolve().parent
PROJECT_NAME = "job-hunter-skill"
PROJECT_VERSION = "0.1.0"
RUNTIME_HOME_ENV = "JOB_HUNTER_HOME"
CONFIG_FILENAME = "config.json"
DEFAULT_GREETING = "您好，我对贵司岗位很感兴趣，期待进一步沟通。"
DEFAULT_PLATFORM_PORTS = {
    "boss": 9222,
    "sxs": 9223,
}
DEFAULT_USER_DATA_DIRS = {
    "boss": ".job_hunter/browser/boss",
    "sxs": ".job_hunter/browser/sxs",
}

DEFAULT_CONFIG: dict[str, Any] = {
    "resume_path": "",
    "greeting": DEFAULT_GREETING,
    "skills": [],
    "target_roles": [],
    "exclude_keywords": [],
    "min_score": 80,
    "default_count": 20,
    "default_mode": "rehearsal",
    "platform_ports": DEFAULT_PLATFORM_PORTS,
    "user_data_dirs": DEFAULT_USER_DATA_DIRS,
    "llm": {
        "base_url": "",
        "api_key": "",
        "model": "gpt-4o-mini",
        "timeout": 60,
        "temperature": 0.2,
    },
}
LOG_SCHEMA_VERSION = 2
LOG_BUCKETS = ("applied", "skipped", "failed")

PLATFORM_LABELS = {
    "boss": "Boss直聘",
    "sxs": "实习僧",
}

PLATFORM_ALIASES = {
    "boss": "boss",
    "boss直聘": "boss",
    "boos": "boss",
    "实习僧": "sxs",
    "sxs": "sxs",
}

RUN_MODE_ALIASES = {
    "rehearsal": "rehearsal",
    "dry-run": "rehearsal",
    "dry_run": "rehearsal",
    "dryrun": "rehearsal",
    "preview": "rehearsal",
    "safe": "rehearsal",
    "演练": "rehearsal",
    "安全演练": "rehearsal",
    "正式": "apply",
    "真投": "apply",
    "投递": "apply",
    "正式投递": "apply",
    "apply": "apply",
    "live": "apply",
    "real": "apply",
}

COMMON_SKILL_KEYWORDS = [
    "Python",
    "SQL",
    "Excel",
    "Power BI",
    "Tableau",
    "Pandas",
    "NumPy",
    "Scikit-learn",
    "PyTorch",
    "TensorFlow",
    "机器学习",
    "深度学习",
    "数据分析",
    "数据建模",
    "用户研究",
    "竞品分析",
    "需求分析",
    "产品设计",
    "产品规划",
    "项目管理",
    "流程优化",
    "增长运营",
    "内容运营",
    "活动运营",
    "社群运营",
    "A/B测试",
    "Prompt Engineering",
    "Prompt",
    "大模型",
    "LLM",
    "RAG",
    "Agent",
    "ChatGPT",
    "OpenAI",
    "NLP",
    "推荐系统",
    "Java",
    "Go",
    "C++",
    "JavaScript",
    "TypeScript",
    "React",
    "Vue",
    "Node.js",
    "Flask",
    "FastAPI",
    "Django",
    "Redis",
    "MySQL",
    "PostgreSQL",
    "MongoDB",
    "Linux",
    "Git",
    "Docker",
    "Kubernetes",
    "自动化测试",
    "接口测试",
    "测试开发",
    "性能测试",
    "爬虫",
    "浏览器自动化",
    "SaaS",
    "B端产品",
    "C端产品",
]

CHINESE_STOPWORDS = {
    "负责",
    "参与",
    "以及",
    "相关",
    "通过",
    "包括",
    "工作",
    "项目",
    "经验",
    "能力",
    "熟悉",
    "能够",
    "进行",
    "完成",
    "搭建",
    "优化",
    "输出",
    "提升",
    "推动",
    "协同",
    "团队",
    "业务",
    "公司",
    "岗位",
    "简历",
    "候选人",
    "用户",
}

ENGLISH_STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "that",
    "this",
    "have",
    "used",
    "using",
    "will",
    "your",
    "you",
    "our",
    "into",
    "such",
    "work",
    "team",
    "project",
    "projects",
    "experience",
    "skills",
    "resume",
}

_LOGGER_NAMES: set[str] = set()


@dataclass
class JobTask:
    """一次投递任务的输入参数。"""

    job_name: str
    city: str
    count: int
    platforms: list[str]
    mode: str = "rehearsal"
    debug_port: int = 9222

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ScoreResult:
    """JD 评分结果。"""

    title: str
    total_score: int
    rule_score: int
    llm_score: int
    decision: str
    reason: str
    llm_reason: str
    skill_hits: list[str] = field(default_factory=list)
    role_hit: str | None = None
    exclude_hit: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def resolve_skill_dir(skill_dir: str | Path | None = None) -> Path:
    if skill_dir:
        return Path(skill_dir).expanduser().resolve()

    env_runtime = os.getenv(RUNTIME_HOME_ENV, "").strip()
    if env_runtime:
        return Path(env_runtime).expanduser().resolve()

    return Path.cwd().resolve()


def config_path(skill_dir: str | Path | None = None) -> Path:
    return resolve_skill_dir(skill_dir) / CONFIG_FILENAME


def default_config() -> dict[str, Any]:
    return copy.deepcopy(DEFAULT_CONFIG)


def merge_config(config: dict[str, Any] | None = None) -> dict[str, Any]:
    merged = default_config()
    if not config:
        return merged
    for key, value in config.items():
        if key == "llm" and isinstance(value, dict):
            merged["llm"].update(value)
        elif key in {"platform_ports", "user_data_dirs"} and isinstance(value, dict):
            merged[key].update(value)
        else:
            merged[key] = value
    return merged


def get_logger(name: str = "job-hunter", skill_dir: str | Path | None = None) -> logging.Logger:
    logger = logging.getLogger(name)
    if name in _LOGGER_NAMES:
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False

    log_file = resolve_skill_dir(skill_dir) / "job-hunter.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    _LOGGER_NAMES.add(name)
    return logger


def load_config(skill_dir: str | Path | None = None) -> dict[str, Any]:
    cfg_file = config_path(skill_dir)
    if not cfg_file.exists():
        return default_config()

    try:
        data = json.loads(cfg_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"配置文件格式错误，请检查 {cfg_file}") from exc

    return merge_config(data)


def save_config(config: dict[str, Any], skill_dir: str | Path | None = None) -> Path:
    cfg_file = config_path(skill_dir)
    cfg_file.parent.mkdir(parents=True, exist_ok=True)
    cfg_file.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    return cfg_file


def current_timestamp() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def infer_log_context(log_file: str | Path) -> tuple[str, str]:
    path = Path(log_file)
    stem = path.stem
    if stem.endswith("-log"):
        stem = stem[:-4]
    if "-" not in stem:
        return stem, ""
    platform, city = stem.split("-", 1)
    return platform, city


def empty_log_data(*, platform: str = "", city: str = "") -> dict[str, Any]:
    now = current_timestamp()
    return {
        "schema_version": LOG_SCHEMA_VERSION,
        "meta": {
            "platform": platform,
            "city": city,
            "created_at": now,
            "updated_at": now,
            "last_run_id": "",
        },
        "runs": [],
        "records": {bucket: [] for bucket in LOG_BUCKETS},
        "analytics": {
            "counts": {bucket: 0 for bucket in (*LOG_BUCKETS, "total")},
            "score": {"scored_count": 0, "avg": 0, "min": None, "max": None},
            "top_scores": [],
            "company_totals": [],
        },
    }


def _ensure_record_shape(record: dict[str, Any], bucket: str) -> dict[str, Any]:
    shaped = dict(record)
    shaped.setdefault("bucket", bucket)
    shaped.setdefault("created_at", current_timestamp())
    return shaped


def build_log_analytics(log_data: dict[str, Any]) -> dict[str, Any]:
    records = log_data.get("records", {})
    counts = {bucket: len(records.get(bucket, [])) for bucket in LOG_BUCKETS}
    counts["total"] = sum(counts.values())

    scored_records: list[dict[str, Any]] = []
    company_totals: dict[str, dict[str, Any]] = {}
    for bucket in LOG_BUCKETS:
        for item in records.get(bucket, []):
            company = str(item.get("company", "")).strip() or "未知公司"
            company_entry = company_totals.setdefault(company, {"company": company, "total": 0, "applied": 0})
            company_entry["total"] += 1
            if bucket == "applied":
                company_entry["applied"] += 1

            score = item.get("score")
            if isinstance(score, (int, float)):
                scored_records.append(
                    {
                        "company": company,
                        "job": item.get("job", ""),
                        "score": int(score),
                        "bucket": bucket,
                        "created_at": item.get("created_at", ""),
                        "run_id": item.get("run_id", ""),
                    }
                )

    if scored_records:
        scores = [item["score"] for item in scored_records]
        score_summary = {
            "scored_count": len(scores),
            "avg": round(sum(scores) / len(scores), 2),
            "min": min(scores),
            "max": max(scores),
        }
    else:
        score_summary = {"scored_count": 0, "avg": 0, "min": None, "max": None}

    top_scores = sorted(scored_records, key=lambda item: (-item["score"], item["created_at"]), reverse=False)[:10]
    company_rank = sorted(company_totals.values(), key=lambda item: (-item["total"], -item["applied"], item["company"]))[:10]

    return {
        "counts": counts,
        "score": score_summary,
        "top_scores": top_scores,
        "company_totals": company_rank,
    }


def normalize_log_data(log_data: dict[str, Any] | None = None, log_file: str | Path | None = None) -> dict[str, Any]:
    inferred_platform, inferred_city = infer_log_context(log_file) if log_file else ("", "")
    if not isinstance(log_data, dict):
        log_data = {}

    if "records" not in log_data:
        normalized = empty_log_data(platform=inferred_platform, city=inferred_city)
        for bucket in LOG_BUCKETS:
            normalized["records"][bucket] = [
                _ensure_record_shape(item, bucket)
                for item in log_data.get(bucket, [])
                if isinstance(item, dict)
            ]
        normalized["meta"]["migrated_from_legacy"] = True
    else:
        normalized = empty_log_data(
            platform=str(log_data.get("meta", {}).get("platform") or inferred_platform),
            city=str(log_data.get("meta", {}).get("city") or inferred_city),
        )
        meta = log_data.get("meta", {})
        if isinstance(meta, dict):
            normalized["meta"].update(meta)
        runs = log_data.get("runs", [])
        normalized["runs"] = [dict(item) for item in runs if isinstance(item, dict)]
        records = log_data.get("records", {})
        if isinstance(records, dict):
            for bucket in LOG_BUCKETS:
                normalized["records"][bucket] = [
                    _ensure_record_shape(item, bucket)
                    for item in records.get(bucket, [])
                    if isinstance(item, dict)
                ]

    normalized["schema_version"] = LOG_SCHEMA_VERSION
    normalized["meta"]["platform"] = normalized["meta"].get("platform") or inferred_platform
    normalized["meta"]["city"] = normalized["meta"].get("city") or inferred_city
    normalized["meta"].setdefault("created_at", current_timestamp())
    normalized["meta"]["updated_at"] = current_timestamp()
    normalized["analytics"] = build_log_analytics(normalized)
    return normalized


def load_log(log_file: str | Path) -> dict[str, Any]:
    path = Path(log_file)
    if not path.exists():
        platform, city = infer_log_context(path)
        return empty_log_data(platform=platform, city=city)

    return normalize_log_data(json.loads(path.read_text(encoding="utf-8")), log_file=path)


def save_log(log_data: dict[str, Any], log_file: str | Path) -> Path:
    path = Path(log_file)
    normalized = normalize_log_data(log_data, log_file=path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def log_bucket_items(log_data: dict[str, Any], bucket: str) -> list[dict[str, Any]]:
    normalized = normalize_log_data(log_data)
    return list(normalized.get("records", {}).get(bucket, []))


def start_log_run(
    log_data: dict[str, Any],
    *,
    platform: str,
    task: JobTask,
    min_score: int,
) -> str:
    normalized = normalize_log_data(log_data)
    run_id = f"{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
    run = {
        "run_id": run_id,
        "platform": platform,
        "mode": getattr(task, "mode", "rehearsal"),
        "job_name": task.job_name,
        "city": task.city,
        "target_count": task.count,
        "min_score": int(min_score),
        "debug_port": int(task.debug_port),
        "started_at": current_timestamp(),
        "finished_at": "",
        "status": "running",
        "summary": {},
    }
    normalized["runs"].append(run)
    normalized["meta"]["last_run_id"] = run_id
    normalized["meta"]["updated_at"] = current_timestamp()
    log_data.clear()
    log_data.update(normalized)
    return run_id


def finish_log_run(log_data: dict[str, Any], run_id: str, summary: dict[str, Any]) -> None:
    normalized = normalize_log_data(log_data)
    for run in normalized.get("runs", []):
        if run.get("run_id") == run_id:
            run["finished_at"] = current_timestamp()
            run["status"] = "finished"
            run["summary"] = {
                key: value
                for key, value in summary.items()
                if key in {"mode", "applied", "reviewed", "skipped", "failed", "count", "min_score", "message"}
            }
            break
    normalized["meta"]["updated_at"] = current_timestamp()
    log_data.clear()
    log_data.update(normalized)


def dedupe_keep_order(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        text = str(item).strip()
        if not text:
            continue
        if text.lower() in seen:
            continue
        seen.add(text.lower())
        result.append(text)
    return result


def split_keywords(raw: str | Iterable[str]) -> list[str]:
    if isinstance(raw, str):
        chunks = re.split(r"[,，/\\|；;\n]+", raw)
    else:
        chunks = [str(item) for item in raw]
    return dedupe_keep_order(chunk.strip() for chunk in chunks if str(chunk).strip())


def normalize_platforms(raw: str | Iterable[str]) -> list[str]:
    if isinstance(raw, str):
        tokens = split_keywords(raw)
    else:
        tokens = [str(item).strip() for item in raw]

    normalized: list[str] = []
    for token in tokens:
        key = token.lower().replace(" ", "")
        if key not in PLATFORM_ALIASES:
            raise ValueError(
                f"不支持的平台：{token}。可选值：Boss、实习僧。"
            )
        normalized.append(PLATFORM_ALIASES[key])

    return dedupe_keep_order(normalized)


def platform_label(platform: str) -> str:
    return PLATFORM_LABELS.get(platform, platform)


def platform_debug_port(platform: str, config: dict[str, Any] | None = None) -> int:
    cfg = merge_config(config)
    platform_ports = cfg.get("platform_ports", {})
    default_port = DEFAULT_PLATFORM_PORTS.get(platform, 9222)
    try:
        return int(platform_ports.get(platform, default_port))
    except (TypeError, ValueError):
        return default_port


def platform_user_data_dir(
    platform: str,
    config: dict[str, Any] | None = None,
    *,
    skill_dir: str | Path | None = None,
) -> str:
    cfg = merge_config(config)
    user_data_dirs = cfg.get("user_data_dirs", {})
    value = str(user_data_dirs.get(platform, DEFAULT_USER_DATA_DIRS.get(platform, ".job_hunter/browser/default")))
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = resolve_skill_dir(skill_dir) / path
    return str(path.resolve())


def normalize_run_mode(raw: str | None, config: dict[str, Any] | None = None) -> str:
    if raw:
        key = str(raw).strip().lower().replace(" ", "")
        if key in RUN_MODE_ALIASES:
            return RUN_MODE_ALIASES[key]
        raise ValueError("不支持的运行模式。可选值：rehearsal / apply。")

    cfg = merge_config(config)
    default_mode = str(cfg.get("default_mode", "")).strip()
    if default_mode:
        key = default_mode.lower().replace(" ", "")
        if key in RUN_MODE_ALIASES:
            return RUN_MODE_ALIASES[key]

    if int(cfg.get("min_score", 80) or 80) > 100:
        return "rehearsal"
    return "apply"


def run_mode_label(mode: str) -> str:
    return "安全演练" if normalize_run_mode(mode) == "rehearsal" else "正式投递"


def normalize_text(text: str) -> str:
    text = re.sub(r"&#x?[0-9a-fA-F]+;", " ", text)
    text = re.sub(r"[\ue000-\uf8ff]", " ", text)
    text = text.replace("\u3000", " ").replace("\ufeff", " ").replace("\u200b", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def compact_match_text(text: str) -> str:
    """Return a matching form that tolerates common spacing differences."""

    normalized = normalize_text(text).lower()
    return re.sub(r"[\s\u3000_\-/·・]+", "", normalized)


def keyword_in_text(keyword: str, text: str) -> bool:
    keyword = normalize_text(str(keyword))
    if not keyword:
        return False

    normalized_text = normalize_text(text).lower()
    normalized_keyword = keyword.lower()
    if normalized_keyword in normalized_text:
        return True

    compact_keyword = compact_match_text(keyword)
    if len(compact_keyword) < 2:
        return False
    return compact_keyword in compact_match_text(text)


def sanitize_jd_text(text: str, chinese_only: bool = False) -> str:
    cleaned = normalize_text(text)
    if not chinese_only:
        return cleaned

    chars: list[str] = []
    for char in cleaned:
        if "\u4e00" <= char <= "\u9fff" or char in " ，。；：！？、\n":
            chars.append(char)
        else:
            chars.append(" ")
    return normalize_text("".join(chars))


def clamp_text(text: str, max_chars: int) -> str:
    text = normalize_text(text)
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "…"


def resolve_resume_path(resume_path: str | Path, skill_dir: str | Path | None = None) -> Path:
    candidate = Path(resume_path).expanduser()
    if not candidate.is_absolute():
        candidate = resolve_skill_dir(skill_dir) / candidate
    return candidate.resolve()


def read_text_file(path: str | Path) -> str:
    file_path = Path(path)
    encodings = ("utf-8", "utf-8-sig", "gb18030", "gbk")
    for encoding in encodings:
        try:
            return file_path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise RuntimeError(f"无法识别文件编码：{file_path}")


def read_resume_text(resume_path: str | Path, skill_dir: str | Path | None = None) -> str:
    path = resolve_resume_path(resume_path, skill_dir)
    if not path.exists():
        raise FileNotFoundError(f"找不到简历文件：{path}")
    if path.suffix.lower() == ".pdf":
        raise RuntimeError("当前版本请先将 PDF 简历转换为 .md 或 .txt 后再使用。")
    return read_text_file(path)


def effective_llm_settings(config: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = merge_config(config)
    llm_cfg = dict(cfg.get("llm", {}))

    base_url = (
        llm_cfg.get("base_url")
        or os.getenv("JOB_HUNTER_LLM_BASE_URL")
        or os.getenv("OPENAI_BASE_URL")
        or os.getenv("OPENAI_API_BASE")
        or ""
    )
    api_key = (
        llm_cfg.get("api_key")
        or os.getenv("JOB_HUNTER_LLM_API_KEY")
        or os.getenv("OPENAI_API_KEY")
        or ""
    )
    model = (
        llm_cfg.get("model")
        or os.getenv("JOB_HUNTER_LLM_MODEL")
        or os.getenv("OPENAI_MODEL")
        or "gpt-4o-mini"
    )
    timeout = llm_cfg.get("timeout") or os.getenv("JOB_HUNTER_LLM_TIMEOUT") or 60
    temperature = llm_cfg.get("temperature")
    if temperature is None:
        temperature = os.getenv("JOB_HUNTER_LLM_TEMPERATURE") or 0.2

    return {
        "base_url": str(base_url).strip(),
        "api_key": str(api_key).strip(),
        "model": str(model).strip(),
        "timeout": int(timeout),
        "temperature": float(temperature),
    }


class LLMClient:
    """OpenAI 兼容格式的最小 LLM 客户端。"""

    def __init__(self, settings: dict[str, Any]):
        self.settings = settings

    @property
    def base_url(self) -> str:
        return self.settings.get("base_url", "").rstrip("/")

    @property
    def api_key(self) -> str:
        return self.settings.get("api_key", "")

    @property
    def model(self) -> str:
        return self.settings.get("model", "gpt-4o-mini")

    @property
    def timeout(self) -> int:
        return int(self.settings.get("timeout", 60))

    @property
    def temperature(self) -> float:
        return float(self.settings.get("temperature", 0.2))

    def is_configured(self) -> bool:
        if not self.base_url or not self.model:
            return False
        if self.api_key:
            return True
        return self.base_url.startswith(("http://127.0.0.1", "http://localhost"))

    def _chat_url(self) -> str:
        if self.base_url.endswith("/chat/completions"):
            return self.base_url
        if self.base_url.endswith("/v1"):
            return f"{self.base_url}/chat/completions"
        return f"{self.base_url}/v1/chat/completions"

    def _post_json(self, payload: dict[str, Any]) -> dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        request = Request(
            self._chat_url(),
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"LLM 请求失败（HTTP {exc.code}）：{body}") from exc
        except URLError as exc:
            raise RuntimeError(f"LLM 请求失败：{exc}") from exc

    @staticmethod
    def _message_content(response: dict[str, Any]) -> str:
        choices = response.get("choices") or []
        if not choices:
            raise RuntimeError("LLM 返回结果缺少 choices 字段。")

        message = choices[0].get("message", {})
        content = message.get("content", "")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            texts: list[str] = []
            for item in content:
                if isinstance(item, dict):
                    if item.get("type") == "text" and item.get("text"):
                        texts.append(str(item["text"]))
                    elif item.get("content"):
                        texts.append(str(item["content"]))
            return "\n".join(texts)
        return str(content)

    @staticmethod
    def _extract_json(text: str) -> dict[str, Any]:
        text = text.strip()
        if text.startswith("```"):
            fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
            if fenced:
                text = fenced.group(1).strip()

        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

        start = text.find("{")
        if start == -1:
            raise RuntimeError(f"LLM 未返回 JSON：{text}")

        depth = 0
        in_string = False
        escaping = False
        for index in range(start, len(text)):
            char = text[index]
            if in_string:
                if escaping:
                    escaping = False
                elif char == "\\":
                    escaping = True
                elif char == '"':
                    in_string = False
                continue

            if char == '"':
                in_string = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    fragment = text[start : index + 1]
                    return json.loads(fragment)

        raise RuntimeError(f"无法从 LLM 响应中提取 JSON：{text}")

    def chat_json(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        max_tokens: int = 900,
        temperature: float | None = None,
    ) -> dict[str, Any]:
        if not self.is_configured():
            raise RuntimeError("LLM 未配置。")

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": self.temperature if temperature is None else temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        }

        try:
            response = self._post_json(payload)
        except RuntimeError as exc:
            if "response_format" not in str(exc):
                raise
            payload.pop("response_format", None)
            response = self._post_json(payload)

        return self._extract_json(self._message_content(response))


def build_llm_client(config: dict[str, Any] | None = None) -> LLMClient:
    return LLMClient(effective_llm_settings(config))


def heuristic_extract_skills(resume_text: str, limit: int = 12) -> list[str]:
    normalized = normalize_text(resume_text)
    lowered = normalized.lower()
    matches: list[str] = []

    def add(candidate: str) -> None:
        candidate = candidate.strip(" ,，。；;:/")
        if len(candidate) < 2:
            return
        if candidate.lower() in ENGLISH_STOPWORDS or candidate in CHINESE_STOPWORDS:
            return
        if candidate.lower() not in {item.lower() for item in matches}:
            matches.append(candidate)

    for keyword in COMMON_SKILL_KEYWORDS:
        if keyword.lower() in lowered:
            add(keyword)
        if len(matches) >= limit:
            return matches[:limit]

    english_tokens = re.findall(r"\b[A-Za-z][A-Za-z0-9+#./-]{1,24}\b", normalized)
    for token in english_tokens:
        if token.lower() in ENGLISH_STOPWORDS:
            continue
        if any(char.isdigit() for char in token) and len(token) <= 2:
            continue
        add(token)
        if len(matches) >= limit:
            return matches[:limit]

    chinese_tokens = re.findall(r"[\u4e00-\u9fff]{2,8}", normalized)
    frequencies: dict[str, int] = {}
    for token in chinese_tokens:
        if token in CHINESE_STOPWORDS:
            continue
        if token.startswith(("负责", "参与", "完成", "推动", "能够", "熟悉")):
            continue
        frequencies[token] = frequencies.get(token, 0) + 1

    for token, count in sorted(frequencies.items(), key=lambda item: (-item[1], -len(item[0]))):
        if count < 2 and len(matches) >= 6:
            continue
        add(token)
        if len(matches) >= limit:
            break

    return matches[:limit]


def heuristic_greeting(target_roles: list[str], skills: list[str]) -> str:
    role = target_roles[0] if target_roles else "目标岗位"
    skill_text = "、".join(skills[:2]) if skills else "相关业务"
    greeting = f"您好，我关注贵司{role}岗位，具备{skill_text}相关经验，期待进一步沟通。"
    return clamp_text(greeting, 80)


def build_resume_profile(
    resume_text: str,
    *,
    target_roles: list[str] | None = None,
    exclude_keywords: list[str] | None = None,
    llm_client: LLMClient | None = None,
) -> dict[str, Any]:
    target_roles = target_roles or []
    exclude_keywords = exclude_keywords or []
    llm_client = llm_client or build_llm_client()

    if llm_client.is_configured():
        try:
            payload = llm_client.chat_json(
                (
                    "你是资深招聘顾问。请从简历中提取 8-15 个最能代表候选人的核心技能词，"
                    "并生成一句 80 字以内、真实克制、可直接用于初次沟通的中文打招呼话术。"
                    "只返回 JSON，格式为 {\"skills\":[],\"greeting\":\"\"}。"
                ),
                (
                    f"目标岗位：{', '.join(target_roles) or '未提供'}\n"
                    f"排除关键词：{', '.join(exclude_keywords) or '未提供'}\n"
                    "请基于下面简历内容抽取，不要臆造经验。\n\n"
                    f"{clamp_text(resume_text, 12000)}"
                ),
                max_tokens=900,
            )
            raw_skills = payload.get("skills", [])
            skills = split_keywords(raw_skills if isinstance(raw_skills, list) else str(raw_skills))
            skills = skills[:15]
            if not skills:
                raise RuntimeError("LLM 没有返回技能关键词。")

            greeting = clamp_text(str(payload.get("greeting") or DEFAULT_GREETING), 80)
            return {
                "skills": skills[:15],
                "greeting": greeting,
                "source": "llm",
                "note": "已通过 LLM 完成简历关键词抽取和话术生成。",
            }
        except Exception as exc:
            fallback_skills = heuristic_extract_skills(resume_text)
            return {
                "skills": fallback_skills,
                "greeting": heuristic_greeting(target_roles, fallback_skills),
                "source": "heuristic",
                "note": f"LLM 调用失败，已回退到规则提取：{exc}",
            }

    skills = heuristic_extract_skills(resume_text)
    return {
        "skills": skills,
        "greeting": heuristic_greeting(target_roles, skills),
        "source": "heuristic",
        "note": "未检测到可用的 LLM 配置，已使用规则提取简历关键词。",
    }


def initialize_config_from_resume(
    resume_path: str | Path,
    *,
    target_roles: list[str],
    exclude_keywords: list[str],
    base_config: dict[str, Any] | None = None,
    skill_dir: str | Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    config = merge_config(base_config)
    resolved_resume = resolve_resume_path(resume_path, skill_dir)
    resume_text = read_resume_text(resolved_resume)

    profile = build_resume_profile(
        resume_text,
        target_roles=target_roles,
        exclude_keywords=exclude_keywords,
        llm_client=build_llm_client(config),
    )

    config.update(
        {
            "resume_path": str(resolved_resume),
            "target_roles": dedupe_keep_order(target_roles),
            "exclude_keywords": dedupe_keep_order(exclude_keywords),
            "skills": dedupe_keep_order(profile["skills"])[:15],
            "greeting": clamp_text(str(profile["greeting"]), 80),
            "min_score": int(config.get("min_score", 80) or 80),
        }
    )
    return config, profile


def heuristic_llm_score(
    *,
    role_hit: str | None,
    skill_hits: list[str],
    jd_text: str,
) -> tuple[int, str]:
    score = 6 + min(len(skill_hits) * 4, 20)
    if role_hit:
        score += 8
    jd_lower = jd_text.lower()
    if any(token in jd_lower for token in ("ai", "llm", "模型", "自动化", "数据")):
        score += 4
    score = max(1, min(score, 40))
    return score, "未配置 LLM，按技能重合和岗位相关性做估算。"


def llm_match_score(
    *,
    title: str,
    jd_text: str,
    resume_text: str,
    role_hit: str | None,
    skill_hits: list[str],
    llm_client: LLMClient | None = None,
) -> tuple[int, str]:
    llm_client = llm_client or build_llm_client()
    if not resume_text.strip() or not llm_client.is_configured():
        return heuristic_llm_score(role_hit=role_hit, skill_hits=skill_hits, jd_text=jd_text)

    try:
        payload = llm_client.chat_json(
            (
                "你是求职匹配评分器。你会阅读候选人简历和职位 JD，给出 1-40 分的补充评分。"
                "评分只反映简历与 JD 的真实匹配度，不要重复基础关键词计分。"
                "只输出 JSON：{\"score\":1-40,\"reason\":\"不超过 60 字\"}。"
            ),
            (
                f"岗位标题：{title}\n\n"
                f"候选人简历：\n{clamp_text(resume_text, 6000)}\n\n"
                f"职位 JD：\n{clamp_text(jd_text, 5000)}"
            ),
            max_tokens=600,
            temperature=0.1,
        )
        score = int(payload.get("score", 0))
        score = max(1, min(score, 40))
        reason = clamp_text(str(payload.get("reason") or "LLM 认为岗位匹配度中等。"), 60)
        return score, reason
    except Exception:
        return heuristic_llm_score(role_hit=role_hit, skill_hits=skill_hits, jd_text=jd_text)


def score_jd(
    title: str,
    jd_text: str,
    config: dict[str, Any] | None = None,
    *,
    skill_dir: str | Path | None = None,
    resume_text: str | None = None,
    llm_client: LLMClient | None = None,
) -> ScoreResult:
    cfg = merge_config(config)
    title_clean = normalize_text(title)
    jd_clean = sanitize_jd_text(jd_text)
    combined = f"{title_clean}\n{jd_clean}"

    for keyword in cfg.get("exclude_keywords", []):
        if keyword_in_text(keyword, combined):
            return ScoreResult(
                title=title_clean,
                total_score=0,
                rule_score=0,
                llm_score=0,
                decision="skip",
                reason=f"命中排除关键词：{keyword}",
                llm_reason="未进入 LLM 判定。",
                exclude_hit=keyword,
            )

    rule_score = 0
    role_hit: str | None = None
    for role in cfg.get("target_roles", []):
        if keyword_in_text(role, title_clean):
            role_hit = role
            rule_score += 30
            break

    skill_hits = [
        skill
        for skill in cfg.get("skills", [])
        if keyword_in_text(skill, combined)
    ]
    skill_hits = dedupe_keep_order(skill_hits)
    rule_score += min(len(skill_hits) * 5, 30)

    if resume_text is None and cfg.get("resume_path"):
        try:
            resume_text = read_resume_text(cfg["resume_path"], skill_dir=skill_dir)
        except Exception:
            resume_text = ""

    llm_score, llm_reason = llm_match_score(
        title=title_clean,
        jd_text=jd_clean,
        resume_text=resume_text or "",
        role_hit=role_hit,
        skill_hits=skill_hits,
        llm_client=llm_client or build_llm_client(cfg),
    )

    total_score = min(rule_score + llm_score, 100)
    decision = "apply" if total_score >= int(cfg.get("min_score", 80) or 80) else "skip"

    reason_parts: list[str] = []
    if role_hit:
        reason_parts.append(f"岗位加分: {role_hit}(+30)")
    if skill_hits:
        reason_parts.append(f"技能命中: {'/'.join(skill_hits[:6])}(+{min(len(skill_hits) * 5, 30)})")
    reason_parts.append(f"LLM补分: +{llm_score}")
    reason_parts.append(f"阈值: {cfg.get('min_score', 80)}")

    return ScoreResult(
        title=title_clean,
        total_score=total_score,
        rule_score=rule_score,
        llm_score=llm_score,
        decision=decision,
        reason="；".join(reason_parts),
        llm_reason=llm_reason,
        skill_hits=skill_hits,
        role_hit=role_hit,
    )


def is_cdp_port_ready(debug_port: int = 9222, *, host: str = "127.0.0.1", timeout: float = 0.8) -> bool:
    try:
        with socket.create_connection((host, int(debug_port)), timeout=timeout):
            return True
    except OSError:
        return False


def assert_cdp_port_ready(debug_port: int = 9222) -> None:
    if is_cdp_port_ready(debug_port):
        return
    raise RuntimeError(
        f"未检测到已打开的浏览器调试端口 {debug_port}。"
        "请先按提示手动启动浏览器并登录；skill 不会自动新开浏览器。"
    )


def connect_browser(debug_port: int = 9222):
    """使用 DrissionPage 的 CDP 端口接管模式接入已打开的浏览器。"""

    try:
        from DrissionPage import Chromium, ChromiumOptions
    except ImportError as exc:
        raise RuntimeError(
            "未安装 DrissionPage，请先执行 `pip install DrissionPage`。"
        ) from exc

    assert_cdp_port_ready(debug_port)

    options = ChromiumOptions()
    options.set_local_port(debug_port)

    try:
        browser = Chromium(options)
    except TypeError:
        browser = Chromium(addr_or_opts=options)

    return browser


def human_sleep(min_seconds: float = 2.0, max_seconds: float = 5.0) -> None:
    time.sleep(random.uniform(min_seconds, max_seconds))


def print_browser_login_instructions(
    *,
    platforms: Iterable[str] | None = None,
    config: dict[str, Any] | None = None,
    skill_dir: str | Path | None = None,
    print_func=print,
) -> None:
    cfg = merge_config(config)
    selected_platforms = list(platforms or ["boss", "sxs"])

    print_func("\n[登录确认] 请先手动启动浏览器并完成登录。")
    print_func("请分别启动对应平台的独立浏览器会话，避免 Boss 和 实习僧 共用同一个 CDP 端口。")
    for platform in selected_platforms:
        label = platform_label(platform)
        debug_port = platform_debug_port(platform, cfg)
        user_data_dir = platform_user_data_dir(platform, cfg, skill_dir=skill_dir)
        print_func(f"{label}：")
        print_func(
            '(Windows) & "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe" '
            f'--remote-debugging-port={debug_port} --user-data-dir="{user_data_dir}"'
        )
        print_func(
            "(Mac) /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome "
            f"--remote-debugging-port={debug_port} --user-data-dir=/tmp/chrome-debug-{platform}"
        )
    print_func("登录完成后，请输入 'yes' 继续执行。")


def wait_for_manual_login(
    *,
    skip_prompt: bool = False,
    platforms: Iterable[str] | None = None,
    config: dict[str, Any] | None = None,
    skill_dir: str | Path | None = None,
    input_func=input,
    print_func=print,
) -> bool:
    if skip_prompt:
        return True

    print_browser_login_instructions(
        platforms=platforms,
        config=config,
        skill_dir=skill_dir,
        print_func=print_func,
    )
    while True:
        answer = input_func("请输入 yes 继续，或输入 quit 退出: ").strip().lower()
        if answer == "yes":
            return True
        if answer in {"quit", "exit", "q", "no"}:
            return False
        print_func("未识别输入，请输入 yes 或 quit。")


def open_tab(browser: Any, url: str | None = None):
    """优先新开标签页，失败时退回到最后激活标签页。"""

    tab = None
    try:
        if url:
            tab = browser.new_tab(url)
        else:
            tab = browser.new_tab()
    except Exception:
        tab = getattr(browser, "latest_tab", None)
        if isinstance(tab, str):
            tab = browser.get_tab(tab)
        if url and tab is not None:
            tab.get(url)

    if tab is None:
        raise RuntimeError("无法从浏览器对象获取可操作标签页。")

    try:
        tab.set.timeouts(8)
    except Exception:
        pass
    return tab


def find_first(root: Any, locators: Iterable[str], timeout: float = 1.5):
    if root is None:
        return None
    for locator in locators:
        try:
            element = root.ele(locator, timeout=timeout)
            if element:
                return element
        except Exception:
            continue
    return None


def find_all(root: Any, locators: Iterable[str], timeout: float = 0.8) -> list[Any]:
    if root is None:
        return []
    for locator in locators:
        try:
            elements = root.eles(locator, timeout=timeout)
            if elements:
                return list(elements)
        except Exception:
            continue
    return []


def safe_text(node: Any) -> str:
    if node is None:
        return ""
    for attr_name in ("text", "raw_text", "inner_html", "html"):
        try:
            value = getattr(node, attr_name)
            if callable(value):
                value = value()
            if value:
                return normalize_text(str(value))
        except Exception:
            continue
    return ""


def text_from_locators(root: Any, locators: Iterable[str], timeout: float = 1.0) -> str:
    if root is None:
        return ""
    texts: list[str] = []
    for locator in locators:
        try:
            elements = root.eles(locator, timeout=timeout)
        except Exception:
            elements = []
        if not elements:
            continue
        for element in elements:
            text = safe_text(element)
            if text:
                texts.append(text)
    return normalize_text("\n".join(dedupe_keep_order(texts)))


def safe_attr(node: Any, attr_name: str) -> str:
    if node is None:
        return ""
    try:
        value = node.attr(attr_name)
        return "" if value is None else str(value)
    except Exception:
        return ""


def safe_click(node: Any, *, by_js: bool | None = None) -> bool:
    if node is None:
        return False

    try:
        node.scroll.to_see()
    except Exception:
        pass

    try:
        if by_js is None:
            result = node.click(by_js=None)
        else:
            result = node.click(by_js=by_js)
        return False if result is False else True
    except Exception:
        return False


def safe_input(node: Any, value: str, *, clear: bool = True) -> bool:
    if node is None:
        return False
    try:
        node.scroll.to_see()
    except Exception:
        pass
    try:
        node.input(value, clear=clear)
        return True
    except Exception:
        try:
            node.click()
            node.input(value, clear=clear, by_js=True)
            return True
        except Exception:
            return False


def click_any(root: Any, locators: Iterable[str], timeout: float = 1.0) -> bool:
    if root is None:
        return False
    element = find_first(root, locators, timeout=timeout)
    return safe_click(element, by_js=None)


def input_any(root: Any, locators: Iterable[str], value: str, *, clear: bool = True) -> bool:
    if root is None:
        return False
    element = find_first(root, locators, timeout=1.0)
    return safe_input(element, value, clear=clear)


def smooth_scroll(target: Any, steps: int = 5, *, min_pixel: int = 350, max_pixel: int = 900) -> None:
    if target is None:
        return
    for _ in range(max(1, steps)):
        pixel = random.randint(min_pixel, max_pixel)
        try:
            target.scroll.down(pixel)
        except Exception:
            try:
                target.run_js(f"window.scrollBy(0, {pixel});")
            except Exception:
                break
        time.sleep(random.uniform(0.3, 0.9))


def build_boss_search_url(job_name: str, city_code: str) -> str:
    return f"https://www.zhipin.com/web/geek/jobs?query={quote(job_name)}&city={city_code}"


def build_sxs_search_url(job_name: str) -> str:
    return f"https://www.shixiseng.com/interns?keyword={quote(job_name)}"


def prepare_runtime(
    *,
    config: dict[str, Any] | None = None,
    skill_dir: str | Path | None = None,
    browser: Any = None,
    debug_port: int = 9222,
) -> tuple[dict[str, Any], Any, str, LLMClient]:
    cfg = merge_config(config if config is not None else load_config(skill_dir))
    working_browser = browser or connect_browser(debug_port=debug_port)
    resume_text = ""
    if cfg.get("resume_path"):
        try:
            resume_text = read_resume_text(cfg["resume_path"], skill_dir=skill_dir)
        except Exception:
            resume_text = ""
    return cfg, working_browser, resume_text, build_llm_client(cfg)


def make_job_key(platform: str, title: str, company: str) -> str:
    return f"{platform}|{normalize_text(title).lower()}|{normalize_text(company).lower()}"


def append_log(log_data: dict[str, Any], bucket: str, entry: dict[str, Any]) -> None:
    normalized = normalize_log_data(log_data)
    shaped = _ensure_record_shape(entry, bucket)
    normalized["records"].setdefault(bucket, [])
    normalized["records"][bucket].append(shaped)
    normalized["meta"]["updated_at"] = current_timestamp()
    log_data.clear()
    log_data.update(normalized)


def log_contains(log_data: dict[str, Any], bucket: str, key: str) -> bool:
    for item in log_bucket_items(log_data, bucket):
        if str(item.get("job_key", "")) == key:
            return True
    return False


def find_clickable_by_text(root: Any, keywords: Iterable[str]):
    """在容器中寻找按钮/链接类元素，按文本命中关键字返回第一个。"""

    if root is None:
        return None
    normalized_keywords = [str(keyword).strip() for keyword in keywords if str(keyword).strip()]
    locators = [
        "css:button",
        "css:a",
        "css:input",
        "css:[role=button]",
        "css:[class*=btn]",
        "css:[class*=button]",
        "css:[class*=apply]",
        "css:[class*=chat]",
        "css:[class*=send]",
        "css:[class*=deliver]",
    ]
    seen_ids: set[int] = set()

    for locator in locators:
        try:
            elements = root.eles(locator, timeout=0.4)
        except Exception:
            elements = []
        for element in elements:
            if id(element) in seen_ids:
                continue
            seen_ids.add(id(element))
            text = safe_text(element)
            value = safe_attr(element, "value")
            merged_text = f"{text} {value}".strip()
            if any(keyword in merged_text for keyword in normalized_keywords):
                return element
    return None
