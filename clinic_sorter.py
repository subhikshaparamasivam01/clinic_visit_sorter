
"""
CLINIC VISIT SORTER
Educational, non-diagnostic prototype.
A nurse must review every student.
"""

import csv
import json
import os
import re
from datetime import datetime

INPUT_FILE = "visits.csv"
QUEUE_FILE = "nurse_queue.csv"
SUMMARY_FILE = "summary.txt"
PROMPT_FILE = "system_prompt.txt"

CATEGORIES = {
    "injury", "fever_cold", "stomach",
    "pain", "allergy", "other"
}

PRIORITIES = {"see_now", "today", "routine"}

RED_FLAGS = [
    "chest pain",
    "chest ache",
    "breathing difficulty",
    "difficulty breathing",
    "can't breathe",
    "cannot breathe",
    "shortness of breath",
    "breathless",
    "fainting",
    "fainted",
    "heavy bleeding",
    "severe bleeding",
    "lip swelling",
    "lips are swelling",
    "swelling lips",
    "face swelling",
    "facial swelling",
    "cannot stand",
    "can't stand",
    "unable to stand",
    "nenju vali",
    "moochu",
    "moochu kashtam",
    "mayakkam",
    "adhiga ratham",
    "udhadu veekam",
    "mugam veekam"
]


def load_visits(path=INPUT_FILE):
    """Read and validate the student visit CSV."""

    with open(path, newline="", encoding="utf-8-sig") as input_file:
        reader = csv.DictReader(input_file)

        required = {"id", "time", "note"}

        if not required.issubset(reader.fieldnames or []):
            raise ValueError(
                "visits.csv must contain id,time,note columns"
            )

        visits = list(reader)

    if not visits:
        raise ValueError("No student visits found in visits.csv")

    return visits


def is_valid(result):
    """Validate the LLM JSON response."""

    if not isinstance(result, dict):
        return False

    if set(result) != {"category", "priority", "summary"}:
        return False

    if result["category"] not in CATEGORIES:
        return False

    if result["priority"] not in PRIORITIES:
        return False

    if not isinstance(result["summary"], str):
        return False

    if len(result["summary"].split()) > 12:
        return False

    return True


def contains_red_flag(note):
    """Detect listed English and Tamil red-flag phrases."""

    text = note.lower()

    return any(flag in text for flag in RED_FLAGS)


def remove_diagnosis(summary):
    """Remove common diagnosis-style phrases."""

    summary = re.sub(
        r"\b(diagnosed with|you have|this is|likely has|suffering from)\b",
        "",
        summary,
        flags=re.IGNORECASE
    )

    summary = re.sub(r"\s+", " ", summary).strip(" .,:;")

    words = summary.split()[:12]

    return " ".join(words) or "Student report requires nurse review"


def raise_priority(result, note):
    """Never lower priority; listed red flags become see_now."""

    updated = dict(result)

    if contains_red_flag(note):
        updated["priority"] = "see_now"

    return updated


def offline_classify(note):
    """Simple keyword-based fallback classification."""

    text = note.lower()

    category = "other"

    if any(word in text for word in [
        "cut", "wound", "bleeding", "bruise",
        "twisted", "sprain"
    ]):
        category = "injury"

    elif any(word in text for word in [
        "fever", "cold", "sneez", "sore throat", "cough"
    ]):
        category = "fever_cold"

    elif any(word in text for word in [
        "stomach", "vomit", "nausea", "வயிறு"
    ]):
        category = "stomach"

    elif any(word in text for word in [
        "itch", "swelling", "rash", "allergy"
    ]):
        category = "allergy"

    elif any(word in text for word in [
        "pain", "vali", "ache", "headache"
    ]):
        category = "pain"

    routine_words = [
        "certificate",
        "fitness certificate",
        "medical certificate"
    ]

    if any(word in text for word in routine_words):
        priority = "routine"
    else:
        priority = "today"

    result = {
        "category": category,
        "priority": priority,
        "summary": remove_diagnosis(note)
    }

    return raise_priority(result, note)


