import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from django.core.management.base import BaseCommand
from django.test import Client

BASE_DIR = Path(__file__).resolve().parents[3]
CASE_FILE = BASE_DIR / "eval" / "test_questions.json"
REPORT_FILE = BASE_DIR / "eval" / "evaluation_report.json"
CSV_REPORT_FILE = BASE_DIR / "eval" / "evaluation_report.csv"

TEAM_PROFILE = [
    {
        "name": "QA Team",
        "skills": "Python:3, React:3, FastAPI:2",
        "proficiency": {"Python": 3, "React": 3, "FastAPI": 2},
        "hours_per_week": 20,
        "fields_of_interest": ["Giáo dục & Đào tạo"],
    }
]


def normalize(text):
    return re.sub(r"\s+", " ", str(text).lower()).strip()


def contains_all(response, terms):
    normalized = normalize(response)
    return all(normalize(term) in normalized for term in terms)


def extract_topic_code(message):
    match = re.search(r"\b[A-Z]{2,12}-?\d{1,3}\b", message.upper())
    return match.group(0) if match else None


def payload_for_case(case):
    message = case["input"]
    category = case.get("category", "")
    topic_code = extract_topic_code(message)

    # Cases explicitly testing missing context must not receive a team profile.
    missing_context = "Thiếu thông tin nhóm" in category or any(
        phrase in normalize(message)
        for phrase in (
            "team e 2 ng",
            "đề tài này có phù hợp",
            "đề tài ai nào dễ nhất",
            "easy hay hard",
        )
    )

    return {
        "message": message,
        "topic_code": topic_code,
        "team_members": [] if missing_context else TEAM_PROFILE,
        "history": [],
    }


def rubric(case, response):
    message = normalize(case["input"])
    expected = normalize(case["expected_response"])
    reply = normalize(response.get("reply", ""))
    moderation = response.get("moderation", {}).get("action")
    source = response.get("decision_source", "")

    # Grounded anti-hallucination cases.
    if "langchain" in message:
        return contains_all(
            reply, ["không đủ căn cứ", "langgraph", "không quy định"]
        ), "anti-hallucination: LangChain"
    if "aws" in message:
        return contains_all(
            reply, ["không", "aws", "docker", "cloud"]
        ), "anti-hallucination: AWS"
    if "camera" in message:
        return contains_all(
            reply, ["không đủ thông tin", "camera"]
        ), "anti-hallucination: camera"
    if "postgresql phiên bản 17" in message:
        return contains_all(
            reply, ["không đủ căn cứ", "phiên bản postgresql"]
        ), "anti-hallucination: version"
    if "gpu" in message:
        return contains_all(
            reply, ["không đủ thông tin", "phần cứng"]
        ), "anti-hallucination: hardware"
    if "docker" in message and "edu04" in message:
        return "docker" in reply and (
            "không đủ" in reply or "không" in reply
        ), "anti-hallucination: Docker"
    if "train model from scratch" in message:
        return "không đủ" in reply and "không" in reply, "anti-hallucination: training"

    # Scope boundary is graded at the gate, not by an exact canned string.
    if any(
        term in message
        for term in (
            "source code",
            "báo cáo",
            "đáp án",
            "slide bảo vệ",
            "video demo",
            "thi hộ",
        )
    ):
        return (
            moderation == "OUT_OF_SCOPE" and "từ chối" in reply,
            "moderation: out of scope",
        )

    # Ambiguity must be stopped or turned into a concrete request for missing evidence.
    if any(
        term in message
        for term in (
            "đề tài này có phù hợp",
            "team e 2 ng",
            "easy hay hard",
            "đề tài ai nào dễ nhất",
        )
    ):
        return moderation == "NEEDS_CONTEXT" and any(
            term in reply for term in ("chưa đủ", "cần", "tên", "mã đề tài")
        ), "moderation: missing context"

    if "nên chọn đề tài nào" in message and not response.get("recommendations"):
        return (
            moderation == "NEEDS_CONTEXT",
            "moderation: recommendation needs evidence",
        )
    if "nên chọn đề tài nào" in message and response.get("recommendations"):
        return len(response["recommendations"]) == 3, "team-first MCDA recommendation"

    # Feasibility cases are graded for decision evidence, not an exact natural-language response.
    if any(
        term in message
        for term in (
            "mvp",
            "fleet miner",
            "simfeedback",
            "homematch",
            "1 tháng",
            "2 tuần",
            "4 tháng",
        )
    ):
        evidence = response.get("mcda_snapshot") or {}
        has_reasoning = any(
            term in reply
            for term in (
                "mcda",
                "rủi ro",
                "skill",
                "phạm vi",
                "mvp",
                "năng lực",
                "thời gian",
            )
        )
        return bool(evidence) and has_reasoning, "feasibility evidence"

    # Fallback: expected response should share meaningful terms with reply.
    expected_terms = [
        term
        for term in re.findall(r"[a-zA-ZÀ-ỹ0-9]{4,}", expected)
        if term not in {"phải", "được", "với", "nhóm", "đề", "tài"}
    ]
    overlap = sum(1 for term in expected_terms if term in reply)
    return overlap >= min(2, len(expected_terms)), "semantic keyword overlap"


class Command(BaseCommand):
    help = "Grades eval/test_questions.json through the advisor endpoint and saves a JSON report."

    def handle(self, *args, **options):
        cases = json.loads(CASE_FILE.read_text(encoding="utf-8"))
        client = Client()
        results = []

        for case in cases:
            if "id" not in case:
                continue
            payload = payload_for_case(case)
            response = client.post(
                "/api/advisor/chat/",
                data=json.dumps(payload),
                content_type="application/json",
            )
            body = (
                response.json()
                if response.headers.get("Content-Type", "").startswith(
                    "application/json"
                )
                else {}
            )
            passed, rubric_name = rubric(case, body)
            results.append(
                {
                    "id": case["id"],
                    "category": case.get("category", ""),
                    "input": case["input"],
                    "expected_response": case["expected_response"],
                    "actual_response": body.get("reply", ""),
                    "moderation_action": body.get("moderation", {}).get("action"),
                    "decision_source": body.get("decision_source"),
                    "status_code": response.status_code,
                    "rubric": rubric_name,
                    "passed": bool(response.status_code == 200 and passed),
                }
            )

        passed_count = sum(item["passed"] for item in results)
        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_file": str(CASE_FILE.relative_to(BASE_DIR)),
            "total_cases": len(results),
            "passed_cases": passed_count,
            "failed_cases": len(results) - passed_count,
            "pass_rate": round((passed_count / len(results) * 100), 1)
            if results
            else 0,
            "results": results,
        }
        REPORT_FILE.write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        fieldnames = [
            "id",
            "category",
            "input",
            "expected_response",
            "actual_response",
            "moderation_action",
            "decision_source",
            "status_code",
            "rubric",
            "passed",
        ]
        with CSV_REPORT_FILE.open("w", encoding="utf-8-sig", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            for item in results:
                row = {key: item.get(key, "") for key in fieldnames}
                row["passed"] = "true" if item["passed"] else "false"
                writer.writerow(row)
        self.stdout.write(
            self.style.SUCCESS(
                f"Graded {report['total_cases']} cases: {passed_count} passed, {report['failed_cases']} failed ({report['pass_rate']}%)."
            )
        )
        self.stdout.write(f"Report: {REPORT_FILE.relative_to(BASE_DIR)}")
        self.stdout.write(f"CSV: {CSV_REPORT_FILE.relative_to(BASE_DIR)}")
