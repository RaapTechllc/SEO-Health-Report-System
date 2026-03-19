#!/usr/bin/env python3
"""
Sync PLAN.md to GitHub Issues & Milestones

Usage:
    python3 scripts/sync_plan_to_github.py [--dry-run]

Requirements:
    - gh CLI installed and authenticated (gh auth login)
    - PLAN.md in the root directory (or ../PLAN.md relative to script)
"""

import argparse
import json
import os
import re
import subprocess
import sys
from typing import Optional

# --- Configuration ---
PLAN_PATH = os.path.join(os.path.dirname(__file__), "../PLAN.md")

# ANSI Colors for Output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

    @staticmethod
    def print(text, color=None):
        if color:
            print(f"{color}{text}{Colors.ENDC}")
        else:
            print(text)

# --- Data Structures ---
class Milestone:
    def __init__(self, number: int, title: str, raw_title: str):
        self.number = number
        self.title = title
        self.raw_title = raw_title # e.g., "Milestone 1 — Foundation..."
        self.issues: list[Issue] = []

    def __repr__(self):
        return f"<Milestone {self.number}: {self.title}>"

class Issue:
    def __init__(self, number_id: str, title: str):
        self.number_id = number_id # e.g., "1.1"
        self.title = title
        self.body_lines: list[str] = []
        self.labels: list[str] = []
        self.milestone_obj: Optional[Milestone] = None

    @property
    def body(self) -> str:
        return "\n".join(self.body_lines).strip()

    def __repr__(self):
        return f"<Issue {self.number_id}: {self.title}>"

# --- Parser ---
def parse_plan(path: str) -> list[Milestone]:
    if not os.path.exists(path):
        Colors.print(f"Error: PLAN.md not found at {path}", Colors.RED)
        sys.exit(1)

    with open(path, encoding='utf-8') as f:
        lines = f.readlines()

    milestones: list[Milestone] = []
    current_milestone: Optional[Milestone] = None
    current_issue: Optional[Issue] = None

    # Regex patterns
    milestone_pattern = re.compile(r'^#\s+(Milestone\s+(\d+)\s+—\s+(.+))')
    issue_pattern = re.compile(r'^##\s+(Issue\s+(\d+\.\d+)\s+—\s+(.+))')
    labels_pattern = re.compile(r'^\*\*Labels:\*\*\s+(.+)')

    for line in lines:
        line = line.rstrip()

        # Check for Milestone header
        m_match = milestone_pattern.match(line)
        if m_match:
            # Save previous issue if exists
            if current_issue and current_milestone:
                current_milestone.issues.append(current_issue)
                current_issue = None

            # Create new milestone
            raw_title = m_match.group(1).strip()
            m_num = int(m_match.group(2))
            m_match.group(3).strip()
            # Clean milestone title for GitHub - stick to the full string typically or simplified
            # Let's use the full "Milestone X — Name" as the title for clarity in GH
            final_title = raw_title

            current_milestone = Milestone(m_num, final_title, raw_title)
            milestones.append(current_milestone)
            continue

        # Check for Issue header
        i_match = issue_pattern.match(line)
        if i_match:
            # Save previous issue
            if current_issue and current_milestone:
                current_milestone.issues.append(current_issue)

            raw_issue_title = i_match.group(3).strip()
            issue_id = i_match.group(2)

            # Start new issue
            current_issue = Issue(issue_id, raw_issue_title)
            current_issue.milestone_obj = current_milestone
            continue

        # If inside an issue, parse body and labels
        if current_issue:
            # Parse labels line
            l_match = labels_pattern.match(line)
            if l_match:
                # Extract labels like `P0`, `area:ops`
                raw_labels = l_match.group(1)
                # Find all code-ticked items or just split?
                # The format is `P0`, `area:ops`, ...
                # Let's extract between backticks
                labels = re.findall(r'`([^`]+)`', raw_labels)
                current_issue.labels.extend(labels)
                # We also add the Labels line to the body so it's visible in the issue description
                current_issue.body_lines.append(line)
            else:
                current_issue.body_lines.append(line)

    # Add very last issue
    if current_issue and current_milestone:
        current_milestone.issues.append(current_issue)

    return milestones

# --- GitHub CLI Wrapper ---
def run_gh_command(args: list[str], dry_run: bool = False) -> Optional[str]:
    cmd = ["gh"] + args
    cmd_str = " ".join(cmd)

    if dry_run:
        Colors.print(f"[DRY-RUN] Would execute: {cmd_str}", Colors.YELLOW)
        return None

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        Colors.print(f"Error running command: {cmd_str}", Colors.RED)
        Colors.print(f"Stderr: {e.stderr}", Colors.RED)
        # Don't exit immediately, allow caller to handle or fail
        raise e

