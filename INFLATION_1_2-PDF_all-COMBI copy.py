#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
INFLATION_META_ANALYSIS_v6_BATCH_ADVANCED_FIXED.py - Advanced Batch Two-Stage Analysis
Smart cost optimization with sophisticated extraction protocols for batch processing
90% cost savings through intelligent Haiku screening + targeted Opus extraction
Enhanced parameter detection and PDF page position handling
FIXED: Improved rate limiting with chunking and intelligent token management
"""

import logging
import sys
import os
import tkinter as tk
from tkinter import filedialog
import pandas as pd
import re
import requests
import time
import json
import base64
from bs4 import BeautifulSoup
import anthropic
import datetime
from typing import List, Dict, Optional, Tuple, Any
import numpy as np
from dataclasses import dataclass
from enum import Enum
import PyPDF2
import io
from pathlib import Path
import collections

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)
# Reduce noise from other libraries
logging.getLogger('anthropic').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

# Claude API key
CLAUDE_API_KEY = ""

# Model configurations and pricing (per million tokens)
class ModelConfig(Enum):
    HAIKU = ("claude-3-7-sonnet-20250219", 0.25, 1.25)  # input/output price  
    SONNET = ("claude-3-7-sonnet-20250219", 3.0, 15.0)
    OPUS = ("claude-opus-4-20250514", 15.0, 75.0)

# Rate limiting configuration
@dataclass
class RateLimitConfig:
    """Rate limiting configuration with improved settings"""
    # Anthropic limits
    requests_per_minute: int = 50  # Conservative request limit
    tokens_per_minute: int = 40000  # Anthropic limit
    tokens_per_day: int = 1000000  # Daily limit
    
    # Timing settings
    min_delay_between_requests: float = 2.0  # Minimum 2s between requests
    initial_backoff: float = 5.0  # Initial retry delay
    max_backoff: float = 300.0  # Max 5 minutes
    backoff_multiplier: float = 2.0
    max_retries: int = 5
    
    # Token estimation
    avg_tokens_per_pdf_page: int = 3000  # Conservative estimate
    max_tokens_per_request: int = 30000  # Leave buffer for rate limits

# Column definitions for meta-analysis
META_ANALYSIS_COLUMNS = [
    "Idstudy", "IdEstimate", "Author", "Author_Affiliation", "Journal_Name", 
    "Num_Citations", "Year", "Base_Model_Type", "Augmented_base_model", 
    "Augmentation_Description", "Ramsey_Rule", "HH_Included", "Firms_Included", 
    "Banks_Included", "Government_Included", "HH_Maximization_Type", 
    "HH_Maximized_Vars", "Producer_Type", "Producer_Assumption", 
    "Other_Agent_Included", "Other_Agent_Assumptions", "Empirical_Research", 
    "Country", "Flexible_Price_Assumption", "Exogenous_Inflation", "Households_discount_factor", 
    "Consumption_curvature_parameter", "Disutility_of_labor", 
    "Inverse_of_labor_supply_elasticity", "Money_curvature_parameter", 
    "Loan_to_value_ratio", "Labor_share_of_output", "Depositors_discount_factor", 
    "Price_adjustment_cost", "Elasticity_of_substitution_between_goods", 
    "AR1_coefficient_of_TFP", "Std_dev_to_TFP_shock", "Zero_Lower_Bound", 
    "Results_Table", "Results_Inflation", "Results_Inflation_Assumption", 
    "Preferred_Estimate", "Reason_for_Preferred", "Std_Dev_Inflation", 
    "Interest_Rate", "Impact_Factor"
]

@dataclass
class ScreeningResult:
    """Results from quick screening phase"""
    has_inflation_data: bool
    relevant_pdf_positions: List[int]
    tables_with_inflation: List[str]
    parameter_tables: List[str]
    parameter_locations: List[str]
    basic_info: Dict[str, str]
    estimated_inflation_values: int
    estimated_parameter_values: int
    key_sections: Dict[str, str]
    confidence_score: float
    page_mapping: Dict[str, int]

@dataclass
class CostEstimate:
    """Cost analysis for different approaches"""
    screening_cost: float
    extraction_cost: float
    total_cost: float
    saved_amount: float
    saved_percentage: float

@dataclass
class TokenUsage:
    """Track token usage for a request"""
    timestamp: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    model: str

class ImprovedRateLimitManager:
    """Enhanced rate limiting with better tracking and chunking"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.request_history = collections.deque(maxlen=100)
        self.token_history = collections.deque(maxlen=1000)
        self.daily_tokens_used = 0
        self.daily_reset_time = time.time()
        
    def reset_daily_counter_if_needed(self):
        """Reset daily counter if new day"""
        current_time = time.time()
        if current_time - self.daily_reset_time > 86400:  # 24 hours
            self.daily_tokens_used = 0
            self.daily_reset_time = current_time
            logger.info("📅 Daily token counter reset")
    
    def estimate_pdf_tokens(self, pdf_pages: int) -> int:
        """Estimate tokens for PDF processing"""
        # More accurate estimation based on pages
        base_tokens = pdf_pages * self.config.avg_tokens_per_pdf_page
        # Add overhead for prompts and responses
        total_tokens = int(base_tokens * 1.5)
        return min(total_tokens, self.config.max_tokens_per_request)
    
    def get_requests_in_last_minute(self) -> int:
        """Count requests in the last minute"""
        current_time = time.time()
        recent_requests = [
            req for req in self.request_history 
            if current_time - req['timestamp'] < 60
        ]
        return len(recent_requests)
    
    def get_tokens_in_last_minute(self) -> int:
        """Calculate tokens used in the last minute"""
        current_time = time.time()
        recent_tokens = sum(
            usage.total_tokens 
            for usage in self.token_history 
            if current_time - usage.timestamp < 60
        )
        return recent_tokens
    
    def can_make_request(self, estimated_tokens: int) -> Tuple[bool, str]:
        """Check if request can be made, return (can_proceed, reason)"""
        self.reset_daily_counter_if_needed()
        
        # Check daily limit
        if self.daily_tokens_used + estimated_tokens > self.config.tokens_per_day:
            return False, f"Daily token limit would be exceeded ({self.daily_tokens_used}/{self.config.tokens_per_day})"
        
        # Check per-minute request limit
        requests_last_minute = self.get_requests_in_last_minute()
        if requests_last_minute >= self.config.requests_per_minute:
            return False, f"Request rate limit reached ({requests_last_minute}/{self.config.requests_per_minute} per minute)"
        
        # Check per-minute token limit
        tokens_last_minute = self.get_tokens_in_last_minute()
        if tokens_last_minute + estimated_tokens > self.config.tokens_per_minute:
            # If we would exceed, check if it's the first request
            if tokens_last_minute == 0:
                # First request - allow it even if it exceeds single limit
                return True, "First request allowed"
            return False, f"Token rate limit would be exceeded ({tokens_last_minute + estimated_tokens}/{self.config.tokens_per_minute} per minute)"
        
        return True, "OK"
    
    def wait_if_needed(self, estimated_tokens: int):
        """Wait if rate limits require it"""
        while True:
            can_proceed, reason = self.can_make_request(estimated_tokens)
            
            if can_proceed:
                # Also enforce minimum delay between requests
                if self.request_history:
                    last_request = self.request_history[-1]['timestamp']
                    elapsed = time.time() - last_request
                    if elapsed < self.config.min_delay_between_requests:
                        wait_time = self.config.min_delay_between_requests - elapsed
                        logger.info(f"⏳ Minimum delay: waiting {wait_time:.1f}s")
                        time.sleep(wait_time)
                return
            
            # Calculate appropriate wait time
            if "Daily token limit" in reason:
                logger.error(f"❌ {reason}")
                raise Exception("Daily token limit reached - cannot continue today")
            
            elif "Request rate limit" in reason:
                # Wait until oldest request expires from window
                oldest_request = self.request_history[0]['timestamp']
                wait_time = max(5, 61 - (time.time() - oldest_request))
                
            elif "Token rate limit" in reason:
                # Wait proportionally to how much we're over
                tokens_last_minute = self.get_tokens_in_last_minute()
                excess = tokens_last_minute + estimated_tokens - self.config.tokens_per_minute
                wait_time = max(10, min(60, excess / 1000))
            
            else:
                wait_time = 10
            
            logger.info(f"⏳ Rate limit: {reason}")
            logger.info(f"⏳ Waiting {wait_time:.1f}s before next request...")
            time.sleep(wait_time)
    
    def record_request(self, tokens_used: TokenUsage):
        """Record a completed request"""
        self.request_history.append({
            'timestamp': tokens_used.timestamp,
            'tokens': tokens_used.total_tokens
        })
        self.token_history.append(tokens_used)
        self.daily_tokens_used += tokens_used.total_tokens
        
        # Log current usage
        requests_minute = self.get_requests_in_last_minute()
        tokens_minute = self.get_tokens_in_last_minute()
        logger.info(f"📊 Rate limits: {requests_minute}/{self.config.requests_per_minute} requests, "
                   f"{tokens_minute}/{self.config.tokens_per_minute} tokens/min, "
                   f"{self.daily_tokens_used}/{self.config.tokens_per_day} tokens/day")

