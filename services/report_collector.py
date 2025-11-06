# services/report_collector.py

import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime

class AnalysisResultsCollector:
    """
    Collects all analysis results from comparison.py and other modules
    to prepare data for AI report generation.
    """
    
    def __init__(self):
        self.results = {
            'metadata': {
                'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_files': 0,
                'total_sheets': 0,
                'groups_analyzed': []
            },
            'group_summaries': {},  # Summaries by financial statement group
            'comparisons': {},      # Category comparison results
            'duplicates': {},       # Duplicate detection results
            'missing_items': {},    # Missing items between categories
            'unrecognized_files': [],
            'period_analysis': {}   # Year/Month aggregations
        }
    
    def reset(self):
        """Reset all collected data"""
        self.__init__()
    
    def set_metadata(self, file_metadata: Dict):
        """Extract metadata from st.session_state.file_metadata"""
        self.results['metadata']['total_files'] = len(file_metadata)
        
        total_sheets = 0
        for file_name, sheets in file_metadata.items():
            total_sheets += len(sheets)
        
        self.results['metadata']['total_sheets'] = total_sheets
    
    def add_group_summary(self, group_name: str, categories: Dict[str, pd.DataFrame]):
        """Capture summary statistics for a financial statement group"""
        group_data = {
            'group_name': group_name,
            'num_categories': len(categories),
            'category_names': list(categories.keys()),
            'total_records': sum(len(df) for df in categories.values()),
            'date_range': {},
            'amount_totals': {}
        }
        
        # Extract date ranges and totals for each category
        for cat_name, df in categories.items():
            if 'TRANSACTION DATE' in df.columns:
                min_date = df['TRANSACTION DATE'].min()
                max_date = df['TRANSACTION DATE'].max()
                group_data['date_range'][cat_name] = {
                    'from': str(min_date.date()) if pd.notna(min_date) else 'N/A',
                    'to': str(max_date.date()) if pd.notna(max_date) else 'N/A',
                    'records': len(df)
                }
            
            # Get amount columns totals
            amount_cols = [col for col in df.select_dtypes(include='number').columns 
                          if 'AMOUNT' in col.upper() or 'VAT' in col.upper() or 'TOTAL' in col.upper()]
            
            if amount_cols:
                group_data['amount_totals'][cat_name] = {
                    col: float(df[col].sum()) if pd.notna(df[col].sum()) else 0 
                    for col in amount_cols
                }
        
        self.results['group_summaries'][group_name] = group_data
        
        # Track analyzed groups
        if group_name not in self.results['metadata']['groups_analyzed']:
            self.results['metadata']['groups_analyzed'].append(group_name)
    
    def add_comparison_result(self, group_name: str, cat1_name: str, cat2_name: str, 
                             numeric_results: List[Dict], text_results: List[Dict]):
        """Store comparison results from fn_compare_numeric_fields and fn_compare_non_numeric_fields"""
        comparison_key = f"{group_name}::{cat1_name}_vs_{cat2_name}"
        
        # Calculate summary statistics
        total_numeric_diffs = sum(abs(r.get('Difference', 0)) for r in numeric_results)
        max_diff = max((abs(r.get('Difference', 0)) for r in numeric_results), default=0)
        
        self.results['comparisons'][comparison_key] = {
            'group': group_name,
            'category_1': cat1_name,
            'category_2': cat2_name,
            'numeric_comparisons': numeric_results,
            'text_comparisons': text_results,
            'summary_stats': {
                'num_numeric_comparisons': len(numeric_results),
                'num_text_comparisons': len(text_results),
                'total_numeric_differences': float(total_numeric_diffs),
                'max_difference': float(max_diff)
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def add_missing_items_summary(self, group_name: str, cat1_name: str, cat2_name: str,
                                 missing_1in2: List[pd.DataFrame], missing_2in1: List[pd.DataFrame]):
        """Store summary of missing items between categories"""
        key = f"{group_name}::{cat1_name}_vs_{cat2_name}"
        
        summary = {
            'group': group_name,
            'category_1': cat1_name,
            'category_2': cat2_name,
            f'missing_from_{cat2_name}': {
                'count': sum(len(df) for df in missing_1in2) if missing_1in2 else 0,
                'total_amount': 0,
                'fields': []
            },
            f'missing_from_{cat1_name}': {
                'count': sum(len(df) for df in missing_2in1) if missing_2in1 else 0,
                'total_amount': 0,
                'fields': []
            }
        }
        
        # Calculate total amounts and identify fields for missing items from cat2
        if missing_1in2:
            df_combined = pd.concat(missing_1in2, ignore_index=True)
            amount_cols = [c for c in df_combined.select_dtypes(include='number').columns 
                          if 'AMOUNT' in c.upper()]
            if amount_cols:
                summary[f'missing_from_{cat2_name}']['total_amount'] = float(df_combined[amount_cols[0]].sum())
            
            if 'Comparison_Field' in df_combined.columns:
                summary[f'missing_from_{cat2_name}']['fields'] = df_combined['Comparison_Field'].unique().tolist()
        
        # Calculate total amounts and identify fields for missing items from cat1
        if missing_2in1:
            df_combined = pd.concat(missing_2in1, ignore_index=True)
            amount_cols = [c for c in df_combined.select_dtypes(include='number').columns 
                          if 'AMOUNT' in c.upper()]
            if amount_cols:
                summary[f'missing_from_{cat1_name}']['total_amount'] = float(df_combined[amount_cols[0]].sum())
            
            if 'Comparison_Field' in df_combined.columns:
                summary[f'missing_from_{cat1_name}']['fields'] = df_combined['Comparison_Field'].unique().tolist()
        
        self.results['missing_items'][key] = summary
    
    def add_duplicate_summary(self, group_name: str, category: str, df: pd.DataFrame):
        """Capture duplicate detection results"""
        if 'Duplicate Status' not in df.columns:
            return
        
        dup_counts = df['Duplicate Status'].value_counts().to_dict()
        
        # ✅ FIXED: Count only records where 'Duplicate Status' == "IS duplicate" (case-insensitive)
        # Normalize the status values to handle case and whitespace variations
        normalized_counts = {}
        total_duplicates = 0
        
        for status, count in dup_counts.items():
            # Normalize: strip whitespace and convert to uppercase
            normalized_status = str(status).strip().upper()
            normalized_counts[normalized_status] = normalized_counts.get(normalized_status, 0) + count
            
            # Count as duplicate if it matches "IS DUPLICATE"
            if normalized_status == "IS DUPLICATE":
                total_duplicates += count
        
        key = f"{group_name}::{category}"
        self.results['duplicates'][key] = {
            'group': group_name,
            'category': category,
            'total_records': len(df),
            'duplicate_counts': dup_counts,  # Keep original for display
            'normalized_counts': normalized_counts,  # Add normalized version
            'total_duplicates': int(total_duplicates),
            'duplicate_percentage': round((total_duplicates / len(df) * 100), 2) if len(df) > 0 else 0,
            'unique_records': len(df) - total_duplicates
        }
    
    def add_unrecognized_file(self, filename: str, reason: str = "Format not recognized"):
        """Track files that couldn't be processed"""
        self.results['unrecognized_files'].append({
            'filename': filename,
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        })
    
    def get_summary_for_ai(self, report_level: str = 'short') -> Dict[str, Any]:
        """
        Prepare structured summary for AI based on report level.
        This is what gets sent to Gemini API.
        """
        if report_level == 'short':
            return self._create_short_summary()
        elif report_level == 'medium':
            return self._create_medium_summary()
        else:
            return self._create_detailed_summary()
    
    def _create_short_summary(self) -> Dict[str, Any]:
        """High-level statistics only - for quick executive summary"""
        total_groups = len(self.results['group_summaries'])
        total_comparisons = len(self.results['comparisons'])
        total_records = sum(g['total_records'] for g in self.results['group_summaries'].values())
        
        # ✅ FIXED: Count all duplicates correctly
        total_duplicates = sum(
            d.get('total_duplicates', 0)
            for d in self.results['duplicates'].values()
        )
        
        # ✅ FIXED: Safer missing items summation
        total_missing = 0
        for m in self.results['missing_items'].values():
            for key, val in m.items():
                if key.startswith("missing_from_") and isinstance(val, dict):
                    total_missing += val.get("count", 0)
        
        return {
            'level': 'short',
            'files_processed': self.results['metadata']['total_files'],
            'sheets_processed': self.results['metadata']['total_sheets'],
            'total_groups': total_groups,
            'group_names': list(self.results['group_summaries'].keys()),
            'total_records': total_records,
            'comparisons_made': total_comparisons,
            'duplicates_found': total_duplicates,
            'missing_items_count': total_missing,
            'unrecognized_files': len(self.results['unrecognized_files'])
        }
    
    def _create_medium_summary(self) -> Dict[str, Any]:
        """Include category-level details and highlights"""
        short_summary = self._create_short_summary()
        
        # Add group-level breakdowns with date ranges
        group_details = {}
        for group_name, group_data in self.results['group_summaries'].items():
            group_details[group_name] = {
                'categories': group_data['category_names'],
                'num_categories': group_data['num_categories'],
                'total_records': group_data['total_records'],
                'date_ranges': group_data.get('date_range', {}),
                'amount_totals': {}
            }
            
            # Summarize amounts per category
            for cat, amounts in group_data.get('amount_totals', {}).items():
                if amounts:
                    group_details[group_name]['amount_totals'][cat] = {
                        'total': sum(amounts.values()),
                        'by_field': amounts,
                        'fields': list(amounts.keys())
                    }
        
        # Add comparison highlights - top differences
        comparison_highlights = []
        for comp_key, comp_data in self.results['comparisons'].items():
            if comp_data['numeric_comparisons']:
                # Find largest difference
                largest_diff = max(
                    comp_data['numeric_comparisons'], 
                    key=lambda x: abs(x.get('Difference', 0))
                )
                comparison_highlights.append({
                    'categories': f"{comp_data['category_1']} vs {comp_data['category_2']}",
                    'group': comp_data['group'],
                    'largest_difference': largest_diff.get('Difference', 0),
                    'field': largest_diff.get('Field Category 1', 'Unknown'),
                    'aggregation': largest_diff.get('Aggregation Function', 'N/A')
                })
        
        # Sort by absolute difference and take top 5
        comparison_highlights.sort(key=lambda x: abs(x['largest_difference']), reverse=True)
        
        # Missing items breakdown
        missing_items_detail = {}
        for key, missing_data in self.results['missing_items'].items():
            missing_items_detail[key] = {
                'group': missing_data['group'],
                'comparison': f"{missing_data['category_1']} vs {missing_data['category_2']}",
                'missing_counts': {
                    k: v['count'] for k, v in missing_data.items() 
                    if isinstance(v, dict) and 'count' in v
                },
                'missing_amounts': {
                    k: v['total_amount'] for k, v in missing_data.items() 
                    if isinstance(v, dict) and 'total_amount' in v
                }
            }
        
        return {
            **short_summary,
            'level': 'medium',
            'group_details': group_details,
            'comparison_highlights': comparison_highlights[:5],
            'duplicate_details': self.results['duplicates'],
            'missing_items_detail': missing_items_detail
        }
    
    def _create_detailed_summary(self) -> Dict[str, Any]:
        """Complete data dump for comprehensive analysis"""
        medium_summary = self._create_medium_summary()
        
        return {
            **medium_summary,
            'level': 'detailed',
            'full_comparisons': self.results['comparisons'],
            'full_missing_items': self.results['missing_items'],
            'period_breakdowns': self.results['period_analysis'],
            'unrecognized_files_detail': self.results['unrecognized_files'],
            'raw_group_data': self.results['group_summaries']
        }
    
    def to_dict(self) -> Dict:
        """Export complete results as dictionary"""
        return self.results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get quick statistics for display"""
        return {
            'total_groups': len(self.results['group_summaries']),
            'total_categories': sum(g['num_categories'] for g in self.results['group_summaries'].values()),
            'total_records': sum(g['total_records'] for g in self.results['group_summaries'].values()),
            'total_comparisons': len(self.results['comparisons']),
            'total_duplicates': sum(d.get('total_duplicates', 0) for d in self.results['duplicates'].values()),
            'total_unrecognized': len(self.results['unrecognized_files'])
        }