def classify(note):
    """Use the LLM twice, then use offline fallback."""

    api_key = os.getenv("OPENAI_API_KEY")

    if api_key:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)

            with open(PROMPT_FILE, encoding="utf-8") as prompt_file:
                system_prompt = prompt_file.read()

            for attempt in range(2):

                try:
                    response = client.chat.completions.create(
                        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                        temperature=0,
                        response_format={"type": "json_object"},
                        messages=[
                            {
                                "role": "system",
                                "content": system_prompt
                            },
                            {
                                "role": "user",
                                "content": note
                            }
                        ]
                    )

                    result = json.loads(
                        response.choices[0].message.content
                    )

                    if is_valid(result):
                        result["summary"] = remove_diagnosis(
                            result["summary"]
                        )

                        return raise_priority(result, note)

                except Exception:
                    if attempt == 1:
                        break

        except Exception:
            pass

    # Safe offline fallback
    fallback = offline_classify(note)

    return raise_priority(fallback, note)


def priority_rank(priority):
    """Define the order of priority."""

    return {
        "see_now": 0,
        "today": 1,
        "routine": 2
    }.get(priority, 1)


def write_reports(
    visits,
    results,
    queue_path=QUEUE_FILE,
    summary_path=SUMMARY_FILE
):
    """Generate nurse queue and summary report."""

    rows = []

    for visit, result in zip(visits, results):

        rows.append({
            "id": visit["id"],
            "time": visit["time"],
            "category": result["category"],
            "priority": result["priority"],
            "summary": result["summary"],
            "original_note": visit["note"]
        })

    # Sort by urgency and then arrival time
    rows.sort(
        key=lambda row: (
            priority_rank(row["priority"]),
            row["time"]
        )
    )

    # Write nurse queue CSV
    fields = [
        "id",
        "time",
        "category",
        "priority",
        "summary",
        "original_note"
    ]

    with open(
        queue_path,
        "w",
        newline="",
        encoding="utf-8"
    ) as output_file:

        writer = csv.DictWriter(
            output_file,
            fieldnames=fields
        )

        writer.writeheader()
        writer.writerows(rows)

    # Count priorities
    counts = {
        p: sum(
            1 for r in rows
            if r["priority"] == p
        )
        for p in PRIORITIES
    }

    # Count categories
    category_counts = {
        c: sum(
            1 for r in rows
            if r["category"] == c
        )
        for c in CATEGORIES
    }

    # Count visits by hour
    hourly_counts = {}

    for row in rows:

        try:
            hour = datetime.strptime(
                row["time"], "%H:%M"
            ).strftime("%H:00")

        except ValueError:
            hour = "Unknown"

        hourly_counts[hour] = (
            hourly_counts.get(hour, 0) + 1
        )

    # Write the complete summary report
    with open(
        summary_path,
        "w",
        encoding="utf-8"
    ) as report_file:

        report_file.write(
            "CLINIC VISIT SORTER - NURSE SUMMARY\n"
        )

        report_file.write(
            "All students remain in the queue. "
            "Nurse review is required.\n\n"
        )

        report_file.write(
            f"Total visits: {len(rows)}\n\n"
        )

        report_file.write("Priority counts:\n")

        for key in ("see_now", "today", "routine"):
            report_file.write(
                f"  {key}: {counts[key]}\n"
            )

        report_file.write("\nCategory counts:\n")

        for key in sorted(category_counts):
            report_file.write(
                f"  {key}: {category_counts[key]}\n"
            )

        report_file.write("\nHourly visit counts:\n")

        for hour in sorted(hourly_counts):
            report_file.write(
                f"  {hour}: {hourly_counts[hour]}\n"
            )


def main():
    """Main program."""

    visits = load_visits()

    results = [
        classify(visit["note"])
        for visit in visits
    ]

    write_reports(visits, results)

    print(f"Processed {len(visits)} visits.")

    print(
        f"Queue saved to {QUEUE_FILE}; "
        f"summary saved to {SUMMARY_FILE}."
    )

    print(
        "This tool does not diagnose or provide medical advice. "
        "Nurse review is required."
    )


if __name__ == "__main__":
    main()
