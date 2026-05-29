import requests
from requests.auth import HTTPBasicAuth
import json
import os

# ─── CONFIG ──────────────────────────────────────────────
JIRA_URL    = "https://prathamesh-kletech-1008.atlassian.net"
EMAIL       = "01fe24bci006@kletech.ac.in"
API_TOKEN   = os.environ.get("JIRA_API_TOKEN")
PROJECT_KEY = "AP1"

if not API_TOKEN:
    print("❌ JIRA_API_TOKEN not set. Run: set JIRA_API_TOKEN=your-token")
    exit(1)
# ─────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────

auth    = HTTPBasicAuth(EMAIL, API_TOKEN)
headers = {"Accept": "application/json", "Content-Type": "application/json"}

# ── 1. CREATE AN ISSUE ────────────────────────────────────
def create_issue(summary, issue_type="Task", description=""):
    url  = f"{JIRA_URL}/rest/api/3/issue"
    data = {
        "fields": {
            "project"    : {"key": PROJECT_KEY},
            "summary"    : summary,
            "issuetype"  : {"name": issue_type},
            "description": {
                "type"   : "doc",
                "version": 1,
                "content": [{
                    "type"   : "paragraph",
                    "content": [{"type": "text", "text": description}]
                }]
            }
        }
    }
    response = requests.post(url, headers=headers,
                             auth=auth, data=json.dumps(data))
    if response.status_code == 201:
        key = response.json().get("key", "UNKNOWN")
        print(f"  ✅ Created: {key} — {summary}")
        return key
    else:
        print(f"  ❌ Failed to create '{summary}'")
        print(f"     Status: {response.status_code}")
        print(f"     Reason: {response.text}")
        return None

# ── 2. GET ALL ISSUES ─────────────────────────────────────
def get_all_issues():
    url  = f"{JIRA_URL}/rest/api/3/search/jql"
    body = {
        "jql"        : f"project = {PROJECT_KEY} ORDER BY created DESC",
        "maxResults" : 20,
        "fields"     : ["summary", "status", "issuetype", "assignee"]
    }
    response = requests.post(url, headers=headers,
                              auth=auth, data=json.dumps(body))
    if response.status_code != 200:
        print(f"  ❌ Could not fetch issues")
        print(f"     Status: {response.status_code}")
        print(f"     Reason: {response.text}")
        return

    data   = response.json()
    issues = data.get("issues", [])

    if not issues:
        print("  ⚠️  No issues found in project.")
        return

    print(f"  {'KEY':<10} {'STATUS':<15} {'SUMMARY'}")
    print(f"  {'-'*10} {'-'*15} {'-'*40}")
    for issue in issues:
        key     = issue.get("key", "???")
        fields  = issue.get("fields", {})
        summary = fields.get("summary", "No summary")
        status  = fields.get("status", {}).get("name", "Unknown")
        print(f"  {key:<10} {status:<15} {summary}")

# ── 3. MOVE ISSUE TO IN PROGRESS ──────────────────────────
def move_to_inprogress(issue_key):
    url      = f"{JIRA_URL}/rest/api/3/issue/{issue_key}/transitions"
    response = requests.get(url, headers=headers, auth=auth)

    if response.status_code != 200:
        print(f"  ❌ Could not get transitions for {issue_key}")
        return

    transitions = response.json().get("transitions", [])
    for t in transitions:
        name = t.get("name", "").lower()
        to   = t.get("to", {}).get("name", "").lower()
        if "progress" in name or "progress" in to:
            body = {"transition": {"id": t["id"]}}
            requests.post(url, headers=headers,
                          auth=auth, data=json.dumps(body))
            print(f"  🔄 Moved {issue_key} → In Progress")
            return
    print(f"  ⚠️  No 'In Progress' transition found for {issue_key}")

# ── MAIN ──────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    print("   ApniLeap Jira Automation")
    print("=" * 50)

    print("\n[1] Creating Issues via API...")
    key1 = create_issue(
        "College Onboarding — COEP Pilot Setup",
        issue_type="Task",
        description="Set up COEP as the pilot college in the hub-and-spoke model."
    )
    key2 = create_issue(
        "Company Project Assignment Module",
        issue_type="Story",
        description="As a company, I want to assign projects to students via ApniLeap."
    )
    key3 = create_issue(
        "Student Enrollment API Integration",
        issue_type="Task",
        description="Integrate student enrollment data with Jira tracking system."
    )

    print("\n[2] Moving issue to In Progress...")
    if key1:
        move_to_inprogress(key1)

    print("\n[3] All Issues in Project:")
    get_all_issues()

    print("\n" + "=" * 50)
    print("   Done!")
    print("=" * 50)