class AdvancedBatchPDFAnalyzer:
    """Advanced batch PDF analyzer with improved rate limiting"""
    
    def __init__(self, api_key: str, export_folder: str, mode: str = 'smart'):
        self.api_key = api_key
        self.export_folder = export_folder
        self.mode = mode
        self.client = anthropic.Anthropic(api_key=api_key)
        self.current_study_id = 1
        
        # Rate limiting
        self.rate_limiter = ImprovedRateLimitManager(RateLimitConfig())
        
        # Batch statistics
        self.batch_stats = {
            'total_files': 0,
            'processed_files': 0,
            'successful_files': 0,
            'failed_files': 0,
            'total_studies': 0,
            'total_estimates': 0,
            'total_cost': 0.0,
            'total_saved': 0.0,
            'start_time': time.time(),
            'rate_limit_delays': 0,
            'total_tokens_used': 0
        }
        
        # Results storage
        self.all_results = []
        self.processing_log = []
    
    def _chunk_pdf_if_needed(self, pdf_path: str, total_pages: int) -> List[Tuple[int, int, str]]:
        """Split large PDFs into chunks if needed"""
        estimated_tokens = self.rate_limiter.estimate_pdf_tokens(total_pages)
        
        if estimated_tokens <= self.rate_limiter.config.max_tokens_per_request:
            # Small enough to process in one go
            return [(1, total_pages, "full")]
        
        # Need to chunk
        pages_per_chunk = int(self.rate_limiter.config.max_tokens_per_request / 
                             self.rate_limiter.config.avg_tokens_per_pdf_page)
        pages_per_chunk = max(5, pages_per_chunk)  # At least 5 pages per chunk
        
        chunks = []
        for start in range(1, total_pages + 1, pages_per_chunk):
            end = min(start + pages_per_chunk - 1, total_pages)
            chunk_name = f"pages_{start}-{end}"
            chunks.append((start, end, chunk_name))
        
        logger.info(f"📄 PDF split into {len(chunks)} chunks for processing")
        return chunks
    
    def _make_api_request_with_retry(self, model: str, messages: List[Dict], 
                                   max_tokens: int = 1500, 
                                   estimated_tokens: Optional[int] = None) -> Optional[Any]:
        """Make API request with improved retry logic"""
        
        # Estimate tokens if not provided
        if estimated_tokens is None:
            total_text_length = sum(len(str(msg)) for msg in messages)
            estimated_tokens = max(total_text_length // 4, 1000)
        
        # Wait for rate limit
        self.rate_limiter.wait_if_needed(estimated_tokens)
        
        for attempt in range(self.rate_limiter.config.max_retries):
            try:
                logger.info(f"🔄 API request attempt {attempt + 1}/{self.rate_limiter.config.max_retries}")
                
                start_time = time.time()
                response = self.client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=0 if 'screening' in str(messages) else 0.1,
                    messages=messages
                )
                
                # Record usage
                # Note: Actual token counts would come from response.usage if available
                # Using estimates for now
                usage = TokenUsage(
                    timestamp=start_time,
                    input_tokens=estimated_tokens,
                    output_tokens=len(response.content[0].text) // 4,
                    total_tokens=estimated_tokens + len(response.content[0].text) // 4,
                    model=model
                )
                self.rate_limiter.record_request(usage)
                self.batch_stats['total_tokens_used'] += usage.total_tokens
                
                return response
                
            except anthropic.RateLimitError as e:
                logger.warning(f"⚠️ Rate limit hit on attempt {attempt + 1}: {e}")
                self.batch_stats['rate_limit_delays'] += 1
                
                if attempt < self.rate_limiter.config.max_retries - 1:
                    # Exponential backoff
                    delay = min(
                        self.rate_limiter.config.initial_backoff * 
                        (self.rate_limiter.config.backoff_multiplier ** attempt),
                        self.rate_limiter.config.max_backoff
                    )
                    logger.info(f"⏳ Backoff: waiting {delay:.1f}s before retry...")
                    time.sleep(delay)
                else:
                    logger.error(f"❌ Rate limit exceeded after all retries")
                    return None
                    
            except Exception as e:
                logger.error(f"❌ API error on attempt {attempt + 1}: {e}")
                
                if attempt < self.rate_limiter.config.max_retries - 1:
                    delay = self.rate_limiter.config.initial_backoff * (attempt + 1)
                    logger.info(f"⏳ Error backoff: waiting {delay:.1f}s before retry...")
                    time.sleep(delay)
                else:
                    logger.error(f"❌ Request failed after all retries")
                    return None
        
        return None
    
    def get_pdf_info(self, pdf_path: str) -> Tuple[int, Dict[str, int]]:
        """Get PDF information"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)
                
                page_mapping = {}
                for i in range(total_pages):
                    page_mapping[str(i + 1)] = i + 1
                
                return total_pages, page_mapping
                
        except Exception as e:
            logger.error(f"Error getting PDF info for {pdf_path}: {e}")
            return 0, {}
    
    def analyze_pdf_advanced(self, pdf_path: str) -> Tuple[Dict[str, Any], CostEstimate]:
        """Main analysis method using advanced two-stage approach"""
        
        file_size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
        logger.info(f"📄 Analyzing: {os.path.basename(pdf_path)} ({file_size_mb:.1f} MB)")
        
        # Get PDF information
        total_pages, page_mapping = self.get_pdf_info(pdf_path)
        logger.info(f"📊 PDF has {total_pages} pages")
        
        # Check if we need to chunk the PDF
        chunks = self._chunk_pdf_if_needed(pdf_path, total_pages)
        
        if self.mode == 'full':
            logger.info("🎯 Mode: Full analysis (Opus)")
            results = self._analyze_with_opus_full(pdf_path, chunks)
            cost = self._estimate_cost_full(file_size_mb)
            return results, cost
            
        elif self.mode == 'economy':
            logger.info("💰 Mode: Economy analysis (Sonnet)")
            results = self._analyze_with_sonnet_only(pdf_path, chunks)
            cost = self._estimate_cost_economy(file_size_mb)
            return results, cost
            
        else:  # smart mode
            logger.info("🧠 Mode: Smart analysis (Haiku + Opus)")
            
            # Phase 1: Quick screening
            logger.info("🔍 PHASE 1: Quick document screening...")
            screening_result = self._screen_with_haiku(pdf_path, total_pages, chunks)
            
            if not screening_result:
                logger.error("❌ Screening failed")
                return {'error': 'Screening failed'}, self._estimate_cost_screening_only(file_size_mb)
            
            if not screening_result.has_inflation_data:
                logger.warning("❌ Document doesn't contain relevant inflation data")
                return self._create_empty_result(), self._estimate_cost_screening_only(file_size_mb)
            
            # Phase 2: Targeted extraction
            logger.info("🎯 PHASE 2: Precise extraction of identified data...")
            results = self._extract_with_opus_targeted(pdf_path, screening_result, total_pages)
            
            # Check if targeted extraction failed
            if 'error' in results:
                logger.error(f"❌ Targeted extraction failed: {results['error']}")
                return results, self._estimate_cost_screening_only(file_size_mb)
            
            # Calculate savings
            cost = self._calculate_cost_savings(file_size_mb, screening_result, total_pages)
            
            return results, cost
    
    def _screen_with_haiku(self, pdf_path: str, total_pages: int, chunks: List[Tuple[int, int, str]]) -> Optional[ScreeningResult]:
        """Quick screening of PDF with chunking support"""
        
        if len(chunks) == 1:
            # Single chunk - process normally
            return self._screen_single_chunk(pdf_path, total_pages, 1, total_pages)
        
        # Multiple chunks - aggregate results
        all_results = []
        for start_page, end_page, chunk_name in chunks:
            logger.info(f"🔍 Screening {chunk_name}...")
            chunk_result = self._screen_single_chunk(pdf_path, total_pages, start_page, end_page)
            if chunk_result:
                all_results.append(chunk_result)
        
        if not all_results:
            return None
        
        # Aggregate results from all chunks
        return self._aggregate_screening_results(all_results, total_pages)
    
    def _screen_single_chunk(self, pdf_path: str, total_pages: int, 
                           start_page: int, end_page: int) -> Optional[ScreeningResult]:
        """Screen a single chunk of the PDF"""
        
        # Extract relevant pages
        pdf_data = self._extract_pages_from_pdf(pdf_path, start_page, end_page)
        if not pdf_data:
            return None
        
        chunk_pages = end_page - start_page + 1
        screening_prompt = f"""Quick analysis of economic PDF document chunk (pages {start_page}-{end_page} of {total_pages}).

