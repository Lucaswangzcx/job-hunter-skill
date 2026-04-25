"""实习僧自动投递脚本，使用 DrissionPage 接管本地浏览器。"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

from job_hunter_skill.shared import (
    JobTask,
    ScoreResult,
    append_log,
    build_sxs_search_url,
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
    normalize_text,
    normalize_run_mode,
    open_tab,
    platform_label,
    prepare_runtime,
    resolve_skill_dir,
    run_mode_label,
    safe_attr,
    safe_click,
    safe_text,
    sanitize_jd_text,
    save_log,
    score_jd,
    start_log_run,
    smooth_scroll,
    finish_log_run,
    wait_for_manual_login,
)


PLATFORM = "sxs"
PLATFORM_NAME = platform_label(PLATFORM)

CARD_LOCATORS = [
    "css:.intern-wrap.intern-item",
    "css:.intern-wrap",
    "css:[class*=intern-wrap]",
    "css:[class*=intern-item]",
    "css:[class*=position-item]",
    "css:[class*=job-item]",
]

TITLE_LOCATORS = [
    "css:.intern-detail__job a.title",
    "css:.intern-detail__job .title",
    "css:a.title",
    "css:[class*=title]",
    "css:h3",
    "css:a",
]

COMPANY_LOCATORS = [
    "css:.intern-detail__company a[title]",
    "css:.intern-detail__company a",
    "css:.company_name",
    "css:[class*=company]",
    "css:[class*=brand]",
    "css:[class*=enterprise]",
]

CITY_LOCATORS = [
    "css:.intern-detail__job .city",
    "css:.city",
    "css:[class*=city]",
    "css:[class*=area]",
    "css:[class*=location]",
]

DETAIL_LOCATORS = [
    "css:.job_detail",
    "css:.job-content",
    "css:.content_left",
    "css:.intern-detail-page",
    "css:[class*=job_detail]",
    "css:[class*=job-content]",
    "css:[class*=content_left]",
]

DETAIL_TITLE_LOCATORS = [
    "css:.new_job_name",
    "css:.job_name",
    "css:.job-title",
    "css:h1",
]

DETAIL_COMPANY_LOCATORS = [
    "css:.com-name",
    "css:.job_company_name",
    "css:[class*=company] a[title]",
    "css:[class*=company-name]",
]

MODAL_LOCATORS = [
    "css:.el-dialog__wrapper.deliver-dialog-box",
    "css:.deliver-dialog-box__body",
    "css:.dialog-content",
    "css:.el-dialog",
    "css:.el-dialog__wrapper",
    "css:.modal-content",
    "css:[class*=dialog-content]",
    "css:[class*=dialog]",
    "css:[class*=modal]",
]

MODAL_CLOSE_LOCATORS = [
    "css:.common-deliver__header img",
    "css:.success-content img",
    "css:.dialog-close",
    "css:.el-dialog__close",
    "css:[class*=dialog-close]",
    "css:[class*=modal-close]",
    "css:[class*=close]",
]

APPLY_BUTTON_LOCATORS = [
    "css:.btn-box.resume_apply.com_res",
    "css:.resume_apply.com_res",
    "css:.con-job.resume_content .resume_apply.com_res",
]

CONFIRM_BUTTON_LOCATORS = [
    "css:.common-deliver__footer .btn",
    "css:.common-deliver__footer [class*=btn]",
    "xpath://div[normalize-space(text())='确认投递']",
]

SUCCESS_LOCATORS = [
    "xpath://*[contains(normalize-space(.), '投递成功')]",
    "css:.success-content",
    "css:[class*=success]",
]


def parse_args(default_count: int, default_min_score: int) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=PLATFORM_NAME)
    parser.add_argument("--job", required=True, help="搜索岗位名")
    parser.add_argument("--city", default="全国", help="目标城市")
    parser.add_argument("--count", type=int, default=default_count, help="投递数量")
    parser.add_argument("--min-score", type=int, default=default_min_score, help="最低分")
    parser.add_argument("--mode", choices=("rehearsal", "apply"), help="运行模式")
    parser.add_argument("--port", type=int, default=9223, help="浏览器调试端口")
    parser.add_argument("--skill-dir", default=str(resolve_skill_dir()), help="运行目录")
    parser.add_argument("--skip-login-prompt", action="store_true", help="跳过手动登录确认提示")
    return parser.parse_args()


def extract_card_info(card: Any) -> dict[str, str]:
    title_node = find_first(card, TITLE_LOCATORS, timeout=0.4)
    company_node = find_first(card, COMPANY_LOCATORS, timeout=0.4)
    title = safe_text(title_node)
    company = safe_text(company_node)
    city = safe_text(find_first(card, CITY_LOCATORS, timeout=0.4))
    href = ""

    link_candidates = find_all(card, ["css:a[href*='/intern/']", "css:a"], timeout=0.3)
    for link in link_candidates:
        link_href = safe_attr(link, "href")
        if "/intern/" in link_href:
            href = urljoin("https://www.shixiseng.com", link_href)
            if not title:
                title = safe_text(link)
            break
        if not href and link_href:
            href = urljoin("https://www.shixiseng.com", link_href)

    if not company:
        company = safe_attr(company_node, "title")
    if not title:
        title = safe_attr(title_node, "title")

    raw_text = safe_text(card)
    if not title:
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        title = lines[0] if lines else ""
        company = company or (lines[1] if len(lines) > 1 else "")

    company = normalize_text(company)
    if company:
        company = re.split(r"\s{2,}| 以上| 不需要融资| 已上市| 天使轮| A轮| B轮| C轮| 民营| 国企| 外资", company)[0].strip()

    return {
        "title": title,
        "company": company,
        "city": city,
        "href": href,
        "raw_text": raw_text,
    }


def safe_value(node: Any, attr_name: str) -> str:
    if node is None:
        return ""
    try:
        value = getattr(node, attr_name)
        if callable(value):
            value = value()
        return normalize_text(str(value)) if value else ""
    except Exception:
        return ""


def pick_best_text(blocks: list[str]) -> str:
    cleaned_blocks: list[str] = []
    for text in blocks:
        cleaned = sanitize_jd_text(text)
        if cleaned:
            cleaned_blocks.append(cleaned)
    if not cleaned_blocks:
        return ""
    unique_blocks = []
    for text in cleaned_blocks:
        if text not in unique_blocks:
            unique_blocks.append(text)
    unique_blocks.sort(key=len, reverse=True)
    return unique_blocks[0]


def extract_detail_payload(detail_tab: Any, fallback: dict[str, str]) -> dict[str, str]:
    if detail_tab is None:
        return {
            "title": fallback.get("title", ""),
            "company": fallback.get("company", ""),
            "jd_text": "",
        }

    smooth_scroll(detail_tab, steps=4, min_pixel=260, max_pixel=760)

    detail_title = safe_text(find_first(detail_tab, DETAIL_TITLE_LOCATORS, timeout=0.8))
    detail_company = safe_text(find_first(detail_tab, DETAIL_COMPANY_LOCATORS, timeout=0.8))
    page_title = safe_value(detail_tab, "title")
    if not detail_title and page_title:
        detail_title = page_title.split("实习招聘", 1)[0].strip("- ")
    if page_title and not detail_company:
        company_match = re.search(r"实习招聘-([^-]+)", page_title)
        if company_match:
            detail_company = company_match.group(1).strip()

    jd_candidates: list[str] = []
    for locator in DETAIL_LOCATORS:
        block = find_first(detail_tab, [locator], timeout=1.0)
        text = safe_text(block)
        if not text:
            continue
        if any(noise in text for noise in ("百科详情", "登录后查看", "扫码登录", "订阅该职位")):
            continue
        jd_candidates.append(text)

    if not jd_candidates:
        page_text = safe_text(detail_tab)
        if page_text:
            jd_candidates.append(page_text)

    jd_text = pick_best_text(jd_candidates)
    jd_text_zh = sanitize_jd_text(jd_text, chinese_only=True)
    if len(jd_text_zh) >= 80:
        jd_text = jd_text_zh

    section_patterns = [
        r"(岗位职责[:：]?.*?)(任职要求[:：]|职位要求[:：]|岗位要求[:：]|职位亮点[:：]|$)",
        r"(任职要求[:：]?.*?)(职位亮点[:：]|福利待遇[:：]|工作地点[:：]|$)",
        r"(职位描述[:：]?.*?)(职位要求[:：]|任职要求[:：]|岗位要求[:：]|$)",
    ]
    extracted_sections: list[str] = []
    for pattern in section_patterns:
        for match in re.finditer(pattern, jd_text, flags=re.DOTALL):
            section = sanitize_jd_text(match.group(1))
            if section and section not in extracted_sections:
                extracted_sections.append(section)

    if extracted_sections:
        jd_text = "\n".join(extracted_sections)

    return {
        "title": detail_title or fallback.get("title", ""),
        "company": detail_company or fallback.get("company", ""),
        "jd_text": jd_text,
    }


def click_apply(detail_tab: Any) -> tuple[str, str]:
    if detail_tab is None:
        return "failed", "未打开详情页，无法点击投递简历。"
    apply_button = find_first(detail_tab, APPLY_BUTTON_LOCATORS, timeout=1.2)
    if apply_button is None:
        apply_button = find_clickable_by_text(detail_tab, ["投个简历", "投递简历", "立即投递", "立即申请", "申请职位"])
    if apply_button is None:
        return "failed", "未找到投递简历按钮。"

    button_text = safe_text(apply_button)
    classes = safe_attr(apply_button, "class").lower()
    if any(word in button_text for word in ("已投递", "已申请", "停止招聘")):
        return "skipped", f"按钮状态不可投递：{button_text}"
    if "disabled" in classes:
        return "skipped", "投递按钮处于禁用状态。"

    clicked = safe_click(apply_button, by_js=None) or safe_click(apply_button, by_js=True)
    if not clicked:
        return "failed", "点击投递简历失败。"

    human_sleep(1.0, 1.8)
    modal_root = find_first(detail_tab, MODAL_LOCATORS, timeout=2.0) or detail_tab
    modal_text = safe_text(modal_root)

    if "投递成功" not in modal_text:
        confirm_button = find_first(modal_root, CONFIRM_BUTTON_LOCATORS, timeout=1.2)
        if confirm_button is None:
            confirm_button = find_clickable_by_text(detail_tab, ["确认投递", "投递简历", "继续投递", "确定"])
        if confirm_button is not None:
            confirm_classes = safe_attr(confirm_button, "class").lower()
            confirm_text = safe_text(confirm_button)
            if any(word in confirm_text for word in ("已投递", "已申请")):
                return "skipped", f"按钮状态不可投递：{confirm_text}"
            if any(flag in confirm_classes for flag in ("disabled", "disable")):
                return "skipped", "确认投递按钮处于禁用状态，页面信息需人工补充。"
            clicked = safe_click(confirm_button, by_js=None) or safe_click(confirm_button, by_js=True)
            if not clicked:
                return "failed", "点击确认投递失败。"
            human_sleep(1.0, 2.0)
        else:
            return "failed", "未找到确认投递按钮。"

    success_root = find_first(detail_tab, SUCCESS_LOCATORS, timeout=2.0)
    if success_root is None:
        success_root = find_first(detail_tab, MODAL_LOCATORS, timeout=1.0) or detail_tab
    success_text = safe_text(success_root)
    applied_state = find_clickable_by_text(detail_tab, ["已投递", "已申请"])
    if "投递成功" not in success_text and applied_state is None:
        return "failed", "未检测到投递成功提示。"

    close_button = find_clickable_by_text(success_root, ["关闭", "知道了", "完成"])
    if close_button is None:
        close_button = find_first(success_root, MODAL_CLOSE_LOCATORS, timeout=0.3)
    if close_button is not None:
        safe_click(close_button, by_js=None) or safe_click(close_button, by_js=True)
        human_sleep(0.5, 1.0)

    return "applied", "已完成投递并准备关闭详情页"


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
    run_mode = normalize_run_mode(getattr(task, "mode", None), cfg)
    dry_run = run_mode == "rehearsal"
    logger = get_logger("job-hunter.sxs", skill_dir=skill_dir)

    log_file = skill_dir / f"sxs-{task.city}-log.json"
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

    tab = open_tab(browser, build_sxs_search_url(task.job_name))
    human_sleep(2.5, 4.0)

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
    while (summary["reviewed"] < task.count if dry_run else summary["applied"] < task.count) and idle_rounds < 3:
        cards = find_all(tab, CARD_LOCATORS, timeout=2.0)
        if not cards:
            smooth_scroll(tab, steps=3, min_pixel=360, max_pixel=820)
            cards = find_all(tab, CARD_LOCATORS, timeout=2.0)
            if not cards:
                idle_rounds += 1
                continue

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
            title = info["title"] or f"未命名岗位-{index}"
            company = info["company"] or "未知公司"
            job_key = make_job_key(PLATFORM, title, company)
            if job_key in seen_keys or log_contains(log_data, "applied", job_key):
                continue

            seen_keys.add(job_key)
            progressed = True
            if task.city not in ("", "全国") and task.city not in info["raw_text"] and task.city not in info["city"]:
                summary["skipped"] += 1
                append_log(
                    log_data,
                    "skipped",
                    {
                        "platform": PLATFORM,
                        "company": company,
                        "job": title,
                        "job_key": job_key,
                        "run_id": run_id,
                        "mode": run_mode,
                        "city": task.city,
                        "target_job": task.job_name,
                        "min_score": int(cfg.get("min_score", 80) or 80),
                        "reason": f"城市不匹配，目标城市：{task.city}",
                    },
                )
                save_log(log_data, log_file)
                continue

            if not info["href"]:
                summary["failed"] += 1
                append_log(
                    log_data,
                    "failed",
                    {
                        "platform": PLATFORM,
                        "company": company,
                        "job": title,
                        "job_key": job_key,
                        "run_id": run_id,
                        "mode": run_mode,
                        "city": task.city,
                        "target_job": task.job_name,
                        "min_score": int(cfg.get("min_score", 80) or 80),
                        "reason": "未提取到详情链接。",
                    },
                )
                save_log(log_data, log_file)
                continue

            human_sleep(1.5, 3.0)
            detail_tab = open_tab(browser, info["href"])
            current_url = getattr(detail_tab, "url", "") if detail_tab is not None else info["href"]
            detail_payload = extract_detail_payload(detail_tab, info)
            title = detail_payload["title"] or title
            company = detail_payload["company"] or company
            jd_text = detail_payload["jd_text"]
            result: ScoreResult = score_jd(
                title,
                jd_text,
                cfg,
                skill_dir=skill_dir,
                resume_text=resume_text,
                llm_client=llm_client,
            )
            logger.info("%s | %s | %s分 | %s", company, title, result.total_score, result.reason)
            summary["reviewed"] += 1

            record = {
                "platform": PLATFORM,
                "company": company,
                "job": title,
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
                "url": current_url,
            }

            if result.decision != "apply":
                summary["skipped"] += 1
                append_log(log_data, "skipped", record)
                save_log(log_data, log_file)
                if detail_tab is not None:
                    try:
                        detail_tab.close()
                    except Exception:
                        pass
                continue

            status, action_reason = click_apply(detail_tab)
            record["action_reason"] = action_reason

            if detail_tab is not None:
                try:
                    detail_tab.close()
                except Exception:
                    pass

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

            if dry_run and summary["reviewed"] < task.count:
                human_sleep(1.0, 2.0)
            elif not dry_run and summary["applied"] < task.count:
                human_sleep(1.0, 2.0)

        previous_count = len(cards)
        smooth_scroll(tab, steps=3, min_pixel=420, max_pixel=840)
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
