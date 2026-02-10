# Comprehensive Guide to Creating Claude Skills

Based on analysis of Anthropic's skills repository (https://github.com/anthropics/skills)

---

## What Are Skills?

Skills are **modular, self-contained packages** that extend Claude's capabilities by providing specialized knowledge, workflows, and tools. Think of them as "onboarding guides" for specific domains or tasks.

### What Skills Provide:
1. **Specialized workflows** - Multi-step procedures for specific domains
2. **Tool integrations** - Instructions for working with specific file formats or APIs
3. **Domain expertise** - Company-specific knowledge, schemas, business logic
4. **Bundled resources** - Scripts, references, and assets for complex and repetitive tasks

---

## Core Principles

### 1. Concise is Key 🎯
**Default assumption: Claude is already very smart.**

- Only add context Claude doesn't already have
- Challenge each piece of information: "Does Claude really need this?"
- Prefer concise examples over verbose explanations
- The context window is a public good - don't waste it!

### 2. Set Appropriate Degrees of Freedom

Match specificity to task fragility:

| Freedom Level | When to Use | Format |
|--------------|-------------|---------|
| **High** | Multiple valid approaches, context-dependent decisions | Text-based instructions |
| **Medium** | Preferred pattern exists, some variation acceptable | Pseudocode or scripts with parameters |
| **Low** | Fragile operations, consistency critical, specific sequence required | Specific scripts, few parameters |

Think of Claude as exploring a path:
- Narrow bridge with cliffs → Need guardrails (low freedom)
- Open field → Many valid routes (high freedom)

### 3. Progressive Disclosure Design 📚

Skills use a three-level loading system:

1. **Metadata** (name + description) - Always in context (~100 words)
2. **SKILL.md body** - When skill triggers (<5k words, ideally <500 lines)
3. **Bundled resources** - As needed by Claude (unlimited, scripts can execute without loading)

---

## Anatomy of a Skill

### Required Structure:

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter metadata
│   │   ├── name: (required)
│   │   ├── description: (required)
│   │   └── compatibility: (optional)
│   └── Markdown instructions
└── Bundled Resources (optional)
    ├── scripts/          - Executable code (Python/Bash)
    ├── references/       - Documentation loaded as needed
    └── assets/           - Files used in output (templates, icons, fonts)
```

### SKILL.md Components:

#### Frontmatter (YAML):
```yaml
---
name: my-skill-name
description: Complete description of what this does and WHEN TO USE IT. Include all triggers here!
---
```

**Critical:** The `description` field is THE PRIMARY TRIGGERING MECHANISM. Include:
- What the skill does
- All specific triggers/contexts
- When to use it

Example:
```yaml
description: "Comprehensive document creation, editing, and analysis with support for tracked changes, comments, formatting preservation, and text extraction. Use when Claude needs to work with professional documents (.docx files) for: (1) Creating new documents, (2) Modifying or editing content, (3) Working with tracked changes, (4) Adding comments, or any other document tasks"
```

#### Body (Markdown):
Instructions and guidance for using the skill and its bundled resources.

---

## Bundled Resources

### 1. Scripts (`scripts/`)
**When to include:** When same code is repeatedly rewritten or deterministic reliability is needed

**Examples:**
- `scripts/rotate_pdf.py` for PDF rotation
- `scripts/recalc.py` for Excel formula recalculation
- `scripts/validate.py` for validation tasks

**Benefits:**
- Token efficient
- Deterministic
- May execute without loading into context

**Note:** Must be tested by actually running them!

### 2. References (`references/`)
**When to include:** For documentation Claude should reference while working

**Examples:**
- `references/finance.md` - Financial schemas
- `references/api_docs.md` - API specifications
- `references/policies.md` - Company policies

**Best practices:**
- Keep SKILL.md lean by moving detailed info to references
- If files >10k words, include grep search patterns in SKILL.md
- Avoid duplication between SKILL.md and references
- For files >100 lines, include table of contents at top

### 3. Assets (`assets/`)
**When to include:** Files used in final output (not loaded into context)

**Examples:**
- `assets/logo.png` - Brand assets
- `assets/slides.pptx` - PowerPoint templates
- `assets/frontend-template/` - HTML/React boilerplate
- `assets/font.ttf` - Typography files

**Benefits:**
- Separates output resources from documentation
- Claude can use files without loading them

---

## Progressive Disclosure Patterns

### Pattern 1: High-level guide with references

```markdown
# PDF Processing