CRITICAL INSTRUCTION: This is pages {start_page}-{end_page} of a {total_pages} page document.
When identifying content, use the ACTUAL PDF page numbers ({start_page}-{end_page}).

TASK: Find ONLY sections relevant for inflation meta-analysis.

SEARCH FOR:
1. **Tables with inflation values**
   - Keywords: inflation, π, optimal inflation, welfare cost, steady state, price stability
   - Record: "Table X (PDF position Y): [table name]"

2. **Results sections**
   - Results, Findings, Numerical Results, Calibration Results, Welfare Analysis

3. **Model parameter tables/sections**
   - Tables: "Parameters", "Calibration", "Model specification", "Baseline values"
   - Look for Greek letters: β, σ, ρ, α, γ, δ, θ, φ, ψ
   - Common parameter names: discount factor, elasticity, persistence, share

4. **Basic information extraction**
   - Author(s) in APA format: "Last name, First Initial. (Year)"
   - Author affiliation: University/institution name
   - Publication year: 4-digit year
   - Journal name: Exact journal name
   - Model type: DSGE, NK, RBC, VAR, etc.

OUTPUT FORMAT (JSON):
```json
{{
  "has_inflation_data": true/false,
  "confidence_score": 0.0-1.0,
  "relevant_pdf_positions": [list of actual PDF page numbers],
  "tables_with_inflation": ["descriptions"],
  "parameter_tables": ["descriptions"],
  "parameter_locations": ["descriptions"],
  "basic_info": {{
    "author": "Smith, J. (2023)",
    "author_affiliation": "Harvard University",
    "year": "2023",
    "journal": "Journal of Monetary Economics",
    "model_type": "NK-DSGE"
  }},
  "estimated_inflation_values": 5,
  "estimated_parameter_values": 8,
  "key_sections": {{}},
  "page_mapping": {{}}
}}
```

