#!/usr/bin/env python3
"""
Todoist Import Script
Converts tasks.json to CSV format and syncs with Todoist API
"""

import json
import csv
import argparse
import sys
import os
from datetime import datetime
import requests

def load_tasks_from_json(json_path):
    """Load tasks from JSON file"""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('tasks', [])
    except FileNotFoundError:
        print(f"Error: Tasks file not found at {json_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {json_path}: {e}")
        sys.exit(1)

def convert_to_csv(tasks, csv_path):
    """Convert tasks to CSV format for Todoist import"""
    try:
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['TYPE', 'CONTENT', 'PRIORITY', 'INDENT', 'AUTHOR', 'RESPONSIBLE', 'DATE', 'DATE_LANG', 'TIMEZONE']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            
            for task in tasks:
                # Only sync tasks marked with 'todone': true
                if not task.get('todone', False):
                    continue
                    
                # Skip completed tasks
                if task.get('completed', False):
                    continue
                
                content = task.get('task', 'Untitled Task')
                due_date = task.get('due_date', '')
                
                # Convert due date format if present
                formatted_date = ''
                if due_date:
                    try:
                        # Parse from DD-Month-YYYY format
                        dt = datetime.strptime(due_date, '%d-%B-%Y')
                        # Convert to YYYY-MM-DD format for Todoist
                        formatted_date = dt.strftime('%Y-%m-%d')
                    except ValueError:
                        print(f"Warning: Invalid date format for task '{content}': {due_date}")
                
                writer.writerow({
                    'TYPE': 'task',
                    'CONTENT': content,
                    'PRIORITY': '1',  # Normal priority
                    'INDENT': '1',    # Top level
                    'AUTHOR': '',
                    'RESPONSIBLE': '',
                    'DATE': formatted_date,
                    'DATE_LANG': 'en',
                    'TIMEZONE': 'UTC'
                })
        
        print(f"CSV file created successfully: {csv_path}")
        return True
        
    except Exception as e:
        print(f"Error creating CSV file: {e}")
        return False

def sync_to_todoist_api(tasks, token):
    """Sync tasks directly to Todoist API"""
    if not token:
        print("Error: No Todoist API token provided")
        return False
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Get existing projects
    try:
        projects_response = requests.get('https://api.todoist.com/rest/v2/projects', headers=headers)
        projects_response.raise_for_status()
        projects = projects_response.json()
        
        # Use default project (Inbox)
        default_project_id = None
        for project in projects:
            if project.get('name', '').lower() == 'inbox' or project.get('is_inbox_project', False):
                default_project_id = project['id']
                break
        
        if not default_project_id and projects:
            default_project_id = projects[0]['id']  # Use first project as fallback
            
    except requests.RequestException as e:
        print(f"Error fetching projects: {e}")
        return False
    
    synced_count = 0
    
    for task in tasks:
        # Only sync tasks marked with 'todone': true
        if not task.get('todone', False):
            continue
            
        # Skip completed tasks
        if task.get('completed', False):
            continue
        
        content = task.get('task', 'Untitled Task')
        due_date = task.get('due_date', '')
        
        # Prepare task data
        task_data = {
            'content': content,
            'project_id': default_project_id
        }
        
        # Add due date if present
        if due_date:
            try:
                # Parse from DD-Month-YYYY format
                dt = datetime.strptime(due_date, '%d-%B-%Y')
                # Convert to YYYY-MM-DD format for Todoist
                task_data['due_date'] = dt.strftime('%Y-%m-%d')
            except ValueError:
                print(f"Warning: Invalid date format for task '{content}': {due_date}")
        
        # Create task in Todoist
        try:
            response = requests.post('https://api.todoist.com/rest/v2/tasks', 
                                   headers=headers, 
                                   json=task_data)
            response.raise_for_status()
            synced_count += 1
            print(f"Synced task: {content}")
            
        except requests.RequestException as e:
            print(f"Error syncing task '{content}': {e}")
            if hasattr(e, 'response') and e.response:
                print(f"Response: {e.response.text}")
    
    print(f"Successfully synced {synced_count} tasks to Todoist")
    return synced_count > 0

def main():
    parser = argparse.ArgumentParser(description='Import tasks to Todoist')
    parser.add_argument('json_file', help='Path to tasks.json file')
    parser.add_argument('--csv', help='Path to output CSV file')
    parser.add_argument('--token', help='Todoist API token')
    parser.add_argument('--api-only', action='store_true', help='Sync directly via API without creating CSV')
    
    args = parser.parse_args()
    
    # Validate inputs
    if not os.path.exists(args.json_file):
        print(f"Error: JSON file not found: {args.json_file}")
        sys.exit(1)
    
    if not args.token:
        print("Error: Todoist API token is required")
        sys.exit(1)
    
    # Load tasks
    tasks = load_tasks_from_json(args.json_file)
    
    if not tasks:
        print("No tasks found in JSON file")
        sys.exit(0)
    
    # Filter tasks marked for Todoist sync
    todoist_tasks = [task for task in tasks if task.get('todone', False) and not task.get('completed', False)]
    
    if not todoist_tasks:
        print("No tasks marked for Todoist sync (todone: true)")
        sys.exit(0)
    
    print(f"Found {len(todoist_tasks)} tasks marked for Todoist sync")
    
    success = True
    
    # Create CSV if requested
    if args.csv and not args.api_only:
        success = convert_to_csv(tasks, args.csv)
    
    # Sync via API
    if success:
        api_success = sync_to_todoist_api(tasks, args.token)
        if not api_success:
            success = False
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()