# services/global_analysis_orchestrator.py - FIXED VERSION
"""
Global Analysis Orchestrator - Fixed to work with group_summaries structure
"""

import pandas as pd
import streamlit as st
from typing import Dict, List
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.quick_analysis_engine import QuickAnalysisEngine


class GlobalAnalysisOrchestrator:
    """
    Orchestrates the complete global analysis with progress tracking
    Fixed to work with group-based structure from QuickAnalysisEngine
    """
    
    def __init__(self, file_metadata: Dict):
        """Initialize the orchestrator"""
        self.file_metadata = file_metadata
        self.results = {
            'metadata': {
                'analysis_start_time': datetime.now(),
                'analysis_end_time': None,
                'analysis_duration': None,
                'files_processed': [],
                'categories_found': [],
                'groups_found': [],
                'total_records': 0,
                'analysis_depth': None,
                'status': 'initialized'
            },
            'quick_summary': {},
            'validation': {},
            'errors': []
        }
    
    def run_analysis(self, analysis_depth: str = 'quick') -> Dict:
        """Main entry point - runs staged analysis with progress tracking"""
        self.results['metadata']['analysis_depth'] = analysis_depth
        
        # Define analysis stages based on depth
        if analysis_depth == 'quick':
            stages = [
                ('🔍 Validating uploaded data', self._stage_validate_data),
                ('📊 Generating high-level summaries', self._stage_quick_summary),
                ('📈 Analyzing duplicates', self._stage_duplicate_analysis),
                ('🎯 Generating top partner analysis', self._stage_top_analysis),
                ('✅ Finalizing results', self._stage_finalize)
            ]
        elif analysis_depth == 'standard':
            stages = [
                ('🔍 Validating uploaded data', self._stage_validate_data),
                ('📊 Generating high-level summaries', self._stage_quick_summary),
                ('📈 Analyzing duplicates', self._stage_duplicate_analysis),
                ('📅 Generating monthly breakdowns', self._stage_monthly_analysis),
                ('🎯 Generating top partner analysis', self._stage_top_analysis),
                ('✅ Finalizing results', self._stage_finalize)
            ]
        else:  # comprehensive
            stages = [
                ('🔍 Validating uploaded data', self._stage_validate_data),
                ('📊 Generating high-level summaries', self._stage_quick_summary),
                ('📈 Analyzing duplicates', self._stage_duplicate_analysis),
                ('📅 Generating monthly breakdowns', self._stage_monthly_analysis),
                ('🎯 Generating detailed top partner analysis', self._stage_top_analysis),
                ('📝 Generating detailed reports', self._stage_detailed_reports),
                ('✅ Finalizing results', self._stage_finalize)
            ]
        
        return self._execute_stages(stages)
    
    def _execute_stages(self, stages: List[tuple]) -> Dict:
        """Execute analysis stages with progress bar"""
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, (stage_name, stage_func) in enumerate(stages):
            try:
                status_text.info(f"{stage_name}...")
                stage_func()
                progress = (i + 1) / len(stages)
                progress_bar.progress(progress)
                
            except Exception as e:
                error_msg = f"Error in stage '{stage_name}': {str(e)}"
                self.results['errors'].append(error_msg)
                st.error(f"⚠️ {error_msg}")
                print(f"❌ {error_msg}")
                import traceback
                print(traceback.format_exc())
        
        progress_bar.empty()
        status_text.empty()
        
        return self.results
    
    # ========================================================================
    # STAGE FUNCTIONS - FIXED FOR GROUP STRUCTURE
    # ========================================================================
    
    def _stage_validate_data(self):
        """Stage 1: Validate uploaded data"""
        validation = {
            'files_count': len(self.file_metadata),
            'categories': [],
            'groups': [],
            'total_records': 0,
            'date_coverage': {},
            'issues': []
        }
        
        for file_name, sheets in self.file_metadata.items():
            self.results['metadata']['files_processed'].append(file_name)
            
            for sheet_name, sheet_data in sheets.items():
                category = sheet_data[0]
                df = sheet_data[5]
                
                # Track categories
                if category not in validation['categories'] and category.upper() != 'UNKNOWN':
                    validation['categories'].append(category)
                    self.results['metadata']['categories_found'].append(category)
                
                # Track groups
                if 'FINANCIAL STATEMENT GROUP' in df.columns:
                    groups = df['FINANCIAL STATEMENT GROUP'].unique()
                    for group in groups:
                        if group not in validation['groups']:
                            validation['groups'].append(group)
                            self.results['metadata']['groups_found'].append(group)
                
                # Count records
                validation['total_records'] += len(df)
                self.results['metadata']['total_records'] += len(df)
                
                # Check for UNKNOWN categories
                if category.upper() == 'UNKNOWN':
                    validation['issues'].append(
                        f"File '{file_name}' sheet '{sheet_name}' has unknown category"
                    )
        
        self.results['validation'] = validation
        print(f"   ✅ Validated {validation['files_count']} files, " +
              f"{len(validation['groups'])} groups, " +
              f"{len(validation['categories'])} categories, " +
              f"{validation['total_records']:,} records")
    
    def _stage_quick_summary(self):
        """Stage 2: Generate quick summaries using QuickAnalysisEngine"""
        engine = QuickAnalysisEngine(self.file_metadata)
        quick_results = engine.generate_quick_analysis()
        
        # Store results - NOW USES group_summaries structure
        self.results['quick_summary'] = quick_results
        
        # Count groups and categories
        group_summaries = quick_results.get('group_summaries', {})
        total_categories = sum(
            len(group_data['category_analyses']) 
            for group_data in group_summaries.values()
        )
        
        print(f"   ✅ Generated summaries for {len(group_summaries)} groups, " +
              f"{total_categories} categories")
    
    def _stage_duplicate_analysis(self):
        """Stage 3: Analyze duplicate data - FIXED for group structure"""
        total_duplicates = 0
        categories_with_dups = []
        
        # FIXED: Iterate through group_summaries, not category_summaries
        group_summaries = self.results['quick_summary'].get('group_summaries', {})
        
        for group_name, group_data in group_summaries.items():
            category_analyses = group_data.get('category_analyses', {})
            
            for category, analysis in category_analyses.items():
                dup_summary = analysis.get('duplicate_summary', {})
                dup_count = dup_summary.get('is_duplicate', 0)
                
                if dup_count > 0:
                    total_duplicates += dup_count
                    categories_with_dups.append(f"{group_name}/{category}")
        
        self.results['metadata']['total_duplicates'] = total_duplicates
        self.results['metadata']['categories_with_duplicates'] = categories_with_dups
        
        if total_duplicates > 0:
            print(f"   ⚠️ Found {total_duplicates:,} duplicate records in " +
                  f"{len(categories_with_dups)} categories")
        else:
            print(f"   ✅ No duplicates found")
    
    def _stage_monthly_analysis(self):
        """Stage 4: Generate monthly analysis (for standard/comprehensive levels)"""
        print(f"   ℹ️ Monthly analysis stage (to be implemented)")
    
    def _stage_top_analysis(self):
        """Stage 5: Top partner analysis - FIXED for group structure"""
        # FIXED: Iterate through group_summaries
        group_summaries = self.results['quick_summary'].get('group_summaries', {})
        
        total_top_analyses = 0
        for group_data in group_summaries.values():
            category_analyses = group_data.get('category_analyses', {})
            for analysis in category_analyses.values():
                if analysis.get('top_analysis'):
                    total_top_analyses += 1
        
        print(f"   ✅ Generated top partner analysis for {total_top_analyses} categories")
    
    def _stage_detailed_reports(self):
        """Stage 6: Generate detailed reports (for comprehensive level)"""
        print(f"   ℹ️ Detailed reports stage (to be implemented)")
    
    def _stage_finalize(self):
        """Final stage: Finalize and package results"""
        self.results['metadata']['analysis_end_time'] = datetime.now()
        
        duration = (self.results['metadata']['analysis_end_time'] - 
                   self.results['metadata']['analysis_start_time'])
        
        self.results['metadata']['analysis_duration'] = str(duration).split('.')[0]
        self.results['metadata']['status'] = 'completed'
        
        print(f"   ✅ Analysis completed in {self.results['metadata']['analysis_duration']}")
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def get_summary_statistics(self) -> Dict:
        """Get high-level summary statistics for display"""
        return {
            'total_files': len(self.results['metadata']['files_processed']),
            'total_groups': len(self.results['metadata']['groups_found']),
            'total_categories': len(self.results['metadata']['categories_found']),
            'total_records': self.results['metadata']['total_records'],
            'total_duplicates': self.results['metadata'].get('total_duplicates', 0),
            'analysis_duration': self.results['metadata'].get('analysis_duration', 'N/A'),
            'analysis_depth': self.results['metadata']['analysis_depth']
        }
    
    def get_category_list(self) -> List[str]:
        """Get list of analyzed categories"""
        return self.results['metadata']['categories_found']
    
    def get_group_list(self) -> List[str]:
        """Get list of analyzed groups"""
        return self.results['metadata']['groups_found']
    
    def get_validation_issues(self) -> List[str]:
        """Get list of validation issues"""
        return self.results['validation'].get('issues', [])
    
    def has_errors(self) -> bool:
        """Check if any errors occurred during analysis"""
        return len(self.results['errors']) > 0
    
    def get_errors(self) -> List[str]:
        """Get list of errors"""
        return self.results['errors']