def check_gh_auth():
    try:
        subprocess.run(["gh", "auth", "status"], capture_output=True, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

# --- Sync Logic ---
def get_existing_milestones(dry_run: bool) -> dict[str, str]:
    """Returns map of Title -> NodeID or Number"""
    if dry_run:
        return {} # Assume none exist

    try:
        output = run_gh_command(["milestone", "list", "--json", "title,number"], dry_run)
        if output:
            data = json.loads(output)
            return {m['title']: m['number'] for m in data}
    except Exception:
        pass
    return {}

def get_existing_labels(dry_run: bool) -> list[str]:
    if dry_run: return []
    try:
        output = run_gh_command(["label", "list", "--json", "name"], dry_run)
        if output:
            data = json.loads(output)
            return [l['name'] for l in data]
    except Exception:
        pass
    return []

def ensure_label(name: str, color: str, dry_run: bool, existing_labels: list[str]):
    if name in existing_labels:
        return # Already exists

    # Create label
    args = ["label", "create", name, "--color", color, "--description", "Synced from PLAN.md"]
    try:
        run_gh_command(args, dry_run)
        Colors.print(f"Created label: {name}", Colors.GREEN)
    except Exception as e:
         Colors.print(f"Failed to create label {name}: {e}", Colors.RED)

def sync(dry_run: bool = False):
    Colors.print(f"--- Parsing {PLAN_PATH} ---", Colors.HEADER)
    milestones = parse_plan(PLAN_PATH)

    total_issues = sum(len(m.issues) for m in milestones)
    Colors.print(f"Found {len(milestones)} milestones and {total_issues} issues.", Colors.BLUE)

    if not dry_run:
        if not check_gh_auth():
            Colors.print("❌ Not authenticated with GitHub CLI. Please run 'gh auth login' first.", Colors.RED)
            return

    # 1. Sync Milestones
    existing_milestones = get_existing_milestones(dry_run)
    milestone_title_to_number = {}

    Colors.print("\n--- Syncing Milestones ---", Colors.HEADER)
    for m in milestones:
        if m.title in existing_milestones:
            Colors.print(f"Milestone exists: {m.title}", Colors.BLUE)
            milestone_title_to_number[m.title] = existing_milestones[m.title]
        else:
            Colors.print(f"Creating milestone: {m.title}", Colors.GREEN)
            try:
                # gh milestone create --title "..." --description "..."
                # We need to capture the number. gh doesn't easily return just the number in text mode?
                # Actually, capturing stdout gives the URL usually.
                # Let's assume we can fetch it again or parse output.
                # Output format: https://github.com/org/repo/milestone/1
                out = run_gh_command(["milestone", "create", "--title", m.title, "--description", f"Imported from {PLAN_PATH}"], dry_run)
                if dry_run:
                    milestone_title_to_number[m.title] = 999 # Placeholder
                elif out:
                    # simplistic parse
                    match = re.search(r'/milestone/(\d+)', out)
                    if match:
                        milestone_title_to_number[m.title] = int(match.group(1))
            except Exception:
                Colors.print(f"Failed to create milestone {m.title}", Colors.RED)

    # 2. Sync Labels (Basic set)
    # We won't pre-create all labels, but we could.
    # gh issue create automatically creates labels if permissions allow? No, usually errors or creates generic.
    # It sends labels as list. GitHub usually handles creation if they don't exist?
    # Actually, often it requires them to exist. Let's rely on GH handling or simplistic "create if fail" approach?
    # Better: Assume standard labels. The user plan has "P0", "P1", "area:..."
    # We'll skip explicit label creation for now for simplicity, assuming user has permissions or they exist.

    # 3. Sync Issues
    Colors.print("\n--- Syncing Issues ---", Colors.HEADER)

    # We need to check existing issues to avoid duplicates.
    # Use 'gh issue list' filtering? Or just title matching?
    # Scanning ALL issues might be slow.
    # Strategy: Just create them. If we want idempotency, we need a unique identifier in body.
    # We can embed "PLAN_ID: X.Y" in the body text (hidden comment?).

    # Let's perform a search for "PLAN_ID: X.Y" to check existence.
    existing_issue_map = {} # "1.1" -> issue_number

    if not dry_run:
        Colors.print("Fetching existing issues to check for duplicates...", Colors.BLUE)
        try:
             # Search for all issues created by me? or just list all
             # limit 1000
             out = run_gh_command(["issue", "list", "--state", "all", "--limit", "1000", "--json", "title,body,number"], dry_run)
             if out:
                 issues_json = json.loads(out)
                 for i_json in issues_json:
                     # Check body for identifier
                     body = i_json.get('body', '') or ''
                     match = re.search(r'<!-- PLAN_ID: (\d+\.\d+) -->', body)
                     if match:
                         existing_issue_map[match.group(1)] = i_json['number']
        except Exception:
             Colors.print("Could not fetch existing issues. Proceeding carelessly.", Colors.YELLOW)

    for m in milestones:
        m_number = milestone_title_to_number.get(m.title)

        for issue in m.issues:
            if issue.number_id in existing_issue_map:
                Colors.print(f"Skipping Issue {issue.number_id} (already exists as #{existing_issue_map[issue.number_id]})", Colors.BLUE)
                continue

            Colors.print(f"Creating Issue {issue.number_id}: {issue.title}", Colors.GREEN)

            # Add hidden ID to body
            final_body = f"{issue.body}\n\n<!-- PLAN_ID: {issue.number_id} -->"

            cmd_args = ["issue", "create", "--title", issue.title, "--body", final_body]

            if issue.labels:
                 # gh expects --label "l1" --label "l2"
                 for l in issue.labels:
                     cmd_args.extend(["--label", l])

            if m_number:
                cmd_args.extend(["--milestone", str(m_number)])

            try:
                run_gh_command(cmd_args, dry_run)
            except Exception:
                Colors.print(f"Failed to create issue {issue.number_id}", Colors.RED)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Sync PLAN.md to GitHub')
    parser.add_argument('--dry-run', action='store_true', help='Do not actually create things in GitHub')
    args = parser.parse_args()

    try:
        sync(dry_run=args.dry_run)
    except KeyboardInterrupt:
        print("\nAborted.")
