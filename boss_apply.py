"""Boss直聘自动投递脚本，强制使用 DrissionPage 接管本地 9222 端口浏览器。"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

from shared import (
    JobTask,
    ScoreResult,
    append_log,
    build_boss_search_url,
    find_all,
    find_clickable_by_text,
    find_first,
    get_logger,
    human_sleep,
    load_config,
    load_log,
    log_bucket_items,
    log_contains,
    make_job_key,
    normalize_run_mode,
    open_tab,
    platform_label,
    prepare_runtime,
    resolve_skill_dir,
    run_mode_label,
    safe_attr,
    safe_click,
    safe_input,
    safe_text,
    save_log,
    score_jd,
    start_log_run,
    smooth_scroll,
    finish_log_run,
    wait_for_manual_login,
)


PLATFORM = "boss"
PLATFORM_NAME = platform_label(PLATFORM)

CITY_CODES = {
    "全国": "100010000",
    "北京": "101010100",
    "上海": "101020100",
    "广州": "101280100",
    "深圳": "101280600",
    "杭州": "101210100",
    "成都": "101270100",
    "武汉": "101200100",
    "南京": "101190100",
    "苏州": "101190400",
    "西安": "101110100",
}

CARD_LOCATORS = [
    "css:.job-card-wrap",
    "css:.job-card-wrapper",
    "css:[class*=job-card-wrap]",
    "css:[class*=job-card-wrapper]",
]

TITLE_LOCATORS = [
    "css:.job-name",
    "css:.job-title",
    "css:[class*=job-name]",
    "css:[class*=job-title]",
    "css:h3",
]

COMPANY_LOCATORS = [
    "css:.company-name",
    "css:.brand-name",
    "css:[class*=company-name]",
    "css:[class*=brand-name]",
]

SALARY_LOCATORS = [
    "css:.salary",
    "css:.job-salary",
    "css:[class*=salary]",
]

DETAIL_LOCATORS = [
    "css:.job-detail-body",
    "css:.job-detail-box",
    "css:.job-detail-section",
    "css:.job-sec-text",
    "css:[class*=job-detail]",
    "css:[class*=job-sec]",
]

GREETING_INPUT_LOCATORS = [
    "css:textarea",
    "css:input[placeholder*='打招呼']",
    "css:textarea[placeholder*='打招呼']",
    "css:[contenteditable='true']",
]


def parse_args(default_count: int, default_min_score: int) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=PLATFORM_NAME)
    parser.add_argument("--job", required=True, help="搜索岗位名")
    parser.add_argument("--city", default="全国", help="目标城市")
    parser.add_argument("--count", type=int, default=default_count, help="投递数量")
    parser.add_argument("--min-score", type=int, default=default_min_score, help="最低分")
    parser.add_argument("--mode", choices=("rehearsal", "apply"), help="运行模式")
    parser.add_argument("--port", type=int, default=9222, help="浏览器调试端口")
    parser.add_argument("--skill-dir", default=str(resolve_skill_dir()), help="运行目录")
    parser.add_argument("--skip-login-prompt", action="store_true", help="跳过手动登录确认提示")
    return parser.parse_args()


def extract_card_info(card: Any) -> dict[str, str]:
    title = safe_text(find_first(card, TITLE_LOCATORS, timeout=0.5))
    company = safe_text(find_first(card, COMPANY_LOCATORS, timeout=0.5))
    salary = safe_text(find_first(card, SALARY_LOCATORS, timeout=0.5))

    links = find_all(card, ["css:a"], timeout=0.2)
    href = ""
    for link in links:
        text = safe_text(link)
        link_href = safe_attr(link, "href")
        if not href and "/job_detail/" in link_href:
            href = urljoin("https://www.zhipin.com", link_href)
        if not company and text and text != title and "/gongsi/" in link_href:
            company = text
    if not href:
        link = find_first(card, ["css:a"], timeout=0.2)
        href = urljoin("https://www.zhipin.com", safe_attr(link, "href"))

    if not title:
        lines = [line.strip() for line in safe_text(card).splitlines() if line.strip()]
        title = lines[0] if lines else ""
        company = company or (lines[1] if len(lines) > 1 else "")

    return {
        "title": title,
        "company": company,
        "salary": salary,
        "href": href,
        "raw_text": safe_text(card),
    }


def extract_detail_text(tab: Any) -> str:
    detail_root = find_first(tab, DETAIL_LOCATORS, timeout=1.5)
    if detail_root is not None:
        try:
            detail_root.scroll.to_see()
        except Exception:
            pass
        smooth_scroll(detail_root, steps=4, min_pixel=240, max_pixel=520)
        text = safe_text(detail_root)
        if text:
            return text

    smooth_scroll(tab, steps=4, min_pixel=260, max_pixel=580)
    for locator in DETAIL_LOCATORS:
        root = find_first(tab, [locator], timeout=0.8)
        text = safe_text(root)
        if text:
            return text
    return safe_text(tab)


def click_apply_button(detail_tab: Any, greeting: str) -> tuple[str, str]:
    button = find_clickable_by_text(detail_tab, ["立即沟通", "继续沟通", "立即投递", "发送简历"])
    if button is None:
        return "failed", "未找到立即沟通按钮。"

    button_text = safe_text(button)
    button_class = safe_attr(button, "class").lower()
    if any(flag in button_text for flag in ("已沟通", "继续沟通", "今日沟通上限", "停止招聘")):
        return "skipped", f"按钮状态不允许继续投递：{button_text}"
    if any(flag in button_class for flag in ("disabled", "is-disabled")):
        return "skipped", "立即沟通按钮处于禁用状态。"

    if not safe_click(button, by_js=None):
        if not safe_click(button, by_js=True):
            return "failed", "点击立即沟通失败。"

    human_sleep(2.0, 3.5)

    if greeting:
        input_box = find_first(detail_tab, GREETING_INPUT_LOCATORS, timeout=1.2)
        if input_box is not None:
            safe_input(input_box, greeting, clear=True)
            send_button = find_clickable_by_text(detail_tab, ["发送", "发送消息", "打招呼"])
            if send_button is not None:
                safe_click(send_button, by_js=None)
                human_sleep(1.0, 2.0)

    return "applied", button_text or "已点击立即沟通"


def apply_jobs(
    *,
    task: JobTask,
    config: dict[str, Any] | None = None,
    browser: Any = None,
    skill_dir: Path | None = None,
) -> dict[str, Any]:
    skill_dir = resolve_skill_dir(skill_dir)
    cfg, browser, resume_text, llm_client = prepare_runtime(
        config=config,
        skill_dir=skill_dir,
        browser=browser,
        debug_port=task.debug_port,
    )
    cfg["min_score"] = int(cfg.get("min_score", 80) if config is None else config.get("min_score", cfg.get("min_score", 80)))
    run_mode = normalize_run_mode(getattr(task, "mode", None), cfg)
    dry_run = run_mode == "rehearsal"
    logger = get_logger("job-hunter.boss", skill_dir=skill_dir)

    city_code = CITY_CODES.get(task.city, CITY_CODES["全国"])
    search_url = build_boss_search_url(task.job_name, city_code)
    log_file = skill_dir / f"boss-{task.city}-log.json"
    log_data = load_log(log_file)

    history_buckets = ("applied", "failed")
    seen_keys = {
        item.get("job_key", "")
        for bucket in history_buckets
        for item in log_bucket_items(log_data, bucket)
    }
    run_id = start_log_run(
        log_data,
        platform=PLATFORM,
        task=task,
        min_score=int(cfg.get("min_score", 80) or 80),
    )

    tab = open_tab(browser, search_url)
    human_sleep(3.0, 4.5)

    summary = {
        "platform": PLATFORM,
        "mode": run_mode,
        "run_id": run_id,
        "applied": 0,
        "reviewed": 0,
        "skipped": 0,
        "failed": 0,
        "count": task.count,
        "min_score": int(cfg.get("min_score", 80) or 80),
        "log_file": str(log_file),
        "message": "",
    }

    idle_rounds = 0
    round_index = 0
    while (summary["reviewed"] < task.count if dry_run else summary["applied"] < task.count) and idle_rounds < 3:
        cards = find_all(tab, CARD_LOCATORS, timeout=2.0)
        if not cards:
            smooth_scroll(tab, steps=3, min_pixel=420, max_pixel=860)
            cards = find_all(tab, CARD_LOCATORS, timeout=2.0)
            if not cards:
                idle_rounds += 1
                continue

        round_index += 1
        logger.info("%s 第 %s 轮扫描，找到 %s 张卡片。", PLATFORM_NAME, round_index, len(cards))
        progressed = False

        for index in range(len(cards)):
            if dry_run and summary["reviewed"] >= task.count:
                break
            if not dry_run and summary["applied"] >= task.count:
                break

            cards = find_all(tab, CARD_LOCATORS, timeout=1.0)
            if index >= len(cards):
                break
            card = cards[index]

            info = extract_card_info(card)
            title = info["title"] or f"未命名岗位-{round_index}-{index}"
            company = info["company"] or "未知公司"
            job_key = make_job_key(PLATFORM, title, company)
            if job_key in seen_keys or log_contains(log_data, "applied", job_key):
                continue

            seen_keys.add(job_key)
            progressed = True
            human_sleep(2.0, 5.0)
            detail_tab = None
            detail_url = info["href"]
            try:
                if detail_url:
                    detail_tab = open_tab(browser, detail_url)
                    human_sleep(1.5, 2.5)
                else:
                    if not safe_click(card, by_js=None):
                        safe_click(card, by_js=True)
                    human_sleep(1.2, 2.2)
                    detail_tab = tab

                jd_text = extract_detail_text(detail_tab)
            except Exception:
                if detail_tab is not None and detail_tab is not tab:
                    try:
                        detail_tab.close()
                    except Exception:
                        pass
                raise

            result: ScoreResult = score_jd(
                title,
                jd_text,
                cfg,
                skill_dir=skill_dir,
                resume_text=resume_text,
                llm_client=llm_client,
            )
            logger.info(
                "%s | %s | %s | %s分 | %s",
                company,
                title,
                info["salary"],
                result.total_score,
                result.reason,
            )
            summary["reviewed"] += 1

            record = {
                "platform": PLATFORM,
                "company": company,
                "job": title,
                "salary": info["salary"],
                "score": result.total_score,
                "rule_score": result.rule_score,
                "llm_score": result.llm_score,
                "reason": result.reason,
                "llm_reason": result.llm_reason,
                "job_key": job_key,
                "run_id": run_id,
                "mode": run_mode,
                "city": task.city,
                "target_job": task.job_name,
                "min_score": int(cfg.get("min_score", 80) or 80),
                "url": getattr(detail_tab, "url", "") if detail_tab is not None else detail_url,
            }

            if result.decision != "apply":
                summary["skipped"] += 1
                record["skip_reason"] = result.reason
                append_log(log_data, "skipped", record)
                save_log(log_data, log_file)
                if detail_tab is not None and detail_tab is not tab:
                    try:
                        detail_tab.close()
                    except Exception:
                        pass
                continue

            try:
                status, apply_reason = click_apply_button(detail_tab, cfg.get("greeting", ""))
            except Exception as exc:
                status, apply_reason = "failed", str(exc)

            record["action_reason"] = apply_reason
            if status == "applied":
                summary["applied"] += 1
                append_log(log_data, "applied", record)
            elif status == "skipped":
                summary["skipped"] += 1
                append_log(log_data, "skipped", record)
            else:
                summary["failed"] += 1
                append_log(log_data, "failed", record)
            save_log(log_data, log_file)
            if detail_tab is not None and detail_tab is not tab:
                try:
                    detail_tab.close()
                except Exception:
                    pass

            if dry_run and summary["reviewed"] < task.count:
                human_sleep(1.0, 2.0)
            elif not dry_run and summary["applied"] < task.count:
                human_sleep(1.5, 3.0)

        previous_count = len(cards)
        smooth_scroll(tab, steps=3, min_pixel=480, max_pixel=980)
        current_count = len(find_all(tab, CARD_LOCATORS, timeout=1.2))
        idle_rounds = 0 if progressed or current_count > previous_count else idle_rounds + 1

    if dry_run:
        summary["message"] = f"{PLATFORM_NAME} {run_mode_label(run_mode)}完成，共检查 {summary['reviewed']} 条岗位。"
    else:
        summary["message"] = f"{PLATFORM_NAME} {run_mode_label(run_mode)}完成。"
    finish_log_run(log_data, run_id, summary)
    save_log(log_data, log_file)
    return summary


def main() -> int:
    defaults = load_config(resolve_skill_dir())
    args = parse_args(int(defaults.get("default_count", 20)), int(defaults.get("min_score", 80)))
    skill_dir = resolve_skill_dir(args.skill_dir)
    config = load_config(skill_dir)
    config["min_score"] = args.min_score
    if args.mode:
        config["default_mode"] = args.mode
    if not wait_for_manual_login(
        skip_prompt=args.skip_login_prompt,
        platforms=[PLATFORM],
        config=config,
        skill_dir=skill_dir,
    ):
        print("用户取消执行。")
        return 0
    task = JobTask(
        job_name=args.job,
        city=args.city,
        count=args.count,
        platforms=[PLATFORM],
        mode=normalize_run_mode(args.mode, config),
        debug_port=args.port,
    )
    result = apply_jobs(task=task, config=config, skill_dir=skill_dir)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
