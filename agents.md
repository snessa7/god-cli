# Agents.md - Development Guidelines & Project Management

This document serves as the central development guide for the God CLI tool project. It contains agent rules, development guidelines, to-do lists, and project management information.

## 🎉 **MAJOR MILESTONE ACHIEVED - Custom Instructions System Simplified!**

### ✅ **Custom Instructions System Simplification COMPLETED**
**Date:** August 29, 2024  
**Commit:** `57bc0a0` - "Simplify custom instructions system to single configurable system prompt"

**What Was Accomplished:**
- ✅ **Removed complex custom instruction sets** - No more multiple instruction sets (developer, creative, analytical, teacher, etc.)
- ✅ **Simplified to single system prompt** - One configurable `system_prompt` field
- ✅ **Added `/prompt` command** - Simple system prompt management interface
- ✅ **Added `/cleanup` command** - Automatic removal of old configuration fields
- ✅ **Improved user experience** - Much simpler and more intuitive interface
- ✅ **Maintained functionality** - All note-taking and AI behavior customization still available
- ✅ **Reduced complexity** - Eliminated confusion and potential for errors

**Result:** The system is now much cleaner, easier to use, and more maintainable while preserving all the functionality users need.

---

## 🎯 **Current Progress Summary**

### ✅ **Successfully Fixed Functions (5/6)**
1. **Model Switcher** - ✅ **COMPLETED** - Working perfectly with auto-fix capabilities
2. **Copy Functionality** - ✅ **COMPLETED** - Platform validation and error handling
3. **Memory Extraction** - ✅ **COMPLETED** - Database validation and progress indicators
4. **Search System** - ✅ **COMPLETED** - Prerequisites validation and metadata indexing
5. **Custom Instruction Sets** - ✅ **COMPLETED** - Full management system with switching functionality

### 🔄 **Next Function to Fix**
6. **Knowledge Base System** (`/knowledge`) - Apply the same validation + user feedback pattern

### 📋 **Remaining Functions**
6. **Slash Command Handling** - Improve overall command system robustness

### 🚀 **Established Fix Pattern Success Rate: 100%**
Every function we've applied the fix pattern to has been successfully improved with:
- ✅ Prerequisites validation
- ✅ Auto-fix capabilities  
- ✅ Progress indicators
- ✅ Comprehensive error handling
- ✅ User-friendly feedback
- ✅ Diagnostic test commands

---

## Current Features Status

### ✅ Implemented
- [x] Basic CLI structure with argparse
- [x] Ollama integration and model switching
- [x] Interactive chat interface
- [x] Configuration management (JSON-based)
- [x] Copy to clipboard functionality
- [x] Slash command system (`/copy`, `/clear`, `/help`, etc.)
- [x] Auto-completion for slash commands
- [x] System prompt management
- [x] SQLite-based conversation memory
- [x] Session tracking and management
- [x] Information extraction system
- [x] Advanced search capabilities
- [x] System knowledge base
- [x] File picker integration
- [x] Model selector with Ollama CLI integration
- [x] MCP configuration for external tools
- [x] **Search System with validation and error handling**
- [x] **Custom Instruction Sets Manager** - Full management system implemented

### 🔄 In Progress
- [x] Model switcher functionality (completed - working pattern established)
- [x] Function fixes and improvements (copy, memory, search, custom instructions completed)
- [ ] Performance optimization for large conversation histories
- [ ] Enhanced error handling and user feedback

### 📋 Planned Features
- [ ] Export/import conversation data
- [ ] Conversation templates and presets
- [ ] Advanced model configuration options
- [ ] Plugin system for extensibility
- [ ] Web interface option
- [ ] Multi-user support
- [ ] Conversation analytics and insights
- [ ] Integration with external note-taking apps
- [ ] Voice input/output capabilities
- [ ] Cross-platform clipboard handling improvements

## Development To-Do List

### High Priority
1. **Function Fixes & Improvements** ✅ **IN PROGRESS**
   - [x] Fix model switcher (completed - working pattern established)
   - [x] Fix copy functionality (same pattern: validation + user feedback)
   - [x] Fix memory extraction system (same pattern: validation + user feedback)
   - [x] Fix search functionality (same pattern: validation + user feedback)
   - [x] Fix custom instruction sets (same pattern: validation + user feedback)
   - [ ] Fix knowledge base system (same pattern: validation + user feedback)
   - [ ] Fix slash command handling (same pattern: validation + user feedback)

2. **Performance Optimization**
   - [ ] Optimize database queries for large datasets
   - [ ] Implement pagination for long conversation lists
   - [ ] Add caching for frequently accessed data

3. **Error Handling Enhancement**
   - [x] Fix configuration save spam (completed - added quiet parameter)
   - [x] Fix model validation issues (completed - auto-fix on startup)
   - [ ] Improve error messages for common failure scenarios
   - [ ] Add retry mechanisms for network operations
   - [ ] Implement graceful degradation for missing features

4. **Testing Infrastructure**
   - [ ] Set up unit testing framework
   - [ ] Add integration tests for Ollama API
   - [ ] Create test data fixtures

### Medium Priority
1. **User Experience Improvements**
   - [ ] Add progress indicators for long operations
   - [ ] Implement undo/redo functionality
   - [ ] Add keyboard shortcuts for common actions

2. **Data Management**
   - [ ] Implement data export in multiple formats (JSON, CSV, Markdown)
   - [ ] Add data import capabilities
   - [ ] Create backup and restore functionality

3. **Configuration Enhancements**
   - [ ] Add configuration validation
   - [ ] Implement configuration profiles
   - [ ] Add configuration migration support

