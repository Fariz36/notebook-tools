import json
import os
import re


def run(notebook, request):
    skills_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "skills.md",
    )

    if not os.path.exists(skills_path):
        alt_path = os.path.join(os.getcwd(), "skills.md")
        if os.path.exists(alt_path):
            skills_path = alt_path
        else:
            return {
                "data": {"available": False, "error": "skills.md not found"},
                "warnings": [],
                "mode": "file_only",
                "observability": {"source": "observed"},
            }

    with open(skills_path, "r") as f:
        content = f.read()

    raw = request.get("raw", False)
    skill_filter = request.get("skill")

    if raw:
        return {
            "data": {
                "available": True,
                "raw_content": content,
                "raw_path": skills_path,
            },
            "warnings": [],
            "mode": "file_only",
            "observability": {"source": "observed"},
        }

    skills = _parse_skills(content)

    if skill_filter:
        skills = [s for s in skills if s["name"].lower() == skill_filter.lower()]

    return {
        "data": {
            "available": True,
            "skills": skills,
            "raw_path": skills_path,
        },
        "warnings": [],
        "mode": "file_only",
        "observability": {"source": "observed"},
    }


def _parse_skills(content):
    skills = []
    current_skill = None
    current_lines = []

    for line in content.splitlines():
        if line.startswith("### "):
            if current_skill is not None:
                skills.append(_build_skill(current_skill, current_lines))
            title = line.replace("### ", "").strip()
            if title in (
                "Notebook Orientation",
                "Error Triage",
                "EDA Copilot",
                "Visualization Assistant",
                "Notebook Cleanup",
                "Reproducibility Auditor",
            ):
                current_skill = title
                current_lines = []
            else:
                current_skill = None
                current_lines = []
            continue

        if line.startswith("## ") and current_skill is not None:
            skills.append(_build_skill(current_skill, current_lines))
            current_skill = None
            current_lines = []
            continue

        if current_skill is not None:
            current_lines.append(line)

    if current_skill is not None:
        skills.append(_build_skill(current_skill, current_lines))

    return skills


def _build_skill(name, lines):
    skill = {"name": name, "goal": "", "triggers": [], "flow": [], "output": ""}
    section = None

    for line in lines:
        stripped = line.strip()

        if _matches_section(stripped, "goal"):
            section = "goal"
            _extract_inline(skill, section, stripped)
            continue
        if _matches_section(stripped, "triggers"):
            section = "triggers"
            _extract_inline(skill, section, stripped)
            continue
        if _matches_section(stripped, "flow"):
            section = "flow"
            continue
        if _matches_section(stripped, "output"):
            section = "output"
            _extract_inline(skill, section, stripped)
            continue

        if section == "goal" and stripped and not stripped.startswith("-"):
            skill["goal"] += stripped + " "
        elif section == "triggers" and stripped.startswith("-"):
            skill["triggers"].append(stripped.lstrip("- ").strip('"').strip("'"))
        elif section == "flow" and stripped:
            cleaned = re.sub(r"^\d+\.\s*", "", stripped)
            skill["flow"].append(cleaned)
        elif section == "output" and stripped and not stripped.startswith("-"):
            skill["output"] += stripped + " "

    skill["goal"] = skill["goal"].strip()
    skill["output"] = skill["output"].strip()

    return skill


def _matches_section(stripped, section):
    bold = f"**{section.capitalize()}:**"
    plain = f"{section.capitalize()}:"
    if section == "triggers":
        bold = "**Triggers:**"
        plain = "Triggers:"
    elif section == "flow":
        bold = "**Flow:**"
        plain = "Flow:"
    elif section == "output":
        bold = "**Expected output:**"
        plain = "Expected output:"
    elif section == "goal":
        bold = "**Goal:**"
        plain = "Goal:"
    return stripped.startswith(bold) or stripped.startswith(plain)


def _extract_inline(skill, section, stripped):
    if section == "goal":
        val = re.sub(r"^\*\*Goal:\*\*\s*", "", stripped)
        val = re.sub(r"^Goal:\s*", "", val)
        skill["goal"] = val.strip().rstrip(".").strip()
    elif section == "triggers":
        val = re.sub(r"^\*\*Triggers:\*\*\s*", "", stripped)
        val = re.sub(r"^Triggers:\s*", "", val)
        parts = [p.strip().strip('"').strip("'") for p in val.split(",")]
        skill["triggers"] = [p for p in parts if p]
    elif section == "output":
        val = re.sub(r"^\*\*Expected output:\*\*\s*", "", stripped)
        val = re.sub(r"^Expected output:\s*", "", val)
        skill["output"] = val.strip()
