# services/ai_report_generator.py - ENHANCED WITH MORE TABLES
"""
Enhanced AI Report Generator with:
- More comprehensive table generation
- Better data presentation
- Improved prompts for table creation
"""

import streamlit as st
import google.generativeai as genai
from typing import Dict, Any, List
import json


class AIReportGenerator:
    """Generate AI-powered financial analysis reports using Gemini"""
    
    def __init__(self, api_key: str):
        """Initialize the AI report generator"""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("models/gemini-2.0-flash-exp")
    
    def generate_report(self, data_source, level: str = 'short') -> str:
        """Generate AI report from either collector or global_analysis_results"""
        
        # Check if data_source is a dict (global_analysis_results) or object (collector)
        if isinstance(data_source, dict):
            summary_data = self._convert_global_results_to_summary(data_source, level)
        else:
            summary_data = data_source.get_summary_for_ai(level)
        
        prompt = self._create_prompt(summary_data, level)
        
        try:
            data_hash = self._create_data_hash(summary_data)
            response = self._generate_with_cache(prompt, level, data_hash)
            return response
        except Exception as e:
            return self._format_error_message(str(e))
    
    def _convert_global_results_to_summary(self, results: Dict, level: str) -> Dict[str, Any]:
        """Convert global_analysis_results to summary format expected by prompts"""
        
        metadata = results.get('metadata', {})
        quick_summary = results.get('quick_summary', {})
        group_summaries = quick_summary.get('group_summaries', {})
        
        # Build summary in expected format
        summary = {
            'files_processed': len(metadata.get('files_processed', [])),
            'sheets_processed': len(metadata.get('files_processed', [])),
            'total_groups': len(group_summaries),
            'group_names': list(group_summaries.keys()),
            'total_records': metadata.get('total_records', 0),
            'comparisons_made': 0,
            'duplicates_found': metadata.get('total_duplicates', 0),
            'missing_items_count': 0,
            'unrecognized_files': len(results.get('validation', {}).get('issues', [])),
            'level': level
        }
        
        # Build group details with enhanced statistics
        group_details = {}
        all_categories = []
        
        for group_name, group_analysis in group_summaries.items():
            category_analyses = group_analysis['category_analyses']
            
            group_details[group_name] = {
                'categories': list(category_analyses.keys()),
                'total_records': sum(ca['total_records'] for ca in category_analyses.values()),
                'date_ranges': {},
                'amount_totals': {},
                'duplicate_breakdown': {}
            }
            
            for category, analysis in category_analyses.items():
                all_categories.append(category)
                
                # Date ranges
                group_details[group_name]['date_ranges'][category] = {
                    'from': analysis['date_range']['from'],
                    'to': analysis['date_range']['to'],
                    'records': analysis['total_records']
                }
                
                # Duplicate breakdown
                dup_summary = analysis['duplicate_summary']
                if dup_summary['status'] == 'checked':
                    group_details[group_name]['duplicate_breakdown'][category] = {
                        'clean_records': dup_summary['no_duplicates'] + dup_summary['has_duplicates'],
                        'is_duplicate': dup_summary['is_duplicate'],
                        'total_records': analysis['total_records'],
                        'duplicate_rate': (dup_summary['is_duplicate'] / analysis['total_records'] * 100) if analysis['total_records'] > 0 else 0
                    }
                
                # Extract amount totals from yearly_summary
                if analysis['yearly_summary'] is not None and not analysis['yearly_summary'].empty:
                    yearly_df = analysis['yearly_summary']
                    numeric_cols = [col for col in yearly_df.columns 
                                   if col not in ['YEAR', 'Date Range']]
                    
                    totals_by_field = {}
                    total_sum = 0
                    
                    for col in numeric_cols:
                        field_total = yearly_df[col].sum()
                        totals_by_field[col] = field_total
                        total_sum += field_total
                    
                    group_details[group_name]['amount_totals'][category] = {
                        'total': total_sum,
                        'by_field': totals_by_field,
                        'by_year': {}
                    }
                    
                    # Add year-by-year breakdown
                    for _, row in yearly_df.iterrows():
                        year = str(int(row['YEAR']))
                        year_totals = {}
                        for col in numeric_cols:
                            year_totals[col] = row[col]
                        group_details[group_name]['amount_totals'][category]['by_year'][year] = year_totals
        
        summary['group_details'] = group_details
        summary['all_categories'] = all_categories
        
        # Add duplicate details
        duplicate_details = {}
        for group_name, group_data in group_details.items():
            for category, dup_data in group_data.get('duplicate_breakdown', {}).items():
                key = f"{group_name}_{category}"
                duplicate_details[key] = {
                    'group': group_name,
                    'category': category,
                    'total_duplicates': dup_data['is_duplicate'],
                    'total_records': dup_data['total_records'],
                    'duplicate_percentage': dup_data['duplicate_rate']
                }
        
        summary['duplicate_details'] = duplicate_details
        summary['comparison_highlights'] = []
        summary['missing_items_detail'] = {}
        summary['full_comparisons'] = {}
        
        # Add unrecognized files detail
        validation_issues = results.get('validation', {}).get('issues', [])
        summary['unrecognized_files_detail'] = [
            {'filename': issue, 'reason': 'Format not recognized'}
            for issue in validation_issues
        ]
        
        return summary
    
    def _create_prompt(self, data: Dict[str, Any], level: str) -> str:
        """Create optimized prompts for each report level"""
        
        # Base context
        base_context = f"""
You are FINDAP's AI Financial Analysis Assistant specializing in e-invoice data analysis.
You provide clear, actionable insights from financial data organized by groups and categories.

📊 ANALYSIS OVERVIEW:
- Files Processed: {data['files_processed']}
- Groups Analyzed: {data['total_groups']} ({', '.join(data['group_names']) if data['group_names'] else 'None'})
- Categories: {len(data.get('all_categories', []))}
- Total Records: {data['total_records']:,}
- Duplicates Detected: {data['duplicates_found']:,}
- Unrecognized Files: {data['unrecognized_files']}
"""
        
        if level == 'short':
            group_details_str = self._format_group_details(data.get('group_details', {}))
            duplicate_summary_str = self._format_duplicate_summary(data.get('duplicate_details', {}))

            return base_context + f"""            

📋 DETAILED BREAKDOWN:

{group_details_str}

{duplicate_summary_str}

📝 TASK: Create a SHORT EXECUTIVE SUMMARY REPORT

**CRITICAL REQUIREMENTS FOR TABLES:**
1. **ALWAYS include AT LEAST 3 markdown tables**
2. **Required tables:**
   - Table 1: Summary by Group (Groups, Categories, Records, Date Range)
   - Table 2: Amount Totals by Category (Category, Amount Fields, Totals)
   - Table 3: Duplicate Analysis by Category (Category, Clean Records, Duplicates, Rate)

3. **Table formatting:**
   - Use proper markdown: `| Column | Column |`
   - Include separator line: `|--------|--------|`
   - Format numbers with commas: 1,234,567
   - Align numbers to the right

**Report Structure:**

## 📊 Executive Summary
Brief 2-3 sentence overview of the financial data analyzed.

## 📁 Data Coverage by Group

**REQUIRED TABLE 1:**
| Group | Categories | Total Records | Date Range |
|-------|-----------|---------------|------------|
| Income Statement | 2 | 15,234 | 01-Jan-2023 to 31-Dec-2024 |
| ... | ... | ... | ... |

## 💰 Financial Totals Analysis

**REQUIRED TABLE 2:**
For EACH category, create a table showing:
| Category | Amount Field | Total |
|----------|-------------|--------|
| EBM Sales | AMOUNT WITHOUT VAT | 12,345,678 |
| EBM Sales | VAT AMOUNT | 2,345,678 |
| EBM Sales | TOTAL | 14,691,356 |

*Create one table per category with all numeric fields*

## 🔍 Duplicate Analysis

**REQUIRED TABLE 3:**
| Category | Clean Records | IS DUPLICATE | Duplicate Rate |
|----------|--------------|--------------|----------------|
| EBM Sales | 15,109 | 125 | 0.8% |
| ETAX Sales | 14,567 | 0 | 0.0% |

## 💡 Key Findings
- List 3-4 key insights (bullet points)
- Highlight significant patterns
- Note any concerns

## 🎯 Recommendations
1. **Data Quality:** One specific action
2. **Process Improvement:** One specific action
3. **Further Analysis:** One specific action

**FORMATTING RULES:**
- Use markdown headers (##, ###)
- **Bold** important numbers and findings
- Use tables extensively - **MINIMUM 3 TABLES REQUIRED**
- Keep professional tone
- Be specific with numbers
- Format all numbers with commas
"""

        elif level == 'medium':
            group_details_str = self._format_group_details(data.get('group_details', {}))
            duplicate_summary_str = self._format_duplicate_summary(data.get('duplicate_details', {}))
            
            return base_context + f"""

📋 DETAILED BREAKDOWN:

{group_details_str}

{duplicate_summary_str}

📝 TASK: Create a MEDIUM-LENGTH DETAILED REPORT

**CRITICAL TABLE REQUIREMENTS:**
**You MUST include AT LEAST 5 comprehensive markdown tables:**
1. Group Summary Table (Groups, Categories, Records, Date Ranges)
2. Category Details Table (Category, Group, Records, Date Range, Duplicates)
3. Amount Totals by Category (separate table for each category showing all fields)
4. Year-by-Year Analysis (for each category showing yearly breakdown)
5. Duplicate Analysis Summary (Clean vs IS DUPLICATE breakdown)

## Executive Summary
2-3 sentence overview.

## 📁 Data Coverage Overview

**TABLE 1: Group Summary**
| Group | Categories | Total Records | Date Coverage |
|-------|-----------|---------------|---------------|
| ... | ... | ... | ... |

## 📊 Category Analysis

**TABLE 2: Category Details**
| Category | Group | Records | Date From | Date To | Has Duplicates |
|----------|-------|---------|-----------|---------|----------------|
| ... | ... | ... | ... | ... | ... |

## 💰 Financial Totals by Category

For EACH category, create a detailed table:

**TABLE 3a: [Category Name] - Amount Breakdown**
| Amount Type | Total |
|------------|--------|
| AMOUNT WITHOUT VAT | 12,345,678 |
| VAT AMOUNT | 2,345,678 |
| AMOUNT VAT INCLUSIVE | 14,691,356 |

**TABLE 3b: [Category Name] - Yearly Breakdown**
| Year | AMOUNT WITHOUT VAT | VAT AMOUNT | TOTAL |
|------|-------------------|------------|-------|
| 2023 | 6,234,567 | 1,234,567 | 7,469,134 |
| 2024 | 6,111,111 | 1,111,111 | 7,222,222 |

*Repeat for each category*

## 🔍 Duplicate Analysis

**TABLE 4: Duplicate Breakdown by Category**
| Category | Total Records | Clean Records | IS DUPLICATE | Duplicate Rate |
|----------|--------------|---------------|--------------|----------------|
| ... | ... | ... | ... | ... |

## 📈 Key Findings by Group
For each group:
- Notable patterns
- Significant totals
- Data quality observations

## 💡 Insights & Trends
- Cross-category patterns
- Year-over-year changes
- Notable concentrations

## 🎯 Recommendations

### Critical (Immediate)
1. Action item with specific details

### Important (Address Soon)
2. Action item with specific details

### Future Enhancements
3. Action item with specific details

**FORMATTING:**
- Use markdown headers (##, ###, ####)
- **Bold** all important findings
- **MINIMUM 5 TABLES** - use tables extensively
- Format numbers: 1,234,567
- Professional tone
- Be thorough but organized
"""

        else:  # detailed
            group_details_str = self._format_group_details(data.get('group_details', {}))
            duplicate_summary_str = self._format_duplicate_summary(data.get('duplicate_details', {}))
            
            return base_context + f"""

📋 COMPLETE DATA:

{group_details_str}

{duplicate_summary_str}

📝 TASK: Create a COMPREHENSIVE DETAILED REPORT

**MANDATORY TABLE REQUIREMENTS:**
**You MUST include AT LEAST 8-10 comprehensive markdown tables throughout the report.**

Required tables:
1. Executive Summary Table (key metrics)
2. Group Overview Table
3. Complete Category Details Table
4. Amount Totals by Category (one table per category with all fields)
5. Year-by-Year Breakdown (one table per category)
6. Duplicate Analysis Summary Table
7. Duplicate Details by Category Table
8. Clean vs Duplicate Records Comparison Table
9. Data Quality Assessment Table
10. Additional tables as needed for comprehensive analysis

## 1. Executive Summary

**TABLE 1: Key Metrics at a Glance**
| Metric | Value | Status |
|--------|-------|--------|
| Total Files | X | ✅ |
| Total Groups | X | ✅ |
| Total Categories | X | ✅ |
| Total Records | X,XXX,XXX | ✅ |
| Duplicate Records | X,XXX | ⚠️ |
| Data Quality | XX% | ✅ |

Brief overview paragraph (3-4 sentences).

## 2. Analysis Scope

**TABLE 2: Group Overview**
| Group | Categories | Total Records | Date From | Date To | Duplicate Rate |
|-------|-----------|---------------|-----------|---------|----------------|
| ... | ... | ... | ... | ... | ... |

## 3. Complete Category Analysis

**TABLE 3: Category Details**
| Category | Group | Records | Clean Records | IS DUPLICATE | Duplicate % | Date From | Date To |
|----------|-------|---------|--------------|--------------|-------------|-----------|---------|
| ... | ... | ... | ... | ... | ... | ... | ... |

## 4. Financial Analysis by Category

For EACH category, provide:

### 4.X [Category Name]

**TABLE 4.X.a: Amount Field Breakdown**
| Amount Type | Total | Percentage |
|------------|--------|------------|
| AMOUNT WITHOUT VAT | XX,XXX,XXX | XX% |
| VAT AMOUNT | X,XXX,XXX | XX% |
| AMOUNT VAT INCLUSIVE | XX,XXX,XXX | XX% |
| Other fields... | ... | ... |

**TABLE 4.X.b: Yearly Breakdown**
| Year | Date Range | AMOUNT WITHOUT VAT | VAT AMOUNT | TOTAL |
|------|-----------|-------------------|------------|-------|
| 2023 | 01-Jan to 31-Dec | X,XXX,XXX | X,XXX,XXX | X,XXX,XXX |
| 2024 | 01-Jan to 31-Dec | X,XXX,XXX | X,XXX,XXX | X,XXX,XXX |

Brief analysis paragraph for this category.

*Repeat for ALL categories*

## 5. Duplicate Analysis

**TABLE 5: Duplicate Summary**
| Category | Total | Clean (NO + HAS) | IS DUPLICATE | Duplicate Rate |
|----------|-------|-----------------|--------------|----------------|
| ... | ... | ... | ... | ... |

**TABLE 6: Duplicate Impact Analysis**
| Category | Total Amount (Clean) | Total Amount (Duplicates) | Duplicate Impact |
|----------|---------------------|-------------------------|------------------|
| ... | ... | ... | ... |

## 6. Data Quality Assessment

**TABLE 7: Data Quality Metrics**
| Metric | Value | Assessment |
|--------|-------|------------|
| Completeness | XX% | Good/Fair/Poor |
| Duplicate Rate | X.X% | Good/Fair/Poor |
| Date Coverage | X years | Good/Fair/Poor |

### 6.1 Strengths
- List strengths with specific metrics

### 6.2 Areas for Improvement
- List issues with specific metrics

## 7. Trends & Patterns

### 7.1 Temporal Analysis
Year-over-year trends observed

### 7.2 Category Patterns
Patterns across categories

## 8. Detailed Findings by Group

For each group:
### 8.X [Group Name]
- Detailed observations
- Category comparisons
- Notable patterns

## 9. Recommendations

**TABLE 8: Prioritized Recommendations**
| Priority | Recommendation | Expected Impact | Effort |
|----------|---------------|----------------|--------|
| CRITICAL | ... | High | Low |
| HIGH | ... | High | Medium |
| MEDIUM | ... | Medium | Low |

### 9.1 Critical (Immediate Action)
Detailed recommendations

### 9.2 Important (Address Soon)
Detailed recommendations

### 9.3 Future Enhancements
Detailed recommendations

## 10. Conclusion & Next Steps
- Summary of key takeaways
- Prioritized action items
- Expected outcomes

**FORMATTING RULES:**
- Use markdown headers at all levels (##, ###, ####)
- **Bold** ALL important findings and numbers
- **MINIMUM 8-10 TABLES** - be table-heavy
- Format ALL numbers with commas: 1,234,567
- Use tables for ANY data that can be tabulated
- Professional, thorough, comprehensive tone
- Be VERY detailed and specific
"""
    
    def _format_group_details(self, group_details: Dict) -> str:
        """Format group details for prompt"""
        if not group_details:
            return "No group details available."
        
        lines = ["GROUP BREAKDOWN:"]
        for group, details in group_details.items():
            lines.append(f"\n📁 {group}:")
            lines.append(f"   - Categories: {', '.join(details['categories'])}")
            lines.append(f"   - Total Records: {details['total_records']:,}")
            
            # Date ranges
            if details.get('date_ranges'):
                lines.append("   - Date Ranges by Category:")
                for cat, date_range in details['date_ranges'].items():
                    lines.append(f"     • {cat}: {date_range['from']} to {date_range['to']} ({date_range['records']:,} records)")
            
            # Amount totals
            if details.get('amount_totals'):
                lines.append("   - Amount Totals by Category:")
                for cat, amounts in details['amount_totals'].items():
                    lines.append(f"     • {cat}:")
                    if amounts.get('by_field'):
                        for field, value in amounts['by_field'].items():
                            lines.append(f"       - {field}: {value:,.2f}")
                    
                    # Year-by-year breakdown
                    if amounts.get('by_year'):
                        lines.append(f"       - Year-by-Year Breakdown:")
                        for year, year_data in amounts['by_year'].items():
                            lines.append(f"         * {year}:")
                            for field, value in year_data.items():
                                lines.append(f"           - {field}: {value:,.2f}")
            
            # Duplicate breakdown
            if details.get('duplicate_breakdown'):
                lines.append("   - Duplicate Breakdown:")
                for cat, dup_data in details['duplicate_breakdown'].items():
                    lines.append(f"     • {cat}:")
                    lines.append(f"       - Clean Records: {dup_data['clean_records']:,}")
                    lines.append(f"       - IS DUPLICATE: {dup_data['is_duplicate']:,}")
                    lines.append(f"       - Duplicate Rate: {dup_data['duplicate_rate']:.2f}%")
        
        return "\n".join(lines)
    
    def _format_duplicate_summary(self, duplicate_details: Dict) -> str:
        """Format duplicate summary for prompt"""
        if not duplicate_details:
            return "DUPLICATE ANALYSIS:\nNo duplicates detected or duplicate status column not available."
        
        lines = ["DUPLICATE ANALYSIS:"]
        for key, dup_data in duplicate_details.items():
            pct = dup_data['duplicate_percentage']
            total = dup_data['total_duplicates']
            lines.append(f"- {dup_data['group']} / {dup_data['category']}: {total:,} duplicates ({pct:.2f}% of {dup_data['total_records']:,} records)")
        
        return "\n".join(lines)
    
    def _create_data_hash(self, data: Dict) -> str:
        """Create hash of data for caching purposes"""
        hash_components = [
            str(data.get('files_processed', 0)),
            str(data.get('total_records', 0)),
            str(data.get('duplicates_found', 0)),
            data.get('level', 'short')
        ]
        return "_".join(hash_components)
    
    @st.cache_data(ttl=3600, show_spinner=False)
    def _generate_with_cache(_self, prompt: str, level: str, data_hash: str) -> str:
        """Generate report with caching"""
        response = _self.model.generate_content(prompt)
        return response.text
    
    def _format_error_message(self, error: str) -> str:
        """Format error message as markdown"""
        return f"""
# ❌ Error Generating Report

An error occurred while generating the AI report:

```
{error}
```

## Troubleshooting Steps:

1. **Check API Key**: Ensure your Gemini API key is valid
2. **Check Internet Connection**: AI report generation requires internet access
3. **Check Data**: Ensure analysis has been run and results are available
"""
