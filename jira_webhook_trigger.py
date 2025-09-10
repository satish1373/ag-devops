#!/usr/bin/env python3
"""
Jira Ticket Reader and Webhook Trigger Script
Reads Jira tickets and generates curl commands to trigger LangGraph DevOps workflow
"""

import os
import sys
import json
import subprocess
import argparse
import requests
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from jira import JIRA
    JIRA_AVAILABLE = True
except ImportError:
    JIRA_AVAILABLE = False
    print("Warning: python-jira not installed. Install with: pip install jira")

try:
    from dotenv import load_dotenv
    load_dotenv()
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False


@dataclass
class JiraConfig:
    """Jira configuration"""
    url: str = os.getenv("JIRA_URL", "")
    username: str = os.getenv("JIRA_USERNAME", "")
    token: str = os.getenv("JIRA_TOKEN", "")
    project_key: str = os.getenv("JIRA_PROJECT_KEY", "DEVOPS")


@dataclass
class WebhookConfig:
    """Webhook configuration"""
    url: str = os.getenv("WEBHOOK_URL", "http://localhost:8000/webhook/jira")
    secret: str = os.getenv("JIRA_WEBHOOK_SECRET", "test-secret")


class JiraTicketReader:
    """Read and process Jira tickets"""
    
    def __init__(self, config: JiraConfig):
        self.config = config
        self.jira_client = None
        
        if JIRA_AVAILABLE and all([config.url, config.username, config.token]):
            try:
                self.jira_client = JIRA(
                    server=config.url,
                    basic_auth=(config.username, config.token)
                )
                print(f"✅ Connected to Jira: {config.url}")
            except Exception as e:
                print(f"❌ Failed to connect to Jira: {e}")
                self.jira_client = None
        else:
            print("⚠️ Jira not configured or unavailable")
    
    def get_ticket(self, ticket_key: str) -> Optional[Dict[str, Any]]:
        """Get ticket details from Jira"""
        if not self.jira_client:
            print(f"❌ Jira client not available for ticket: {ticket_key}")
            return None
        
        try:
            issue = self.jira_client.issue(ticket_key, expand='changelog')
            
            # Extract comprehensive ticket data
            ticket_data = {
                "key": issue.key,
                "id": issue.id,
                "self": issue.self,
                "fields": {
                    "summary": issue.fields.summary,
                    "description": getattr(issue.fields, 'description', '') or '',
                    "issuetype": {
                        "id": issue.fields.issuetype.id,
                        "name": issue.fields.issuetype.name,
                        "subtask": issue.fields.issuetype.subtask
                    },
                    "priority": {
                        "id": issue.fields.priority.id if issue.fields.priority else "3",
                        "name": issue.fields.priority.name if issue.fields.priority else "Medium"
                    },
                    "status": {
                        "id": issue.fields.status.id,
                        "name": issue.fields.status.name,
                        "statusCategory": {
                            "id": issue.fields.status.statusCategory.id,
                            "name": issue.fields.status.statusCategory.name
                        }
                    },
                    "project": {
                        "id": issue.fields.project.id,
                        "key": issue.fields.project.key,
                        "name": issue.fields.project.name
                    },
                    "assignee": {
                        "name": issue.fields.assignee.name if issue.fields.assignee else "unassigned",
                        "emailAddress": issue.fields.assignee.emailAddress if issue.fields.assignee else "",
                        "displayName": issue.fields.assignee.displayName if issue.fields.assignee else "Unassigned"
                    },
                    "creator": {
                        "name": issue.fields.creator.name,
                        "emailAddress": issue.fields.creator.emailAddress,
                        "displayName": issue.fields.creator.displayName
                    },
                    "created": issue.fields.created,
                    "updated": issue.fields.updated,
                    "labels": issue.fields.labels or []
                }
            }
            
            print(f"✅ Retrieved ticket: {ticket_key} - {issue.fields.summary}")
            return ticket_data
            
        except Exception as e:
            print(f"❌ Failed to get ticket {ticket_key}: {e}")
            return None
    
    def search_tickets(self, jql: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search for tickets using JQL"""
        if not self.jira_client:
            print("❌ Jira client not available for search")
            return []
        
        try:
            issues = self.jira_client.search_issues(jql, maxResults=max_results, expand='changelog')
            tickets = []
            
            for issue in issues:
                ticket_data = self.get_ticket(issue.key)
                if ticket_data:
                    tickets.append(ticket_data)
            
            print(f"✅ Found {len(tickets)} tickets matching: {jql}")
            return tickets
            
        except Exception as e:
            print(f"❌ Failed to search tickets: {e}")
            return []


class WebhookGenerator:
    """Generate and send webhook payloads"""
    
    def __init__(self, config: WebhookConfig):
        self.config = config
    
    def create_webhook_payload(self, ticket_data: Dict[str, Any], event_type: str = "jira:issue_created") -> Dict[str, Any]:
        """Create realistic Jira webhook payload"""
        
        webhook_payload = {
            "timestamp": int(time.time() * 1000),
            "webhookEvent": event_type,
            "issue_event_type_name": event_type.split(':')[1] if ':' in event_type else event_type,
            "user": {
                "self": f"{self.config.url}/rest/api/2/user?username={ticket_data['fields']['creator']['name']}",
                "name": ticket_data['fields']['creator']['name'],
                "emailAddress": ticket_data['fields']['creator']['emailAddress'],
                "displayName": ticket_data['fields']['creator']['displayName'],
                "active": True
            },
            "issue": ticket_data,
            "changelog": {
                "id": f"{int(time.time())}{ticket_data['id']}",
                "items": [
                    {
                        "field": "status",
                        "fieldtype": "jira",
                        "from": None,
                        "fromString": None,
                        "to": ticket_data['fields']['status']['id'],
                        "toString": ticket_data['fields']['status']['name']
                    }
                ]
            }
        }
        
        return webhook_payload
    
    def generate_curl_command(self, webhook_payload: Dict[str, Any]) -> str:
        """Generate curl command for the webhook"""
        
        # Convert payload to JSON string
        payload_json = json.dumps(webhook_payload, indent=2)
        
        # Generate curl command
        curl_command = f"""curl -X POST {self.config.url} \\
  -H "Content-Type: application/json" \\
  -H "X-Atlassian-Webhook-Identifier: $(uuidgen)" \\
  -H "X-Hub-Signature-256: sha256={self.config.secret}" \\
  -d '{payload_json}'"""
        
        return curl_command
    
    def send_webhook(self, webhook_payload: Dict[str, Any]) -> bool:
        """Send webhook directly using requests"""
        
        headers = {
            "Content-Type": "application/json",
            "X-Atlassian-Webhook-Identifier": f"webhook-{int(time.time())}",
            "X-Hub-Signature-256": f"sha256={self.config.secret}"
        }
        
        try:
            response = requests.post(
                self.config.url,
                json=webhook_payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code in [200, 201, 202]:
                print(f"✅ Webhook sent successfully: {response.status_code}")
                try:
                    result = response.json()
                    if 'trace_id' in result:
                        print(f"🔍 Trace ID: {result['trace_id']}")
                    print(f"📋 Response: {result}")
                except:
                    print(f"📋 Response: {response.text}")
                return True
            else:
                print(f"❌ Webhook failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to send webhook: {e}")
            return False


class TicketSimulator:
    """Simulate Jira tickets for testing"""
    
    @staticmethod
    def create_sample_tickets() -> List[Dict[str, Any]]:
        """Create sample tickets for testing"""
        
        base_time = datetime.now().isoformat()
        
        sample_tickets = [
            {
                "key": "DEVOPS-101",
                "id": "10001",
                "self": "https://company.atlassian.net/rest/api/2/issue/10001",
                "fields": {
                    "summary": "Add CSV export functionality to todo dashboard",
                    "description": "As a user, I want to export my todos to CSV format so I can analyze them in Excel. The export should include all todo details: title, description, priority, category, completion status, and creation date. Add an export button that shows the number of todos being exported.",
                    "issuetype": {
                        "id": "10001",
                        "name": "Story",
                        "subtask": False
                    },
                    "priority": {
                        "id": "2",
                        "name": "High"
                    },
                    "status": {
                        "id": "10000",
                        "name": "To Do",
                        "statusCategory": {
                            "id": 2,
                            "name": "To Do"
                        }
                    },
                    "project": {
                        "id": "10000",
                        "key": "DEVOPS",
                        "name": "DevOps Automation"
                    },
                    "assignee": {
                        "name": "frontend-dev",
                        "emailAddress": "frontend@company.com",
                        "displayName": "Frontend Developer"
                    },
                    "creator": {
                        "name": "product-manager",
                        "emailAddress": "pm@company.com",
                        "displayName": "Product Manager"
                    },
                    "created": base_time,
                    "updated": base_time,
                    "labels": ["export", "csv", "dashboard", "automation"]
                }
            },
            {
                "key": "DEVOPS-102",
                "id": "10002",
                "self": "https://company.atlassian.net/rest/api/2/issue/10002",
                "fields": {
                    "summary": "Implement real-time search and filtering",
                    "description": "Add a search bar that allows users to filter todos in real-time. The search should work on both title and description fields. Include a clear button to reset the search and show filtered count vs total count.",
                    "issuetype": {
                        "id": "10001",
                        "name": "Story",
                        "subtask": False
                    },
                    "priority": {
                        "id": "3",
                        "name": "Medium"
                    },
                    "status": {
                        "id": "10000",
                        "name": "To Do",
                        "statusCategory": {
                            "id": 2,
                            "name": "To Do"
                        }
                    },
                    "project": {
                        "id": "10000",
                        "key": "DEVOPS",
                        "name": "DevOps Automation"
                    },
                    "assignee": {
                        "name": "fullstack-dev",
                        "emailAddress": "fullstack@company.com",
                        "displayName": "Fullstack Developer"
                    },
                    "creator": {
                        "name": "ux-designer",
                        "emailAddress": "ux@company.com",
                        "displayName": "UX Designer"
                    },
                    "created": base_time,
                    "updated": base_time,
                    "labels": ["search", "filter", "ui", "automation"]
                }
            },
            {
                "key": "DEVOPS-103",
                "id": "10003",
                "self": "https://company.atlassian.net/rest/api/2/issue/10003",
                "fields": {
                    "summary": "Fix todo deletion confirmation dialog styling",
                    "description": "The delete confirmation dialog is not properly styled and hard to read. Update the styling to match the application theme and ensure good contrast for accessibility.",
                    "issuetype": {
                        "id": "10004",
                        "name": "Bug",
                        "subtask": False
                    },
                    "priority": {
                        "id": "2",
                        "name": "High"
                    },
                    "status": {
                        "id": "10000",
                        "name": "To Do",
                        "statusCategory": {
                            "id": 2,
                            "name": "To Do"
                        }
                    },
                    "project": {
                        "id": "10000",
                        "key": "DEVOPS",
                        "name": "DevOps Automation"
                    },
                    "assignee": {
                        "name": "ui-developer",
                        "emailAddress": "ui@company.com",
                        "displayName": "UI Developer"
                    },
                    "creator": {
                        "name": "qa-tester",
                        "emailAddress": "qa@company.com",
                        "displayName": "QA Tester"
                    },
                    "created": base_time,
                    "updated": base_time,
                    "labels": ["bug", "styling", "accessibility", "urgent"]
                }
            }
        ]
        
        return sample_tickets


class WorkflowTrigger:
    """Main class to orchestrate the workflow"""
    
    def __init__(self):
        self.jira_config = JiraConfig()
        self.webhook_config = WebhookConfig()
        self.jira_reader = JiraTicketReader(self.jira_config)
        self.webhook_generator = WebhookGenerator(self.webhook_config)
        self.simulator = TicketSimulator()
    
    def trigger_from_ticket_key(self, ticket_key: str, send_webhook: bool = True) -> bool:
        """Trigger workflow from a specific ticket key"""
        
        print(f"🎯 Processing ticket: {ticket_key}")
        
        # Get ticket data
        ticket_data = self.jira_reader.get_ticket(ticket_key)
        if not ticket_data:
            print(f"❌ Could not retrieve ticket: {ticket_key}")
            return False
        
        return self._process_ticket(ticket_data, send_webhook)
    
    def trigger_from_jql(self, jql: str, send_webhook: bool = True, max_results: int = 10) -> int:
        """Trigger workflow from JQL search results"""
        
        print(f"🔍 Searching tickets with JQL: {jql}")
        
        tickets = self.jira_reader.search_tickets(jql, max_results)
        if not tickets:
            print("❌ No tickets found matching the search criteria")
            return 0
        
        successful_triggers = 0
        for ticket_data in tickets:
            if self._process_ticket(ticket_data, send_webhook):
                successful_triggers += 1
                time.sleep(2)  # Wait between requests
        
        print(f"✅ Successfully triggered {successful_triggers}/{len(tickets)} workflows")
        return successful_triggers
    
    def trigger_sample_tickets(self, send_webhook: bool = True) -> int:
        """Trigger workflow from sample tickets"""
        
        print("🧪 Processing sample tickets...")
        
        sample_tickets = self.simulator.create_sample_tickets()
        successful_triggers = 0
        
        for ticket_data in sample_tickets:
            print(f"\n📋 Processing sample ticket: {ticket_data['key']}")
            if self._process_ticket(ticket_data, send_webhook):
                successful_triggers += 1
                time.sleep(2)  # Wait between requests
        
        print(f"✅ Successfully triggered {successful_triggers}/{len(sample_tickets)} workflows")
        return successful_triggers
    
    def _process_ticket(self, ticket_data: Dict[str, Any], send_webhook: bool = True) -> bool:
        """Process a single ticket"""
        
        try:
            # Create webhook payload
            webhook_payload = self.webhook_generator.create_webhook_payload(ticket_data)
            
            # Generate curl command
            curl_command = self.webhook_generator.generate_curl_command(webhook_payload)
            
            print(f"\n📤 Generated curl command for {ticket_data['key']}:")
            print("=" * 80)
            print(curl_command)
            print("=" * 80)
            
            # Optionally send the webhook
            if send_webhook:
                print(f"\n🚀 Sending webhook for {ticket_data['key']}...")
                success = self.webhook_generator.send_webhook(webhook_payload)
                
                if success:
                    print(f"✅ Workflow triggered successfully for {ticket_data['key']}")
                    
                    # Check status after a delay
                    time.sleep(3)
                    self._check_workflow_status(ticket_data['key'])
                    
                else:
                    print(f"❌ Failed to trigger workflow for {ticket_data['key']}")
                
                return success
            else:
                print(f"📋 Curl command generated for {ticket_data['key']} (not sent)")
                return True
                
        except Exception as e:
            print(f"❌ Error processing ticket {ticket_data['key']}: {e}")
            return False
    
    def _check_workflow_status(self, ticket_key: str):
        """Check the status of a triggered workflow"""
        
        try:
            # Try to get status from the webhook endpoint
            status_url = self.webhook_config.url.replace('/webhook/jira', f'/status/{ticket_key}')
            response = requests.get(status_url, timeout=10)
            
            if response.status_code == 200:
                status_data = response.json()
                print(f"📊 Workflow Status for {ticket_key}:")
                print(f"   Status: {status_data.get('status', 'Unknown')}")
                print(f"   Progress: {status_data.get('progress', 'Unknown')}")
                if 'files_generated' in status_data:
                    print(f"   Files Generated: {status_data['files_generated']}")
            else:
                print(f"⚠️ Could not check status for {ticket_key}")
                
        except Exception as e:
            print(f"⚠️ Status check failed: {e}")


def main():
    """Main function with CLI interface"""
    
    parser = argparse.ArgumentParser(
        description="Jira Ticket Reader and Webhook Trigger for LangGraph DevOps",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Trigger from specific ticket
  python jira_webhook_trigger.py --ticket DEVOPS-123

  # Trigger from JQL search
  python jira_webhook_trigger.py --jql "project = DEVOPS AND status = 'To Do'"

  # Use sample tickets for testing
  python jira_webhook_trigger.py --sample

  # Generate curl commands without sending
  python jira_webhook_trigger.py --ticket DEVOPS-123 --no-send

  # Process multiple tickets with delay
  python jira_webhook_trigger.py --jql "labels in (automation) AND created >= -7d" --max-results 5
        """
    )
    
    # Ticket selection options
    ticket_group = parser.add_mutually_exclusive_group(required=True)
    ticket_group.add_argument('--ticket', '-t', 
                             help='Specific Jira ticket key (e.g., DEVOPS-123)')
    ticket_group.add_argument('--jql', '-j', 
                             help='JQL query to search for tickets')
    ticket_group.add_argument('--sample', '-s', action='store_true',
                             help='Use sample tickets for testing')
    
    # Options
    parser.add_argument('--no-send', action='store_true',
                       help='Generate curl commands without sending webhooks')
    parser.add_argument('--max-results', '-m', type=int, default=10,
                       help='Maximum number of tickets to process (default: 10)')
    parser.add_argument('--webhook-url', '-w', 
                       help='Override webhook URL (default: from env)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Print what would be done without doing it')
    
    args = parser.parse_args()
    
    print("🚀 Jira Ticket Reader and Webhook Trigger")
    print("=" * 50)
    
    # Override webhook URL if provided
    if args.webhook_url:
        os.environ['WEBHOOK_URL'] = args.webhook_url
    
    # Initialize workflow trigger
    trigger = WorkflowTrigger()
    
    # Dry run mode
    if args.dry_run:
        print("🔍 DRY RUN MODE - No webhooks will be sent")
        send_webhook = False
    else:
        send_webhook = not args.no_send
    
    # Process based on arguments
    success = False
    
    if args.ticket:
        success = trigger.trigger_from_ticket_key(args.ticket, send_webhook)
    elif args.jql:
        count = trigger.trigger_from_jql(args.jql, send_webhook, args.max_results)
        success = count > 0
    elif args.sample:
        count = trigger.trigger_sample_tickets(send_webhook)
        success = count > 0
    
    # Final status
    if success:
        print("\n🎉 Workflow triggering completed successfully!")
        if send_webhook and not args.dry_run:
            print("Check your LangGraph DevOps system for automation progress.")
            print("Monitor logs: tail -f logs/devops_autocoder.log")
            print("View reports: ls -la reports/")
    else:
        print("\n❌ Workflow triggering failed or no tickets processed")
        sys.exit(1)


if __name__ == "__main__":
    main()