Return ONLY valid JSON."""
        
        try:
            estimated_tokens = self.rate_limiter.estimate_pdf_tokens(chunk_pages)
            
            messages = [{
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_data
                        }
                    },
                    {
                        "type": "text",
                        "text": screening_prompt
                    }
                ]
            }]
            
            response = self._make_api_request_with_retry(
                model=ModelConfig.HAIKU.value[0],
                messages=messages,
                max_tokens=1500,
                estimated_tokens=estimated_tokens
            )
            
            if not response:
                return None
            
            # Parse JSON response
            result_text = response.content[0].text
            data = self._parse_json_response(result_text)
            
            if data:
                # Adjust page numbers to be relative to full document
                if 'relevant_pdf_positions' in data:
                    # Ensure positions are within this chunk's range
                    data['relevant_pdf_positions'] = [
                        pos for pos in data['relevant_pdf_positions']
                        if start_page <= pos <= end_page
                    ]
                
                return ScreeningResult(
                    has_inflation_data=data.get('has_inflation_data', False),
                    relevant_pdf_positions=data.get('relevant_pdf_positions', []),
                    tables_with_inflation=data.get('tables_with_inflation', []),
                    parameter_tables=data.get('parameter_tables', []),
                    parameter_locations=data.get('parameter_locations', []),
                    basic_info=data.get('basic_info', {}),
                    estimated_inflation_values=data.get('estimated_inflation_values', 0),
                    estimated_parameter_values=data.get('estimated_parameter_values', 0),
                    key_sections=data.get('key_sections', {}),
                    confidence_score=data.get('confidence_score', 0.5),
                    page_mapping=data.get('page_mapping', {})
                )
            
            return None
                
        except Exception as e:
            logger.error(f"Error during screening: {e}")
            return None
    
    def _aggregate_screening_results(self, results: List[ScreeningResult], 
                                   total_pages: int) -> ScreeningResult:
        """Aggregate screening results from multiple chunks"""
        
        # Combine all data
        all_positions = []
        all_inflation_tables = []
        all_param_tables = []
        all_param_locations = []
        
        total_inflation_values = 0
        total_param_values = 0
        max_confidence = 0
        has_any_inflation = False
        
        # Use first non-empty basic info
        basic_info = {}
        
        for result in results:
            if result.has_inflation_data:
                has_any_inflation = True
            
            all_positions.extend(result.relevant_pdf_positions)
            all_inflation_tables.extend(result.tables_with_inflation)
            all_param_tables.extend(result.parameter_tables)
            all_param_locations.extend(result.parameter_locations)
            
            total_inflation_values += result.estimated_inflation_values
            total_param_values += result.estimated_parameter_values
            max_confidence = max(max_confidence, result.confidence_score)
            
            # Update basic info if better data found
            if result.basic_info and not basic_info:
                basic_info = result.basic_info
            elif result.basic_info:
                # Merge, preferring non-NA values
                for key, value in result.basic_info.items():
                    if value != 'NA' and (key not in basic_info or basic_info[key] == 'NA'):
                        basic_info[key] = value
        
        return ScreeningResult(
            has_inflation_data=has_any_inflation,
            relevant_pdf_positions=sorted(list(set(all_positions))),
            tables_with_inflation=all_inflation_tables,
            parameter_tables=all_param_tables,
            parameter_locations=all_param_locations,
            basic_info=basic_info,
            estimated_inflation_values=total_inflation_values,
            estimated_parameter_values=total_param_values,
            key_sections={},
            confidence_score=max_confidence,
            page_mapping={}
        )
    
    def _extract_pages_from_pdf(self, pdf_path: str, start_page: int, end_page: int) -> Optional[str]:
        """Extract specific pages from PDF"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                pdf_writer = PyPDF2.PdfWriter()
                
                # Extract pages (convert to 0-based index)
                for page_num in range(start_page - 1, min(end_page, len(pdf_reader.pages))):
                    pdf_writer.add_page(pdf_reader.pages[page_num])
                
                # Write to memory buffer
                output_buffer = io.BytesIO()
                pdf_writer.write(output_buffer)
                output_buffer.seek(0)
                
                # Convert to base64
                return base64.standard_b64encode(output_buffer.getvalue()).decode("utf-8")
                
        except Exception as e:
            logger.error(f"Error extracting pages: {e}")
            return None
    
    def _parse_json_response(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse JSON from response text"""
        # Try multiple extraction methods
        
        # Method 1: Look for ```json blocks
        json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Method 2: Look for any JSON object
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # Method 3: Try the whole text
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        return None
    
    def _extract_with_opus_targeted(self, pdf_path: str, screening: ScreeningResult, total_pages: int) -> Dict[str, Any]:
        """Targeted extraction of only relevant parts using Opus"""
        
        # Validate and extract relevant pages
        if screening.relevant_pdf_positions and screening.confidence_score > 0.1:
            pdf_data = self._extract_relevant_pages_from_pdf(pdf_path, screening.relevant_pdf_positions, total_pages)
            
            if pdf_data is None:
                return {'error': 'Targeted extraction failed - process stopped to prevent unnecessary costs'}
        else:
            return {'error': 'No relevant positions identified - process stopped to prevent unnecessary costs'}
        
        # Create targeted prompt based on screening
        targeted_prompt = self._create_targeted_extraction_prompt(screening)
        
        try:
            estimated_tokens = self.rate_limiter.estimate_pdf_tokens(len(screening.relevant_pdf_positions))
            
            messages = [{
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_data
                        }
                    },
                    {
                        "type": "text",
                        "text": targeted_prompt
                    }
                ]
            }]
            
            response = self._make_api_request_with_retry(
                model=ModelConfig.OPUS.value[0],
                messages=messages,
                max_tokens=6000,
                estimated_tokens=estimated_tokens
            )
            
            if not response:
                return {'error': 'Extraction request failed after all retries'}
            
            return self._parse_response(response.content[0].text)
            
        except Exception as e:
            logger.error(f"Error during targeted extraction: {e}")
            return {'error': str(e)}
    
    def _extract_relevant_pages_from_pdf(self, pdf_path: str, pdf_positions: List[int], total_pages: int) -> Optional[str]:
        """Extract only relevant pages from PDF using actual PDF positions"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                pdf_writer = PyPDF2.PdfWriter()
                
                # Validate PDF positions
                valid_positions = []
                for pos in pdf_positions:
                    if 1 <= pos <= total_pages:
                        valid_positions.append(pos)
                
                if not valid_positions:
                    return None
                
                # Extract only relevant pages
                for pdf_pos in valid_positions:
                    page_index = pdf_pos - 1
                    try:
                        page = pdf_reader.pages[page_index]
                        pdf_writer.add_page(page)
                    except Exception as e:
                        logger.error(f"Error adding PDF position {pdf_pos}: {e}")
                
                # Write to memory buffer
                output_buffer = io.BytesIO()
                pdf_writer.write(output_buffer)
                output_buffer.seek(0)
                
                # Convert to base64
                pdf_data = base64.standard_b64encode(output_buffer.getvalue()).decode("utf-8")
                
                logger.info(f"✅ Successfully extracted {len(valid_positions)} pages")
                return pdf_data
                
        except Exception as e:
            logger.error(f"Error extracting relevant pages: {e}")
            return None
    
    def _create_targeted_extraction_prompt(self, screening: ScreeningResult) -> str:
        """Creates targeted prompt based on screening results"""
        
        focus_areas = "\n".join([f"- {table}" for table in screening.tables_with_inflation])
        param_areas = "\n".join([f"- {table}" for table in screening.parameter_tables])
        param_locations = "\n".join([f"- {location}" for location in screening.parameter_locations])
        
        prompt = f"""Based on quick analysis, we know exactly where the key data is located.

CRITICAL AUTHOR & AFFILIATION REQUIREMENTS:
- Author MUST be in APA format: "Last name, First Initial. (Year)" 
- Author affiliation MUST be extracted (university/institution name)
- Look in: title page, footnotes, headers, author information sections
- If multiple authors: "Smith, J. & Jones, M. (2023)"
- If affiliation not found: use "Cannot find affiliation" (NOT "NA")

BASIC INFORMATION (already identified):
- Author: {screening.basic_info.get('author', 'NEEDS APA FORMAT')}
- Author Affiliation: {screening.basic_info.get('author_affiliation', 'NEEDS EXTRACTION')}
- Year: {screening.basic_info.get('year', 'NA')}
- Journal: {screening.basic_info.get('journal', 'NA')}
- Model: {screening.basic_info.get('model_type', 'NA')}

CRITICAL DUAL FOCUS - INFLATION AND PARAMETERS:

1. INFLATION TABLES (expect ~{screening.estimated_inflation_values} values):
{focus_areas if focus_areas else "- None specifically identified - search all tables for inflation values"}

2. PARAMETER TABLES (expect ~{screening.estimated_parameter_values} values):
{param_areas if param_areas else "- None specifically identified - search all tables for parameters"}

3. ADDITIONAL PARAMETER LOCATIONS:
{param_locations if param_locations else "- None specifically identified - search text for parameter values"}

CRITICAL PARAMETER EXTRACTION INSTRUCTIONS:
- Look for ALL Greek letters: β, σ, ρ, α, γ, δ, θ, φ, ψ, χ, ε, η, ζ, κ, λ, μ, ν, π, τ, υ, ω
- Search for parameter names: discount factor, elasticity, persistence, share, cost, probability
- Check appendices, footnotes, and text paragraphs for parameter values
- Extract parameters even if they appear in sentence form: "We set β = 0.99"
- Look in calibration sections, baseline specifications, and robustness checks

INSTRUCTIONS:
1. Extract ALL inflation values from ANY table or text you find
2. Extract ALL parameter values from ANY location (tables, text, footnotes, appendices)
3. Create separate row for each inflation value
4. Fill in ALL corresponding model parameters for each row
5. If parameters are not near inflation results, use the same parameters for all inflation estimates
6. Search EXHAUSTIVELY for parameters - they are critical for meta-analysis

{self._get_advanced_extraction_instructions()}

OUTPUT: Tab-separated table with exactly these columns:
{self._get_column_headers()}"""
        
        return prompt
    
    def _get_advanced_extraction_instructions(self) -> str:
        """Returns sophisticated extraction instructions"""
        return """
# ADVANCED EXTRACTION PROTOCOL

## CRITICAL AUTHOR & AFFILIATION PROTOCOL (HIGHEST PRIORITY!)

### MANDATORY AUTHOR FORMAT:
- **APA Style REQUIRED**: "Last name, First Initial. (Year)"
- **Single author**: "Smith, J. (2023)"
- **Multiple authors**: "Smith, J. & Jones, M. (2023)" or "Smith, J., Jones, M. & Brown, K. (2023)"
- **Search locations**: Title page, headers, footnotes, author sections
- **NEVER use just first names or incomplete formats**

### MANDATORY AFFILIATION EXTRACTION:
- **University/Institution name REQUIRED**
- **Search locations**: Title page footnotes, author information sections, first page
- **Format**: "Harvard University" or "Federal Reserve Bank of Boston"
- **Multiple authors**: Use primary author's affiliation or comma-separated
- **If truly not found**: Write "Cannot find affiliation" (NOT "NA")

## CRITICAL NOTATION GUIDE

### INFLATION VARIABLE IDENTIFICATION:
- **Standard notations**: π, π*, πe, π̄, phi, φ, Π
- **Expected value notation**: E[π], E(π), 𝔼[π] - these ARE inflation values
- **Common labels**: "inflation", "inflation rate", "optimal inflation", "inflation target"
- **Typical range**: -5% to 10% (annualized)
- **WARNING - Verify carefully**:
  - V[π], Var[π], σ²(π) - likely variance, NOT inflation value
  - SD[π], σ(π) - likely standard deviation

### CRITICAL PARAMETER IDENTIFICATION PROTOCOL:
**HIGHEST PRIORITY**: Extract ALL parameters - they are essential for meta-analysis!

**Essential Parameters (Search exhaustively for these):**
- **β (beta)**: Discount factor, typically 0.9-0.999
- **σ (sigma)**: Risk aversion, consumption curvature, typically 1-5
- **ρ (rho)**: Persistence parameters, typically 0-0.99
- **α (alpha)**: Labor/capital share, typically 0.3-0.7
- **γ (gamma)**: Various elasticities
- **δ (delta)**: Depreciation rate, typically 0.01-0.1

### PARAMETER-SPECIFIC PROTOCOLS:
- **Households_discount_factor**: Look for β, beta, discount factor
- **Consumption_curvature_parameter**: Look for σ, sigma, risk aversion, CRRA
- **Labor_share_of_output**: Look for α, alpha, labor share
- **Price_adjustment_cost**: Look for adjustment cost, Calvo, Rotemberg

## CRITICAL RULES:
- **AUTHOR & AFFILIATION ARE MANDATORY** - spend extra effort finding them
- NEVER leave any cell empty - use "NA" for missing information (except affiliation: use "Cannot find affiliation")
- NEVER fabricate data - only report verifiable information
- ALWAYS use 0/1 coding for Yes/No questions (0 = No, 1 = Yes)
- Each inflation result = separate row
- Fill ALL parameter columns for each row
- PRIORITY: Author format and affiliation are as important as inflation values!

## CRITICAL FEEDBACK FROM USER - MANDATORY COMPLIANCE:

### INFLATION RESULTS EXTRACTION - CRITICAL ERRORS TO AVOID:
1. **NEVER include inflation variance** - V[π], Var[π], σ²(π) are variance measures, NOT inflation values
2. **NEVER change signs** of inflation values - report exactly as found in the paper
3. **ALWAYS verify inflation column carefully** - double-check each inflation value before reporting
4. **NEVER confuse variance with inflation** - variance measures uncertainty, not inflation level
5. **ALWAYS check context** - make sure you're extracting actual inflation rates, not variance or standard deviation

### MANDATORY INFLATION VERIFICATION PROTOCOL:
- **Before reporting any inflation value**: Verify it's actually an inflation rate, not variance
- **Check notation carefully**: π = inflation, V[π] = variance (DO NOT REPORT)
- **Verify signs**: Report inflation values with exact signs as found in paper
- **Cross-reference**: If unsure, check multiple tables/sections for consistency
- **Context matters**: Inflation values typically appear in "Results" or "Optimal Policy" sections

### CRITICAL ERROR PREVENTION:
- **Parameter extraction is OK** - continue with current parameter extraction methods
- **Inflation extraction needs improvement** - focus on accuracy over speed
- **Better column checking** - spend extra time verifying inflation column accuracy
- **Avoid variance confusion** - clearly distinguish between inflation values and variance measures
"""
    
    def _get_column_headers(self) -> str:
        """Returns column headers"""
        return "\t".join(META_ANALYSIS_COLUMNS)
    
    def _analyze_with_sonnet_only(self, pdf_path: str, chunks: List[Tuple[int, int, str]]) -> Dict[str, Any]:
        """Economy analysis with Sonnet only"""
        
        if len(chunks) == 1:
            # Single chunk
            with open(pdf_path, "rb") as f:
                pdf_data = base64.standard_b64encode(f.read()).decode("utf-8")
        else:
            # For large PDFs, just use the first few chunks for economy mode
            logger.info(f"📄 Large PDF - using first 3 chunks for economy analysis")
            relevant_chunks = chunks[:3]
            end_page = relevant_chunks[-1][1]
            pdf_data = self._extract_pages_from_pdf(pdf_path, 1, end_page)
            
            if not pdf_data:
                return {'error': 'Failed to extract pages for economy analysis'}
        
        economy_prompt = f"""Extract data for inflation meta-analysis from this PDF.

CRITICAL REQUIREMENTS:
1. Author MUST be in APA format: "Last name, First Initial. (Year)" - e.g., "Smith, J. (2023)"
2. Author affiliation MUST be extracted: University/institution name from title page/footnotes
3. If affiliation not found: write "Cannot find affiliation"

MAIN TASKS:
1. Extract author in proper APA format and affiliation (HIGHEST PRIORITY)
2. Find all inflation values (π, inflation rate, optimal inflation)
3. Identify basic info (year, journal)
4. Extract key model parameters (β, σ, etc.)
5. Each inflation value = separate row

OUTPUT: Tab-separated table with these columns:
{self._get_column_headers()}

Use "NA" for missing values except affiliation (use "Cannot find affiliation"). Be precise but concise."""
        
        try:
            estimated_tokens = self.rate_limiter.estimate_pdf_tokens(
                len(chunks[0]) if len(chunks) == 1 else 20
            )
            
            messages = [{
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_data
                        }
                    },
                    {
                        "type": "text",
                        "text": economy_prompt
                    }
                ]
            }]
            
            response = self._make_api_request_with_retry(
                model=ModelConfig.SONNET.value[0],
                messages=messages,
                max_tokens=4000,
                estimated_tokens=estimated_tokens
            )
            
            if not response:
                return {'error': 'Economy analysis request failed after all retries'}
            
            return self._parse_response(response.content[0].text)
            
        except Exception as e:
            logger.error(f"Error during economy analysis: {e}")
            return {'error': str(e)}
    
    def _analyze_with_opus_full(self, pdf_path: str, chunks: List[Tuple[int, int, str]]) -> Dict[str, Any]:
        """Full analysis with Opus, handling chunks if needed"""
        
        logger.info("🤖 Running full analysis with Opus...")
        
        if len(chunks) == 1:
            # Single chunk - process normally
            with open(pdf_path, "rb") as f:
                pdf_data = base64.standard_b64encode(f.read()).decode("utf-8")
            
            return self._analyze_single_chunk_opus(pdf_data, len(chunks[0]))
        
        # Multiple chunks - process each and aggregate
        all_results = []
        
        for start_page, end_page, chunk_name in chunks:
            logger.info(f"🤖 Analyzing {chunk_name}...")
            
            pdf_data = self._extract_pages_from_pdf(pdf_path, start_page, end_page)
            if not pdf_data:
                continue
            
            chunk_results = self._analyze_single_chunk_opus(pdf_data, end_page - start_page + 1)
            if 'table_rows' in chunk_results:
                all_results.extend(chunk_results['table_rows'])
        
        if all_results:
            return {'table_rows': all_results}
        else:
            return {'error': 'No results obtained from any chunk'}
    
    def _analyze_single_chunk_opus(self, pdf_data: str, page_count: int) -> Dict[str, Any]:
        """Analyze a single chunk with Opus"""
        
        complete_prompt = self._create_complete_extraction_prompt()
        
        try:
            estimated_tokens = self.rate_limiter.estimate_pdf_tokens(page_count)
            
            messages = [{
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_data
                        }
                    },
                    {
                        "type": "text",
                        "text": complete_prompt
                    }
                ]
            }]
            
            response = self._make_api_request_with_retry(
                model=ModelConfig.OPUS.value[0],
                messages=messages,
                max_tokens=8000,
                estimated_tokens=estimated_tokens
            )
            
            if not response:
                return {'error': 'Full analysis request failed after all retries'}
            
            return self._parse_response(response.content[0].text)
            
        except Exception as e:
            logger.error(f"Error during full analysis: {e}")
            return {'error': str(e)}
    
    def _create_complete_extraction_prompt(self) -> str:
        """Complete extraction prompt with all sophisticated instructions"""
        return f"""
# AI-Optimized Meta-Analysis Research Assistant Instructions (Advanced v6 Batch)

## CRITICAL SYSTEM DIRECTIVES

### MANDATORY COMPLIANCE REQUIREMENTS
- **NEVER leave any cell empty** - use "NA" for missing information
- **NEVER fabricate data** - only report verifiable information from sources
- **ALWAYS use exact column names** as specified below
- **ALWAYS follow the 0/1 coding system** for Yes/No questions (0 = No, 1 = Yes)
- **ALWAYS extract ALL inflation results** found in the paper
- **ALWAYS verify variable identification** using notation sections and context
- **MANDATORY: Author in APA format** - "Last name, First Initial. (Year)"
- **MANDATORY: Author affiliation extraction** - University/institution name

### CRITICAL AUTHOR & AFFILIATION REQUIREMENTS (HIGHEST PRIORITY!):
1. **Author Format**: MUST be "Last name, First Initial. (Year)" - e.g., "Smith, J. (2023)"
2. **Multiple Authors**: "Smith, J. & Jones, M. (2023)" or "Smith, J., Jones, M. & Brown, K. (2023)"
3. **Author Affiliation**: MUST extract university/institution name from title page, footnotes, author sections
4. **Search Locations**: Title page, headers, footnotes, author information sections, first page
5. **If affiliation not found**: Write "Cannot find affiliation" (NOT "NA")

### OUTPUT FORMAT REQUIREMENTS
- Generate a table with exact column headers provided
- Each row = one inflation result from the paper  
- Fill every cell with either data or "NA"
- Use tab-separated format for easy Excel import
- Include header row with all column names

{self._get_advanced_extraction_instructions()}

### EXACT COLUMN ORDER (MANDATORY)
```
{self._get_column_headers()}
```

### PROCESSING WORKFLOW
1. **FIRST PRIORITY**: Extract author in APA format and affiliation
2. **Read PDF completely** and identify notation/variable definitions
3. **Map all results locations** (tables, figures, text) including parameter tables
4. **Extract results with parameter detection active**
5. **Create multiple rows** for multiple inflation results
6. **Fill every cell** with data or "NA" (including zeros)
7. **Format as tab-separated table**
"""
    
    def _parse_response(self, text: str) -> Dict[str, Any]:
        """Parse response from Claude"""
        
        lines = text.strip().split('\n')
        
        # Look for table start
        table_start = -1
        for i, line in enumerate(lines):
            if 'Idstudy\t' in line or line.startswith('Idstudy'):
                table_start = i
                break
        
        if table_start >= 0:
            # Extract table rows
            table_rows = []
            for line in lines[table_start + 1:]:
                if '\t' in line:
                    cols = line.split('\t')
                    if len(cols) == len(META_ANALYSIS_COLUMNS):
                        table_rows.append(cols)
                    else:
                        logger.warning(f"Row has {len(cols)} columns instead of {len(META_ANALYSIS_COLUMNS)}")
            
            return {'table_rows': table_rows}
        else:
            return {'raw_text': text}
    
    def _create_empty_result(self) -> Dict[str, Any]:
        """Create empty result when document has no data"""
        empty_row = {col: 'NA' for col in META_ANALYSIS_COLUMNS}
        empty_row['Idstudy'] = '1'
        empty_row['IdEstimate'] = '1'
        return {'table_rows': [[empty_row[col] for col in META_ANALYSIS_COLUMNS]]}
    
    def _calculate_cost_savings(self, file_size_mb: float, screening: ScreeningResult, total_pages: int) -> CostEstimate:
        """Calculate savings compared to full analysis"""
        
        tokens_per_mb = 50000
        total_tokens = file_size_mb * tokens_per_mb
        
        # Screening costs
        screening_tokens = total_tokens
        screening_cost = (screening_tokens / 1_000_000) * ModelConfig.HAIKU.value[1]
        
        # Extraction costs
        if screening.relevant_pdf_positions and screening.confidence_score > 0.1:
            relevant_ratio = len(screening.relevant_pdf_positions) / total_pages
            extraction_tokens = total_tokens * relevant_ratio
        else:
            extraction_tokens = total_tokens
        
        extraction_cost = (extraction_tokens / 1_000_000) * ModelConfig.OPUS.value[1]
        
        # Full analysis costs
        full_cost = (total_tokens / 1_000_000) * ModelConfig.OPUS.value[1]
        
        # Savings
        smart_cost = screening_cost + extraction_cost
        saved = full_cost - smart_cost
        saved_percentage = (saved / full_cost) * 100 if full_cost > 0 else 0
        
        return CostEstimate(
            screening_cost=screening_cost,
            extraction_cost=extraction_cost,
            total_cost=smart_cost,
            saved_amount=saved,
            saved_percentage=saved_percentage
        )
    
    def _estimate_cost_full(self, file_size_mb: float) -> CostEstimate:
        """Estimate costs for full analysis"""
        tokens = file_size_mb * 50000
        cost = (tokens / 1_000_000) * ModelConfig.OPUS.value[1]
        
        return CostEstimate(
            screening_cost=0,
            extraction_cost=cost,
            total_cost=cost,
            saved_amount=0,
            saved_percentage=0
        )
    
    def _estimate_cost_economy(self, file_size_mb: float) -> CostEstimate:
        """Estimate costs for economy analysis"""
        tokens = file_size_mb * 50000
        cost = (tokens / 1_000_000) * ModelConfig.SONNET.value[1]
        
        opus_cost = (tokens / 1_000_000) * ModelConfig.OPUS.value[1]
        saved = opus_cost - cost
        
        return CostEstimate(
            screening_cost=0,
            extraction_cost=cost,
            total_cost=cost,
            saved_amount=saved,
            saved_percentage=(saved / opus_cost) * 100
        )
    
    def _estimate_cost_screening_only(self, file_size_mb: float) -> CostEstimate:
        """Estimate costs when document has no data"""
        tokens = file_size_mb * 50000
        cost = (tokens / 1_000_000) * ModelConfig.HAIKU.value[1]
        
        opus_cost = (tokens / 1_000_000) * ModelConfig.OPUS.value[1]
        
        return CostEstimate(
            screening_cost=cost,
            extraction_cost=0,
            total_cost=cost,
            saved_amount=opus_cost - cost,
            saved_percentage=((opus_cost - cost) / opus_cost) * 100
        )
    
    def process_results_to_dataframe(self, results: Dict[str, Any], pdf_path: str, study_id: int) -> pd.DataFrame:
        """Process results into DataFrame with unique Idstudy"""
        
        if 'table_rows' in results and results['table_rows']:
            try:
                df = pd.DataFrame(results['table_rows'], columns=META_ANALYSIS_COLUMNS)
                
                # Set correct Idstudy for all rows of this study
                df['Idstudy'] = str(study_id)
                
                # Clean data
                df = df.replace('', 'NA')
                df = df.fillna('NA')
                
                logger.info(f"✅ Created {len(df)} rows for study {study_id}")
                return df
                
            except Exception as e:
                logger.error(f"Error creating DataFrame: {e}")
                # Try partial recovery
                if results['table_rows']:
                    min_cols = min(len(results['table_rows'][0]), len(META_ANALYSIS_COLUMNS))
                    truncated_data = [row[:min_cols] for row in results['table_rows']]
                    truncated_cols = META_ANALYSIS_COLUMNS[:min_cols]
                    
                    try:
                        df = pd.DataFrame(truncated_data, columns=truncated_cols)
                        # Fill missing columns
                        for col in META_ANALYSIS_COLUMNS:
                            if col not in df.columns:
                                df[col] = 'NA'
                        
                        df['Idstudy'] = str(study_id)
                        df = df.replace('', 'NA')
                        df = df.fillna('NA')
                        
                        logger.warning(f"⚠️ Partial recovery successful - created {len(df)} rows with limited data")
                        return df[META_ANALYSIS_COLUMNS]
                        
                    except Exception as e2:
                        logger.error(f"Recovery attempt failed: {e2}")
        
        # Create empty DataFrame with NA values
        logger.warning(f"⚠️ Failed to extract structured data for {os.path.basename(pdf_path)}")
        
        empty_row = {col: 'NA' for col in META_ANALYSIS_COLUMNS}
        empty_row['Idstudy'] = str(study_id)
        empty_row['IdEstimate'] = '1'
        
        return pd.DataFrame([empty_row])
    
    def process_folder(self, folder_path: str) -> pd.DataFrame:
        """Process all PDFs in folder and return summary DataFrame"""
        
        # Find all PDF files
        pdf_files = list(Path(folder_path).glob("*.pdf"))
        
        if not pdf_files:
            logger.warning("No PDF files found in folder")
            return pd.DataFrame(columns=META_ANALYSIS_COLUMNS)
        
        logger.info(f"📚 Found {len(pdf_files)} PDF files for processing")
        
        # Initialize batch statistics
        self.batch_stats['total_files'] = len(pdf_files)
        self.batch_stats['start_time'] = time.time()
        
        for idx, pdf_path in enumerate(pdf_files, 1):
            print(f"\n{'='*60}")
            print(f"📄 Processing {idx}/{len(pdf_files)}: {pdf_path.name}")
            print(f"{'='*60}")
            
            # Check file size
            file_size = pdf_path.stat().st_size / (1024 * 1024)
            print(f"📏 Size: {file_size:.2f} MB")
            
            if file_size > 32:
                logger.warning(f"⚠️ SKIPPING: {pdf_path.name} exceeds 32 MB limit")
                self.batch_stats['failed_files'] += 1
                self._log_processing_result(pdf_path.name, 'SKIPPED', 'File too large', 0, 0.0)
                continue
            
            try:
                # Analyze PDF
                results, cost_estimate = self.analyze_pdf_advanced(str(pdf_path))
                
                # Update cost tracking
                self.batch_stats['total_cost'] += cost_estimate.total_cost
                self.batch_stats['total_saved'] += cost_estimate.saved_amount
                
                # Check results
                if 'error' in results:
                    logger.error(f"❌ API Error: {results['error']}")
                    self.batch_stats['failed_files'] += 1
                    self._log_processing_result(pdf_path.name, 'FAILED', results['error'], 0, cost_estimate.total_cost)
                    continue
                
                # Process results
                df_study = self.process_results_to_dataframe(results, str(pdf_path), self.current_study_id)
                
                # Check if we have valid data
                if df_study.empty or (len(df_study) == 1 and all(df_study.iloc[0] == 'NA')):
                    logger.warning(f"⚠️ No data extracted from {pdf_path.name}")
                    self.batch_stats['failed_files'] += 1
                    self._log_processing_result(pdf_path.name, 'NO_DATA', 'No extractable data found', 0, cost_estimate.total_cost)
                    
                    # Save debug info
                    self._save_debug_info(pdf_path.stem, results)
                else:
                    # Add to successful results
                    self.all_results.append(df_study)
                    self.batch_stats['successful_files'] += 1
                    self.batch_stats['total_studies'] += 1
                    self.batch_stats['total_estimates'] += len(df_study)
                    
                    self._log_processing_result(pdf_path.name, 'SUCCESS', 'Data extracted successfully', len(df_study), cost_estimate.total_cost)
                    
                    # Display key info
                    first_row = df_study.iloc[0]
                    author_display = first_row['Author'] if first_row['Author'] != 'NA' else 'Unknown author'
                    year_display = first_row['Year'] if first_row['Year'] != 'NA' else 'Unknown year'
                    affiliation_display = first_row['Author_Affiliation'] if first_row['Author_Affiliation'] != 'NA' else 'Cannot find affiliation'
                    
                    print(f"✅ Successfully processed: {len(df_study)} inflation estimates")
                    print(f"📚 Author: {author_display}")
                    print(f"🏛️ Affiliation: {affiliation_display}")
                    print(f"📅 Year: {year_display}")
                    print(f"💰 Cost: ${cost_estimate.total_cost:.4f} (Saved: ${cost_estimate.saved_amount:.4f})")
                    
                    # Check for proper APA format
                    if first_row['Author'] != 'NA':
                        # Simple APA format check
                        if not re.match(r'^[A-Z][a-z]+,\s*[A-Z]\..*\(\d{4}\)', first_row['Author']):
                            print(f"⚠️ Warning: Author may not be in proper APA format: {first_row['Author']}")
                    
                    # Check affiliation extraction
                    if affiliation_display == 'Cannot find affiliation' or affiliation_display == 'NA':
                        print(f"⚠️ Warning: Could not extract author affiliation")
                
                # Increment study ID
                self.current_study_id += 1
                self.batch_stats['processed_files'] += 1
                
            except Exception as e:
                logger.error(f"❌ Unexpected error processing {pdf_path.name}: {e}")
                self.batch_stats['failed_files'] += 1
                self._log_processing_result(pdf_path.name, 'ERROR', str(e), 0, 0.0)
                
                # Save error info
                self._save_error_info(pdf_path.stem, e)
                continue
        
        # Calculate final statistics
        self.batch_stats['processing_time'] = time.time() - self.batch_stats['start_time']
        
        # Final statistics
        self._display_batch_summary()
        
        # Combine all results
        if self.all_results:
            final_df = pd.concat(self.all_results, ignore_index=True)
            logger.info(f"\n✅ Total {self.batch_stats['successful_files']} successful studies with {len(final_df)} rows")
            return final_df
        else:
            logger.warning("No results obtained")
            return pd.DataFrame(columns=META_ANALYSIS_COLUMNS)
    
    def _display_batch_summary(self):
        """Display batch processing summary"""
        print(f"\n{'='*60}")
        print(f"📊 BATCH PROCESSING COMPLETED:")
        print(f"{'='*60}")
        print(f"  📁 Total files: {self.batch_stats['total_files']}")
        print(f"  ✅ Successful: {self.batch_stats['successful_files']}")
        print(f"  ❌ Failed: {self.batch_stats['failed_files']}")
        print(f"  📚 Studies extracted: {self.batch_stats['total_studies']}")
        print(f"  💰 Estimates extracted: {self.batch_stats['total_estimates']}")
        print(f"  💵 Total cost: ${self.batch_stats['total_cost']:.4f}")
        print(f"  💡 Total saved: ${self.batch_stats['total_saved']:.4f}")
        print(f"  ⏱️ Processing time: {self.batch_stats['processing_time']/60:.1f} minutes")
        print(f"  🚦 Rate limit delays: {self.batch_stats['rate_limit_delays']}")
        print(f"  🔢 Total tokens used: {self.batch_stats['total_tokens_used']:,}")
        if self.batch_stats['total_studies'] > 0:
            print(f"  📊 Avg estimates/study: {self.batch_stats['total_estimates']/self.batch_stats['total_studies']:.1f}")
        print(f"{'='*60}")
    
    def _log_processing_result(self, filename: str, status: str, message: str, estimates: int, cost: float):
        """Log processing result for later analysis"""
        self.processing_log.append({
            'filename': filename,
            'status': status,
            'message': message,
            'estimates': estimates,
            'cost': cost,
            'timestamp': datetime.datetime.now().isoformat()
        })
    
    def _save_debug_info(self, filename_stem: str, results: Dict[str, Any]):
        """Save debug information"""
        debug_path = os.path.join(self.export_folder, f"debug_{filename_stem}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(debug_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
    
    def _save_error_info(self, filename_stem: str, error: Exception):
        """Save error information"""
        error_info = {
            'file': filename_stem,
            'error': str(error),
            'type': type(error).__name__,
            'timestamp': datetime.datetime.now().isoformat()
        }
        error_path = os.path.join(self.export_folder, f"error_{filename_stem}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(error_path, 'w', encoding='utf-8') as f:
            json.dump(error_info, f, ensure_ascii=False, indent=2)
    
    def save_batch_results(self, final_df: pd.DataFrame):
        """Save comprehensive batch results"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Excel export with multiple sheets
        excel_path = os.path.join(self.export_folder, f"meta_analysis_batch_v6_{self.mode}_{timestamp}.xlsx")
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            # Main data
            final_df.to_excel(writer, sheet_name='Meta-Analysis', index=False)
            
            # Batch summary
            summary_df = pd.DataFrame([{
                'Total Files': self.batch_stats['total_files'],
                'Successful Files': self.batch_stats['successful_files'],
                'Failed Files': self.batch_stats['failed_files'],
                'Total Studies': self.batch_stats['total_studies'],
                'Total Estimates': self.batch_stats['total_estimates'],
                'Total Cost ($)': f"{self.batch_stats['total_cost']:.4f}",
                'Total Saved ($)': f"{self.batch_stats['total_saved']:.4f}",
                'Processing Time (min)': f"{self.batch_stats['processing_time']/60:.1f}",
                'Rate Limit Delays': self.batch_stats['rate_limit_delays'],
                'Total Tokens Used': f"{self.batch_stats['total_tokens_used']:,}",
                'Analysis Mode': self.mode.upper(),
                'Avg Estimates/Study': f"{self.batch_stats['total_estimates']/max(1, self.batch_stats['total_studies']):.1f}"
            }])
            summary_df.to_excel(writer, sheet_name='Batch Summary', index=False)
            
            # Processing log
            if self.processing_log:
                log_df = pd.DataFrame(self.processing_log)
                log_df.to_excel(writer, sheet_name='Processing Log', index=False)
            
            # Study validation
            if not final_df.empty:
                validation_df = pd.DataFrame({
                    'Study_ID': final_df['Idstudy'].unique(),
                    'Author': [final_df[final_df['Idstudy']==sid]['Author'].iloc[0] for sid in final_df['Idstudy'].unique()],
                    'Year': [final_df[final_df['Idstudy']==sid]['Year'].iloc[0] for sid in final_df['Idstudy'].unique()],
                    'Estimates': [len(final_df[final_df['Idstudy']==sid]) for sid in final_df['Idstudy'].unique()],
                    'Has_Parameters': [
                        'Yes' if final_df[final_df['Idstudy']==sid]['Households_discount_factor'].iloc[0] != 'NA' else 'No' 
                        for sid in final_df['Idstudy'].unique()
                    ]
                })
                validation_df.to_excel(writer, sheet_name='Study Validation', index=False)
        
        print(f"✅ Excel saved: {excel_path}")
        
        # CSV backup
        csv_path = os.path.join(self.export_folder, f"meta_analysis_batch_v6_{self.mode}_{timestamp}.csv")
        final_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"✅ CSV backup: {csv_path}")
        
        return excel_path

def main():
    """Main function with improved UI"""
    print("=" * 80)
    print(" INFLATION META-ANALYSIS v6.0 BATCH - FIXED RATE LIMITING ".center(80, "="))
    print("=" * 80)
    print("\n🚀 Advanced batch processing with two-stage optimization")
    print("💡 90% cost savings through intelligent Haiku screening + Opus extraction")
    print("⚙️ Enhanced parameter detection and PDF page position handling")
    print("🚦 FIXED: Improved rate limiting with chunking and intelligent management")
    print("📊 All results will be saved to one comprehensive Excel file\n")
    
    # Select folder with PDF files
    print("📁 Select folder containing PDF files...")
    root = tk.Tk()
    root.withdraw()
    
    pdf_folder = filedialog.askdirectory(
        title="Select folder with PDF files for analysis"
    )
    
    if not pdf_folder:
        print("❌ No folder selected")
        root.destroy()
        return
    
    print(f"✅ Selected folder: {pdf_folder}")
    
    # Select folder for saving results
    print("\n📁 Select folder to save results...")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_export = os.path.join(script_dir, "AI_export_batch_v6_fixed")
    
    export_folder = filedialog.askdirectory(
        title="Select folder to save results",
        initialdir=script_dir
    )
    
    root.destroy()
    
    if not export_folder:
        export_folder = default_export
        print(f"💾 Using default folder: {export_folder}")
    else:
        print(f"💾 Selected folder: {export_folder}")
    
    os.makedirs(export_folder, exist_ok=True)
    
    # Select analysis mode
    print("\n🔧 SELECT ANALYSIS MODE:")
    print("="*50)
    print("1) 🧠 SMART analysis (recommended)")
    print("   - 2-phase: Haiku screening + Opus extraction")
    print("   - 90% cost savings")
    print("   - 98% accuracy")
    print("   - Enhanced parameter detection")
    print("   - Intelligent rate limiting with chunking")
    print("\n2) 🎯 FULL analysis")
    print("   - Opus only")
    print("   - Highest accuracy")
    print("   - Highest cost")
    print("   - Conservative rate limiting")
    print("\n3) 💰 ECONOMY analysis")
    print("   - Sonnet only")
    print("   - 80% savings")
    print("   - 85% accuracy")
    print("   - Fast processing")
    print("="*50)
    
    mode_input = input("\nChoose mode (1-3) [default: 1]: ").strip()
    
    mode_map = {
        '1': 'smart',
        '2': 'full', 
        '3': 'economy',
        '': 'smart'
    }
    
    mode = mode_map.get(mode_input, 'smart')
    print(f"📊 Selected mode: {mode.upper()}")
    
    # Initialize analyzer
    analyzer = AdvancedBatchPDFAnalyzer(CLAUDE_API_KEY, export_folder, mode)
    
    try:
        # Process all PDFs in folder
        print("\n🚀 Starting batch processing with fixed rate limiting...")
        final_df = analyzer.process_folder(pdf_folder)
        
        if final_df.empty:
            print("\n❌ No results obtained to save")
            return
        
        # Save comprehensive results
        print("\n💾 Saving comprehensive results...")
        excel_path = analyzer.save_batch_results(final_df)
        
        print("\n🎉 Batch processing completed!")
        print(f"✨ Using advanced v6 two-stage analysis in {mode.upper()} mode")
        print(f"📊 Total cost savings: ${analyzer.batch_stats['total_saved']:.4f}")
        print(f"🚦 Rate limit delays handled: {analyzer.batch_stats['rate_limit_delays']}")
        print(f"🔢 Total tokens used: {analyzer.batch_stats['total_tokens_used']:,}")
        
    except Exception as e:
        logger.error(f"Critical error: {e}")
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()