# services/quick_analysis_engine.py - ENHANCED VERSION
"""
Quick Analysis Engine - ENHANCED: 
1. Top Partners Analysis done ONLY on Clean Records (NO + HAS Duplicates)
2. Uses "Top Clients Analysis" for SALES group
3. Uses "Top Suppliers Analysis" for COGS-EXPENSES group
"""

import pandas as pd
import streamlit as st
from typing import Dict, List, Tuple
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.file_handler import (
    get_numeric_columns,
    get_date_range,
    format_date_for_display,
    ComparisonRulesManager,
    cls_Customfiles_Filetypehandler as filehandler
)


class QuickAnalysisEngine:
    """
    Generates quick high-level analysis for each category independently
    ENHANCED: Top Partners Analysis on Clean Records Only
    """
    
    def __init__(self, file_metadata: Dict):
        """Initialize Quick Analysis Engine"""
        self.file_metadata = file_metadata
        self.results = {
            'group_summaries': {},
            'metadata': {
                'analysis_timestamp': datetime.now(),
                'total_files': len(file_metadata),
                'groups_analyzed': [],
                'categories_analyzed': []
            },
            'processed_dataframes': {}  # Store dataframes with duplicate columns
        }
        
        _, self.exclude_patterns = ComparisonRulesManager.get_numeric_field_config()
    
    def generate_quick_analysis(self) -> Dict:
        """Generate quick analysis for all uploaded categories organized by groups"""
        print("🚀 Starting Quick Analysis...")
        
        # Organize data by GROUP and CATEGORY
        data_groups = self._organize_by_groups()
        
        # Analyze each group and its categories
        for group_name, categories in data_groups.items():
            print(f"   📁 Analyzing Group: {group_name}")
            
            group_analysis = {
                'group_name': group_name,
                'category_analyses': {},
                'group_statistics': {}
            }
            
            # Analyze each category within the group
            for category, df in categories.items():
                print(f"      📊 Analyzing Category: {category}")
                
                # Apply duplicate detection
                df_with_dups = filehandler.fn_check_duplicatedrecords(df, category)
                
                # Store the dataframe with duplicate column
                storage_key = f"{group_name}_{category}"
                self.results['processed_dataframes'][storage_key] = df_with_dups
                print(f"         ✅ Stored dataframe with key: {storage_key}")
                print(f"         ✅ Columns: {df_with_dups.columns.tolist()}")
                print(f"         ✅ Has 'Duplicate Status': {'Duplicate Status' in df_with_dups.columns}")
                
                # Add date columns
                if "TRANSACTION DATE" in df_with_dups.columns:
                    df_with_dups["YEAR"] = df_with_dups["TRANSACTION DATE"].dt.year
                    df_with_dups["MONTH"] = df_with_dups["TRANSACTION DATE"].dt.strftime("%b")
                    df_with_dups["DAY"] = df_with_dups["TRANSACTION DATE"].dt.strftime("%d")
                    df_with_dups["YEAR-MONTH"] = df_with_dups["TRANSACTION DATE"].dt.strftime("%Y-%m")
                
                # Analyze this category - pass group_name for proper naming
                category_analysis = self._analyze_single_category(category, df_with_dups, group_name)
                group_analysis['category_analyses'][category] = category_analysis
                
                # Track in metadata
                if category not in self.results['metadata']['categories_analyzed']:
                    self.results['metadata']['categories_analyzed'].append(category)
            
            # Calculate group-level statistics
            group_analysis['group_statistics'] = self._calculate_group_statistics(
                group_name, categories
            )
            
            # Store group analysis
            self.results['group_summaries'][group_name] = group_analysis
            self.results['metadata']['groups_analyzed'].append(group_name)
        
        print(f"✅ Quick Analysis complete! Analyzed {len(data_groups)} groups")
        print(f"✅ Stored {len(self.results['processed_dataframes'])} dataframes with duplicate detection")
        
        return self.results
    
    def _organize_by_groups(self) -> Dict[str, Dict[str, pd.DataFrame]]:
        """Organize by FINANCIAL STATEMENT GROUP and CATEGORY"""
        data_groups = {}
        
        for file_name, metadata in self.file_metadata.items():
            for sheet_name, values in metadata.items():
                category = values[0]
                df_cleaned = values[5].copy()
                
                if category.upper() in ['UNKNOWN', '']:
                    continue
                
                if "FINANCIAL STATEMENT GROUP" in df_cleaned.columns:
                    unique_groups = df_cleaned["FINANCIAL STATEMENT GROUP"].unique()
                    
                    for group in unique_groups:
                        if group not in data_groups:
                            data_groups[group] = {}
                        
                        df_group = df_cleaned[
                            df_cleaned["FINANCIAL STATEMENT GROUP"] == group
                        ].copy()
                        
                        df_group["Source File"] = file_name
                        
                        if category not in data_groups[group]:
                            data_groups[group][category] = df_group
                        else:
                            data_groups[group][category] = pd.concat([
                                data_groups[group][category], 
                                df_group
                            ], ignore_index=True)
                else:
                    group = "Other Financial Data"
                    
                    if group not in data_groups:
                        data_groups[group] = {}
                    
                    df_cleaned["Source File"] = file_name
                    
                    if category not in data_groups[group]:
                        data_groups[group][category] = df_cleaned
                    else:
                        data_groups[group][category] = pd.concat([
                            data_groups[group][category], 
                            df_cleaned
                        ], ignore_index=True)
        
        return data_groups
    
    def _analyze_single_category(self, category: str, df: pd.DataFrame, group_name: str) -> Dict:
        """
        Perform complete analysis for a single category
        🆕 ENHANCEMENT: Now accepts group_name to determine proper terminology
        """
        analysis = {
            'category': category,
            'total_records': len(df),
            'date_range': {},
            'yearly_summary': None,
            'duplicate_summary': {},
            'top_analysis': {},
            'numeric_fields_analyzed': []
        }
        
        # 1. Date Range
        start_date, end_date = get_date_range(df)
        analysis['date_range'] = {
            'from': start_date,
            'to': end_date
        }
        
        # 2. Duplicate Summary
        analysis['duplicate_summary'] = self._get_duplicate_summary(df)
        
        # 3. Yearly Summary with all numeric fields
        analysis['yearly_summary'] = self._generate_yearly_summary(df, category)
        
        # 🆕 ENHANCEMENT: Pass group_name to Top Analysis
        # 4. Top Suppliers/Clients Analysis (ONLY on clean records)
        analysis['top_analysis'] = self._generate_top_analysis(df, group_name)
        
        return analysis
    
    def _get_duplicate_summary(self, df: pd.DataFrame) -> Dict:
        """Get duplicate statistics from Duplicate Status column"""
        dup_col = None
        for col in df.columns:
            if col.upper().strip() == 'DUPLICATE STATUS':
                dup_col = col
                break
        
        if dup_col is None:
            return {
                'has_duplicates': 0,
                'is_duplicate': 0,
                'no_duplicates': len(df),
                'status': 'not_checked'
            }
        
        try:
            status_counts = df[dup_col].str.upper().value_counts()
            
            return {
                'has_duplicates': int(status_counts.get('HAS DUPLICATES', 0)),
                'is_duplicate': int(status_counts.get('IS DUPLICATE', 0)),
                'no_duplicates': int(status_counts.get('NO DUPLICATES', 0)),
                'status': 'checked'
            }
        except Exception as e:
            print(f"   ⚠️ Error reading duplicate status: {e}")
            return {
                'has_duplicates': 0,
                'is_duplicate': 0,
                'no_duplicates': len(df),
                'status': 'error'
            }
    
    def _generate_yearly_summary(self, df: pd.DataFrame, category: str) -> pd.DataFrame:
        """Generate summary by YEAR for all numeric fields"""
        if 'YEAR' not in df.columns:
            print(f"   ⚠️ {category}: YEAR column not found")
            return pd.DataFrame()
        
        numeric_cols = get_numeric_columns(df, self.exclude_patterns)
        
        if not numeric_cols:
            print(f"   ℹ️ {category}: No numeric fields found")
            return pd.DataFrame()
        
        try:
            yearly_data = df.groupby('YEAR')[numeric_cols].sum().reset_index()
            yearly_data = yearly_data.sort_values('YEAR')
            
            date_ranges = []
            for year in yearly_data['YEAR']:
                year_df = df[df['YEAR'] == year]
                start, end = get_date_range(year_df)
                date_ranges.append(f"{start} to {end}")
            
            yearly_data['Date Range'] = date_ranges
            
            cols = ['YEAR', 'Date Range'] + numeric_cols
            yearly_data = yearly_data[cols]
            
            return yearly_data
            
        except Exception as e:
            print(f"   ⚠️ {category}: Error generating yearly summary: {e}")
            return pd.DataFrame()
    
    def _generate_top_analysis(self, df: pd.DataFrame, group_name: str) -> Dict:
        """
        🆕 ENHANCED: Generate Top 5, 10, 20 analysis by year - ONLY on CLEAN RECORDS
        Uses proper terminology based on Financial Statement Group
        """
        if 'YEAR' not in df.columns:
            return {}
        
        # 🆕 ENHANCEMENT 1: Filter to CLEAN RECORDS ONLY
        dup_col = None
        for col in df.columns:
            if col.upper().strip() == 'DUPLICATE STATUS':
                dup_col = col
                break
        
        if dup_col:
            # Filter to clean records: NO DUPLICATES + HAS DUPLICATES
            clean_mask = df[dup_col].str.upper().isin(['NO DUPLICATES', 'HAS DUPLICATES'])
            df_clean = df[clean_mask].copy()
            print(f"   📊 Top Analysis: Using {len(df_clean):,} clean records out of {len(df):,} total")
        else:
            # No duplicate status column - use all records
            df_clean = df.copy()
            print(f"   📊 Top Analysis: No duplicate status found, using all {len(df):,} records")
        
        if df_clean.empty:
            print("   ⚠️ No clean records available for top analysis")
            return {}
        
        numeric_cols = get_numeric_columns(df_clean, self.exclude_patterns)
        
        if not numeric_cols:
            return {}
        
        # 🆕 ENHANCEMENT 2: Determine proper terminology based on group
        partner_col = None
        partner_type = "Partners"  # Default
        
        # Check group name to determine terminology
        group_upper = group_name.upper()
        
        for col in df_clean.columns:
            col_upper = col.upper()
            if 'SUPPLIER NAME' in col_upper:
                partner_col = col
                # Determine if it's Suppliers or Clients based on group
                if 'SALES' in group_upper or 'REVENUE' in group_upper:
                    partner_type = "Clients"
                else:
                    partner_type = "Suppliers"
                break
            elif 'BUYER NAME' in col_upper:
                partner_col = col
                # Buyer name typically means clients
                partner_type = "Clients"
                break
            elif 'CLIENT NAME' in col_upper or 'CUSTOMER NAME' in col_upper:
                partner_col = col
                partner_type = "Clients"
                break
        
        if partner_col is None:
            print("   ℹ️ No SUPPLIER NAME, BUYER NAME, or CLIENT NAME column found")
            return {}
        
        print(f"   📊 Top Analysis: Using '{partner_col}' as {partner_type} column for group '{group_name}'")
        
        try:
            df_analysis = df_clean.copy()
            df_analysis['Total_Amount'] = df_analysis[numeric_cols].sum(axis=1)
            
            partner_yearly = df_analysis.groupby(['YEAR', partner_col])['Total_Amount'].sum().reset_index()
            yearly_totals = partner_yearly.groupby('YEAR')['Total_Amount'].sum()
            
            top_results = []
            
            for year in sorted(partner_yearly['YEAR'].unique()):
                year_data = partner_yearly[partner_yearly['YEAR'] == year].sort_values(
                    'Total_Amount', ascending=False
                )
                
                year_total = yearly_totals[year]
                
                for top_n in [5, 10, 20]:
                    if len(year_data) >= top_n:
                        top_amount = year_data.head(top_n)['Total_Amount'].sum()
                        percentage = (top_amount / year_total * 100) if year_total > 0 else 0
                        
                        top_results.append({
                            'YEAR': year,
                            'Top X': f'Top {top_n}',
                            'Total Amount': top_amount,
                            'Percentage': f'{percentage:.1f}%'
                        })
            
            return {
                'top_analysis_table': pd.DataFrame(top_results),
                'partner_type': partner_type  # 🆕 Store the partner type
            }
            
        except Exception as e:
            print(f"   ⚠️ Error generating top analysis: {e}")
            return {}
    
    def _calculate_group_statistics(self, group_name: str, categories: Dict) -> Dict:
        """Calculate group-level statistics"""
        total_records = sum(len(df) for df in categories.values())
        total_categories = len(categories)
        
        all_dates = []
        for df in categories.values():
            if 'TRANSACTION DATE' in df.columns:
                all_dates.extend(df['TRANSACTION DATE'].dropna().tolist())
        
        if all_dates:
            min_date = format_date_for_display(min(all_dates))
            max_date = format_date_for_display(max(all_dates))
        else:
            min_date = "N/A"
            max_date = "N/A"
        
        return {
            'total_records': total_records,
            'total_categories': total_categories,
            'date_range': {
                'from': min_date,
                'to': max_date
            }
        }
    
    def format_results_for_display(self) -> Dict:
        """Format results for Streamlit display"""
        display_results = {
            'summary_stats': self._format_summary_stats(),
            'group_details': {}
        }
        
        for group_name, group_analysis in self.results['group_summaries'].items():
            display_results['group_details'][group_name] = {
                'group_statistics': group_analysis['group_statistics'],
                'categories': {}
            }
            
            for category, analysis in group_analysis['category_analyses'].items():
                display_results['group_details'][group_name]['categories'][category] = {
                    'total_records': analysis['total_records'],
                    'date_range': analysis['date_range'],
                    'duplicates': analysis['duplicate_summary'],
                    'yearly_summary': analysis['yearly_summary'],
                    'top_analysis': analysis['top_analysis']
                }
        
        return display_results
    
    def _format_summary_stats(self) -> Dict:
        """Format high-level summary statistics"""
        total_records = 0
        total_duplicates = 0
        
        for group_analysis in self.results['group_summaries'].values():
            for category_analysis in group_analysis['category_analyses'].values():
                total_records += category_analysis['total_records']
                total_duplicates += category_analysis['duplicate_summary']['is_duplicate']
        
        return {
            'total_groups': len(self.results['group_summaries']),
            'total_categories': len(self.results['metadata']['categories_analyzed']),
            'total_records': total_records,
            'total_duplicates': total_duplicates,
            'analysis_timestamp': self.results['metadata']['analysis_timestamp']
        }
