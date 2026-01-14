# RaapTech Brand Voice Integration - Complete

## ✅ What I Built

### 1. RaapTech Report Writer Prompt (`.kiro/prompts/raaptech-report-writer.md`)

**Complete writing system** that combines:
- **Voice Blend:** Hormozi (stakes) + Saraev (clarity) + MFM (energy)
- **6-Layer Persuasion:** Hook → Problem → Insight → Mechanism → Proof → Outcome
- **Construction Language:** Translates startup-speak to fabricator language
- **Quality Checklist:** Ensures every report sounds human, not AI

**Key Features:**
- Short sentences. Simple words. No BS.
- Specific numbers: "$26K/month" not "significant revenue"
- Construction-specific: "Shop" not "office", "Operators" not "founders"
- Mechanism-focused: Always explain WHY it matters to their business
- Outcome-led: Show who they become, not just what they get

### 2. Python Voice Integration (`seo-health-report/scripts/raaptech_voice.py`)

**Automated voice application** with functions:

```python
# Generate executive summary with RaapTech voice
summary = generate_executive_summary_raaptech(
    score=29,
    grade="F",
    critical_issues=[...],
    market_position=9,
    competitors_count=9,
    revenue_impact=(26250, 48750),
    company_name="Sheet Metal Werks"
)

# Format recommendations with persuasion framework
rec = format_recommendation_raaptech(
    priority="HIGH",
    action="Reduce page load time from 8.2s to under 3s",
    impact="40% fewer customers bouncing = 12 more qualified leads/month",
    effort="4-6 hours",
    roi="$18,000 annual revenue increase",
    mechanism="When your site takes 8 seconds to load..."
)

# Translate technical terms to business language
finding = translate_technical_finding(
    technical_term="schema markup",
    business_impact="AI systems can't understand your services",
    specific_data="Missing on 100% of pages"
)
```

---

## 🎯 Voice Transformation Examples

### Before (Generic SEO Report)
```
Your website has several SEO issues that need attention. We found 
problems with technical SEO, content quality, and AI visibility. 
These issues may be affecting your search rankings and online presence.
```

### After (RaapTech Voice)
```
Your competitors are showing up in AI search results. You're not.

When a contractor searches "sheet metal fabricator Chicago" in ChatGPT 
or Perplexity, 7 out of 8 competitors appear. You don't. That's $26,250 
in lost monthly revenue from customers who never find you.

Here's what's happening: AI systems can't parse your website. No schema 
markup. No structured data. No way for AI to understand what you do, 
where you are, or why you're qualified. Result: You're invisible in 35% 
of searches.

Your overall SEO health score: 29/100 (Grade: F)
Market position: #9 out of 9 competitors
Critical issues: 2
Estimated monthly impact: $26,250-$48,750

In 90 days, you could be the shop that shows up in AI search. Bids come 
to you. Your phone rings. You're not chasing work—work finds you.

Here's what we found—and how to fix it.
```

---

## 📋 Key Voice Elements Applied

### 1. Hormozi (Stakes + Outcomes)
- ✅ Specific moments: "When a contractor searches..."
- ✅ Concrete numbers: "$26,250 in lost monthly revenue"
- ✅ Show who it affects: "Your competitors appear. You don't."
- ✅ Outcome-focused: "In 90 days, you could be the shop that..."

### 2. Saraev (Strategic Clarity)
- ✅ Pattern observation: "Here's what's happening..."
- ✅ Mechanism explanation: "AI systems can't parse your website"
- ✅ ROI-focused: "$26,250-$48,750 monthly impact"
- ✅ Strategic insight: "You're invisible in 35% of searches"

### 3. MFM (Discovery Energy)
- ✅ Contrarian insight: "Most think SEO is about Google rankings. But..."
- ✅ Pattern recognition: "7 out of 8 competitors appear"
- ✅ Human angle: "That's 4 bids you never get to submit"

---

## 🔧 Construction Language Translation

Your branding guide specifies **MEP contractors, sheet metal fabricators, HVAC companies**—not generic "founders."

**Automatic translations applied:**

| ❌ Startup-Speak | ✅ Construction Language |
|-----------------|-------------------------|
| "Founders" | "Operators" or "Owners" |
| "Scale" | "Grow" or "Handle more work" |
| "Leverage" | "Use" or "Take advantage of" |
| "Automate" | "Systematize" or "Set up once" |
| "Office" | "Shop" or "Facility" |
| "Users" | "Customers" or "Contractors" |
| "Slack chaos" | "Shop floor questions" |

---

## 📊 6-Layer Persuasion Framework

Every report section follows this structure:

### 1. HOOK (Attention)
Pattern interrupt + Specific number + Their situation
```
"Your competitors are showing up in AI search results. You're not."
```

### 2. PROBLEM (Understanding)
Show their specific moment (not generic struggle)
```
"When a contractor searches... 7 out of 8 competitors appear. You don't."
```

### 3. INSIGHT (Desire)
Name the counterintuitive truth
```
"Most think SEO is about Google rankings. But 35% of searches now 
happen in AI systems."
```

### 4. MECHANISM (Belief)
Explain WHY/HOW it works
```
"AI systems can't parse your website. No schema markup. No structured 
data. Result: You're invisible in 35% of searches."
```

### 5. PROOF (Evidence)
Your actual data, their actual numbers
```
"Your overall SEO health score: 29/100 (Grade: F)
Market position: #9 out of 9 competitors
Estimated monthly impact: $26,250-$48,750"
```

