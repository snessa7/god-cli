#!/usr/bin/env python3
"""
God CLI - A Python CLI tool for interacting with local Ollama instances
"""

import json
import os
import sys
import requests
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
import argparse
import readline
import time
import rlcompleter
import sqlite3
from datetime import datetime
import platform

class OllamaCLI:
    def __init__(self, config_path: str = None):
        self.config_path = config_path or os.path.expanduser("~/.god_cli_config.json")
        self.config = self.load_config()
        self.base_url = self.config.get("ollama_url", "http://localhost:11434")
        
        # Setup tab completion for slash commands
        self.setup_tab_completion()
        
        # Available slash commands for completion
        self.slash_commands = [
            '/copy', '/copyall', '/help', '/clear', '/c', 
            '/config', '/verify', '/fixmodels', '/testclipboard', '/testdb', '/testsearch', '/models', '/change', '/prompt', '/memory', '/extract', '/search', '/knowledge', '/cleanup'
        ]
        
        # Initialize database
        self.db_path = os.path.expanduser("~/.god_cli.db")
        self.init_database()
        
        # Generate session ID for this chat session
        self.session_id = f"session_{int(time.time())}_{os.getpid()}"
        self.start_session()
    
    def init_database(self):
        """Initialize SQLite database with tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create conversations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    user_message TEXT NOT NULL,
                    assistant_response TEXT NOT NULL,
                    model_used TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    tokens_used INTEGER DEFAULT 0
                )
            ''')
            
            # Create sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    end_time DATETIME,
                    model_used TEXT,
                    total_messages INTEGER DEFAULT 0,
                    total_tokens INTEGER DEFAULT 0
                )
            ''')
            
            # Create user_preferences table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_preferences (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create extracted_info table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS extracted_info (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    category TEXT NOT NULL,
                    source_session TEXT,
                    extraction_type TEXT NOT NULL,
                    tags TEXT,
                    topic TEXT,
                    summary TEXT,
                    importance_level INTEGER DEFAULT 3,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create metadata_index table for advanced searching
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS metadata_index (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    extracted_info_id INTEGER,
                    date_key TEXT,
                    weekday TEXT,
                    month TEXT,
                    year TEXT,
                    topic_key TEXT,
                    category_key TEXT,
                    tags_key TEXT,
                    FOREIGN KEY (extracted_info_id) REFERENCES extracted_info (id)
                )
            ''')
            
            # Create system_knowledge table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_knowledge (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    file_path TEXT,
                    tags TEXT,
                    importance_level INTEGER DEFAULT 3,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Warning: Could not initialize database: {e}")
    
    def start_session(self):
        """Start a new chat session"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO sessions 
                (session_id, start_time, model_used) 
                VALUES (?, ?, ?)
            ''', (self.session_id, datetime.now().isoformat(), self.config.get('default_model')))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Warning: Could not start session: {e}")
    
    def end_session(self):
        """End the current chat session"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get session stats
            cursor.execute('''
                SELECT COUNT(*) FROM conversations 
                WHERE session_id = ?
            ''', (self.session_id,))
            total_messages = cursor.fetchone()[0]
            
            # Update session
            cursor.execute('''
                UPDATE sessions 
                SET end_time = ?, total_messages = ?
                WHERE session_id = ?
            ''', (datetime.now().isoformat(), total_messages, self.session_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Warning: Could not end session: {e}")
    
    def save_conversation(self, user_message, assistant_response, tokens_used=0):
        """Save a conversation exchange to the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO conversations 
                (session_id, user_message, assistant_response, model_used, tokens_used)
                VALUES (?, ?, ?, ?, ?)
            ''', (self.session_id, user_message, assistant_response, 
                  self.config.get('default_model'), tokens_used))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Warning: Could not save conversation: {e}")
    
    def get_conversation_history(self, limit=50):
        """Get conversation history from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT user_message, assistant_response, timestamp, model_used
                FROM conversations 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
            
            history = cursor.fetchall()
            conn.close()
            
            return history
            
        except Exception as e:
            print(f"Warning: Could not retrieve history: {e}")
            return []
    
    def get_session_stats(self):
        """Get statistics for the current session"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT COUNT(*) FROM conversations 
                WHERE session_id = ?
            ''', (self.session_id,))
            
            message_count = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT SUM(tokens_used) FROM conversations 
                WHERE session_id = ?
            ''', (self.session_id,))
            
            total_tokens = cursor.fetchone()[0] or 0
            
            conn.close()
            
            return {
                'session_id': self.session_id,
                'message_count': message_count,
                'total_tokens': total_tokens
            }
            
        except Exception as e:
            print(f"Warning: Could not get session stats: {e}")
            return {}
    
    def show_memory_info(self):
        """Show memory and database information"""
        print("\n🧠 Memory & Database Info")
        print("=" * 40)
        
        # Current session stats
        session_stats = self.get_session_stats()
        if session_stats:
            print(f"📊 Current Session:")
            print(f"  Session ID: {session_stats['session_id'][:20]}...")
            print(f"  Messages: {session_stats['message_count']}")
            print(f"  Tokens: {session_stats['total_tokens']}")
        
        # Database info
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total conversations
            cursor.execute('SELECT COUNT(*) FROM conversations')
            total_conversations = cursor.fetchone()[0]
            
            # Total sessions
            cursor.execute('SELECT COUNT(*) FROM sessions')
            total_sessions = cursor.fetchone()[0]
            
            # Database size
            db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            db_size_mb = db_size / (1024 * 1024)
            
            print(f"\n💾 Database:")
            print(f"  Total Conversations: {total_conversations}")
            print(f"  Total Sessions: {total_sessions}")
            print(f"  Database Size: {db_size_mb:.2f} MB")
            print(f"  Database Path: {self.db_path}")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Could not retrieve database info: {e}")
        
        print("=" * 40)
    
    def extract_key_details(self):
        """Extract and save key details from conversations"""
        print("\n🔍 Extract Key Details")
        print("=" * 40)
        
        # Validate prerequisites first
        if not self.validate_extraction_prerequisites():
            return
        
        # Show extraction options
        print("📋 Extraction Types:")
        print("  1. Code Snippets - Extract programming code")
        print("  2. Action Items - Extract tasks and to-dos")
        print("  3. Custom - Extract with custom category")
        print("  4. View Saved - Show all extracted items")
        print("  5. Cancel")
        
        while True:
            try:
                choice = input("\nSelect extraction type (1-5): ").strip()
                
                if choice == '1':
                    self.extract_code_snippets()
                    break
                elif choice == '2':
                    self.extract_action_items()
                    break
                elif choice == '3':
                    self.extract_custom()
                    break
                elif choice == '4':
                    self.show_extracted_items()
                    break
                elif choice == '5':
                    print("❌ Extraction cancelled.")
                    break
                else:
                    print("❌ Please enter a number between 1-6")
                    
            except KeyboardInterrupt:
                print("\n❌ Extraction cancelled.")
                break
    
    def extract_code_snippets(self):
        """Extract code snippets from recent conversations"""
        print("\n💻 Code Snippet Extraction")
        print("=" * 40)
        
        # Get recent conversations
        conversations = self.get_conversation_history(limit=20)
        
        if not conversations:
            print("❌ No conversations found to extract from.")
            return
        
        # Look for code patterns
        code_snippets = []
        for user_msg, assistant_msg, timestamp, model in conversations:
            # Simple code detection (lines starting with common code patterns)
            lines = assistant_msg.split('\n')
            code_block = []
            in_code_block = False
            
            for line in lines:
                if '```' in line:
                    in_code_block = not in_code_block
                    continue
                
                if in_code_block:
                    code_block.append(line)
                elif any(line.strip().startswith(prefix) for prefix in ['def ', 'class ', 'import ', 'from ', 'if __name__', 'print(', 'return ', 'for ', 'while ']):
                    code_block.append(line)
            
            if code_block:
                code_snippets.append({
                    'content': '\n'.join(code_block),
                    'timestamp': timestamp,
                    'model': model,
                    'user_msg': user_msg
                })
        
        if not code_snippets:
            print("❌ No code snippets found in recent conversations.")
            return
        
        # Show found snippets
        print(f"🔍 Found {len(code_snippets)} code snippets:")
        for i, snippet in enumerate(code_snippets, 1):
            print(f"\n{i}. Code from {snippet['timestamp']} (Model: {snippet['model']}):")
            print("Context:", snippet['user_msg'][:100] + "..." if len(snippet['user_msg']) > 100 else snippet['user_msg'])
            print("=" * 50)
            print(snippet['content'][:200] + "..." if len(snippet['content']) > 200 else snippet['content'])
            print("=" * 50)
        
        # Let user select which to save
        while True:
            try:
                choice = input(f"\nSelect snippet to save (1-{len(code_snippets)}) or 'all' or 'cancel': ").strip()
                
                if choice.lower() == 'cancel':
                    print("❌ Code extraction cancelled.")
                    return
                elif choice.lower() == 'all':
                    # Save all snippets
                    for snippet in code_snippets:
                        self.collect_metadata_and_save(
                            title=f"Code Snippet from {snippet['timestamp']}",
                            content=snippet['content'],
                            category="code",
                            extraction_type="code_snippets",
                            context=snippet['user_msg']
                        )
                    print(f"✅ Saved {len(code_snippets)} code snippets to memory!")
                    return
                elif choice.isdigit():
                    choice_num = int(choice)
                    if 1 <= choice_num <= len(code_snippets):
                        selected = code_snippets[choice_num - 1]
                        self.collect_metadata_and_save(
                            title=f"Code Snippet from {selected['timestamp']}",
                            content=selected['content'],
                            category="code",
                            extraction_type="code_snippets",
                            context=selected['user_msg']
                        )
                        print("✅ Code snippet saved to memory!")
                        return
                    else:
                        print(f"❌ Please enter a number between 1 and {len(code_snippets)}")
                else:
                    print("❌ Please enter a valid number, 'all', or 'cancel'")
                    
            except KeyboardInterrupt:
                print("\n❌ Code extraction cancelled.")
                return
    

    
    def extract_action_items(self):
        """Extract action items and tasks from conversations"""
        print("\n✅ Action Items Extraction")
        print("=" * 40)
        
        # Get recent conversations
        conversations = self.get_conversation_history(limit=20)
        
        if not conversations:
            print("❌ No conversations found to extract from.")
            return
        
        # Look for action items (simple pattern matching)
        action_items = []
        action_patterns = [
            'todo:', 'to do:', 'action:', 'task:', 'next:', 'remember to',
            'make sure to', 'don\'t forget', 'you should', 'you need to'
        ]
        
        for user_msg, assistant_msg, timestamp, model in conversations:
            content = user_msg + " " + assistant_msg
            content_lower = content.lower()
            
            for pattern in action_patterns:
                if pattern in content_lower:
                    # Extract the sentence containing the pattern
                    sentences = content.split('.')
                    for sentence in sentences:
                        if pattern in sentence.lower():
                            action_items.append({
                                'content': sentence.strip(),
                                'timestamp': timestamp,
                                'model': model,
                                'pattern': pattern
                            })
                            break
        
        if not action_items:
            print("❌ No action items found in recent conversations.")
            return
        
        # Show found action items
        print(f"🔍 Found {len(action_items)} action items:")
        for i, item in enumerate(action_items, 1):
            print(f"\n{i}. From {item['timestamp']} (Pattern: {item['pattern']}):")
            print("=" * 50)
            print(item['content'])
            print("=" * 50)
        
        # Let user select which to save
        while True:
            try:
                choice = input(f"\nSelect action item to save (1-{len(action_items)}) or 'all' or 'cancel': ").strip()
                
                if choice.lower() == 'cancel':
                    print("❌ Action items extraction cancelled.")
                    return
                elif choice.lower() == 'all':
                    # Save all action items
                    for item in action_items:
                        self.save_extracted_info(
                            title=f"Action Item: {item['content'][:50]}...",
                            content=item['content'],
                            category="tasks",
                            extraction_type="action_items"
                        )
                    print(f"✅ Saved {len(action_items)} action items to memory!")
                    return
                elif choice.isdigit():
                    choice_num = int(choice)
                    if 1 <= choice_num <= len(action_items):
                        selected = action_items[choice_num - 1]
                        self.save_extracted_info(
                            title=f"Action Item: {selected['content'][:50]}...",
                            content=selected['content'],
                            category="tasks",
                            extraction_type="action_items"
                        )
                        print("✅ Action item saved to memory!")
                        return
                    else:
                        print(f"❌ Please enter a number between 1 and {len(action_items)}")
                else:
                    print("❌ Please enter a valid number, 'all', or 'copy'")
                    
            except KeyboardInterrupt:
                print("\n❌ Action items extraction cancelled.")
                return
    
    def extract_custom(self):
        """Extract custom information with user-defined category"""
        print("\n🔧 Custom Extraction")
        print("=" * 40)
        
        # Get recent conversations
        conversations = self.get_conversation_history(limit=20)
        
        if not conversations:
            print("❌ No conversations found to extract from.")
            return
        
        print("📝 Enter custom category (e.g., 'ideas', 'quotes', 'solutions'):")
        category = input("Category: ").strip()
        
        if not category:
            print("❌ No category provided.")
            return
        
        print("📝 Enter search text or leave blank to show all recent conversations:")
        search_text = input("Search text: ").strip()
        
        # Filter conversations
        if search_text:
            matching_conversations = []
            for user_msg, assistant_msg, timestamp, model in conversations:
                content = user_msg + " " + assistant_msg
                if search_text.lower() in content.lower():
                    matching_conversations.append({
                        'user_msg': user_msg,
                        'assistant_msg': assistant_msg,
                        'timestamp': timestamp,
                        'model': model
                    })
        else:
            matching_conversations = conversations
        
        if not matching_conversations:
            print("❌ No conversations found matching the criteria.")
            return
        
        # Show matching conversations
        print(f"\n🔍 Found {len(matching_conversations)} conversations:")
        for i, conv in enumerate(matching_conversations, 1):
            print(f"\n{i}. From {conv['timestamp']} (Model: {conv['model']})")
            print("User:", conv['user_msg'][:100] + "..." if len(conv['user_msg']) > 100 else conv['user_msg'])
            print("Assistant:", conv['assistant_msg'][:150] + "..." if len(conv['assistant_msg']) > 150 else conv['assistant_msg'])
        
        # Let user select which to save
        while True:
            try:
                choice = input(f"\nSelect conversation to save (1-{len(matching_conversations)}) or 'all' or 'cancel': ").strip()
                
                if choice.lower() == 'cancel':
                    print("❌ Custom extraction cancelled.")
                    return
                elif choice.lower() == 'all':
                    # Save all matching conversations
                    for conv in matching_conversations:
                        self.save_extracted_info(
                            title=f"{category.title()}: {conv['user_msg'][:50]}...",
                            content=f"User: {conv['user_msg']}\n\nAssistant: {conv['assistant_msg']}",
                            category=category.lower(),
                            extraction_type="custom"
                        )
                    print(f"✅ Saved {len(matching_conversations)} items to memory!")
                    return
                elif choice.isdigit():
                    choice_num = int(choice)
                    if 1 <= choice_num <= len(matching_conversations):
                        selected = conv = matching_conversations[choice_num - 1]
                        self.save_extracted_info(
                            title=f"{category.title()}: {conv['user_msg'][:50]}...",
                            content=f"User: {conv['user_msg']}\n\nAssistant: {conv['assistant_msg']}",
                            category=category.lower(),
                            extraction_type="custom"
                        )
                        print("✅ Custom item saved to memory!")
                        return
                    else:
                        print(f"❌ Please enter a number between 1 and {len(matching_conversations)}")
                else:
                    print("❌ Please enter a valid number, 'all', or 'cancel'")
                    
            except KeyboardInterrupt:
                print("\n❌ Custom extraction cancelled.")
                return
    
    def collect_metadata_and_save(self, title, content, category, extraction_type, context="", tags=""):
        """Collect metadata and save extracted information"""
        print(f"\n📝 Metadata Collection for: {title}")
        print("=" * 50)
        
        # Collect topic
        print("💡 What topic does this relate to? (e.g., 'Python', 'Web Development', 'AI')")
        topic = input("Topic: ").strip() or "General"
        
        # Collect summary
        print("📋 Brief summary (what is this about?):")
        summary = input("Summary: ").strip() or "No summary provided"
        
        # Collect importance level
        print("⭐ Importance level (1=Low, 3=Medium, 5=High):")
        try:
            importance = int(input("Importance (1-5): ").strip() or "3")
            importance = max(1, min(5, importance))
        except ValueError:
            importance = 3
        
        # Generate tags from context and content
        auto_tags = []
        if context:
            # Extract key words from context
            words = context.lower().split()
            auto_tags.extend([w for w in words if len(w) > 3 and w.isalpha()][:3])
        if content:
            # Extract key words from content
            words = content.lower().split()
            auto_tags.extend([w for w in words if len(w) > 3 and w.isalpha()][:3])
        
        # Combine auto-generated and user tags
        all_tags = list(set(auto_tags + [t.strip() for t in tags.split(',') if t.strip()]))
        final_tags = ", ".join(all_tags)
        
        print(f"\n🏷️  Auto-generated tags: {', '.join(auto_tags)}")
        print(f"📝 Final tags: {final_tags}")
        
        # Save with metadata
        self.save_extracted_info_with_metadata(
            title, content, category, extraction_type, 
            topic, summary, importance, final_tags
        )
    
    def save_extracted_info_with_metadata(self, title, content, category, extraction_type, topic, summary, importance, tags):
        """Save extracted information with rich metadata"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insert main record
            cursor.execute('''
                INSERT INTO extracted_info 
                (title, content, category, source_session, extraction_type, topic, summary, importance_level, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (title, content, category, self.session_id, extraction_type, topic, summary, importance, tags))
            
            extracted_id = cursor.lastrowid
            
            # Create metadata index
            now = datetime.now()
            cursor.execute('''
                INSERT INTO metadata_index 
                (extracted_info_id, date_key, weekday, month, year, topic_key, category_key, tags_key)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                extracted_id,
                now.strftime('%Y-%m-%d'),
                now.strftime('%A'),
                now.strftime('%B'),
                now.strftime('%Y'),
                topic.lower(),
                category.lower(),
                tags.lower()
            ))
            
            conn.commit()
            conn.close()
            
            print("✅ Saved with rich metadata!")
            
        except Exception as e:
            print(f"❌ Could not save extracted info: {e}")
    
    def save_extracted_info(self, title, content, category, extraction_type, tags=""):
        """Save extracted information to database (backward compatibility)"""
        self.collect_metadata_and_save(title, content, category, extraction_type, "", tags)
    
    def show_extracted_items(self):
        """Show all saved extracted items"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT title, content, category, extraction_type, created_at, tags
                FROM extracted_info 
                ORDER BY created_at DESC
            ''')
            
            items = cursor.fetchall()
            conn.close()
            
            if not items:
                print("❌ No extracted items found in memory.")
                return
            
            print(f"\n📚 Saved Extracted Items ({len(items)} total):")
            print("=" * 60)
            
            for i, (title, content, category, extraction_type, created_at, tags) in enumerate(items, 1):
                print(f"\n{i}. {title}")
                print(f"   Category: {category} | Type: {extraction_type}")
                print(f"   Created: {created_at}")
                if tags:
                    print(f"   Tags: {tags}")
                print(f"   Content: {content[:100]}..." if len(content) > 100 else f"   Content: {content}")
                print("-" * 40)
            
            # Offer to copy specific items
            while True:
                try:
                    choice = input(f"\nSelect item to copy (1-{len(items)}) or 'cancel': ").strip()
                    
                    if choice.lower() == 'cancel':
                        break
                    elif choice.isdigit():
                        choice_num = int(choice)
                        if 1 <= choice_num <= len(items):
                            selected = items[choice_num - 1]
                            self.copy_to_clipboard(selected[1])  # content
                            print("✅ Item copied to clipboard!")
                            break
                        else:
                            print(f"❌ Please enter a number between 1 and {len(items)}")
                    else:
                        print("❌ Please enter a valid number or 'cancel'")
                        
                except KeyboardInterrupt:
                    break
            
        except Exception as e:
            print(f"❌ Could not retrieve extracted items: {e}")
    
    def manage_system_knowledge(self):
        """Manage system knowledge (files, text, etc.)"""
        print("\n🧠 System Knowledge Management")
        print("=" * 40)
        
        print("📋 Knowledge Options:")
        print("  1. Add Text File")
        print("  2. Add Custom Text")
        print("  3. View Knowledge")
        print("  4. Search Knowledge")
        print("  5. Delete Knowledge")
        print("  6. Cancel")
        
        while True:
            try:
                choice = input("\nSelect option (1-6): ").strip()
                
                if choice == '1':
                    self.add_text_file()
                    break
                elif choice == '2':
                    self.add_custom_text()
                    break
                elif choice == '3':
                    self.view_system_knowledge()
                    break
                elif choice == '4':
                    self.search_system_knowledge()
                    break
                elif choice == '5':
                    self.delete_system_knowledge()
                    break
                elif choice == '6':
                    print("❌ Knowledge management cancelled.")
                    break
                else:
                    print("❌ Please enter a number between 1-6")
                    
            except KeyboardInterrupt:
                print("\n❌ Knowledge management cancelled.")
                break
    
    def add_text_file(self):
        """Add a text file to system knowledge"""
        print("\n📁 Add Text File to Knowledge")
        print("=" * 40)
        
        print("💡 Supported file types: .txt, .md, .py, .js, .html, .css, .json, .csv")
        print("📋 File Selection Options:")
        print("  1. Open Finder to select file")
        print("  2. Enter file path manually")
        print("  3. Cancel")
        
        while True:
            try:
                choice = input("\nSelect option (1-3): ").strip()
                
                if choice == '1':
                    file_path = self.open_file_picker()
                    if not file_path:
                        print("❌ No file selected.")
                        return
                    break
                elif choice == '2':
                    file_path = input("Enter file path: ").strip()
                    if not file_path:
                        print("❌ No file path provided.")
                        return
                    break
                elif choice == '3':
                    print("❌ File selection cancelled.")
                    return
                else:
                    print("❌ Please enter a number between 1-3")
                    
            except KeyboardInterrupt:
                print("\n❌ File selection cancelled.")
                return
        
        # Expand user path and check if file exists
        file_path = os.path.expanduser(file_path)
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return
        
        # Check file size (limit to 1MB for now)
        file_size = os.path.getsize(file_path)
        if file_size > 1024 * 1024:
            print(f"❌ File too large: {file_size / 1024 / 1024:.1f}MB (max 1MB)")
            return
        
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Get file info
            file_name = os.path.basename(file_path)
            file_ext = os.path.splitext(file_name)[1].lower()
            
            # Determine source type
            source_type = "text_file"
            if file_ext in ['.py', '.js', '.html', '.css']:
                source_type = "code_file"
            elif file_ext == '.md':
                source_type = "markdown_file"
            elif file_ext == '.json':
                source_type = "json_file"
            elif file_ext == '.csv':
                source_type = "csv_file"
            
            # Get title and tags
            title = input(f"Title for this knowledge (default: {file_name}): ").strip() or file_name
            tags = input("Tags (comma-separated, optional): ").strip()
            
            # Save to database
            self.save_system_knowledge(title, content, source_type, file_path, tags)
            print(f"✅ File '{file_name}' added to system knowledge!")
            
        except UnicodeDecodeError:
            print("❌ File encoding not supported. Please use UTF-8 encoded files.")
        except Exception as e:
            print(f"❌ Error reading file: {e}")
    
    def add_custom_text(self):
        """Add custom text to system knowledge"""
        print("\n📝 Add Custom Text to Knowledge")
        print("=" * 40)
        
        title = input("Title for this knowledge: ").strip()
        if not title:
            print("❌ Title is required.")
            return
        
        print("\n📋 Enter your text content:")
        print("💡 Press Enter twice to finish, or type 'cancel' to abort")
        print("=" * 50)
        
        lines = []
        while True:
            try:
                line = input()
                if line.lower() == 'cancel':
                    print("❌ Text addition cancelled.")
                    return
                elif line == "" and lines and lines[-1] == "":
                    # Two empty lines in a row
                    break
                lines.append(line)
            except KeyboardInterrupt:
                print("\n❌ Text addition cancelled.")
                return
        
        # Remove the last empty line
        if lines and lines[-1] == "":
            lines.pop()
        
        content = '\n'.join(lines)
        
        if not content.strip():
            print("❌ No content provided.")
            return
        
        # Get tags
        tags = input("Tags (comma-separated, optional): ").strip()
        
        # Save to database
        self.save_system_knowledge(title, content, "custom_text", None, tags)
        print("✅ Custom text added to system knowledge!")
    
    def save_system_knowledge(self, title, content, source_type, file_path, tags):
        """Save system knowledge to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO system_knowledge 
                (title, content, source_type, file_path, tags, importance_level)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (title, content, source_type, file_path, tags, 3))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ Could not save knowledge: {e}")
    
    def open_file_picker(self):
        """Open file picker dialog to select a file"""
        try:
            # Use a simple approach - just ask for the file path
            # This avoids the death loop issues with GUI dialogs
            print("\n💡 File Picker (Simplified)")
            print("=" * 30)
            print("📁 Enter the path to your file:")
            print("💡 Examples:")
            print("  ~/Documents/myfile.txt")
            print("  /Users/username/Desktop/script.py")
            print("  ./local_file.md")
            print("  ../parent_folder/data.json")
            
            file_path = input("\nFile path: ").strip()
            
            if not file_path:
                print("❌ No file path provided.")
                return None
            
            # Expand user path and check if file exists
            expanded_path = os.path.expanduser(file_path)
            if not os.path.exists(expanded_path):
                print(f"❌ File not found: {expanded_path}")
                return None
            
            print(f"✅ File found: {expanded_path}")
            return expanded_path
                
        except Exception as e:
            print(f"❌ Error in file picker: {e}")
            return None
    
    def view_system_knowledge(self):
        """View all system knowledge"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, title, content, source_type, tags, created_at, importance_level
                FROM system_knowledge 
                ORDER BY importance_level DESC, created_at DESC
            ''')
            
            knowledge_items = cursor.fetchall()
            conn.close()
            
            if not knowledge_items:
                print("\n❌ No system knowledge found.")
                return
            
            print(f"\n🧠 System Knowledge ({len(knowledge_items)} items):")
            print("=" * 80)
            
            for i, (kid, title, content, source_type, tags, created_at, importance) in enumerate(knowledge_items, 1):
                importance_stars = "⭐" * importance
                content_preview = content[:100] + "..." if len(content) > 100 else content
                
                print(f"\n{i}. {title}")
                print(f"   📂 Type: {source_type} | {importance_stars}")
                print(f"   📅 Created: {created_at}")
                if tags:
                    print(f"   🏷️  Tags: {tags}")
                print(f"   📝 Content: {content_preview}")
                print("-" * 60)
            
            # Offer actions
            print("\n📋 Actions:")
            print("  view <number> - View full content")
            print("  copy <number> - Copy to clipboard")
            print("  delete <number> - Delete this knowledge")
            print("  exit - Return to main menu")
            
            while True:
                try:
                    action = input("\nEnter action: ").strip()
                    
                    if action.lower() == 'exit':
                        break
                    elif action.startswith('view '):
                        try:
                            item_num = int(action.split()[1])
                            if 1 <= item_num <= len(knowledge_items):
                                selected = knowledge_items[item_num - 1]
                                print(f"\n📖 Full Content: {selected[1]}")
                                print("=" * 80)
                                print(selected[2])  # content
                                print("=" * 80)
                                break
                            else:
                                print(f"❌ Invalid item number. Choose 1-{len(knowledge_items)}")
                        except (ValueError, IndexError):
                            print("❌ Invalid format. Use 'view <number>'")
                    elif action.startswith('copy '):
                        try:
                            item_num = int(action.split()[1])
                            if 1 <= item_num <= len(knowledge_items):
                                selected = knowledge_items[item_num - 1]
                                self.copy_to_clipboard(selected[2])  # content
                                print(f"✅ Item {item_num} copied to clipboard!")
                                break
                            else:
                                print(f"❌ Invalid item number. Choose 1-{len(knowledge_items)}")
                        except (ValueError, IndexError):
                            print("❌ Invalid format. Use 'copy <number>'")
                    elif action.startswith('delete '):
                        try:
                            item_num = int(action.split()[1])
                            if 1 <= item_num <= len(knowledge_items):
                                selected = knowledge_items[item_num - 1]
                                confirm = input(f"❌ Delete '{selected[1]}'? (yes/no): ").strip().lower()
                                if confirm == 'yes':
                                    self.delete_knowledge_by_id(selected[0])
                                    print(f"✅ Knowledge item {item_num} deleted!")
                                    break
                                else:
                                    print("❌ Deletion cancelled.")
                                    break
                            else:
                                print(f"❌ Invalid item number. Choose 1-{len(knowledge_items)}")
                        except (ValueError, IndexError):
                            print("❌ Invalid format. Use 'delete <number>'")
                    else:
                        print("❌ Invalid action. Use: view <number>, copy <number>, delete <number>, or exit")
                        
                except KeyboardInterrupt:
                    print("\n❌ Action cancelled.")
                    break
                    
        except Exception as e:
            print(f"❌ Could not retrieve knowledge: {e}")
    
    def search_system_knowledge(self):
        """Search system knowledge by various criteria"""
        print("\n🔍 Search System Knowledge")
        print("=" * 40)
        
        print("📋 Search Options:")
        print("  1. Search by Title")
        print("  2. Search by Content")
        print("  3. Search by Tags")
        print("  4. Search by File Type")
        print("  5. Combined Search")
        print("  6. Cancel")
        
        while True:
            try:
                choice = input("\nSelect search type (1-6): ").strip()
                
                if choice == '1':
                    self.search_knowledge_by_title()
                    break
                elif choice == '2':
                    self.search_knowledge_by_content()
                    break
                elif choice == '3':
                    self.search_knowledge_by_tags()
                    break
                elif choice == '4':
                    self.search_knowledge_by_type()
                    break
                elif choice == '5':
                    self.search_knowledge_combined()
                    break
                elif choice == '6':
                    print("❌ Search cancelled.")
                    break
                else:
                    print("❌ Please enter a number between 1-6")
                    
            except KeyboardInterrupt:
                print("\n❌ Search cancelled.")
                break
    
    def search_knowledge_by_title(self):
        """Search knowledge by title"""
        print("\n📖 Search by Title")
        print("=" * 30)
        
        search_term = input("Enter title to search for: ").strip()
        
        if not search_term:
            print("❌ No search term provided.")
            return
        
        results = self.execute_knowledge_search("title", search_term)
        self.display_knowledge_search_results(results, f"Title: {search_term}")
    
    def search_knowledge_by_content(self):
        """Search knowledge by content"""
        print("\n📝 Search by Content")
        print("=" * 30)
        
        search_term = input("Enter text to search for in content: ").strip()
        
        if not search_term:
            print("❌ No search term provided.")
            return
        
        results = self.execute_knowledge_search("content", search_term)
        self.display_knowledge_search_results(results, f"Content: {search_term}")
    
    def search_knowledge_by_tags(self):
        """Search knowledge by tags"""
        print("\n🏷️  Search by Tags")
        print("=" * 30)
        
        tags = input("Enter tags to search for (comma-separated): ").strip()
        
        if not tags:
            print("❌ No tags provided.")
            return
        
        tag_list = [tag.strip().lower() for tag in tags.split(',')]
        results = self.execute_knowledge_tag_search(tag_list)
        self.display_knowledge_search_results(results, f"Tags: {tags}")
    
    def search_knowledge_by_type(self):
        """Search knowledge by file type"""
        print("\n📂 Search by File Type")
        print("=" * 30)
        
        print("Available types:")
        types = self.get_available_knowledge_types()
        for i, type_name in enumerate(types, 1):
            print(f"  {i}. {type_name}")
        
        type_choice = input("\nEnter type name or number: ").strip()
        
        if type_choice.isdigit():
            type_num = int(type_choice)
            if 1 <= type_num <= len(types):
                type_choice = types[type_num - 1]
            else:
                print("❌ Invalid type number.")
                return
        
        if not type_choice:
            print("❌ No type provided.")
            return
        
        results = self.execute_knowledge_search("source_type", type_choice)
        self.display_knowledge_search_results(results, f"Type: {type_choice}")
    
    def get_available_knowledge_types(self):
        """Get list of available knowledge types"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT DISTINCT source_type FROM system_knowledge ORDER BY source_type')
            types = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            return types
            
        except Exception as e:
            print(f"❌ Could not get types: {e}")
            return []
    
    def search_knowledge_combined(self):
        """Combined search with multiple criteria"""
        print("\n🔍 Combined Knowledge Search")
        print("=" * 30)
        
        title = input("Title (optional): ").strip()
        content = input("Content (optional): ").strip()
        tags = input("Tags (optional, comma-separated): ").strip()
        file_type = input("File type (optional): ").strip()
        
        # Build search criteria
        search_criteria = []
        if title:
            search_criteria.append(f"Title: {title}")
        if content:
            search_criteria.append(f"Content: {content}")
        if tags:
            search_criteria.append(f"Tags: {tags}")
        if file_type:
            search_criteria.append(f"Type: {file_type}")
        
        if not search_criteria:
            print("❌ No search criteria provided.")
            return
        
        results = self.execute_knowledge_combined_search(title, content, tags, file_type)
        self.display_knowledge_search_results(results, "Combined Search: " + " + ".join(search_criteria))
    
    def execute_knowledge_search(self, field, search_term):
        """Execute basic knowledge search"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if field == "title":
                query = '''
                    SELECT id, title, content, source_type, tags, created_at, importance_level
                    FROM system_knowledge 
                    WHERE title LIKE ?
                    ORDER BY importance_level DESC, created_at DESC
                '''
            elif field == "content":
                query = '''
                    SELECT id, title, content, source_type, tags, created_at, importance_level
                    FROM system_knowledge 
                    WHERE content LIKE ?
                    ORDER BY importance_level DESC, created_at DESC
                '''
            elif field == "source_type":
                query = '''
                    SELECT id, title, content, source_type, tags, created_at, importance_level
                    FROM system_knowledge 
                    WHERE source_type = ?
                    ORDER BY importance_level DESC, created_at DESC
                '''
            else:
                return []
            
            cursor.execute(query, (f'%{search_term}%' if field != "source_type" else search_term,))
            results = cursor.fetchall()
            conn.close()
            
            return results
            
        except Exception as e:
            print(f"❌ Search error: {e}")
            return []
    
    def execute_knowledge_tag_search(self, tag_list):
        """Execute tag-based knowledge search"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build tag search query
            tag_conditions = []
            tag_params = []
            for tag in tag_list:
                tag_conditions.append("tags LIKE ?")
                tag_params.append(f'%{tag}%')
            
            query = f'''
                SELECT id, title, content, source_type, tags, created_at, importance_level
                FROM system_knowledge 
                WHERE {' OR '.join(tag_conditions)}
                ORDER BY importance_level DESC, created_at DESC
            '''
            
            cursor.execute(query, tag_params)
            results = cursor.fetchall()
            conn.close()
            
            return results
            
        except Exception as e:
            print(f"❌ Tag search error: {e}")
            return []
    
    def execute_knowledge_combined_search(self, title, content, tags, file_type):
        """Execute combined knowledge search"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build dynamic query
            query_parts = []
            params = []
            
            if title:
                query_parts.append("title LIKE ?")
                params.append(f'%{title}%')
            
            if content:
                query_parts.append("content LIKE ?")
                params.append(f'%{content}%')
            
            if tags:
                tag_list = [tag.strip().lower() for tag in tags.split(',')]
                tag_conditions = []
                for tag in tag_list:
                    tag_conditions.append("tags LIKE ?")
                    params.append(f'%{tag}%')
                query_parts.append(f"({' OR '.join(tag_conditions)})")
            
            if file_type:
                query_parts.append("source_type = ?")
                params.append(file_type)
            
            if not query_parts:
                return []
            
            query = f'''
                SELECT id, title, content, source_type, tags, created_at, importance_level
                FROM system_knowledge 
                WHERE {' AND '.join(query_parts)}
                ORDER BY importance_level DESC, created_at DESC
            '''
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            conn.close()
            
            return results
            
        except Exception as e:
            print(f"❌ Combined search error: {e}")
            return []
    
    def display_knowledge_search_results(self, results, search_description):
        """Display knowledge search results with options"""
        if not results:
            print(f"\n❌ No results found for: {search_description}")
            return
        
        print(f"\n🔍 Search Results for: {search_description}")
        print(f"📊 Found {len(results)} items:")
        print("=" * 80)
        
        for i, (kid, title, content, source_type, tags, created_at, importance) in enumerate(results, 1):
            importance_stars = "⭐" * importance
            content_preview = content[:150] + "..." if len(content) > 150 else content
            
            print(f"\n{i}. {title}")
            print(f"   📂 Type: {source_type} | {importance_stars}")
            print(f"   📅 Created: {created_at}")
            if tags:
                print(f"   🏷️  Tags: {tags}")
            print(f"   📝 Content: {content_preview}")
            print("-" * 60)
        
        # Offer actions
        print("\n📋 Actions:")
        print("  view <number> - View full content")
        print("  copy <number> - Copy to clipboard")
        print("  edit <number> - Edit title/tags")
        print("  delete <number> - Delete this knowledge")
        print("  exit - Return to main menu")
        
        while True:
            try:
                action = input("\nEnter action: ").strip()
                
                if action.lower() == 'exit':
                    break
                elif action.startswith('view '):
                    try:
                        item_num = int(action.split()[1])
                        if 1 <= item_num <= len(results):
                            selected = results[item_num - 1]
                            print(f"\n📖 Full Content: {selected[1]}")
                            print("=" * 80)
                            print(selected[2])  # content
                            print("=" * 80)
                            break
                        else:
                            print(f"❌ Invalid item number. Choose 1-{len(results)}")
                    except (ValueError, IndexError):
                        print("❌ Invalid format. Use 'view <number>'")
                elif action.startswith('copy '):
                    try:
                        item_num = int(action.split()[1])
                        if 1 <= item_num <= len(results):
                            selected = results[item_num - 1]
                            self.copy_to_clipboard(selected[2])  # content
                            print(f"✅ Item {item_num} copied to clipboard!")
                            break
                        else:
                            print(f"❌ Invalid item number. Choose 1-{len(results)}")
                    except (ValueError, IndexError):
                        print("❌ Invalid format. Use 'copy <number>'")
                elif action.startswith('edit '):
                    try:
                        item_num = int(action.split()[1])
                        if 1 <= item_num <= len(results):
                            selected = results[item_num - 1]
                            self.edit_knowledge_item(selected[0])
                            break
                        else:
                            print(f"❌ Invalid item number. Choose 1-{len(results)}")
                    except (ValueError, IndexError):
                        print("❌ Invalid format. Use 'edit <number>'")
                elif action.startswith('delete '):
                    try:
                        item_num = int(action.split()[1])
                        if 1 <= item_num <= len(results):
                            selected = results[item_num - 1]
                            confirm = input(f"❌ Delete '{selected[1]}'? (yes/no): ").strip().lower()
                            if confirm == 'yes':
                                self.delete_knowledge_by_id(selected[0])
                                print(f"✅ Knowledge item {item_num} deleted!")
                                break
                            else:
                                print("❌ Deletion cancelled.")
                                break
                        else:
                            print(f"❌ Invalid item number. Choose 1-{len(results)}")
                    except (ValueError, IndexError):
                        print("❌ Invalid format. Use 'delete <number>'")
                else:
                    print("❌ Invalid action. Use: view <number>, copy <number>, edit <number>, delete <number>, or exit")
                    
            except KeyboardInterrupt:
                break
    
    def edit_knowledge_item(self, knowledge_id):
        """Edit knowledge item title and tags"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT title, tags FROM system_knowledge WHERE id = ?', (knowledge_id,))
            result = cursor.fetchone()
            
            if not result:
                print("❌ Knowledge item not found.")
                return
            
            title, tags = result
            
            print(f"\n✏️  Edit Knowledge Item")
            print("=" * 40)
            print(f"Current title: {title}")
            print(f"Current tags: {tags}")
            
            new_title = input(f"New title (or press Enter to keep '{title}'): ").strip()
            if not new_title:
                new_title = title
            
            new_tags = input(f"New tags (or press Enter to keep '{tags}'): ").strip()
            if not new_tags:
                new_tags = tags
            
            # Update database
            cursor.execute('''
                UPDATE system_knowledge 
                SET title = ?, tags = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (new_title, new_tags, knowledge_id))
            
            conn.commit()
            conn.close()
            
            print("✅ Knowledge item updated!")
            
        except Exception as e:
            print(f"❌ Could not update knowledge: {e}")
    
    def verify_config(self):
        """Verify configuration file and show debugging info"""
        print("\n🔍 Configuration Verification")
        print("=" * 40)
        
        print(f"📁 Config file path: {self.config_path}")
        print(f"📝 Config file exists: {os.path.exists(self.config_path)}")
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    file_content = f.read()
                    file_config = json.loads(file_content)
                
                print(f"📊 File size: {len(file_content)} bytes")
                print(f"📋 File default_model: {file_config.get('default_model', 'NOT FOUND')}")
                print(f"🧠 Memory default_model: {self.config.get('default_model', 'NOT FOUND')}")
                
                if file_config.get('default_model') != self.config.get('default_model'):
                    print("❌ MISMATCH: File and memory configs are different!")
                else:
                    print("✅ MATCH: File and memory configs are the same")
                    
            except Exception as e:
                print(f"❌ Error reading config file: {e}")
        else:
            print("❌ Config file does not exist")
    
    def delete_system_knowledge(self):
        """Delete system knowledge"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT id, title FROM system_knowledge ORDER BY created_at DESC')
            knowledge_items = cursor.fetchall()
            conn.close()
            
            if not knowledge_items:
                print("\n❌ No system knowledge to delete.")
                return
            
            print("\n🗑️  Delete System Knowledge:")
            print("=" * 40)
            
            for i, (kid, title) in enumerate(knowledge_items, 1):
                print(f"{i}. {title}")
            
            try:
                choice = input(f"\nSelect item to delete (1-{len(knowledge_items)}) or 'cancel': ").strip()
                
                if choice.lower() == 'cancel':
                    print("❌ Deletion cancelled.")
                    return
                elif choice.isdigit():
                    choice_num = int(choice)
                    if 1 <= choice_num <= len(knowledge_items):
                        selected = knowledge_items[choice_num - 1]
                        confirm = input(f"❌ Delete '{selected[1]}'? (yes/no): ").strip().lower()
                        if confirm == 'yes':
                            self.delete_knowledge_by_id(selected[0])
                            print(f"✅ Knowledge item deleted!")
                        else:
                            print("❌ Deletion cancelled.")
                    else:
                        print(f"❌ Invalid number. Choose 1-{len(knowledge_items)}")
                else:
                    print("❌ Invalid input.")
                    
            except KeyboardInterrupt:
                print("\n❌ Deletion cancelled.")
                
        except Exception as e:
            print(f"❌ Could not retrieve knowledge: {e}")
    
    def delete_knowledge_by_id(self, knowledge_id):
        """Delete knowledge by ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM system_knowledge WHERE id = ?', (knowledge_id,))
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ Could not delete knowledge: {e}")
    
    def get_system_knowledge_for_context(self):
        """Get system knowledge to include in AI context"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT title, content, source_type, tags
                FROM system_knowledge 
                ORDER BY importance_level DESC, created_at DESC
                LIMIT 5
            ''')
            
            knowledge_items = cursor.fetchall()
            conn.close()
            
            if not knowledge_items:
                return ""
            
            # Format knowledge for AI context
            context = "\n\n=== SYSTEM KNOWLEDGE ===\n"
            for title, content, source_type, tags in knowledge_items:
                context += f"\n📚 {title} ({source_type})"
                if tags:
                    context += f" [Tags: {tags}]"
                context += f"\n{content}\n"
                context += "-" * 50 + "\n"
            
            return context
            
        except Exception as e:
            print(f"Warning: Could not retrieve system knowledge: {e}")
            return ""
    
    def search_memory(self):
        """Search memory with advanced metadata queries"""
        print("\n🔍 Advanced Memory Search")
        print("=" * 40)
        
        # Validate search prerequisites
        if not self.validate_search_prerequisites():
            print("❌ Search system not ready. Please fix the issues above first.")
            return
        
        print("📋 Search Options:")
        print("  1. Search by Date (e.g., 'last Tuesday', '2024-08-20')")
        print("  2. Search by Topic (e.g., 'Python', 'AI', 'Web Development')")
        print("  3. Search by Category (e.g., 'code', 'tasks', 'custom')")
        print("  4. Search by Tags")
        print("  5. Search by Importance Level")
        print("  6. Combined Search")
        print("  7. Cancel")
        
        while True:
            try:
                choice = input("\nSelect search type (1-7): ").strip()
                
                if choice == '1':
                    self.search_by_date()
                    break
                elif choice == '2':
                    self.search_by_topic()
                    break
                elif choice == '3':
                    self.search_by_category()
                    break
                elif choice == '4':
                    self.search_by_tags()
                    break
                elif choice == '5':
                    self.search_by_importance()
                    break
                elif choice == '6':
                    self.combined_search()
                    break
                elif choice == '7':
                    print("❌ Search cancelled.")
                    break
                else:
                    print("❌ Please enter a number between 1-7")
                    
            except KeyboardInterrupt:
                print("\n❌ Search cancelled.")
                break
    
    def search_by_date(self):
        """Search by date with natural language support"""
        print("\n📅 Date Search")
        print("=" * 30)
        
        print("💡 Examples:")
        print("  - 'last Tuesday'")
        print("  - '2024-08-20'")
        print("  - 'this week'")
        print("  - 'August 2024'")
        print("  - 'yesterday'")
        
        date_query = input("\nEnter date search: ").strip()
        
        if not date_query:
            print("❌ No date query provided.")
            return
        
        # Parse natural language date queries
        search_date = self.parse_date_query(date_query)
        if not search_date:
            print("❌ Could not understand date query.")
            return
        
        # Search database
        results = self.search_database_by_date(search_date)
        self.display_search_results(results, f"Date: {date_query}")
    
    def parse_date_query(self, query):
        """Parse natural language date queries"""
        query_lower = query.lower()
        now = datetime.now()
        
        if 'yesterday' in query_lower:
            yesterday = now.replace(day=now.day - 1)
            return yesterday.strftime('%Y-%m-%d')
        elif 'today' in query_lower:
            return now.strftime('%Y-%m-%d')
        elif 'this week' in query_lower:
            # Start of current week (Monday)
            days_since_monday = now.weekday()
            monday = now.replace(day=now.day - days_since_monday)
            return monday.strftime('%Y-%m-%d')
        elif 'last' in query_lower and any(day in query_lower for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']):
            # Find last occurrence of specific weekday
            weekday_map = {'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3, 
                          'friday': 4, 'saturday': 5, 'sunday': 6}
            
            for day_name, day_num in weekday_map.items():
                if day_name in query_lower:
                    days_since = (now.weekday() - day_num) % 7
                    if days_since == 0:
                        days_since = 7
                    target_date = now.replace(day=now.day - days_since)
                    return target_date.strftime('%Y-%m-%d')
        
        # Try to parse as YYYY-MM-DD
        try:
            datetime.strptime(query, '%Y-%m-%d')
            return query
        except ValueError:
            pass
        
        return None
    
    def search_database_by_date(self, date_str):
        """Search database by date"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT ei.title, ei.content, ei.category, ei.topic, ei.importance_level, 
                       ei.created_at, ei.tags
                FROM extracted_info ei
                JOIN metadata_index mi ON ei.id = mi.extracted_info_id
                WHERE mi.date_key = ?
                ORDER BY ei.importance_level DESC, ei.created_at DESC
            ''', (date_str,))
            
            results = cursor.fetchall()
            conn.close()
            
            return results
            
        except Exception as e:
            print(f"❌ Database search error: {e}")
            return []
    
    def search_by_topic(self):
        """Search by topic"""
        print("\n💡 Topic Search")
        print("=" * 30)
        
        topic = input("Enter topic to search for: ").strip()
        
        if not topic:
            print("❌ No topic provided.")
            return
        
        results = self.search_database_by_topic(topic.lower())
        self.display_search_results(results, f"Topic: {topic}")
    
    def search_database_by_topic(self, topic):
        """Search database by topic"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT ei.title, ei.content, ei.category, ei.topic, ei.importance_level, 
                       ei.created_at, ei.tags
                FROM extracted_info ei
                JOIN metadata_index mi ON ei.id = mi.extracted_info_id
                WHERE mi.topic_key LIKE ?
                ORDER BY ei.importance_level DESC, ei.created_at DESC
            ''', (f'%{topic}%',))
            
            results = cursor.fetchall()
            conn.close()
            
            return results
            
        except Exception as e:
            print(f"❌ Database search error: {e}")
            return []
    
    def search_by_category(self):
        """Search by category"""
        print("\n📂 Category Search")
        print("=" * 30)
        
        print("Available categories:")
        categories = self.get_available_categories()
        for i, cat in enumerate(categories, 1):
            print(f"  {i}. {cat}")
        
        category = input("\nEnter category name or number: ").strip()
        
        if category.isdigit():
            cat_num = int(category)
            if 1 <= cat_num <= len(categories):
                category = categories[cat_num - 1]
            else:
                print("❌ Invalid category number.")
                return
        
        if not category:
            print("❌ No category provided.")
            return
        
        results = self.search_database_by_category(category.lower())
        self.display_search_results(results, f"Category: {category}")
    
    def get_available_categories(self):
        """Get list of available categories"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT DISTINCT category FROM extracted_info ORDER BY category')
            categories = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            return categories
            
        except Exception as e:
            print(f"❌ Could not get categories: {e}")
            return []
    
    def search_database_by_category(self, category):
        """Search database by category"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT ei.title, ei.content, ei.category, ei.topic, ei.importance_level, 
                       ei.created_at, ei.tags
                FROM extracted_info ei
                JOIN metadata_index mi ON ei.id = mi.extracted_info_id
                WHERE mi.category_key = ?
                ORDER BY ei.importance_level DESC, ei.created_at DESC
            ''', (category,))
            
            results = cursor.fetchall()
            conn.close()
            
            return results
            
        except Exception as e:
            print(f"❌ Database search error: {e}")
            return []
    
    def search_by_tags(self):
        """Search by tags"""
        print("\n🏷️  Tag Search")
        print("=" * 30)
        
        tags = input("Enter tags to search for (comma-separated): ").strip()
        
        if not tags:
            print("❌ No tags provided.")
            return
        
        tag_list = [tag.strip().lower() for tag in tags.split(',')]
        results = self.search_database_by_tags(tag_list)
        self.display_search_results(results, f"Tags: {tags}")
    
    def search_database_by_tags(self, tag_list):
        """Search database by tags"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build tag search query
            tag_conditions = []
            tag_params = []
            for tag in tag_list:
                tag_conditions.append("mi.tags_key LIKE ?")
                tag_params.append(f'%{tag}%')
            
            query = f'''
                SELECT ei.title, ei.content, ei.category, ei.topic, ei.importance_level, 
                       ei.created_at, ei.tags
                FROM extracted_info ei
                JOIN metadata_index mi ON ei.id = mi.extracted_info_id
                WHERE {' OR '.join(tag_conditions)}
                ORDER BY ei.importance_level DESC, ei.created_at DESC
            '''
            
            cursor.execute(query, tag_params)
            results = cursor.fetchall()
            conn.close()
            
            return results
            
        except Exception as e:
            print(f"❌ Database search error: {e}")
            return []
    
    def search_by_importance(self):
        """Search by importance level"""
        print("\n⭐ Importance Level Search")
        print("=" * 30)
        
        print("Importance levels:")
        print("  1. Low (1)")
        print("  2. Medium (3)")
        print("  3. High (5)")
        print("  4. Custom level")
        
        choice = input("\nSelect importance level: ").strip()
        
        if choice == '1':
            level = 1
        elif choice == '2':
            level = 3
        elif choice == '3':
            level = 5
        elif choice == '4':
            try:
                level = int(input("Enter custom level (1-5): ").strip())
                level = max(1, min(5, level))
            except ValueError:
                print("❌ Invalid importance level.")
                return
        else:
            print("❌ Invalid choice.")
            return
        
        results = self.search_database_by_importance(level)
        self.display_search_results(results, f"Importance Level: {level}")
    
    def search_database_by_importance(self, level):
        """Search database by importance level"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT ei.title, ei.content, ei.category, ei.topic, ei.importance_level, 
                       ei.created_at, ei.tags
                FROM extracted_info ei
                WHERE ei.importance_level >= ?
                ORDER BY ei.importance_level DESC, ei.created_at DESC
            ''', (level,))
            
            results = cursor.fetchall()
            conn.close()
            
            return results
            
        except Exception as e:
            print(f"❌ Database search error: {e}")
            return []
    
    def combined_search(self):
        """Combined search with multiple criteria"""
        print("\n🔍 Combined Search")
        print("=" * 30)
        
        # Collect search criteria
        date_query = input("Date (optional, e.g., 'last Tuesday'): ").strip()
        topic = input("Topic (optional): ").strip()
        category = input("Category (optional): ").strip()
        tags = input("Tags (optional, comma-separated): ").strip()
        
        # Build search query
        search_criteria = []
        if date_query:
            search_criteria.append(f"Date: {date_query}")
        if topic:
            search_criteria.append(f"Topic: {topic}")
        if category:
            search_criteria.append(f"Category: {category}")
        if tags:
            search_criteria.append(f"Tags: {tags}")
        
        if not search_criteria:
            print("❌ No search criteria provided.")
            return
        
        # Execute combined search
        results = self.execute_combined_search(date_query, topic, category, tags)
        self.display_search_results(results, "Combined Search: " + " + ".join(search_criteria))
    
    def execute_combined_search(self, date_query, topic, category, tags):
        """Execute combined search with multiple criteria"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build dynamic query
            query_parts = []
            params = []
            
            if date_query:
                parsed_date = self.parse_date_query(date_query)
                if parsed_date:
                    query_parts.append("mi.date_key = ?")
                    params.append(parsed_date)
            
            if topic:
                query_parts.append("mi.topic_key LIKE ?")
                params.append(f'%{topic.lower()}%')
            
            if category:
                query_parts.append("mi.category_key = ?")
                params.append(category.lower())
            
            if tags:
                tag_list = [tag.strip().lower() for tag in tags.split(',')]
                tag_conditions = []
                for tag in tag_list:
                    tag_conditions.append("mi.tags_key LIKE ?")
                    params.append(f'%{tag}%')
                query_parts.append(f"({' OR '.join(tag_conditions)})")
            
            if not query_parts:
                return []
            
            query = f'''
                SELECT DISTINCT ei.title, ei.content, ei.category, ei.topic, ei.importance_level, 
                       ei.created_at, ei.tags
                FROM extracted_info ei
                JOIN metadata_index mi ON ei.id = mi.extracted_info_id
                WHERE {' AND '.join(query_parts)}
                ORDER BY ei.importance_level DESC, ei.created_at DESC
            '''
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            conn.close()
            
            return results
            
        except Exception as e:
            print(f"❌ Combined search error: {e}")
            return []
    
    def display_search_results(self, results, search_description):
        """Display search results with options"""
        if not results:
            print(f"\n❌ No results found for: {search_description}")
            return
        
        print(f"\n🔍 Search Results for: {search_description}")
        print(f"📊 Found {len(results)} items:")
        print("=" * 80)
        
        for i, (title, content, category, topic, importance, created_at, tags) in enumerate(results, 1):
            importance_stars = "⭐" * importance
            print(f"\n{i}. {title}")
            print(f"   📂 Category: {category} | 💡 Topic: {topic}")
            print(f"   {importance_stars} | 📅 Created: {created_at}")
            if tags:
                print(f"   🏷️  Tags: {tags}")
            print(f"   📝 Content: {content[:150]}..." if len(content) > 150 else f"   📝 Content: {content}")
            print("-" * 60)
        
        # Offer actions
        print("\n📋 Actions:")
        print("  copy <number> - Copy specific item to clipboard")
        print("  copyall - Copy all results to clipboard")
        print("  extract <number> - Save specific item to extracted memory")
        print("  exit - Return to main menu")
        
        while True:
            try:
                action = input("\nEnter action: ").strip()
                
                if action.lower() == 'exit':
                    break
                elif action.lower() == 'copyall':
                    all_content = "\n\n".join([f"Title: {r[0]}\nContent: {r[1]}" for r in results])
                    self.copy_to_clipboard(all_content)
                    print("✅ All results copied to clipboard!")
                    break
                elif action.startswith('copy '):
                    try:
                        item_num = int(action.split()[1])
                        if 1 <= item_num <= len(results):
                            selected = results[item_num - 1]
                            self.copy_to_clipboard(selected[1])  # content
                            print(f"✅ Item {item_num} copied to clipboard!")
                            break
                        else:
                            print(f"❌ Invalid item number. Choose 1-{len(results)}")
                    except (ValueError, IndexError):
                        print("❌ Invalid format. Use 'copy <number>'")
                elif action.startswith('extract '):
                    try:
                        item_num = int(action.split()[1])
                        if 1 <= item_num <= len(results):
                            selected = results[item_num - 1]
                            self.save_extracted_info_with_metadata(
                                f"Extracted from search: {selected[0]}",
                                selected[1],  # content
                                selected[2],  # category
                                "search_extraction",
                                selected[3],  # topic
                                f"Extracted from search: {search_description}",
                                3,  # default importance
                                selected[6] or ""  # tags
                            )
                            print(f"✅ Item {item_num} extracted to memory!")
                            break
                        else:
                            print(f"❌ Invalid item number. Choose 1-{len(results)}")
                    except (ValueError, IndexError):
                        print("❌ Invalid format. Use 'extract <number>'")
                else:
                    print("❌ Invalid action. Use: copy <number>, copyall, extract <number>, or exit")
                    
            except KeyboardInterrupt:
                break
    
    def setup_tab_completion(self):
        """Setup tab completion for slash commands"""
        def slash_completer(text, state):
            """Custom completer for slash commands"""
            if text.startswith('/'):
                # Filter commands that start with the typed text
                matches = [cmd for cmd in self.slash_commands if cmd.startswith(text)]
                if state < len(matches):
                    return matches[state]
            return None
        
        # Set the completer
        readline.set_completer(slash_completer)
        
        # Enable tab completion for different readline implementations
        try:
            readline.parse_and_bind('tab: complete')
        except:
            try:
                readline.parse_and_bind('bind ^I rl_complete')
            except:
                pass
        
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        default_config = {
            "ollama_url": "http://localhost:11434",
            "default_model": "gemma3:1b",
            "temperature": 0.7,
            "max_tokens": 2048,
            "system_prompt": "You are a helpful AI assistant.",
            "chat_history": [],
            "max_history": 10
        }
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    user_config = json.load(f)
                    # Remove old custom_instruction_sets if it exists
                    if 'custom_instruction_sets' in user_config:
                        del user_config['custom_instruction_sets']
                    if 'current_instruction_set' in user_config:
                        del user_config['current_instruction_set']
                    default_config.update(user_config)
            except Exception as e:
                print(f"Warning: Could not load config file: {e}")
                
        return default_config
    
    def save_config(self, quiet=False):
        """Save current configuration to file"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            if not quiet:
                print(f"✅ Configuration saved to: {self.config_path}")
        except Exception as e:
            if not quiet:
                print(f"❌ Error saving config: {e}")
                print(f"Config path: {self.config_path}")
    
    def test_connection(self) -> bool:
        """Test connection to Ollama instance"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def list_models(self) -> list:
        """List available models using ollama CLI command"""
        try:
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and result.stdout.strip():
                models = []
                lines = result.stdout.strip().split('\n')
                # Skip the header line (first line)
                for line in lines[1:]:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 1:
                            model_name = parts[0]
                            models.append(model_name)
                return models
            return []
        except subprocess.TimeoutExpired:
            print("❌ Timeout getting models from Ollama")
            return []
        except Exception as e:
            print(f"❌ Error listing models: {e}")
            return []
    
    def chat(self, message: str, model: str = None) -> str:
        """Send a chat message to Ollama"""
        if not model:
            model = self.config.get("default_model", "phi3.5:latest")
            
        # Get system knowledge to include in context
        system_knowledge = self.get_system_knowledge_for_context()
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": self.config.get("system_prompt", "") + system_knowledge},
                {"role": "user", "content": message}
            ],
            "stream": False,
            "options": {
                "temperature": self.config.get("temperature", 0.7),
                "num_predict": self.config.get("max_tokens", 2048)
            }
        }
        
        try:
            response = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=60)
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("message", {}).get("content", "No response")
                
                # Save to database
                self.save_conversation(message, response_text)
                
                # Update chat history (keep for backward compatibility)
                self.config["chat_history"].append({
                    "user": message,
                    "assistant": response_text,
                    "timestamp": time.time()
                })
                
                # Keep only recent history
                if len(self.config["chat_history"]) > self.config.get("max_history", 10):
                    self.config["chat_history"] = self.config["chat_history"][-self.config.get("max_history", 10):]
                
                self.save_config(quiet=True)
                return response_text
            else:
                return f"Error: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Error: {e}"
    
    def interactive_chat(self):
        """Start interactive chat session"""
        # Validate and fix model configuration first
        self.force_update_model_config()
        
        # Validate clipboard access
        self.validate_clipboard_access()
        
        # Validate database connection
        self.validate_database_connection()
        
        print("🤖 God CLI - Ollama Chat Interface")
        print("=" * 50)
        print(f"Connected to: {self.base_url}")
        print(f"Current model: {self.config.get('default_model', 'phi3.5:latest')}")
        print("Type 'quit', 'exit', or 'q' to end session")
        print("Type 'help' for commands")
        print("=" * 50)
        
        while True:
            try:
                user_input = input("\n💬 You: ").strip()
                
                # Show auto-complete suggestions for partial slash commands
                if user_input.startswith('/') and len(user_input) > 1:
                    selected_command = self.show_autocomplete_suggestions(user_input)
                    if selected_command:
                        user_input = selected_command
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    self.end_session()
                    break
                elif user_input.lower() == 'help':
                    self.show_help()
                    continue
                elif user_input.lower() == 'models':
                    self.show_models_menu()
                    continue
                elif user_input.lower() == 'change':
                    self.change_model()
                    continue
                elif user_input.lower() == 'config':
                    self.show_config()
                    continue
                elif user_input.lower() == 'clear':
                    os.system('clear' if os.name == 'posix' else 'cls')
                    continue
                elif user_input.startswith('/'):
                    self.handle_slash_command(user_input)
                    continue
                elif not user_input:
                    continue
                
                print("\n🤖 Assistant: ", end="", flush=True)
                response = self.chat(user_input)
                print(response)
                
                # Store the last response for copy commands
                self.last_response = response
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                self.end_session()
                break
            except EOFError:
                print("\n\n👋 Goodbye!")
                self.end_session()
                break
    
    def show_help(self):
        """Show available commands"""
        print("\n📖 Available Commands:")
        print("  help     - Show this help message")
        print("  models   - List available models")
        print("  change   - Change current model")
        print("  config   - Show current configuration")
        print("  clear    - Clear the screen")
        print("  quit/exit/q - Exit the chat")
        print("\n🔧 Slash Commands:")
        print("  /copy     - Copy last AI response")
        print("  /copyall  - Copy entire conversation")
        print("  /help     - Show slash commands help")
        print("\n💡 Just type your message to chat with the AI!")
    
    def show_models_menu(self):
        """Show available models with selection options"""
        models = self.list_models()
        if not models:
            print("❌ No models found or connection failed")
            print("💡 Try installing a model: ollama pull mistral:7b")
            return
        
        print("\n📚 Available Models:")
        print("=" * 30)
        for i, model in enumerate(models, 1):
            current_indicator = " ← Current" if model == self.config.get('default_model') else ""
            print(f"{i:2d}. {model}{current_indicator}")
        print("=" * 30)
        print("Commands:")
        print("  change - Change current model")
        print("  models - Show this menu again")
        
        # Offer model selection
        try:
            choice = input(f"\nSelect model (1-{len(models)}) or press Enter to continue: ").strip()
            if choice.isdigit():
                choice_num = int(choice)
                if 1 <= choice_num <= len(models):
                    selected_model = models[choice_num - 1]
                    if selected_model != self.config.get('default_model'):
                        old_model = self.config.get('default_model')
                        print(f"🔄 Changing model from '{old_model}' to '{selected_model}'")
                        
                        # Update the config
                        self.config['default_model'] = selected_model
                        self.save_config()
                        
                        print(f"✅ Model changed successfully!")
                        print(f"🔄 New default model: {selected_model}")
                    else:
                        print(f"✅ '{selected_model}' is already the current model")
                else:
                    print(f"❌ Please enter a number between 1 and {len(models)}")
        except KeyboardInterrupt:
            print("\nModel selection cancelled.")
        except ValueError:
            print("❌ Please enter a valid number")
    
    def change_model(self):
        """Interactive model selection"""
        models = self.list_models()
        if not models:
            print("❌ No models available")
            return
        
        print("\n🔄 Model Selection:")
        print("=" * 30)
        for i, model in enumerate(models, 1):
            current_indicator = " ← Current" if model == self.config.get('default_model') else ""
            print(f"{i:2d}. {model}{current_indicator}")
        print("=" * 30)
        
        while True:
            try:
                choice = input(f"Select model (1-{len(models)}) or 'cancel': ").strip()
                
                if choice.lower() == 'cancel':
                    print("Model change cancelled.")
                    break
                
                try:
                    model_index = int(choice) - 1
                    if 0 <= model_index < len(models):
                        selected_model = models[model_index]
                        old_model = self.config.get('default_model')
                        print(f"🔄 Changing model from '{old_model}' to '{selected_model}'")
                        
                        # Update the config
                        self.config['default_model'] = selected_model
                        print(f"📝 Config updated in memory")
                        
                        # Save to file
                        self.save_config()
                        
                        # Verify the change
                        current_model = self.config.get('default_model')
                        print(f"✅ Model changed successfully!")
                        print(f"🔄 New default model: {current_model}")
                        print(f"📁 Config saved to: {self.config_path}")
                        break
                    else:
                        print(f"❌ Please enter a number between 1 and {len(models)}")
                except ValueError:
                    print("❌ Please enter a valid number or 'cancel'")
                    
            except KeyboardInterrupt:
                print("\nModel change cancelled.")
                break
    
    def handle_slash_command(self, command):
        """Handle slash commands like /copy, /copyall, etc."""
        cmd_parts = command.lower().split()
        cmd = cmd_parts[0]
        
        if cmd == '/copy':
            if len(cmd_parts) > 1:
                # Copy specific text: /copy "text to copy"
                text_to_copy = ' '.join(cmd_parts[1:])
                if self.copy_to_clipboard(text_to_copy):
                    print("✅ Custom text copied to clipboard!")
            else:
                # Copy the last assistant response
                if hasattr(self, 'last_response') and self.last_response:
                    if self.copy_to_clipboard(self.last_response):
                        print("✅ Last response copied to clipboard!")
                else:
                    print("❌ No response to copy. Chat with the AI first!")
                
        elif cmd == '/copyall':
            # Copy entire conversation
            self.copy_conversation_to_clipboard()
            
        elif cmd == '/help':
            self.show_slash_commands_help()
            
        elif cmd == '/clear' or cmd == '/c':
            os.system('clear' if os.name == 'posix' else 'cls')
            
        elif cmd == '/config':
            self.show_config()
            
        elif cmd == '/verify':
            self.verify_config()
            
        elif cmd == '/fixmodels':
            self.force_update_model_config()
            
        elif cmd == '/testclipboard':
            self.test_clipboard()
            
        elif cmd == '/testdb':
            self.test_database()
            
        elif cmd == '/testsearch':
            self.test_search_system()
            
        elif cmd == '/models':
            self.show_models_menu()
            
        elif cmd == '/change':
            self.change_model()
            
        elif cmd == '/prompt':
            self.manage_system_prompt()
            
        elif cmd == '/memory':
            self.show_memory_info()
            
        elif cmd == '/extract':
            self.extract_key_details()
            
        elif cmd == '/search':
            self.search_memory()
            
        elif cmd == '/knowledge':
            self.manage_system_knowledge()
            

            
        else:
            # Show suggestions for partial matches
            suggestions = [c for c in self.slash_commands if c.startswith(cmd)]
            if suggestions:
                print(f"❌ Unknown slash command: {cmd}")
                print("Did you mean one of these?")
                for suggestion in suggestions:
                    print(f"  {suggestion}")
            else:
                print(f"❌ Unknown slash command: {cmd}")
                print("Type /help to see available slash commands")
    
    def show_autocomplete_suggestions(self, partial_command):
        """Show auto-complete suggestions for partial slash commands"""
        suggestions = [cmd for cmd in self.slash_commands if cmd.startswith(partial_command)]
        if suggestions:
            print(f"\n💡 Auto-complete suggestions for '{partial_command}':")
            for i, suggestion in enumerate(suggestions, 1):
                print(f"  {i}. {suggestion}")
            print()
            
            # Offer quick selection
            try:
                choice = input("Quick select (1-{}) or press Enter to continue typing: ".format(len(suggestions))).strip()
                if choice.isdigit():
                    choice_num = int(choice)
                    if 1 <= choice_num <= len(suggestions):
                        selected_command = suggestions[choice_num - 1]
                        print(f"✅ Selected: {selected_command}")
                        return selected_command
            except KeyboardInterrupt:
                pass
        return None
    
    def change_system_prompt(self):
        """Interactive system prompt change"""
        print("\n🤖 Edit System Prompt")
        print("=" * 40)
        print(f"Current system prompt:")
        print(f"'{self.config.get('system_prompt', 'You are a helpful AI assistant.')}'")
        print("\n" + "=" * 40)
        
        print("\n📝 Enter new system prompt (or 'cancel' to keep current, 'reset' for default):")
        
        try:
            new_prompt = input("New prompt: ").strip()
            
            if new_prompt.lower() == 'cancel':
                print("❌ System prompt change cancelled.")
                return
            elif new_prompt.lower() == 'reset':
                new_prompt = "You are a helpful AI assistant."
                self.config['system_prompt'] = new_prompt
                self.save_config()
                print("✅ System prompt reset to default!")
                return
            elif not new_prompt:
                print("❌ System prompt cannot be empty.")
                return
            
            # Confirm the change
            print(f"\n📋 New system prompt:")
            print("=" * 40)
            print(new_prompt)
            print("=" * 40)
            
            confirm = input("\n✅ Save this new system prompt? (y/n): ").strip().lower()
            if confirm in ['y', 'yes']:
                self.config['system_prompt'] = new_prompt
                self.save_config()
                print("✅ System prompt updated and saved!")
                print("🔄 New prompt will be used for future conversations.")
            else:
                print("❌ System prompt change cancelled.")
                
        except KeyboardInterrupt:
            print("\n❌ System prompt change cancelled.")
        except EOFError:
            print("\n❌ Input ended unexpectedly.")
    
    def show_slash_commands_help(self):
        """Show help for slash commands"""
        print("\n🔧 Slash Commands:")
        print("=" * 30)
        print("  /copy     - Copy last AI response")
        print("  /copyall  - Copy entire conversation")
        print("  /copy text - Copy specific text")
        print("  /help     - Show this help")
        print("  /clear    - Clear screen")
        print("  /config   - Show configuration")
        print("  /verify   - Verify configuration file")
        print("  /fixmodels - Fix model configuration issues")
        print("  /testclipboard - Test clipboard functionality")
        print("  /testdb   - Test database functionality")
        print("  /testsearch   - Test search system functionality")
        print("  /models   - Show available models")
        print("  /change   - Change model")
        print("  /prompt   - Change system prompt")
        print("  /memory   - Show memory & database info")
        print("  /extract  - Extract key details from conversations")
        print("  /search   - Advanced memory search with metadata")
        print("  /knowledge - Manage system knowledge (files, text)")
        print("  /prompt   - Manage system prompt")
        print("  /cleanup  - Clean up old configuration")
        print("=" * 30)
    
    def validate_clipboard_access(self):
        """Validate clipboard access and return available method"""
        try:
            import platform
            system = platform.system()
            
            if system == "Darwin":  # macOS
                # Test pbcopy availability
                result = subprocess.run(['which', 'pbcopy'], capture_output=True, text=True)
                if result.returncode == 0:
                    return "pbcopy", "macOS clipboard"
                else:
                    return None, "pbcopy not found on macOS"
                    
            elif system == "Linux":
                # Test xclip first
                result = subprocess.run(['which', 'xclip'], capture_output=True, text=True)
                if result.returncode == 0:
                    return "xclip", "Linux xclip clipboard"
                # Test xsel as fallback
                result = subprocess.run(['which', 'xsel'], capture_output=True, text=True)
                if result.returncode == 0:
                    return "xsel", "Linux xsel clipboard"
                else:
                    return None, "Neither xclip nor xsel found on Linux"
                    
            elif system == "Windows":
                # Test clip availability
                result = subprocess.run(['where', 'clip'], capture_output=True, text=True)
                if result.returncode == 0:
                    return "clip", "Windows clipboard"
                else:
                    return None, "clip command not found on Windows"
            else:
                return None, f"Unsupported system: {system}"
                
        except Exception as e:
            return None, f"Error detecting clipboard: {e}"
    
    def copy_to_clipboard(self, text, quiet=False):
        """Copy text to clipboard using system commands with validation"""
        if not text or not text.strip():
            if not quiet:
                print("❌ No text to copy")
            return False
            
        # Validate clipboard access first
        method, description = self.validate_clipboard_access()
        if not method:
            if not quiet:
                print(f"❌ Clipboard not available: {description}")
                print("💡 Install required tools:")
                if platform.system() == "Linux":
                    print("  - xclip: sudo apt install xclip (Ubuntu/Debian)")
                    print("  - xsel: sudo apt install xsel (Ubuntu/Debian)")
            return False
            
        try:
            if method == "pbcopy":
                process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
                process.communicate(input=text.encode('utf-8'))
            elif method == "xclip":
                process = subprocess.Popen(['xclip', '-selection', 'clipboard'], stdin=subprocess.PIPE)
                process.communicate(input=text.encode('utf-8'))
            elif method == "xsel":
                process = subprocess.Popen(['xsel', '--clipboard', '--input'], stdin=subprocess.PIPE)
                process.communicate(input=text.encode('utf-8'))
            elif method == "clip":
                process = subprocess.Popen(['clip'], stdin=subprocess.PIPE)
                process.communicate(input=text.encode('utf-8'))
            
            if not quiet:
                print(f"✅ Text copied to clipboard using {description}")
            return True
                
        except Exception as e:
            if not quiet:
                print(f"❌ Failed to copy to clipboard: {e}")
            return False
    
    def copy_conversation_to_clipboard(self):
        """Copy entire conversation history to clipboard"""
        if not self.config.get('chat_history'):
            print("❌ No conversation history to copy")
            return False
            
        conversation = []
        for entry in self.config['chat_history']:
            conversation.append(f"You: {entry['user']}")
            conversation.append(f"Assistant: {entry['assistant']}")
            conversation.append("")  # Empty line between exchanges
        
        full_conversation = "\n".join(conversation)
        if self.copy_to_clipboard(full_conversation, quiet=True):
            print("✅ Full conversation copied to clipboard!")
            return True
        else:
            print("❌ Failed to copy conversation to clipboard")
            return False
    
    def show_config(self):
        """Show current configuration"""
        print("\n⚙️  Current Configuration:")
        print(f"  Ollama URL: {self.config.get('ollama_url')}")
        print(f"  Current Model: {self.config.get('default_model')}")
        print(f"  Temperature: {self.config.get('temperature')}")
        print(f"  Max Tokens: {self.config.get('max_tokens')}")
        print(f"  System Prompt: {self.config.get('system_prompt')[:50]}...")
        print(f"  Chat History: {len(self.config.get('chat_history', []))} messages")
    
    def force_update_model_config(self):
        """Force update configuration with available models"""
        available_models = self.list_models()
        if not available_models:
            print("❌ No models available")
            return False
            
        print(f"🔄 Available models: {', '.join(available_models)}")
        print(f"📝 Current config model: {self.config.get('default_model')}")
        
        # If current model is not available, switch to first available
        if self.config.get('default_model') not in available_models:
            new_model = available_models[0]
            print(f"🔄 Switching to '{new_model}' (first available)")
            self.config['default_model'] = new_model
            self.save_config()
            print(f"✅ Configuration updated!")
            return True
        else:
            print(f"✅ Current model '{self.config.get('default_model')}' is available")
            return True
    
    def show_models_menu(self):
        """Show available models with selection options"""
        models = self.list_models()
        if not models:
            print("❌ No models found or connection failed")
            print("💡 Try installing a model: ollama pull mistral:7b")
            return
        
        print("\n📚 Available Models:")
        print("=" * 30)
        for i, model in enumerate(models, 1):
            current_indicator = " ← Current" if model == self.config.get('default_model') else ""
            print(f"{i:2d}. {model}{current_indicator}")
        print("=" * 30)
        print("Commands:")
        print("  change - Change current model")
        print("  models - Show this menu again")
        
        # Offer model selection
        try:
            choice = input(f"\nSelect model (1-{len(models)}) or press Enter to continue: ").strip()
            if choice.isdigit():
                choice_num = int(choice)
                if 1 <= choice_num <= len(models):
                    selected_model = models[choice_num - 1]
                    if selected_model != self.config.get('default_model'):
                        old_model = self.config.get('default_model')
                        print(f"🔄 Changing model from '{old_model}' to '{selected_model}'")
                        
                        # Update the config
                        self.config['default_model'] = selected_model
                        self.save_config()
                        
                        print(f"✅ Model changed successfully!")
                        print(f"🔄 New default model: {selected_model}")
                    else:
                        print(f"✅ '{selected_model}' is already the current model")
                else:
                    print(f"❌ Please enter a number between 1 and {len(models)}")
        except KeyboardInterrupt:
            print("\nModel selection cancelled.")
        except ValueError:
            print("❌ Please enter a valid number")
    
    def test_clipboard(self):
        """Test clipboard functionality"""
        print("\n📋 Clipboard Functionality Test")
        print("=" * 40)
        
        method, description = self.validate_clipboard_access()
        if method:
            print(f"✅ Clipboard available: {description}")
            
            # Test with a simple text
            test_text = "God CLI clipboard test - " + datetime.now().strftime("%H:%M:%S")
            if self.copy_to_clipboard(test_text, quiet=True):
                print("✅ Test copy successful! Check your clipboard.")
                print(f"📝 Test text: '{test_text}'")
            else:
                print("❌ Test copy failed")
        else:
            print(f"❌ Clipboard not available: {description}")
            print("\n💡 Troubleshooting:")
            if platform.system() == "Darwin":
                print("  - Ensure you're on macOS")
                print("  - pbcopy should be available by default")
            elif platform.system() == "Linux":
                print("  - Install xclip: sudo apt install xclip (Ubuntu/Debian)")
                print("  - Or install xsel: sudo apt install xsel (Ubuntu/Debian)")
            elif platform.system() == "Windows":
                print("  - clip command should be available by default")
                print("  - Try running as administrator if issues persist")
        
        print("=" * 40)
    
    def validate_database_connection(self):
        """Validate database connection and return status"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Test basic operations
            cursor.execute('SELECT COUNT(*) FROM conversations')
            cursor.fetchone()
            
            cursor.execute('SELECT COUNT(*) FROM extracted_info')
            cursor.fetchone()
            
            conn.close()
            return True, "Database connection successful"
            
        except sqlite3.OperationalError as e:
            if "no such table" in str(e).lower():
                return False, "Database tables not initialized. Run the CLI to create them."
            else:
                return False, f"Database operational error: {e}"
        except sqlite3.DatabaseError as e:
            return False, f"Database corruption detected: {e}"
        except Exception as e:
            return False, f"Database connection failed: {e}"
    
    def validate_extraction_prerequisites(self):
        """Validate prerequisites for extraction operations"""
        # Check database connection
        db_ok, db_message = self.validate_database_connection()
        if not db_ok:
            print(f"❌ Database issue: {db_message}")
            return False
        
        # Check if there are conversations to extract from
        conversations = self.get_conversation_history(limit=1)
        if not conversations:
            print("❌ No conversations found to extract from.")
            print("💡 Chat with the AI first to create some conversation history.")
            return False
        
        return True
    
    def show_extraction_progress(self, current, total, operation="Processing"):
        """Show progress indicator for extraction operations"""
        if total <= 1:
            return
        
        percentage = (current / total) * 100
        bar_length = 20
        filled_length = int(bar_length * current // total)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        
        print(f"\r{operation}: [{bar}] {current}/{total} ({percentage:.1f}%)", end='', flush=True)
        if current == total:
            print()  # New line when complete
    
    def test_database(self):
        """Test database functionality and connection"""
        print("\n🗄️  Database Functionality Test")
        print("=" * 40)
        
        # Test connection
        db_ok, db_message = self.validate_database_connection()
        if db_ok:
            print(f"✅ {db_message}")
            
            # Test basic operations
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Test conversations table
                cursor.execute('SELECT COUNT(*) FROM conversations')
                conv_count = cursor.fetchone()[0]
                print(f"✅ Conversations table: {conv_count} records")
                
                # Test extracted_info table
                cursor.execute('SELECT COUNT(*) FROM extracted_info')
                extract_count = cursor.fetchone()[0]
                print(f"✅ Extracted info table: {extract_count} records")
                
                # Test sessions table
                cursor.execute('SELECT COUNT(*) FROM sessions')
                session_count = cursor.fetchone()[0]
                print(f"✅ Sessions table: {session_count} records")
                
                # Database size
                db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
                db_size_mb = db_size / (1024 * 1024)
                print(f"✅ Database size: {db_size_mb:.2f} MB")
                
                conn.close()
                
                # Test extraction prerequisites
                if self.validate_extraction_prerequisites():
                    print("✅ Extraction prerequisites: Ready")
                else:
                    print("⚠️  Extraction prerequisites: Some issues detected")
                    
            except Exception as e:
                print(f"❌ Database test failed: {e}")
        else:
            print(f"❌ {db_message}")
            print("\n💡 Troubleshooting:")
            print("  - Ensure the CLI has been run at least once to initialize the database")
            print("  - Check file permissions for the database directory")
            print("  - Try restarting the CLI")
        
        print("=" * 40)
    
    def validate_database_connection(self):
        """Validate database connection and return status"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Test basic operations
            cursor.execute('SELECT COUNT(*) FROM conversations')
            cursor.fetchone()
            
            cursor.execute('SELECT COUNT(*) FROM extracted_info')
            cursor.fetchone()
            
            conn.close()
            return True, "Database connection successful"
            
        except sqlite3.OperationalError as e:
            if "no such table" in str(e).lower():
                return False, "Database tables not initialized. Run the CLI to create them."
            else:
                return False, f"Database operational error: {e}"
        except sqlite3.DatabaseError as e:
            return False, f"Database corruption detected: {e}"
        except Exception as e:
            return False, f"Database connection failed: {e}"
    
    def validate_search_prerequisites(self):
        """Validate search system prerequisites"""
        try:
            # Check database connection
            if not self.validate_database_connection():
                return False
            
            # Check if any extracted info exists
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM extracted_info')
            extracted_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM metadata_index')
            metadata_count = cursor.fetchone()[0]
            
            conn.close()
            
            if extracted_count == 0:
                print("❌ No extracted information found in memory.")
                print("💡 Use /extract to create some memory entries first.")
                return False
                
            if metadata_count == 0:
                print("⚠️  Warning: No metadata index found.")
                print("💡 This may affect search performance.")
                print("🔄 Attempting to rebuild metadata index...")
                self.rebuild_metadata_index()
            
            return True
            
        except Exception as e:
            print(f"❌ Search validation error: {e}")
            return False
    
    def rebuild_metadata_index(self):
        """Rebuild the metadata index for better search performance"""
        try:
            print("🔄 Rebuilding metadata index...")
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Clear existing index
            cursor.execute('DELETE FROM metadata_index')
            
            # Get all extracted info
            cursor.execute('''
                SELECT id, created_at, topic, category, tags 
                FROM extracted_info
            ''')
            
            extracted_items = cursor.fetchall()
            
            if not extracted_items:
                print("❌ No extracted information to index.")
                conn.close()
                return
            
            # Show progress
            total = len(extracted_items)
            for i, (item_id, created_at, topic, category, tags) in enumerate(extracted_items, 1):
                self.show_extraction_progress(i, total, "Indexing")
                
                # Parse date components
                try:
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    date_key = dt.strftime('%Y-%m-%d')
                    weekday = dt.strftime('%A').lower()
                    month = dt.strftime('%B').lower()
                    year = dt.strftime('%Y')
                except:
                    date_key = created_at[:10] if created_at else 'unknown'
                    weekday = 'unknown'
                    month = 'unknown'
                    year = 'unknown'
                
                # Insert metadata
                cursor.execute('''
                    INSERT INTO metadata_index 
                    (extracted_info_id, date_key, weekday, month, year, topic_key, category_key, tags_key)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (item_id, date_key, weekday, month, year, 
                      topic.lower() if topic else '', 
                      category.lower() if category else '',
                      tags.lower() if tags else ''))
            
            conn.commit()
            conn.close()
            print(f"\n✅ Metadata index rebuilt successfully! Indexed {total} items.")
            
        except Exception as e:
            print(f"❌ Error rebuilding metadata index: {e}")
            if 'conn' in locals():
                conn.close()
    
    def test_search_system(self):
        """Test search system functionality"""
        print("\n🔍 Search System Test")
        print("=" * 50)
        
        # Test database connection
        print("1. Testing database connection...")
        if self.validate_database_connection():
            print("   ✅ Database connection successful")
        else:
            print("   ❌ Database connection failed")
            return
        
        # Test search prerequisites
        print("2. Testing search prerequisites...")
        if self.validate_search_prerequisites():
            print("   ✅ Search prerequisites met")
        else:
            print("   ❌ Search prerequisites not met")
            return
        
        # Test metadata index
        print("3. Testing metadata index...")
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM extracted_info')
            extracted_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM metadata_index')
            metadata_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM conversations')
            conversations_count = cursor.fetchone()[0]
            
            conn.close()
            
            print(f"   📊 Extracted info: {extracted_count} items")
            print(f"   📊 Metadata index: {metadata_count} entries")
            print(f"   📊 Conversations: {conversations_count} messages")
            
            if metadata_count == 0 and extracted_count > 0:
                print("   ⚠️  Metadata index is empty - search may be slow")
            elif metadata_count > 0:
                print("   ✅ Metadata index is populated")
                
        except Exception as e:
            print(f"   ❌ Error testing metadata: {e}")
            return
        
        print("\n✅ Search system test completed!")
        print("💡 Use /search to start searching your memory.")
    
    def manage_system_prompt(self):
        """Simple system prompt management - view and edit"""
        print("\n🤖 System Prompt Management")
        print("=" * 50)
        
        current_prompt = self.config.get('system_prompt', 'You are a helpful AI assistant.')
        print(f"📝 Current system prompt:")
        print("=" * 50)
        print(current_prompt)
        print("=" * 50)
        
        while True:
            print(f"\n📋 Actions:")
            print("  1. Edit system prompt")
            print("  2. Reset to default")
            print("  3. Back to main menu")
            
            try:
                choice = input("\nSelect action (1-3): ").strip()
                
                if choice == '1':
                    self.change_system_prompt()
                    break
                elif choice == '2':
                    self.config['system_prompt'] = "You are a helpful AI assistant."
                    self.save_config()
                    print("✅ System prompt reset to default!")
                    break
                elif choice == '3':
                    print("✅ Returning to main menu...")
                    break
                else:
                    print("❌ Please enter a number between 1-3")
                    
            except KeyboardInterrupt:
                print("\n❌ Operation cancelled.")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                break
    
    def cleanup_old_config(self):
        """Clean up old configuration by removing deprecated fields and resetting to defaults"""
        print("\n🧹 Cleaning up old configuration...")
        
        # Remove old fields
        old_fields = ['custom_instruction_sets', 'current_instruction_set']
        removed_fields = []
        
        for field in old_fields:
            if field in self.config:
                del self.config[field]
                removed_fields.append(field)
        
        # Reset system prompt to default if it was from old instruction sets
        if self.config.get('system_prompt') != "You are a helpful AI assistant.":
            old_prompt = self.config.get('system_prompt', '')
            self.config['system_prompt'] = "You are a helpful AI assistant."
            print(f"🔄 Reset system prompt from '{old_prompt[:50]}...' to default")
        
        # Save the cleaned config
        self.save_config(quiet=True)
        
        if removed_fields:
            print(f"✅ Removed old fields: {', '.join(removed_fields)}")
        print("✅ Configuration cleaned up and reset to defaults!")

def main():
    parser = argparse.ArgumentParser(description="God CLI - Ollama Chat Interface")
    parser.add_argument("--config", help="Path to config file")
    parser.add_argument("--url", help="Ollama server URL")
    parser.add_argument("--model", help="Default model to use")
    parser.add_argument("--test", action="store_true", help="Test connection and exit")
    
    args = parser.parse_args()
    
    cli = OllamaCLI(args.config)
    
    if args.url:
        cli.config["ollama_url"] = args.url
        cli.base_url = args.url
        
    if args.model:
        cli.config["default_model"] = args.model
    
    if args.test:
        if cli.test_connection():
            print("✅ Connection successful!")
            models = cli.list_models()
            if models:
                print(f"📚 Available models: {', '.join(models)}")
            else:
                print("❌ No models found")
        else:
            print("❌ Connection failed!")
            print(f"Make sure Ollama is running at: {cli.base_url}")
        return
    
    # Default behavior: go straight to chat
    if not cli.test_connection():
        print("❌ Cannot connect to Ollama!")
        print(f"Make sure Ollama is running at: {cli.base_url}")
        print("You can specify a different URL with --url")
        return
    
    cli.interactive_chat()

if __name__ == "__main__":
    main()
