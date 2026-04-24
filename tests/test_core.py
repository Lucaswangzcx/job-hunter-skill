from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from shared import (
    JobTask,
    append_log,
    load_log,
    log_bucket_items,
    normalize_platforms,
    normalize_run_mode,
    platform_user_data_dir,
    resolve_skill_dir,
    save_log,
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


if __name__ == "__main__":
    unittest.main()