### Low Priority
1. **Advanced Features**
   - [ ] Plugin architecture for custom commands
   - [ ] Integration with external services
   - [ ] Advanced analytics and reporting

2. **Documentation**
   - [ ] Create user manual
   - [ ] Add developer documentation
   - [ ] Create video tutorials

## Technical Debt & Refactoring

### ✅ **Established Fix Pattern** (Model Switcher Success)
The model switcher fix established a proven pattern for fixing other functions:

1. **Root Cause Analysis**
   - Identify the specific failure point (e.g., model parsing, config spam)
   - Trace through the code to find where the issue occurs

2. **Validation & Auto-Fix**
   - Add validation methods that check function prerequisites
   - Implement auto-fix logic for common failure scenarios
   - Provide clear user feedback on what was fixed

3. **User Experience Improvements**
   - Make functions interactive where appropriate
   - Add proper error handling and recovery
   - Eliminate unnecessary output (e.g., quiet config saves)

4. **Configuration Management**
   - Ensure changes persist properly
   - Validate configuration against available resources
   - Provide fallback options when resources are unavailable

**Example Implementation:**
```python
def validate_and_fix_function_config(self):
    """Validate function configuration and fix if needed"""
    # Check prerequisites
    # Auto-fix common issues
    # Provide user feedback
    # Save configuration if needed
```

### Code Structure
- [ ] Refactor large methods into smaller, focused functions
- [ ] Implement proper dependency injection
- [ ] Add type hints throughout the codebase
- [ ] Create proper abstraction layers

### **Function-Specific Fixes Needed**

#### **Copy Functionality** (`/copy`, `/copyall`) ✅ **COMPLETED**
- [x] Validate clipboard access before attempting copy
- [x] Add fallback for unsupported platforms
- [x] Improve error messages for copy failures
- [x] Add copy confirmation feedback

#### **Memory Extraction System** (`/extract`) ✅ **COMPLETED**
- [x] Validate database connection before extraction
- [x] Add progress indicators for large extractions
- [x] Improve metadata collection validation
- [x] Add extraction preview before saving

#### **Search Functionality** (`/search`) ✅ **COMPLETED**
- [x] Validate search parameters before execution
- [x] Add search result pagination
- [x] Improve search performance for large datasets
- [x] Add search history and saved searches
- [x] **Added validation methods for search prerequisites**
- [x] **Added metadata index rebuilding for performance**
- [x] **Added progress indicators for indexing operations**
- [x] **Added comprehensive error handling and user feedback**
- [x] **Added /testsearch command for diagnostics**

#### **Custom Instruction Sets** (`/instructions`) ✅ **COMPLETED**
- [x] Basic framework and command structure
- [x] Display available instruction set types
- [x] Full instruction set management (create, edit, delete)
- [x] Instruction set switching functionality
- [x] Custom instruction set persistence
- [x] Instruction set validation and error handling
- [x] Progress indicators for large instruction sets

#### **Knowledge Base System** (`/knowledge`)
- [ ] Validate file paths and permissions
- [ ] Add file size and format validation
- [ ] Improve error handling for file operations
- [ ] Add knowledge base integrity checks

#### **Slash Command System** (All `/` commands)
- [ ] Add command validation and prerequisites
- [ ] Improve error recovery for failed commands
- [ ] Add command usage statistics
- [ ] Implement command aliases and shortcuts

### Database Schema
- [ ] Optimize table indexes for common queries
- [ ] Consider database normalization improvements
- [ ] Add database versioning and migration system

### Error Handling
- [ ] Implement centralized error handling
- [ ] Add error reporting and logging
- [ ] Create user-friendly error recovery suggestions

## Quality Assurance

### Testing Strategy
- **Unit Tests**: Cover all individual functions and methods
- **Integration Tests**: Test Ollama API interactions
- **User Acceptance Tests**: Verify CLI behavior matches requirements
- **Performance Tests**: Ensure acceptable response times

### Code Review Checklist
- [ ] Code follows style guidelines
- [ ] Error handling is comprehensive
- [ ] Documentation is complete
- [ ] Tests are included
- [ ] Performance considerations addressed

## Release Planning

### Version 1.0 (Current)
- Core CLI functionality
- Basic Ollama integration
- Memory system
- Essential slash commands

### Version 1.1 (Next)
- Performance improvements
- Enhanced error handling
- Additional export options
- User experience refinements

### Version 1.2 (Future)
- Plugin system
- Advanced analytics
- Web interface
- Multi-user support

## Development Workflow

### Feature Development Process
1. **Planning**: Define requirements and acceptance criteria
2. **Implementation**: Code the feature following guidelines
3. **Testing**: Verify functionality and performance
4. **Code Review**: Peer review for quality assurance
5. **Integration**: Merge into main branch
6. **Documentation**: Update relevant documentation

### Bug Fix Process
1. **Reproduction**: Verify the bug can be reproduced
2. **Investigation**: Identify root cause
3. **Fix**: Implement solution following guidelines
4. **Testing**: Verify fix resolves the issue
5. **Documentation**: Update bug tracking and documentation

## Contributing Guidelines

### For Developers
- Follow the established code style
- Write tests for new features
- Update documentation as needed
- Use meaningful commit messages
- Create feature branches for development

### For Users
- Report bugs with clear reproduction steps
- Suggest features with use case descriptions
- Provide feedback on user experience
- Share configuration examples

## Monitoring & Maintenance

### Performance Metrics
- Response time for commands
- Memory usage patterns
- Database query performance
- User interaction patterns

### Health Checks
- Ollama service availability
- Database connection status
- Configuration file validity
- Required dependencies status

---

*This document is actively maintained and updated as the project evolves. Last updated: [Current Date]*
