from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from job_hunter_skill.skill_entry import prompt_review_skills
from job_hunter_skill.shared import (
    JobTask,
    append_log,
    initialize_config_from_resume,
    keyword_in_text,
    load_log,
    log_bucket_items,
    merge_config,
    normalize_platforms,
    normalize_run_mode,
    platform_user_data_dir,
    resolve_skill_dir,
    save_log,
    sanitize_json_text,
    score_jd,
    split_keywords,
    start_log_run,
    finish_log_run,
)


class SharedTests(unittest.TestCase):
    def test_resolve_skill_dir_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            self.assertEqual(resolve_skill_dir(tmpdir), Path(tmpdir).resolve())

    def test_split_keywords(self) -> None:
        self.assertEqual(
            split_keywords("Java开发实习生, AI产品实习生，Java开发实习生"),
            ["Java开发实习生", "AI产品实习生"],
        )

    def test_keyword_match_tolerates_spacing(self) -> None:
        self.assertTrue(keyword_in_text("Java开发实习生", "Java 开发实习生"))
        self.assertTrue(keyword_in_text("Spring Boot", "SpringBoot 项目经验"))

    def test_normalize_platforms(self) -> None:
        self.assertEqual(normalize_platforms("Boss, 实习僧"), ["boss", "sxs"])

    def test_normalize_run_mode(self) -> None:
        self.assertEqual(normalize_run_mode("安全演练"), "rehearsal")
        self.assertEqual(normalize_run_mode("apply"), "apply")

    def test_platform_user_data_dir_resolves_relative_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = platform_user_data_dir(
                "boss",
                {"user_data_dirs": {"boss": ".job_hunter/browser/boss"}},
                skill_dir=tmpdir,
            )
            self.assertTrue(path.startswith(str(Path(tmpdir).resolve())))

    def test_log_round_trip_with_runs_and_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "boss-北京-log.json"
            task = JobTask(
                job_name="Java开发实习生",
                city="北京",
                count=1,
                platforms=["boss"],
                mode="rehearsal",
                debug_port=9222,
            )

            log_data = load_log(log_path)
            run_id = start_log_run(log_data, platform="boss", task=task, min_score=80)
            append_log(
                log_data,
                "skipped",
                {
                    "run_id": run_id,
                    "job_key": "boss|java开发实习生|测试公司",
                    "job": "Java开发实习生",
                    "company": "测试公司",
                    "score": 72,
                },
            )
            finish_log_run(
                log_data,
                run_id,
                {
                    "mode": "rehearsal",
                    "applied": 0,
                    "reviewed": 1,
                    "skipped": 1,
                    "failed": 0,
                    "count": 1,
                    "min_score": 80,
                    "message": "done",
                },
            )
            save_log(log_data, log_path)

            reloaded = load_log(log_path)
            self.assertEqual(reloaded["schema_version"], 2)
            self.assertEqual(reloaded["meta"]["platform"], "boss")
            self.assertEqual(len(reloaded["runs"]), 1)
            self.assertEqual(len(log_bucket_items(reloaded, "skipped")), 1)
            self.assertEqual(reloaded["analytics"]["counts"]["skipped"], 1)

    def test_score_jd_matches_target_role_with_spacing_difference(self) -> None:
        result = score_jd(
            "Java 开发实习生",
            "岗位要求：熟悉 Java、MySQL、SQL。",
            {
                "target_roles": ["Java开发实习生"],
                "skills": ["Java", "MySQL", "SQL"],
                "min_score": 80,
            },
            resume_text="",
        )

        self.assertEqual(result.role_hit, "Java开发实习生")
        self.assertEqual(result.rule_score, 45)

    def test_score_jd_uses_configurable_scoring(self) -> None:
        result = score_jd(
            "Java 开发实习生",
            "岗位要求：熟悉 Java、MySQL、SQL。",
            {
                "target_roles": ["Java开发实习生"],
                "skills": ["Java", "MySQL", "SQL"],
                "min_score": 80,
                "scoring": {
                    "role_title_score": 40,
                    "skill_score_each": 6,
                    "skill_score_cap": 12,
                    "heuristic_base_score": 0,
                    "heuristic_skill_score_each": 0,
                    "heuristic_skill_score_cap": 0,
                    "heuristic_role_score": 0,
                    "heuristic_bonus_keywords": [],
                    "heuristic_bonus_score": 0,
                },
            },
            resume_text="",
        )

        self.assertEqual(result.rule_score, 52)
        self.assertIn("岗位加分: Java开发实习生(+40)", result.reason)
        self.assertIn("技能命中: Java/MySQL/SQL(+12)", result.reason)

    def test_merge_config_keeps_default_scoring_keys(self) -> None:
        cfg = merge_config({"scoring": {"role_title_score": 42}})

        self.assertEqual(cfg["scoring"]["role_title_score"], 42)
        self.assertIn("skill_score_each", cfg["scoring"])

    def test_sanitize_json_text_removes_surrogates(self) -> None:
        cleaned = sanitize_json_text({"skills": ["Java\udc80"]})

        self.assertEqual(cleaned, {"skills": ["Java "]})

    def test_initialize_config_keeps_user_greeting(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            resume = Path(tmpdir) / "resume.md"
            resume.write_text("Java MySQL Redis Spring Boot Git Linux Docker SQL", encoding="utf-8")

            config, _profile = initialize_config_from_resume(
                resume,
                target_roles=["Java开发实习生"],
                exclude_keywords=["销售"],
                base_config={"greeting": "用户自己填写的话术"},
                skill_dir=tmpdir,
            )

            self.assertEqual(config["greeting"], "用户自己填写的话术")

    def test_prompt_review_skills_requires_user_confirmation(self) -> None:
        inputs = iter(
            [
                "编辑",
                "Java,Spring Boot,MySQL,Redis,Git,Linux,Docker,SQL",
                "接受",
            ]
        )

        with patch("builtins.input", lambda _prompt: next(inputs)), patch(
            "job_hunter_skill.skill_entry.print_line",
            lambda _message="": None,
        ):
            skills = prompt_review_skills(["Java", "MySQL"])

        self.assertEqual(
            skills,
            ["Java", "Spring Boot", "MySQL", "Redis", "Git", "Linux", "Docker", "SQL"],
        )


if __name__ == "__main__":
    unittest.main()