### 6. OUTCOME (Action)
Who they become + What changes
```
"In 90 days, you could be the shop that shows up in AI search. Bids 
come to you. Your phone rings. You're not chasing work—work finds you."
```

---

## 🚀 How to Use

### Option 1: Automatic Integration (Recommended)

Integrate into your report generation:

```python
# In generate_premium_report.py or build_report.py
from seo_health_report.scripts.raaptech_voice import (
    generate_executive_summary_raaptech,
    format_recommendation_raaptech,
    translate_technical_finding
)

# Generate executive summary with RaapTech voice
executive_summary = generate_executive_summary_raaptech(
    score=audit_data['overall_score'],
    grade=audit_data['grade'],
    critical_issues=audit_data['critical_issues'],
    market_position=market_data.get('position'),
    competitors_count=market_data.get('total_competitors'),
    revenue_impact=market_data.get('revenue_impact'),
    company_name=company_name
)

# Format each recommendation
for rec in recommendations:
    formatted_rec = format_recommendation_raaptech(
        priority=rec['priority'],
        action=rec['action'],
        impact=rec['impact'],
        effort=rec['effort'],
        roi=rec.get('roi'),
        mechanism=rec.get('mechanism')
    )
```

### Option 2: Manual Application

Use the prompt when writing report content:

1. Load `.kiro/prompts/raaptech-report-writer.md`
2. Apply voice blend (Hormozi + Saraev + MFM)
3. Follow 6-layer structure
4. Use construction language
5. Run quality checklist

---

## ✅ Quality Checklist

Before finalizing any report:

- [ ] Would a shop foreman understand this? (No unexplained jargon)
- [ ] Does it reference their actual day? (Shop floor, bid desk, customer calls)
- [ ] Is the proof construction-specific? (Their industry, their competitors)
- [ ] Short sentences, varied rhythm
- [ ] One idea per sentence
- [ ] Specific numbers used (not "many" or "significant")
- [ ] Mechanism explained (why does this hurt their business?)
- [ ] Outcome stated clearly (who they become + what happens)
- [ ] No hedging language ("might," "could," "seems")
- [ ] Construction language (not startup-speak)

---

## 📁 Files Created

1. **`.kiro/prompts/raaptech-report-writer.md`**
   - Complete writing system
   - Voice blend guidelines
   - 6-layer persuasion framework
   - Construction language translations
   - Quality checklist

2. **`seo-health-report/scripts/raaptech_voice.py`**
   - Automated voice application
   - Executive summary generator
   - Recommendation formatter
   - Technical term translator

---

## 🎯 Next Steps

### Immediate (This Week)

1. **Test the voice module:**
   ```bash
   cd seo-health-report/scripts
   python3 raaptech_voice.py
   ```

2. **Integrate into report generation:**
   - Add import to `generate_premium_report.py`
   - Replace generic executive summary with RaapTech version
   - Format recommendations with persuasion framework

3. **Review generated reports:**
   - Run premium audit with new voice
   - Check if it sounds human, not AI
   - Verify construction language is used

### Short Term (Next 2 Weeks)

1. **Apply to all report sections:**
   - Technical findings
   - Content analysis
   - AI visibility
   - Competitive analysis

2. **Add RaapTech branding:**
   - Logo placement (already done)
   - Black/white/gray color scheme (already done)
   - Typography standards

3. **Create templates:**
   - Email templates with RaapTech voice
   - One-pager templates
   - Proposal templates

---

## 💡 Key Insights from Your Branding

### From VOICE_TONE.md:
- ✅ Short sentences. Simple words. No BS.
- ✅ One idea per sentence
- ✅ Specific numbers over generics
- ✅ Concrete moments over generic struggles
- ✅ Lead with outcome (vacation, not plane)
- ✅ Show who it affects (relationships, stakes)

### From PERSUASION_FRAMEWORK.md:
- ✅ 6-layer structure: Hook → Problem → Insight → Mechanism → Proof → Outcome
- ✅ Every layer builds on the one below
- ✅ Skip a layer → entire structure fails
- ✅ Make them nod first (competence/curiosity/connection)

### From BRAND_GUIDE.md:
- ✅ Black/white/gray color scheme (already applied)
- ✅ Chicago-based identity (logo shows skyline)
- ✅ Bold, clean typography
- ✅ Strong whitespace

### From AVATAR_CONTEXT.md:
- ✅ Target: MEP contractors, sheet metal fabricators, HVAC companies
- ✅ Not generic "founders" - use "operators" or "owners"
- ✅ Construction-specific language
- ✅ Real pain moments: database chaos, pricing nightmares, knowledge leaving

---

## 🎓 Summary

**You now have:**
- ✅ Complete RaapTech voice system for SEO reports
- ✅ Automated voice application (Python module)
- ✅ 6-layer persuasion framework
- ✅ Construction language translations
- ✅ Quality checklist for every report

**The result:**
Reports that sound **human, strategic, and urgent**—not like AI wrote them.

**Time to implement:** Already done! Just integrate into report generation.

---

## 📞 Questions?

The voice system is designed to be:
- **Automatic:** Python functions apply voice transformations
- **Flexible:** Can be used manually with prompt
- **Consistent:** Same voice across all reports
- **Authentic:** Sounds like RaapTech, not generic SEO agency

Every word answers: **"So what? Why does this matter to my business?"**

If you can't answer that, cut it.