## Quick start
Extract text with pdfplumber:
[code example]

## Advanced features
- **Form filling**: See [FORMS.md](FORMS.md) for complete guide
- **API reference**: See [REFERENCE.md](REFERENCE.md) for all methods
- **Examples**: See [EXAMPLES.md](EXAMPLES.md) for common patterns
```

### Pattern 2: Domain-specific organization

For skills with multiple domains, organize by domain:

```
bigquery-skill/
├── SKILL.md (overview and navigation)
└── reference/
    ├── finance.md (revenue, billing metrics)
    ├── sales.md (opportunities, pipeline)
    ├── product.md (API usage, features)
    └── marketing.md (campaigns, attribution)
```

### Pattern 3: Framework/variant organization

```
cloud-deploy/
├── SKILL.md (workflow + provider selection)
└── references/
    ├── aws.md (AWS deployment patterns)
    ├── gcp.md (GCP deployment patterns)
    └── azure.md (Azure deployment patterns)
```

**Important guidelines:**
- Avoid deeply nested references (keep one level deep from SKILL.md)
- Structure longer files with table of contents

---

## Skill Creation Process (6 Steps)

### Step 1: Understand with Concrete Examples

Ask clarifying questions:
- "What functionality should this skill support?"
- "Can you give examples of how this skill would be used?"
- "What would a user say that should trigger this skill?"

Conclude when there's a clear sense of required functionality.

### Step 2: Plan Reusable Contents

For each example, identify:
1. How to execute from scratch
2. What scripts, references, and assets would be helpful when repeating this

**Example analysis:**

| Task | Analysis | Solution |
|------|----------|----------|
| "Help me rotate this PDF" | Rotating requires rewriting same code each time | Create `scripts/rotate_pdf.py` |
| "Build me a todo app" | Frontend needs same boilerplate each time | Create `assets/hello-world/` template |
| "How many users logged in today?" | Querying needs rediscovering table schemas | Create `references/schema.md` |

### Step 3: Initialize the Skill

Run the initialization script:

```bash
scripts/init_skill.py <skill-name> --path <output-directory>
```

This generates:
- Skill directory at specified path
- SKILL.md template with frontmatter and TODOs
- Example directories: `scripts/`, `references/`, `assets/`
- Example files in each directory

### Step 4: Edit the Skill

#### Learn Proven Design Patterns:
- **Multi-step processes**: See `references/workflows.md`
- **Specific output formats**: See `references/output-patterns.md`

#### Start with Reusable Contents:
1. Implement `scripts/`, `references/`, `assets/` files
2. Test scripts by actually running them
3. Delete any example files not needed

#### Update SKILL.md:
- Write YAML frontmatter (name + description)
- Write instructions using imperative/infinitive form
- Reference bundled resources clearly
- Keep under 500 lines if possible

### Step 5: Package the Skill

```bash
scripts/package_skill.py <path/to/skill-folder>
```

Optional output directory:
```bash
scripts/package_skill.py <path/to/skill-folder> ./dist
```

The script will:
1. **Validate** automatically:
   - YAML frontmatter format
   - Naming conventions
   - Description completeness
   - File organization
2. **Package** if validation passes
   - Creates `.skill` file (zip with .skill extension)
   - Includes all files with proper structure

### Step 6: Iterate

1. Use skill on real tasks
2. Notice struggles or inefficiencies
3. Identify needed updates
4. Implement changes and test again

---

## Workflow Patterns

### Sequential Workflows

```markdown
Filling a PDF form involves these steps:

