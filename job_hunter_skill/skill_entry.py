"""Job Hunter Skill 入口脚本。"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import inspect
import json
import sys
from pathlib import Path
from typing import Any, Callable

from job_hunter_skill.shared import (
    JobTask,
    PROJECT_NAME,
    PROJECT_VERSION,
    connect_browser,
    get_logger,
    initialize_config_from_resume,
    load_config,
    normalize_platforms,
    normalize_run_mode,
    platform_debug_port,
    platform_label,
    print_browser_login_instructions,
    read_resume_text,
    resolve_skill_dir,
    run_mode_label,
    save_config,
    split_keywords,
)


CODE_DIR = Path(__file__).resolve().parent
SCRIPT_REGISTRY = {
    "boss": {"module": "boss_apply", "functions": ("apply_jobs", "run", "main")},
    "sxs": {"module": "sxs_apply", "functions": ("apply_jobs", "run", "main")},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Job Hunter Skill 入口")
    parser.add_argument(
        "--version",
        action="version",
        version=f"{PROJECT_NAME} {PROJECT_VERSION}",
    )
    parser.add_argument("--platform", help="本次执行的平台，例如 boss 或 sxs")
    parser.add_argument("--job", help="本次搜索岗位名")
    parser.add_argument("--city", help="目标城市")
    parser.add_argument("--count", type=int, help="投递数量")
    parser.add_argument("--mode", help="运行模式：rehearsal 或 apply")
    parser.add_argument("--min-score", type=int, help="本次运行覆盖最低分阈值")
    parser.add_argument("--skill-dir", help="运行目录，用于存放 config.json、resume.md 和日志")
    parser.add_argument("--yes", action="store_true", help="自动确认已完成浏览器登录")
    return parser.parse_args()


def print_line(message: str = "") -> None:
    print(message, flush=True)


def prompt_text(label: str, default: str | None = None, *, required: bool = True) -> str:
    while True:
        suffix = f" [{default}]" if default else ""
        value = input(f"{label}{suffix}: ").strip()
        if value:
            return value
        if default is not None:
            return default
        if not required:
            return ""
        print_line("该项不能为空，请重新输入。")


def prompt_int(label: str, default: int) -> int:
    while True:
        raw = input(f"{label} [{default}]: ").strip()
        if not raw:
            return default
        if raw.isdigit() and int(raw) > 0:
            return int(raw)
        print_line("请输入大于 0 的整数。")


def prompt_keywords(label: str, default: str | None = None) -> list[str]:
    text = prompt_text(label, default=default, required=False)
    return split_keywords(text)


def normalize_single_platform(raw: str) -> str:
    platforms = normalize_platforms(raw)
    if len(platforms) != 1:
        raise ValueError("当前入口一次只执行一个平台，请输入 Boss 或 实习僧。")
    return platforms[0]


def prompt_platform() -> str:
    default_value = "Boss"
    while True:
        raw = prompt_text(
            "本次目标平台（Boss 或 实习僧）",
            default=default_value,
            required=True,
        )
        try:
            return normalize_single_platform(raw)
        except ValueError as exc:
            print_line(str(exc))


def prompt_mode(config: dict[str, Any]) -> str:
    default_value = run_mode_label(normalize_run_mode(None, config))
    while True:
        raw = prompt_text(
            "本次运行模式（安全演练 或 正式投递）",
            default=default_value,
            required=True,
        )
        try:
            return normalize_run_mode(raw, config)
        except ValueError as exc:
            print_line(str(exc))


def ensure_resume_ready(config: dict[str, Any], *, skill_dir: Path) -> dict[str, Any]:
    config_file = skill_dir / "config.json"
    if not config_file.exists():
        return first_run_setup(skill_dir=skill_dir)

    if not config.get("resume_path"):
        print_line("检测到已有 config.json，但缺少 resume_path，重新进入首次引导。")
        return first_run_setup(skill_dir=skill_dir)

    try:
        read_resume_text(config["resume_path"], skill_dir=skill_dir)
        return config
    except Exception as exc:
        print_line(f"现有简历配置不可用：{exc}")
        print_line("将重新进入首次引导。")
        return first_run_setup(skill_dir=skill_dir)


def first_run_setup(*, skill_dir: Path) -> dict[str, Any]:
    print_line("\n[Step 1] 首次引导：生成 config.json")
    default_resume = skill_dir / "resume.md"
    resume_default = str(default_resume) if default_resume.exists() else None

    while True:
        resume_path = prompt_text("请输入 resume.md / resume.txt 路径", default=resume_default)
        target_roles = prompt_keywords("请输入期望岗位关键词（多个用逗号分隔，例如 产品经理,AI产品经理）")
        exclude_keywords = prompt_keywords("请输入排除关键词（多个用逗号分隔，例如 总监,销售）")

        try:
            config, profile = initialize_config_from_resume(
                resume_path,
                target_roles=target_roles,
                exclude_keywords=exclude_keywords,
                skill_dir=skill_dir,
            )
            config_path = save_config(config, skill_dir=skill_dir)
            preview = {
                "resume_path": config["resume_path"],
                "target_roles": config["target_roles"],
                "exclude_keywords": config["exclude_keywords"],
                "skills": config["skills"],
                "greeting": config["greeting"],
                "min_score": config["min_score"],
            }
            print_line(f"\n已生成配置文件：{config_path}")
            print_line(json.dumps(preview, ensure_ascii=False, indent=2))
            print_line(f"初始化方式：{profile['source']} | {profile['note']}")
            return config
        except Exception as exc:
            print_line(f"首次引导失败：{exc}")
            print_line("请修正输入后重试。\n")


def collect_task(config: dict[str, Any], args: argparse.Namespace) -> JobTask:
    print_line("\n[Step 2] 收集本次投递任务信息")
    default_job = config.get("target_roles", [""])[0] if config.get("target_roles") else None
    job_name = args.job or prompt_text("本次搜索岗位名", default=default_job)
    city = args.city or prompt_text("目标城市")
    count = args.count if args.count and args.count > 0 else prompt_int("投递数量", int(config.get("default_count", 20) or 20))
    mode = normalize_run_mode(args.mode, config) if args.mode else prompt_mode(config)
    if args.platform:
        platform = normalize_single_platform(args.platform)
    else:
        platform = prompt_platform()
    return JobTask(job_name=job_name, city=city, count=count, platforms=[platform], mode=mode)


def print_browser_instructions(task: JobTask, config: dict[str, Any], *, skill_dir: Path) -> None:
    print_line("\n[Step 3] 请手动启动浏览器并完成登录")
    print_browser_login_instructions(
        platforms=task.platforms,
        config=config,
        skill_dir=skill_dir,
        print_func=print_line,
    )
    print_line("入口脚本会按平台分别接管各自端口，不再混用同一个浏览器会话。")


def wait_for_confirmation(*, auto_confirm: bool = False) -> bool:
    if auto_confirm:
        return True
    while True:
        answer = input("请输入 yes 继续，或输入 quit 退出: ").strip().lower()
        if answer == "yes":
            return True
        if answer in {"quit", "exit", "q", "no"}:
            return False
        print_line("未识别输入，请输入 yes 或 quit。")


def load_platform_runner(platform: str) -> tuple[Callable[..., Any] | None, Path]:
    script_info = SCRIPT_REGISTRY[platform]
    script_path = CODE_DIR / f"{script_info['module']}.py"
    if not script_path.exists():
        return None, script_path

    module_name = f"job_hunter_skill.{script_info['module']}"
    spec = importlib.util.find_spec(module_name)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载平台脚本：{script_path}")

    module = importlib.import_module(module_name)

    for func_name in script_info["functions"]:
        runner = getattr(module, func_name, None)
        if callable(runner):
            return runner, script_path

    raise RuntimeError(
        f"{script_path.name} 中未找到可调用入口，请实现以下任一函数："
        f"{', '.join(script_info['functions'])}"
    )


def invoke_runner(
    runner: Callable[..., Any],
    *,
    task: JobTask,
    config: dict[str, Any],
    browser: Any,
    skill_dir: Path,
) -> Any:
    signature = inspect.signature(runner)
    call_kwargs: dict[str, Any] = {}
    for parameter in signature.parameters:
        if parameter == "task":
            call_kwargs["task"] = task
        elif parameter == "config":
            call_kwargs["config"] = config
        elif parameter == "browser":
            call_kwargs["browser"] = browser
        elif parameter == "skill_dir":
            call_kwargs["skill_dir"] = skill_dir

    return runner(**call_kwargs)


def print_platform_result(platform: str, result: Any) -> None:
    label = platform_label(platform)
    if result is None:
        print_line(f"{label} 执行完成。")
        return

    if isinstance(result, dict):
        compact = {
            key: value
            for key, value in result.items()
            if key in {"mode", "run_id", "applied", "reviewed", "skipped", "failed", "count", "min_score", "message"}
        }
        if compact:
            print_line(f"{label} 结果：{json.dumps(compact, ensure_ascii=False)}")
            return

    print_line(f"{label} 执行完成，返回：{result}")


def dispatch_platforms(task: JobTask, config: dict[str, Any], *, skill_dir: Path) -> int:
    logger = get_logger(skill_dir=skill_dir)
    executed = 0

    print_line("\n[Step 4] 执行平台投递脚本")
    print_line("说明：当前入口只执行你本次指定的平台，并连接它自己的独立浏览器端口。")

    for platform in task.platforms:
        label = platform_label(platform)
        debug_port = platform_debug_port(platform, config)
        print_line(f"\n开始执行：{label}")
        try:
            runner, script_path = load_platform_runner(platform)
            if runner is None:
                print_line(
                    f"{label} 对应脚本尚未创建：{script_path.name}。"
                    " 入口调度已预留，后续补完适配器即可直接接上。"
                )
                continue

            browser = connect_browser(debug_port=debug_port)
            platform_task = JobTask(
                job_name=task.job_name,
                city=task.city,
                count=task.count,
                platforms=[platform],
                mode=task.mode,
                debug_port=debug_port,
            )
            print_line(f"{label} 将使用浏览器端口 {debug_port}。")
            result = invoke_runner(
                runner,
                task=platform_task,
                config=config,
                browser=browser,
                skill_dir=skill_dir,
            )
            print_platform_result(platform, result)
            executed += 1
        except Exception as exc:
            logger.exception("%s 执行失败", label)
            print_line(f"{label} 执行失败：{exc}")

    return executed


def main() -> int:
    args = parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    runtime_dir = resolve_skill_dir(args.skill_dir)
    logger = get_logger(skill_dir=runtime_dir)
    print_line("Job Hunter 启动中。")
    print_line("流程：配置检查 -> 首次引导/读取配置 -> 收集任务 -> 手动登录浏览器 -> 自动调度平台脚本。\n")
    print_line(f"代码目录：{CODE_DIR}")
    print_line(f"运行目录：{runtime_dir}")

    try:
        config = ensure_resume_ready(load_config(skill_dir=runtime_dir), skill_dir=runtime_dir)
        runtime_config = dict(config)
        if args.min_score is not None:
            runtime_config["min_score"] = int(args.min_score)
        print_line(
            f"当前配置：目标岗位={config.get('target_roles') or []}，"
            f"最低投递分={runtime_config.get('min_score', 80)}，"
            f"默认模式={run_mode_label(normalize_run_mode(None, runtime_config))}。"
        )

        task = collect_task(runtime_config, args)
        print_line(
            f"本次任务：平台={platform_label(task.platforms[0])}，模式={run_mode_label(task.mode)}，"
            f"岗位={task.job_name}，城市={task.city}，数量={task.count}。"
        )
        print_browser_instructions(task, runtime_config, skill_dir=runtime_dir)
        if not wait_for_confirmation(auto_confirm=args.yes):
            print_line("用户取消执行，本次任务结束。")
            return 0

        for platform in task.platforms:
            print_line(
                f"{platform_label(platform)} 预期端口：{platform_debug_port(platform, runtime_config)}"
            )

        executed = dispatch_platforms(task, runtime_config, skill_dir=runtime_dir)
        if executed == 0:
            print_line(
                "\n本次没有成功执行任何平台脚本。请检查浏览器登录状态、平台适配器文件和日志。"
            )
        else:
            print_line(f"\n本次共执行了 {executed} 个平台脚本。当前模式为单平台调度。")
        return 0
    except KeyboardInterrupt:
        print_line("\n用户中断执行。")
        return 130
    except Exception as exc:
        logger.exception("Job Hunter 运行失败")
        print_line(f"\n运行失败：{exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
