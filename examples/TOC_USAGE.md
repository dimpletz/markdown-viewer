# Table of Contents (TOC) Feature

## How to Use TOC

Simply add `[TOC]` anywhere in your markdown document where you want the table of contents to appear:

```markdown
# My Document Title

[TOC]

## Section 1
Content...

## Section 2
More content...
```

## Features

### Automatic Generation
- TOC is automatically generated from all headings (H1-H6)
- Updates automatically when headings change
- No manual maintenance required

### Clickable Navigation
- Every entry in the TOC is a clickable link
- Click to jump directly to that section
- Smooth scrolling behavior

### Permalink Support
- Every heading gets a permalink icon (¶) on hover
- Copy the link to share specific sections
- Bookmarkable URLs

### Multi-level Support
- Supports all heading levels (H1 through H6)
- Proper indentation for nested sections
- Hierarchical structure preserved

## Styling

The TOC comes with beautiful GitHub-inspired styling:

- **Background**: Light gray box with subtle borders
- **Typography**: Clear, readable font with proper spacing
- **Hover Effects**: Links change color on hover
- **Responsive**: Works on all screen sizes

## Configuration

The TOC is configured with these default settings:

- **Permalink**: Enabled (shows ¶ symbol on hover)
- **Depth**: Includes all levels (H1-H6)
- **Title**: "Table of Contents"

## Examples

### Basic TOC

```markdown
# User Guide

[TOC]

## Getting Started
## Installation
## Configuration
```

### Advanced TOC with Deep Nesting

```markdown
# API Documentation

[TOC]

## Authentication
### OAuth 2.0
#### Setup
#### Configuration
### API Keys

## Endpoints
### Users
#### GET /users
#### POST /users
### Projects
#### GET /projects
```

## Tips

1. **Place TOC Early**: Put `[TOC]` near the top of your document, after the main title
2. **Unique Headings**: Use unique heading text to avoid anchor conflicts
3. **Logical Structure**: Use proper heading hierarchy (H1 → H2 → H3)
4. **Descriptive Text**: Make heading text descriptive for better TOC navigation

## Try It Out

Test the TOC feature with the provided demo files:

```bash
# Comprehensive demo with TOC
poetry run mdview COMPREHENSIVE_DEMO.md

# Full documentation example
poetry run mdview TOC_DEMO.md
```

---

**Tip**: The TOC updates automatically - you never need to manually edit it! 🎉