1. Analyze the form (run analyze_form.py)
2. Create field mapping (edit fields.json)
3. Validate mapping (run validate_fields.py)
4. Fill the form (run fill_form.py)
5. Verify output (run verify_output.py)
```

### Conditional Workflows

```markdown
1. Determine the modification type:
   **Creating new content?** → Follow "Creation workflow" below
   **Editing existing content?** → Follow "Editing workflow" below

2. Creation workflow: [steps]
3. Editing workflow: [steps]
```

---

## Output Patterns

### Template Pattern (Strict)

```markdown
## Report structure

ALWAYS use this exact template structure:

# [Analysis Title]

## Executive summary
[One-paragraph overview of key findings]

## Key findings
- Finding 1 with supporting data
- Finding 2 with supporting data

## Recommendations
1. Specific actionable recommendation
2. Specific actionable recommendation
```

### Template Pattern (Flexible)

```markdown
## Report structure

Here is a sensible default format, but use your best judgment:

# [Analysis Title]

## Executive summary
[Overview]

## Key findings
[Adapt sections based on what you discover]

Adjust sections as needed for the specific analysis type.
```

### Examples Pattern

```markdown
## Commit message format

Generate commit messages following these examples:

**Example 1:**
Input: Added user authentication with JWT tokens
Output:
```
feat(auth): implement JWT-based authentication

Add login endpoint and token validation middleware
```

**Example 2:**
Input: Fixed bug where dates displayed incorrectly
Output:
```
fix(reports): correct date formatting in timezone conversion

Use UTC timestamps consistently
```

Follow this style: type(scope): brief description, then detailed explanation.
```

---

## What NOT to Include

Do NOT create these auxiliary files:
- ❌ README.md
- ❌ INSTALLATION_GUIDE.md
- ❌ QUICK_REFERENCE.md
- ❌ CHANGELOG.md

The skill should only contain information needed for an AI agent to do the job.

---

## Key Takeaways

1. **Be concise** - Challenge every token
2. **Progressive disclosure** - Load information only when needed
3. **Scripts for repetitive tasks** - Save tokens, ensure reliability
4. **References for domain knowledge** - Keep SKILL.md lean
5. **Assets for output resources** - Don't load into context
6. **Clear triggering** - Put ALL "when to use" info in description
7. **Test and iterate** - Use it, improve it, repeat

---

## Example Skills to Study

From the Anthropic repository:

| Skill | Type | Key Features |
|-------|------|-------------|
| `doc-coauthoring` | Workflow | Multi-stage guided process |
| `xlsx` | Document | Scripts (recalc.py), validation tools |
| `pdf` | Document | Form filling, extraction, manipulation |
| `skill-creator` | Meta | Self-documenting skill creation guide |
| `brand-guidelines` | Assets | Company branding resources |
| `mcp-builder` | Technical | API integration guidance |

---

## Resources

- **Repository**: https://github.com/anthropics/skills
- **Documentation**:
  - What are skills: https://support.claude.com/en/articles/12512176
  - Using skills: https://support.claude.com/en/articles/12512180
  - Creating skills: https://support.claude.com/en/articles/12512198
- **Blog**: https://anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills
- **Spec**: Check `./spec` directory in repository

---

## Your Trading Performance Analyzer Skill

As a reference, your current `trading-performance-analyzer` skill follows these principles:

✅ Clear description with triggers
✅ Step-by-step workflow
✅ Uses scripts (`analyze_performance.py`)
✅ Focuses on specific domain (Kite trading analysis)
✅ Provides actionable insights

**Potential improvements:**
- Add references for financial formulas/metrics
- Include example analysis outputs
- Add visualization scripts for performance charts
- Create assets folder with report templates

---

*Document created: February 10, 2026*
*Based on Anthropic Skills Repository analysis*
