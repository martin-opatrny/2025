#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
INFLATION_META_ANALYSIS_v8_new_structure.py
Nová struktura dokumentů pro optimální extrakci dat
"""

import logging
import sys
import os
import tkinter as tk
from tkinter import filedialog
import pandas as pd
import PyPDF2
import anthropic
import datetime
import time
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
import hashlib
import json
import pickle
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
from dataclasses import dataclass
from collections import defaultdict

# Nastavení loggingu
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Načtení konfigurace
try:
    from config import CLAUDE_API_KEY, SCOPUS_API_KEY, CLAUDE_MODEL
except ImportError:
    logger.error("❌ Chyba: Soubor config.py nebyl nalezen!")
    print("Vytvořte soubor config.py s:")
    print("CLAUDE_API_KEY = 'your_api_key_here'")
    print("SCOPUS_API_KEY = 'your_scopus_key_here'")
    print("CLAUDE_MODEL = 'claude-opus-4-20250514'  # Claude 4 Opus")
    sys.exit(1)

# Definice sloupců
META_ANALYSIS_COLUMNS = [
    "Idstudy", "IdEstimate", "Author", "Author_Affiliation", "DOI", "Journal_Name", 
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

# EMBEDDED PROMPTS - Nová struktura
DOCUMENT_0_PROMPT = """
# Document 0: Inflation Results Pre-Scanner

## PURPOSE
This document performs a rapid scan to count the total number of inflation results in the paper. This provides an INITIAL ESTIMATE for subsequent documents, but Document 3's detailed extraction takes precedence if counts differ.

## CRITICAL DIRECTIVE
- **ONLY count inflation results** - do not extract any other information
- **Be exhaustive** - scan ALL tables, figures, and text sections
- **Report one number** - the estimated count of distinct inflation results
- **This is a MINIMUM count** - Document 3 may find additional results during detailed extraction

## SCANNING PROTOCOL

### 1. Identify Inflation Variables
Look for these notations and terms:
- **Symbols**: π, π*, πe, π̄, phi, φ, Π, π^*, π_t, π^opt
- **Expected values**: E[π], E(π), 𝔼[π], E_t[π]
- **Labels**: "inflation", "inflation rate", "optimal inflation", "steady-state inflation"
- **DO NOT count**: V[π], Var[π], σ²(π), SD[π], σ(π) (these are variances/standard deviations)

### 2. Scan All Locations
Check these locations in order:
1. **Main text tables** (Table 1, 2, 3, etc.)
2. **Figures** with numerical values
3. **Text sections** with inline results
4. **Appendices** (including online appendices)
5. **Footnotes** with numerical results

### 3. Counting Rules
- Each distinct inflation value = 1 result
- Same value in different scenarios = separate results
- Multiple columns in same table row = count each if they represent different scenarios
- Ranges (e.g., "-2% to 0%") = count endpoints separately if they represent different cases

### 4. Output Format
State clearly: "This paper contains AT LEAST [X] distinct inflation results. Document 3 will perform detailed extraction and may find additional results."

## VALIDATION NOTE
If Document 3 finds more results during detailed extraction, Document 3's count is authoritative. This pre-scan provides a minimum baseline to help subsequent documents prepare.

## EXAMPLES
- Table with 5 rows, each showing optimal inflation under different parameters = 5 results
- Figure comparing 3 different model specifications = 3 results  
- Text mentioning "baseline inflation of 2% and robustness check of 0%" = 2 results


DOCUMENT_1_PROMPT = """
# Document 1: Metadata & Study Identification Instructions

## TASK OVERVIEW
Extract data from academic PDF articles for meta-analysis dataset creation. Process the attached PDF systematically using the numbered questions below. Each question corresponds to a specific Excel column.

## CRITICAL SYSTEM DIRECTIVES

### MANDATORY COMPLIANCE REQUIREMENTS
- **NEVER leave any cell empty** - use "NA" for missing information  
- **NEVER fabricate data** - only report verifiable information from sources
- **ALWAYS use exact column names** as specified in the complete output format
- **ALWAYS fill only assigned columns** - use "NA" for all other columns

### OUTPUT FORMAT REQUIREMENTS
- Generate a table with ALL 47 column headers (complete list at end of document)
- Fill ONLY the columns specified in this document
- Mark all other columns as "NA"
- Use tab-separated format for easy Excel import
- Include header row with all column names

## COMPLETE COLUMN LIST (47 COLUMNS)
```
Idstudy	IdEstimate	Author	Author_Affiliation	DOI	Journal_Name	Num_Citations	Year	Base_Model_Type	Augmented_base_model	Augmentation_Description	Ramsey_Rule	HH_Included	Firms_Included	Banks_Included	Government_Included	HH_Maximization_Type	HH_Maximized_Vars	Producer_Type	Producer_Assumption	Other_Agent_Included	Other_Agent_Assumptions	Empirical_Research	Country	Flexible_Price_Assumption	Exogenous_Inflation	Households_discount_factor	Consumption_curvature_parameter	Disutility_of_labor	Inverse_of_labor_supply_elasticity	Money_curvature_parameter	Loan_to_value_ratio	Labor_share_of_output	Depositors_discount_factor	Price_adjustment_cost	Elasticity_of_substitution_between_goods	AR1_coefficient_of_TFP	Std_dev_to_TFP_shock	Zero_Lower_Bound	Results_Table	Results_Inflation	Results_Inflation_Assumption	Preferred_Estimate	Reason_for_Preferred	Std_Dev_Inflation	Interest_Rate	Impact_Factor
```

## DOCUMENT 1 ASSIGNED COLUMNS
This document extracts the following columns:
- Idstudy
- Author
- Author_Affiliation
- DOI
- Journal_Name
- Num_Citations
- Year
- Base_Model_Type
- Country
- Impact_Factor

All other columns must be filled with "NA".

## EXTRACTION INSTRUCTIONS

### 1. STUDY IDENTIFICATION
**Task 6.1 - Study ID**
- **Column**: `Idstudy`
- **Task**: Assign sequential study ID
- **Format**: Integer starting from 1
- **Note**: Same ID for all rows from same paper

### 2. AUTHOR INFORMATION
**Task 1.1 - Author Names**
- **Column**: `Author`
- **Task**: Extract author names in APA format
- **Format**: Last name, First Initial. (Year). Example: "Smith, J. (2023)"
- **Source**: PDF article header/title page
- **Output**: Text string

**Task 1.2 - Author Affiliations**
- **Column**: `Author_Affiliation`
- **Task**: Find author institutional affiliations
- **Process**: Check PDF title page, footnotes, and author information sections
- **Format**: Institution name only, comma-separated for multiple authors
- **If not found**: Write "Cannot find affiliation"

**Task 1.3 - DOI**
- **Column**: `DOI`
- **Task**: Extract DOI (Digital Object Identifier)
- **Process**: 
  1. Search throughout entire PDF for DOI pattern
  2. Look for "DOI:", "doi:", "https://doi.org/", "http://dx.doi.org/"
  3. Check title page, first page, abstract, references
  4. DOI format: 10.xxxx/xxxxx
- **Format**: Full DOI including "10." prefix
- **If not found**: Write "Cannot find DOI"

### 3. JOURNAL INFORMATION
**Task 2.1 - Journal Name**
- **Column**: `Journal_Name`
- **Task**: Extract journal name
- **Source**: PDF header, first page, or citation info
- **Format**: Exact journal name as appears in PDF
- **If not found**: "Cannot find journal name"

**Task 2.2 - Impact Factor**
- **Column**: `Impact_Factor`
- **Task**: External API will provide impact factor
- **Format**: Leave as "NA" - will be filled externally

### 4. CITATION INFORMATION
**Task 3.1 - Citation Count**
- **Column**: `Num_Citations`
- **Task**: Count citation numbers using Scopus API
- **Source**: Scopus Abstract Citations Count API
- **Process**: 
  1. Use DOI from task 1.3
  2. Call Scopus API with DOI
  3. Extract citation count from response
- **Format**: Number only
- **If not found**: "Cannot find citation count"

### 5. PUBLICATION DATE
**Task 4.1 - Publication Year**
- **Column**: `Year`
- **Task**: Extract publication year
- **Source**: Search throughout entire PDF - title page, header, footer, reference section, journal information, copyright notice
- **Process**: 
  1. Check title page first
  2. Check headers/footers on multiple pages
  3. Check reference section
  4. Check journal citation format anywhere in document
- **Format**: 4-digit year only

### 6. MODEL INFORMATION
**Task 5.1 - Base Model Type**
- **Column**: `Base_Model_Type`
- **Task**: Identify base economic model type
- **Examples**: "DSGE", "New Keynesian", "RBC", "VAR", "OLG", "Cash-in-advance"
- **Source**: PDF abstract, introduction, or methodology section

**Task 5.16 - Country**
- **Column**: `Country`
- **Task**: Identify country/region of data used
- **Process**: Look for calibration data, empirical data sources, parameter values "calibrated to X economy"
- **Examples**: "US", "Euro Area", "UK", "Japan"
- **If none specified**: "NA"

## VALIDATION CHECKLIST

### Pre-Extraction:
- [ ] Located title page and author information
- [ ] Found journal name and year
- [ ] Identified abstract and introduction

### During Extraction:
- [ ] Checked multiple locations for DOI
- [ ] Verified year format (4 digits)
- [ ] Identified base model type from methodology

### Post-Extraction:
- [ ] All assigned columns have values or appropriate "Cannot find" messages
- [ ] All non-assigned columns marked as "NA"
- [ ] Study ID assigned

## OUTPUT EXAMPLE
```
Idstudy  IdEstimate  Author  Author_Affiliation  DOI  Journal_Name  Num_Citations  Year  Base_Model_Type	Augmented_base_model	Augmentation_Description	Ramsey_Rule	HH_Included	Firms_Included	Banks_Included	Government_Included	HH_Maximization_Type	HH_Maximized_Vars	Producer_Type	Producer_Assumption	Other_Agent_Included	Other_Agent_Assumptions	Empirical_Research	Country	Flexible_Price_Assumption	Exogenous_Inflation	Households_discount_factor	Consumption_curvature_parameter	Disutility_of_labor	Inverse_of_labor_supply_elasticity	Money_curvature_parameter	Loan_to_value_ratio	Labor_share_of_output	Depositors_discount_factor	Price_adjustment_cost	Elasticity_of_substitution_between_goods	AR1_coefficient_of_TFP	Std_dev_to_TFP_shock	Zero_Lower_Bound	Results_Table	Results_Inflation	Results_Inflation_Assumption	Preferred_Estimate	Reason_for_Preferred	Std_Dev_Inflation	Interest_Rate	Impact_Factor
1  NA  Smith, J. (2023)  MIT  10.1234/example  Journal of Monetary Economics  45	2023	DSGE	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	US	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA
```
"""

DOCUMENT_2_PROMPT = """
# Document 2: Model Structure & Assumptions Instructions

## CRITICAL SYSTEM DIRECTIVES

### MANDATORY COMPLIANCE REQUIREMENTS
- **NEVER leave any cell empty** - use "NA" for missing information
- **NEVER fabricate data** - only report verifiable information from sources
- **ALWAYS use exact column names** as specified in the complete output format
- **ALWAYS follow the 0/1 coding system** for Yes/No questions (0 = No, 1 = Yes)
- **ALWAYS fill only assigned columns** - use "NA" for all other columns
- **CREATE ONLY ONE ROW PER STUDY** - this document extracts study-level information only

### OUTPUT FORMAT REQUIREMENTS
- Generate a table with ALL 47 column headers (complete list below)
- Fill ONLY the columns specified in this document
- Mark all other columns as "NA"
- Use tab-separated format for easy Excel import
- Include header row with all column names
- **Output exactly ONE row representing the entire study**

## COMPLETE COLUMN LIST (47 COLUMNS)
Idstudy	IdEstimate	Author	Author_Affiliation	DOI	Journal_Name	Num_Citations	Year	Base_Model_Type	Augmented_base_model	Augmentation_Description	Ramsey_Rule	HH_Included	Firms_Included	Banks_Included	Government_Included	HH_Maximization_Type	HH_Maximized_Vars	Producer_Type	Producer_Assumption	Other_Agent_Included	Other_Agent_Assumptions	Empirical_Research	Country	Flexible_Price_Assumption	Exogenous_Inflation	Households_discount_factor	Consumption_curvature_parameter	Disutility_of_labor	Inverse_of_labor_supply_elasticity	Money_curvature_parameter	Loan_to_value_ratio	Labor_share_of_output	Depositors_discount_factor	Price_adjustment_cost	Elasticity_of_substitution_between_goods	AR1_coefficient_of_TFP	Std_dev_to_TFP_shock	Zero_Lower_Bound	Results_Table	Results_Inflation	Results_Inflation_Assumption	Preferred_Estimate	Reason_for_Preferred	Std_Dev_Inflation	Interest_Rate	Impact_Factor

## DOCUMENT 2 ASSIGNED COLUMNS
This document extracts the following study-level columns:
- Idstudy (use value from Document 0's count)
- Augmented_base_model
- Augmentation_Description
- Ramsey_Rule
- HH_Included
- Firms_Included
- Banks_Included
- Government_Included
- HH_Maximization_Type
- HH_Maximized_Vars
- Producer_Type
- Producer_Assumption
- Other_Agent_Included
- Other_Agent_Assumptions
- Empirical_Research

All other columns must be filled with "NA".

## EXTRACTION INSTRUCTIONS

### 1. STUDY IDENTIFICATION
- **Column**: `Idstudy`
- **Task**: Use same ID as Document 1 (or assign starting from 1 if working independently)

### 2. MODEL AUGMENTATION
**Task 5.2 - Augmented Model Check**
- **Column**: `Augmented_base_model`
- **Task**: Determine if model has augmentations beyond the standard version
- **Process**: Look for model modifications, extensions, or additions
- **Output**: 1 (Yes) or 0 (No)

**Task 5.3 - Augmentation Description**
- **Column**: `Augmentation_Description`
- **Task**: Describe model augmentations
- **Condition**: Only if Task 5.2 = 1, otherwise "NA"
- **Format**: Brief description (2-5 words)

### 3. RAMSEY RULE IDENTIFICATION
**Task 5.4 - Enhanced Ramsey Rule Identification**
- **Column**: `Ramsey_Rule`
- **Task**: Identify if the model uses a **Ramsey approach** to jointly determine optimal fiscal and monetary policy
- **Core Question**: Does the model find the optimal inflation rate by treating it as one of several **distortionary taxes** used to fund the government, because **lump-sum taxes are unavailable**?
- **Look for (Positive Signals)**:
  - Phrases: "Ramsey taxation", "optimal tax system", "inflation tax", "seigniorage", "public finance approach"
  - Assumptions: An explicit "government budget constraint" must be financed by "distortionary taxes"; the model states that "lump-sum taxes" are NOT available
  - Citations to authors like Phelps, Lucas & Stokey in the context of optimal policy
  - Discussion of inflation as a revenue source for government
  - Joint optimization of fiscal and monetary instruments
- **Rule out if (Negative Signals)**:
  - The model assumes "lump-sum taxes" are available (this usually points to the "Friedman Rule")
  - The central bank minimizes an "ad-hoc" or "quadratic loss function"
- **Output**: 1 (Yes - Ramsey approach) or 0 (No - not Ramsey approach)

### 4. AGENT IDENTIFICATION
**Task 5.5 - Household Agents**
- **Column**: `HH_Included`
- **Task**: Identify household agents in model
- **Search terms**: "household", "consumers", "families", "representative agent"
- **Output**: 1 (Yes) or 0 (No)

**Task 5.6 - Firm/Entrepreneur Agents**
- **Column**: `Firms_Included`
- **Task**: Identify firm/entrepreneur agents
- **Search terms**: "firms", "entrepreneurs", "producers", "companies"
- **Output**: 1 (Yes) or 0 (No)

**Task 5.7 - Banking Sector**
- **Column**: `Banks_Included`
- **Task**: Identify banking sector in model
- **Search terms**: "banks", "financial intermediaries", "banking sector", "credit"
- **Critical**: Re-read carefully if uncertain
- **Output**: 1 (Yes) or 0 (No)

**Task 5.8 - Government Verification**
- **Column**: `Government_Included`
- **Task**: Identify if government plays ACTIVE ROLE in the model
- **CRITICAL VERIFICATION**: Government must be an active model component
- **Evidence of ACTIVE government role**:
  - Government budget constraint equation
  - Government spending (G) in resource constraint
  - Fiscal policy rules or instruments
  - Tax rates that affect equilibrium
  - Government debt dynamics
  - Transfer payments that enter household budget
- **NOT sufficient**: Only mentioning "government" in text or literature review
- **Output**: 1 (Yes - active role) or 0 (No - not in model)

### 5. AGENT CHARACTERISTICS
**Task 5.9 - Household Maximization Type**
- **Column**: `HH_Maximization_Type`
- **Task**: Identify what households maximize
- **Common answers**: "utility", "welfare", "consumption plus leisure", "expected utility"
- **Format**: Short phrase (2-4 words)

**Task 5.10 - Household Maximized Variables**
- **Column**: `HH_Maximized_Vars`
- **Task**: List variables in household optimization
- **Common answers**: "consumption, labor", "consumption, money, leisure"
- **Format**: Comma-separated list

**Task 5.11 - Producer Types**
- **Column**: `Producer_Type`
- **Task**: Identify all firm types in model
- **Examples**: "intermediate goods firms, final goods firms", "wholesale firms, retail firms"
- **Format**: Comma-separated list

**Task 5.12 - Producer Assumptions**
- **Column**: `Producer_Assumption`
- **Task**: Identify market structure assumptions for each firm type
- **Format**: "firm type: assumption" format
- **Example**: "intermediate firms: monopolistic competition, final firms: perfect competition"

**Task 5.13 - Other Agents Check**
- **Column**: `Other_Agent_Included`
- **Task**: Check for other agents beyond households/firms/banks/government
- **Examples**: "labor unions", "central bank", "foreign sector"
- **Output**: 1 (Yes) or 0 (No)

**Task 5.14 - Other Agent Assumptions**
- **Column**: `Other_Agent_Assumptions`
- **Task**: Describe other agents' assumptions
- **Condition**: Only if Task 5.13 = 1, otherwise "NA"

### 6. RESEARCH TYPE
**Task 5.15 - Empirical Research Check**
- **Column**: `Empirical_Research`
- **Task**: Determine if research uses empirical data/estimation
- **Process**: Look if the result is model output using calibration (not empirical) or based on regression analysis/data estimation (empirical)
- **Output**: 1 (Yes) or 0 (No)

## CRITICAL REMINDERS
1. **ONE ROW ONLY** - This document creates ONE row per study
2. **STUDY-LEVEL ONLY** - All information should apply to the entire paper
3. **BINARY VALUES ARE CRITICAL** - always 0 or 1, never blank
4. **RAMSEY RULE REQUIRES FISCAL COMPONENT** - not just "optimal policy"
5. **GOVERNMENT MUST BE ACTIVE** - not just mentioned in text

## OUTPUT EXAMPLE (ONE ROW ONLY)
Idstudy  IdEstimate  Author	Author_Affiliation	DOI	Journal_Name	Num_Citations	Year	Base_Model_Type  Augmented_base_model  Augmentation_Description  Ramsey_Rule	HH_Included  Firms_Included  Banks_Included  Government_Included  HH_Maximization_Type	HH_Maximized_Vars	Producer_Type	Producer_Assumption	Other_Agent_Included	Other_Agent_Assumptions	Empirical_Research	Country	Flexible_Price_Assumption	Exogenous_Inflation	Households_discount_factor	Consumption_curvature_parameter	Disutility_of_labor	Inverse_of_labor_supply_elasticity	Money_curvature_parameter	Loan_to_value_ratio	Labor_share_of_output	Depositors_discount_factor	Price_adjustment_cost	Elasticity_of_substitution_between_goods	AR1_coefficient_of_TFP	Std_dev_to_TFP_shock	Zero_Lower_Bound	Results_Table	Results_Inflation	Results_Inflation_Assumption	Preferred_Estimate	Reason_for_Preferred	Std_Dev_Inflation	Interest_Rate	Impact_Factor
1  NA  NA  NA  NA  NA  NA  NA  NA  1  Financial frictions  0  1  1  1  1  utility	consumption, labor	intermediate firms, final firms	intermediate firms: monopolistic competition, final firms: perfect competition	0  NA  0  NA  NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA
"""

DOCUMENT_3_PROMPT = """
# Document 3: Results & Parameters Instructions (MODIFIED)

## CRITICAL SYSTEM DIRECTIVES

### MANDATORY COMPLIANCE REQUIREMENTS
- **NEVER leave any cell empty** - use "NA" for missing information
- **NEVER fabricate data** - only report verifiable information from sources
- **ALWAYS use exact column names** as specified in the complete output format
- **ALWAYS extract ALL inflation results** from ALL tables, figures, and the whole study (sensitivity analysis or robustness checks as well)
- **ALWAYS verify variable identification** using notation sections and context
- **ALWAYS reset assumptions for each new table** - never carry over structure assumptions
- **ALWAYS preserve numerical signs** - negative values must include minus sign
- **ALWAYS cross-verify results** when similar tables appear
- **ALWAYS fill only assigned columns** - use "NA" for all other columns

### OUTPUT FORMAT REQUIREMENTS
- Generate a table with ALL 47 column headers (complete list below)
- Fill ONLY the columns specified in this document
- Mark all other columns as "NA"
- Each row = one inflation result from the paper
- Use tab-separated format for easy Excel import
- Include header row with all column names
- **Number of rows should match the count from Document 0**

## COMPLETE COLUMN LIST (47 COLUMNS)

Idstudy	IdEstimate	Author	Author_Affiliation	DOI	Journal_Name	Num_Citations	Year	Base_Model_Type	Augmented_base_model	Augmentation_Description	Ramsey_Rule	HH_Included	Firms_Included	Banks_Included	Government_Included	HH_Maximization_Type	HH_Maximized_Vars	Producer_Type	Producer_Assumption	Other_Agent_Included	Other_Agent_Assumptions	Empirical_Research	Country	Flexible_Price_Assumption	Exogenous_Inflation	Households_discount_factor	Consumption_curvature_parameter	Disutility_of_labor	Inverse_of_labor_supply_elasticity	Money_curvature_parameter	Loan_to_value_ratio	Labor_share_of_output	Depositors_discount_factor	Price_adjustment_cost	Elasticity_of_substitution_between_goods	AR1_coefficient_of_TFP	Std_dev_to_TFP_shock	Zero_Lower_Bound	Results_Table	Results_Inflation	Results_Inflation_Assumption	Preferred_Estimate	Reason_for_Preferred	Std_Dev_Inflation	Interest_Rate	Impact_Factor


## DOCUMENT 3 ASSIGNED COLUMNS
This document extracts the following columns:
- Idstudy (copy from Document 1 or assign if working independently)
- IdEstimate
- Flexible_Price_Assumption (MOVED FROM DOCUMENT 2)
- Exogenous_Inflation (MOVED FROM DOCUMENT 2)
- Households_discount_factor through Std_dev_to_TFP_shock (all parameters)
- Zero_Lower_Bound
- Results_Table
- Results_Inflation
- Results_Inflation_Assumption
- Preferred_Estimate
- Reason_for_Preferred
- Std_Dev_Inflation
- Interest_Rate

All other columns must be filled with "NA".

## CRITICAL NOTATION GUIDE (READ FIRST)

### ENHANCED VARIABLE IDENTIFICATION PROTOCOL

**Inflation Variables - Extended Recognition:**
- **Standard notations**: π, π*, πe, π̄, phi, φ, Π, π^*, π_t, π^opt
- **Expected value notation**: E[π], E(π), 𝔼[π], E_t[π] - these ARE inflation values
- **Common labels**: "inflation", "inflation rate", "optimal inflation", "inflation target", "steady-state inflation"
- **Typical range**: -10% to 10% (annualized) - but can be outside this range
- **CRITICAL SIGN PRESERVATION**: 
  - Always check for negative signs (-) before numbers
  - Look for "deflation" which implies negative inflation
  - Check text descriptions: "negative inflation", "below zero"
  - Friedman rule typically implies negative optimal inflation around -4% to -5%
- **WARNING - Verify these carefully**:
  - V[π], Var[π], σ²(π) - likely variance, NOT inflation value
  - SD[π], σ(π) - likely standard deviation
  - Cov[π,x] - covariance, not inflation

**Interest Rate Variables:**
- Common symbols: i, r, R, i*, r*, ī, r̄, i^n (nominal), r^r (real)
- Common labels: "interest rate", "nominal rate", "policy rate", "real rate"
- Typical range: -5% to 20% (annualized)

## EXTRACTION INSTRUCTIONS

### 1. STUDY IDENTIFICATION
- **Column**: `Idstudy`
- **Task**: Use same ID as Document 1 (or assign starting from 1)

- **Column**: `IdEstimate`
- **Task**: Assign sequential estimate ID for each inflation result
- **Format**: Integer starting from 1 for each study

### 2. RESULT-SPECIFIC MODEL ASSUMPTIONS (MOVED FROM DOCUMENT 2)

**Task 5.17 - Price Flexibility (PER RESULT)**
- **Column**: `Flexible_Price_Assumption`
- **Task**: Check price flexibility assumption for THIS SPECIFIC inflation result
- **Process**: 
  1. Identify the scenario/specification for this result
  2. Determine if prices are flexible or sticky in this scenario
  3. Look for: "flexible prices", "sticky prices", "Calvo pricing", "price rigidity"
- **Output**: 1 (flexible prices) or 0 (sticky prices)
- **CRITICAL**: This can vary across results in the same paper

**Task 5.18 - Exogenous Inflation (PER RESULT)**
- **Column**: `Exogenous_Inflation`
- **Task**: Check if inflation is exogenous for THIS SPECIFIC result
- **Process**: 
  1. Determine if inflation is set externally or determined by the model
  2. Look for: "given inflation rate", "inflation target", "exogenous inflation"
- **Output**: 1 (exogenous) or 0 (endogenous)

**Task 5.20 - Zero Lower Bound (PER RESULT)**
- **Column**: `Zero_Lower_Bound`
- **Task**: Check if ZLB constraint applies to THIS SPECIFIC result
- **Process**: Look for explicit mention of ZLB/ELB consideration for this scenario
- **Search terms**: "zero lower bound", "ZLB", "effective lower bound", "ELB"
- **Output**: 1 (Yes - ZLB considered) or 0 (No - no ZLB)

### 3. CRITICAL RESULTS EXTRACTION

**Task 5.21 - COMPREHENSIVE RESULTS MAPPING**
- **Column**: `Results_Table`
- **Task**: Identify source location for THIS SPECIFIC result
- **Format**: "Table 1", "Figure 2", "Text Section 4.2", etc.

**Task 5.22 - CRITICAL INFLATION EXTRACTION**
- **Column**: `Results_Inflation`
- **Task**: Extract the exact inflation value
- **MANDATORY PROTOCOL**:
  1. Preserve exact decimal places
  2. Include negative sign if present
  3. Verify against Document 0's count
- **Format**: Numerical value (e.g., -0.02, 0.00, 0.035)

### 4. RESULT CHARACTERISTICS

**Task 5.24 - Preferred Estimate**
- **Column**: `Preferred_Estimate`
- **Task**: Identify if THIS result is the author's preferred estimate
- **Identifiers**: "baseline", "main specification", "preferred", emphasized in abstract
- **Output**: 1 (preferred) or 0 (not preferred)

**Task 5.25 - Reason for Preferred**
- **Column**: `Reason_for_Preferred`
- **Task**: Explain why estimate is preferred
- **Condition**: Only if preferred (Task 5.24 = 1), otherwise "NA"

**Task 5.26 - Results Assumptions**
- **Column**: `Results_Inflation_Assumption`
- **Task**: Describe the specific scenario/assumptions for THIS result
- **Format**: Brief description
- **Example**: "Baseline with sticky prices", "Flexible prices with ZLB"

**Task 5.39 - Standard Deviation of Inflation**
- **Column**: `Std_Dev_Inflation`
- **Task**: Extract uncertainty measure if provided for THIS result

**Task 5.40 - Interest Rate**
- **Column**: `Interest_Rate`
- **Task**: Extract interest rate corresponding to THIS inflation result

### 5. PARAMETER EXTRACTION (FOR EACH RESULT)

**CRITICAL**: Parameters may vary across results. Extract the specific values used for each result scenario.

**Task 5.27 - Households' discount factor**
- **Column**: `Households_discount_factor`
- **Common symbols**: β, beta, δ
- **Extract value specific to this result's calibration**

**Task 5.28 - Consumption curvature parameter**
- **Column**: `Consumption_curvature_parameter`
- **Common symbols**: σ, gamma, CRRA, IES (as 1/σ)
- **Common values**: 1-4 (risk aversion), 0.25-1 (as IES)
- **Search enhanced**: "risk aversion", "CRRA", "intertemporal elasticity", "curvature"

**Task 5.29 - Disutility of labor**
- **Column**: `Disutility_of_labor`
- **Common symbols**: χ, psi, ψ, xi
- **Context**: Weight on labor/leisure in utility function
- **Search enhanced**: "labor disutility", "labor weight", "preference for leisure"

**Task 5.30 - Inverse of labor supply elasticity**
- **Column**: `Inverse_of_labor_supply_elasticity`
- **Common symbols**: φ, phi, ν, nu, η
- **Common values**: 0.5-5 (Frisch elasticity is 1/φ)
- **Search enhanced**: "Frisch elasticity", "labor supply elasticity", "labor curvature"

**Task 5.31 - Money curvature parameter**
- **Column**: `Money_curvature_parameter`
- **Common symbols**: ξ, xi, ζ, zeta, b
- **Context**: In money-in-utility or cash-in-advance models
- **Note**: Often 0 in cashless New Keynesian models
- **Search enhanced**: "money demand elasticity", "money in utility"

**Task 5.32 - Loan-to-value ratio**
- **Column**: `Loan_to_value_ratio`
- **Common symbols**: LTV, m, θ
- **Common values**: 0.7-0.9
- **Context**: In models with collateral constraints
- **Search enhanced**: "LTV", "collateral requirement", "borrowing constraint"

**Task 5.33 - Labor share of output**
- **Column**: `Labor_share_of_output`
- **Common symbols**: 1-α, labor share, wage share
- **Common values**: 0.6-0.7
- **Search enhanced**: "labor share", "capital share" (then 1-capital share), "Cobb-Douglas"

**Task 5.34 - Depositors' discount factor**
- **Column**: `Depositors_discount_factor`
- **Common symbols**: β_d, beta_d, β_s (savers)
- **Context**: In models with heterogeneous agents
- **Search enhanced**: "patient households", "savers", "depositors"

**Task 5.35 - Price adjustment cost**
- **Column**: `Price_adjustment_cost`
- **Common symbols**: κ, kappa, φ_p, Rotemberg parameter
- **Context**: Rotemberg (1982) quadratic adjustment costs
- **Note**: Different from Calvo parameter
- **Search enhanced**: "price adjustment cost", "Rotemberg", "menu cost"

**Task 5.36 - Elasticity of substitution between goods**
- **Column**: `Elasticity_of_substitution_between_goods`
- **Common symbols**: ε, epsilon, η, theta
- **Common values**: 6-11 (implies markup of 20%-10%)
- **Search enhanced**: "elasticity of substitution", "markup", "market power"

**Task 5.37 - AR(1) coefficient of TFP**
- **Column**: `AR1_coefficient_of_TFP`
- **Common symbols**: ρ_a, rho_a, ρ_z, persistence
- **Common values**: 0.9-0.99
- **Search enhanced**: "TFP persistence", "technology shock", "AR(1)", "autocorrelation"

**Task 5.38 - Standard deviation to TFP shock**
- **Column**: `Std_dev_to_TFP_shock`
- **Common symbols**: σ_a, sigma_a, σ_z, std(a)
- **Common values**: 0.006-0.02
- **Search enhanced**: "TFP volatility", "technology shock", "standard deviation"

### OUTPUT FORMAT REQUIREMENTS
- Generate a table with ALL 47 column headers (complete list below)
- Fill ONLY the columns specified in this document
- Mark all other columns as "NA"
- Each row = one inflation result from the paper
- Use tab-separated format for easy Excel import
- Include header row with all column names
- **FINAL ROW COUNT**: Extract ALL inflation results found. If more results are found than Document 0's estimate, the higher count is correct.

## ROW COUNT RECONCILIATION PROTOCOL

### If Document 3 finds MORE results than Document 0:
- **This is EXPECTED and CORRECT** - Document 3's detailed extraction is more thorough
- Continue extracting ALL results found
- Common reasons:
  - Results mentioned only in text (easy to miss in quick scan)
  - Results in footnotes or appendices
  - Multiple results in complex table structures
  - Results described verbally without clear numerical presentation

### If Document 3 finds FEWER results than Document 0:
- **STOP and RE-EXAMINE** - This suggests missed results
- Re-check all locations mentioned in Document 0
- Look for:
  - Overlooked columns in tables
  - Figures with numerical annotations
  - Text passages with embedded results
  - Different model specifications in same table

### Final Rule:
**The HIGHER count between Document 0 and Document 3 is always correct.** Document 3 should extract every inflation result found, regardless of Document 0's initial estimate.

## EXTRACTION VERIFICATION PROTOCOL

1. **Row Count Verification**: 
   - If row count > Document 0's estimate → Correct (Document 3 is more thorough)
   - If row count < Document 0's estimate → Re-examine the paper
   - Never artificially limit extraction to match Document 0
   
2. **Completeness Check**:
   - Did I check every table mentioned in the paper?
   - Did I check every figure with numbers?
   - Did I check inline text results?
   - Did I check appendices?

## CRITICAL REMINDERS

1. **COMPLETE EXTRACTION IS MANDATORY** - Number of rows must match Document 0
2. **ASSUMPTIONS ARE PER-RESULT** - Check flexibility/ZLB for each result individually
3. **PARAMETERS MAY VARY** - Different calibrations for different results
4. **SIGN PRESERVATION IS CRITICAL** - Verify negative values

## VALIDATION CHECKLIST

### Pre-Extraction:
- [ ] Confirmed total result count from Document 0
- [ ] Located all results sources
- [ ] Identified parameter variations across results

### During Extraction:
- [ ] Checked model assumptions for EACH result
- [ ] Extracted parameters specific to EACH result
- [ ] Preserved exact signs and decimals

### Post-Extraction:
- [ ] Row count matches Document 0
- [ ] Each result has its assumptions properly coded
- [ ] All signs verified

## OUTPUT EXAMPLE (Multiple rows showing variation)

Idstudy	IdEstimate	Author	Author_Affiliation	DOI	Journal_Name	Num_Citations	Year	Base_Model_Type	Augmented_base_model	Augmentation_Description	Ramsey_Rule	HH_Included	Firms_Included	Banks_Included	Government_Included	HH_Maximization_Type	HH_Maximized_Vars	Producer_Type	Producer_Assumption	Other_Agent_Included	Other_Agent_Assumptions	Empirical_Research	Country	Flexible_Price_Assumption	Exogenous_Inflation	Households_discount_factor	Consumption_curvature_parameter	Disutility_of_labor	Inverse_of_labor_supply_elasticity	Money_curvature_parameter	Loan_to_value_ratio	Labor_share_of_output	Depositors_discount_factor	Price_adjustment_cost	Elasticity_of_substitution_between_goods	AR1_coefficient_of_TFP	Std_dev_to_TFP_shock	Zero_Lower_Bound	Results_Table	Results_Inflation	Results_Inflation_Assumption	Preferred_Estimate	Reason_for_Preferred	Std_Dev_Inflation	Interest_Rate	Impact_Factor
1	1	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	1	0	0.99	2	0.5	1	0	NA	0.67	NA	NA	6	0.95	0.007	0	Table 1	-0.045	Baseline with flexible prices	1	Main specification	NA	0.02	NA
1	2	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	0	0	0.99	2	0.5	1	0	NA	0.67	NA	75	6	0.95	0.007	0	Table 1	0.002	Baseline with sticky prices	0	NA	NA	0.04	NA
1	3	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	0	0	0.99	2	0.5	1	0	NA	0.67	NA	75	6	0.95	0.007	1	Table 2	0.000	Sticky prices with ZLB	0	NA	NA	0.04	NA


@dataclass
class CostEstimate:
    """Třída pro sledování nákladů"""
    input_tokens: int = 0
    output_tokens: int = 0
    cache_write_tokens: int = 0
    cache_read_tokens: int = 0
    
    def calculate_cost(self, model: str = "claude-3-opus-20240229") -> float:
        """Vypočítá odhadované náklady v USD"""
        # Aktualizované ceny pro různé modely (v USD za 1M tokenů)
        pricing = {
            "claude-opus-4-20250514": {
                "input": 15.00,    # $15 per 1M input tokens
                "output": 75.00,   # $75 per 1M output tokens
                "cache_write": 3.75,  # 25% z input ceny
                "cache_read": 0.15    # 1% z input ceny
            },
            "claude-3-opus-20240229": {
                "input": 15.00,    # $15 per 1M input tokens
                "output": 75.00,   # $75 per 1M output tokens
                "cache_write": 3.75,  # 25% z input ceny
                "cache_read": 0.15    # 1% z input ceny
            },
            "claude-3-5-sonnet-20241022": {
                "input": 3.00,     # $3 per 1M input tokens
                "output": 15.00,   # $15 per 1M output tokens
                "cache_write": 0.75,  # 25% z input ceny
                "cache_read": 0.03    # 1% z input ceny
            }
        }
        
        # Použijeme průměrné ceny, protože používáme mix modelů
        opus4_ratio = 0.4  # Přibližně 40% volání je Claude 4 Opus (results + fallbacks)
        sonnet_ratio = 0.6  # 60% je Sonnet (pre-scan, metadata, structure)
        
        avg_prices = {
            "input": (pricing["claude-opus-4-20250514"]["input"] * opus4_ratio + 
                     pricing["claude-3-5-sonnet-20241022"]["input"] * sonnet_ratio),
            "output": (pricing["claude-opus-4-20250514"]["output"] * opus4_ratio + 
                      pricing["claude-3-5-sonnet-20241022"]["output"] * sonnet_ratio),
            "cache_write": (pricing["claude-opus-4-20250514"]["cache_write"] * opus4_ratio + 
                           pricing["claude-3-5-sonnet-20241022"]["cache_write"] * sonnet_ratio),
            "cache_read": (pricing["claude-opus-4-20250514"]["cache_read"] * opus4_ratio + 
                          pricing["claude-3-5-sonnet-20241022"]["cache_read"] * sonnet_ratio)
        }
        
        cost = (
            (self.input_tokens / 1_000_000) * avg_prices["input"] +
            (self.output_tokens / 1_000_000) * avg_prices["output"] +
            (self.cache_write_tokens / 1_000_000) * avg_prices["cache_write"] +
            (self.cache_read_tokens / 1_000_000) * avg_prices["cache_read"]
        )
        
        return cost


class OptimizedPDFAnalyzer:
    """Optimalizovaný analyzátor s novou strukturou dokumentů"""
    
    def __init__(self, api_key: str, export_folder: str):
        self.api_key = api_key
        self.export_folder = export_folder
        self.client = anthropic.Anthropic(api_key=api_key)
        self.current_study_id = 1
        
        # Cache složky
        self.cache_dir = Path(export_folder) / "cache"
        self.cache_dir.mkdir(exist_ok=True)
        
        # Statistiky
        self.cost_tracker = CostEstimate()
        self.extraction_stats = defaultdict(int)
        self.document_stats = defaultdict(list)  # Pro sledování všech dokumentů
        self.quality_metrics = defaultdict(list)  # Pro kvalitu extrakce
        
        # Konfigurace modelů - používáme nejlepší pro složité úkoly
        self.model_config = {
            "pre_scan": "claude-3-5-sonnet-20241022",     # Levnější pro jednoduché počítání
            "metadata": "claude-3-5-sonnet-20241022",     # Levnější pro metadata
            "structure": "claude-3-5-sonnet-20241022",    # Levnější pro strukturu
            "results": "claude-opus-4-20250514",          # Claude 4 Opus pro nejsložitější extrakci
            "fallback": "claude-opus-4-20250514"          # Claude 4 Opus jako fallback
        }
        
    def extract_pdf_content_enhanced(self, pdf_path: str) -> Dict[str, Any]:
        """Vylepšená extrakce PDF s preprocessing"""
        logger.info(f"📄 Extrahuji text z PDF: {os.path.basename(pdf_path)}")
        
        # Check cache first
        cache_key = self._get_pdf_cache_key(pdf_path)
        cached_content = self._load_from_cache(cache_key)
        if cached_content:
            logger.info("📦 Načteno z cache")
            return cached_content
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Strukturovaná extrakce
                content = {
                    "full_text": "",
                    "pages": [],
                    "metadata": self._extract_pdf_metadata(pdf_reader),
                    "sections": {}
                }
                
                # Extrakce po stránkách
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    content["pages"].append(page_text)
                    content["full_text"] += page_text + "\n"
                
                # Detekce sekcí
                content["sections"] = self._detect_sections(content["full_text"])
                
                # Extrakce tabulek
                content["tables"] = self._extract_tables(content["full_text"])
                
                # Uložit do cache
                self._save_to_cache(cache_key, content)
                
                logger.info(f"✅ Extrahováno {len(content['full_text'])} znaků z {len(pdf_reader.pages)} stran")
                return content
                
        except Exception as e:
            logger.error(f"❌ Chyba při čtení PDF: {e}")
            return {"full_text": "", "pages": [], "metadata": {}, "sections": {}}
    
    def _extract_pdf_metadata(self, pdf_reader) -> Dict:
        """Extrahuje metadata z PDF"""
        metadata = {}
        try:
            if pdf_reader.metadata:
                metadata = {
                    "title": pdf_reader.metadata.get('/Title', ''),
                    "author": pdf_reader.metadata.get('/Author', ''),
                    "subject": pdf_reader.metadata.get('/Subject', ''),
                    "creation_date": pdf_reader.metadata.get('/CreationDate', '')
                }
        except:
            pass
        return metadata
    
    def _detect_sections(self, text: str) -> Dict[str, str]:
        """Detekuje sekce v textu"""
        sections = {}
        
        # Hledáme běžné sekce
        section_patterns = [
            (r'abstract[:\s]+(.*?)(?=\n[A-Z]|\n\d|$)', 'abstract'),
            (r'introduction[:\s]+(.*?)(?=\n[A-Z]|\n\d|$)', 'introduction'),
            (r'(methodology|methods)[:\s]+(.*?)(?=\n[A-Z]|\n\d|$)', 'methodology'),
            (r'results[:\s]+(.*?)(?=\n[A-Z]|\n\d|$)', 'results'),
            (r'calibration[:\s]+(.*?)(?=\n[A-Z]|\n\d|$)', 'calibration'),
        ]
        
        for pattern, name in section_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                sections[name] = match.group(1)[:2000]  # Limit délky
        
        return sections
    
    def _extract_tables(self, text: str) -> List[str]:
        """Extrahuje potenciální tabulky z textu"""
        tables = []
        
        # Hledáme struktury které vypadají jako tabulky
        lines = text.split('\n')
        potential_table = []
        in_table = False
        
        for line in lines:
            # Detekce začátku tabulky
            if re.search(r'table\s+\d+', line, re.IGNORECASE):
                in_table = True
                potential_table = [line]
            elif in_table:
                # Kontrola jestli řádek vypadá jako součást tabulky
                if re.search(r'\d+\.\d+|\t|  {2,}', line):
                    potential_table.append(line)
                elif len(potential_table) > 3:
                    # Konec tabulky
                    tables.append('\n'.join(potential_table))
                    in_table = False
                    potential_table = []
        
        return tables
    
    def create_optimized_prompts(self, pdf_content: Dict, doc_type: str) -> Tuple[List[Dict], str]:
        """Vytvoří optimalizované prompty s minimální velikostí"""
        
        # Pro různé dokumenty používáme různé části PDF
        if doc_type == "pre_scan":
            # Pro pre-scan potřebujeme celý dokument ale zkrácený
            relevant_text = pdf_content['full_text'][:30000]  # Limit pro rychlost
        elif doc_type == "metadata":
            # Pro metadata stačí prvních pár stran
            relevant_text = '\n'.join(pdf_content['pages'][:5]) if pdf_content['pages'] else pdf_content['full_text'][:10000]
        elif doc_type == "structure":
            # Pro strukturu potřebujeme metodologii
            relevant_text = pdf_content['sections'].get('methodology', '') + '\n' + pdf_content['sections'].get('introduction', '')
            if len(relevant_text) < 1000:
                relevant_text = pdf_content['full_text'][:20000]
        else:  # results
            # Pro výsledky potřebujeme tabulky a výsledky
            relevant_text = pdf_content['sections'].get('results', '') + '\n' + pdf_content['sections'].get('calibration', '')
            # Přidáme detekované tabulky
            for table in pdf_content['tables'][:5]:  # Max 5 tabulek
                relevant_text += '\n' + table
            if len(relevant_text) < 2000:
                relevant_text = pdf_content['full_text']
        
        # System prompt s cache control
        system_prompt = [
            {
                "type": "text",
                "text": f"You are analyzing an academic paper. Extract ONLY the requested information."
            },
            {
                "type": "text",
                "text": f"PDF CONTENT:\n\n{relevant_text}",
                "cache_control": {"type": "ephemeral"}
            }
        ]
        
        # User prompts podle typu
        if doc_type == "pre_scan":
            user_prompt = DOCUMENT_0_PROMPT
        elif doc_type == "metadata":
            user_prompt = DOCUMENT_1_PROMPT
        elif doc_type == "structure":
            user_prompt = DOCUMENT_2_PROMPT
        else:
            user_prompt = DOCUMENT_3_PROMPT
        
        return system_prompt, user_prompt
    
    def analyze_with_fallback(self, system_prompt: List[Dict], user_prompt: str, 
                            doc_type: str, use_thinking: bool = False) -> Dict[str, Any]:
        """Analyzuje s fallback mechanismem pro levnější modely"""
        
        # Vybereme model podle typu dokumentu
        primary_model = self.model_config.get(doc_type, self.model_config["fallback"])
        
        # První pokus s primárním modelem
        try:
            logger.info(f"🤖 Používám model {primary_model} pro {doc_type}")
            
            params = {
                "model": primary_model,
                "max_tokens": 8000 if not use_thinking else 10000,
                "temperature": 0.1,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_prompt}]
            }
            
            response = self.client.messages.create(**params)
            
            # Tracking nákladů
            self._track_usage(response)
            
            # Validace odpovědi
            result = self._parse_response(response)
            logger.info(f"📊 Parsed result for {doc_type}: {type(result)} - {result}")
            if result is None:
                logger.warning(f"⚠️ Prázdná odpověď od {primary_model}, zkouším fallback")
            elif self._validate_response(result, doc_type):
                self.extraction_stats[f"{doc_type}_success"] += 1
                return result
            else:
                logger.warning(f"⚠️ Nevalidní odpověď od {primary_model}, zkouším fallback")
                
        except Exception as e:
            logger.error(f"❌ Chyba s {primary_model}: {e}")
        
        # Fallback na Opus
        if primary_model != self.model_config["fallback"]:
            logger.info(f"🔄 Fallback na {self.model_config['fallback']}")
            self.extraction_stats[f"{doc_type}_fallback"] += 1
            
            params["model"] = self.model_config["fallback"]
            
            try:
                response = self.client.messages.create(**params)
                self._track_usage(response)
                result = self._parse_response(response)
                if result is None:
                    return {'error': 'Failed to parse response', 'table_rows': []}
                return result
            except Exception as e:
                logger.error(f"❌ Fallback také selhal: {e}")
        
        return {'error': 'Failed to extract data', 'table_rows': []}
    
    def _track_usage(self, response):
        """Sleduje použití tokenů z response"""
        if hasattr(response, 'usage') and response.usage is not None:
            usage = response.usage
            input_tokens = getattr(usage, 'input_tokens', None)
            output_tokens = getattr(usage, 'output_tokens', None)
            cache_write_tokens = getattr(usage, 'cache_creation_input_tokens', None)
            cache_read_tokens = getattr(usage, 'cache_read_input_tokens', None)
            
            if input_tokens is not None:
                self.cost_tracker.input_tokens += input_tokens
            if output_tokens is not None:
                self.cost_tracker.output_tokens += output_tokens
            if cache_write_tokens is not None:
                self.cost_tracker.cache_write_tokens += cache_write_tokens
            if cache_read_tokens is not None:
                self.cost_tracker.cache_read_tokens += cache_read_tokens
    
    def _analyze_document_quality(self, result: Dict, doc_type: str, filename: str) -> Dict:
        """Analyzuje kvalitu extrakce pro daný dokument"""
        
        logger.info(f"🔍 Analyzing document quality for {doc_type}: {type(result)} - {result}")
        
        # Definice kritických polí pro každý typ dokumentu
        critical_fields = {
            "metadata": {
                'Author': 2, 'Year': 7, 'Base_Model_Type': 8, 'DOI': 4
            },
            "structure": {
                'HH_Included': 12, 'Firms_Included': 13, 'Ramsey_Rule': 11
            },
            "results": {
                'Results_Inflation': 40, 'Results_Table': 39, 'IdEstimate': 1
            }
        }
        
        # Všechna očekávaná pole pro každý typ
        expected_fields = {
            "metadata": {
                'Idstudy': 0, 'Author': 2, 'Author_Affiliation': 3, 'DOI': 4, 
                'Journal_Name': 5, 'Num_Citations': 6, 'Year': 7, 
                'Base_Model_Type': 8, 'Country': 23, 'Impact_Factor': 46
            },
            "structure": {
                'Augmented_base_model': 9, 'Augmentation_Description': 10,
                'Ramsey_Rule': 11, 'HH_Included': 12, 'Firms_Included': 13,
                'Banks_Included': 14, 'Government_Included': 15,
                'HH_Maximization_Type': 16, 'HH_Maximized_Vars': 17,
                'Producer_Type': 18, 'Producer_Assumption': 19,
                'Other_Agent_Included': 20, 'Other_Agent_Assumptions': 21,
                'Empirical_Research': 22
            },
            "results": {
                'IdEstimate': 1, 'Flexible_Price_Assumption': 24, 'Exogenous_Inflation': 25,
                'Households_discount_factor': 26, 'Consumption_curvature_parameter': 27,
                'Disutility_of_labor': 28, 'Inverse_of_labor_supply_elasticity': 29,
                'Money_curvature_parameter': 30, 'Loan_to_value_ratio': 31,
                'Labor_share_of_output': 32, 'Depositors_discount_factor': 33,
                'Price_adjustment_cost': 34, 'Elasticity_of_substitution_between_goods': 35,
                'AR1_coefficient_of_TFP': 36, 'Std_dev_to_TFP_shock': 37,
                'Zero_Lower_Bound': 38, 'Results_Table': 39, 'Results_Inflation': 40,
                'Results_Inflation_Assumption': 41, 'Preferred_Estimate': 42,
                'Reason_for_Preferred': 43, 'Std_Dev_Inflation': 44, 'Interest_Rate': 45
            }
        }
        
        quality_info = {
            'file': filename,
            'doc_type': doc_type,
            'valid_fields': 0,
            'total_fields': 0,
            'success_rate': 0.0,
            'missing_critical': [],
            'extracted_fields': [],
            'empty_fields': [],
            'error': False
        }
        
        # Kontrola, zda result není None nebo neobsahuje chybu
        if result is None or 'error' in result:
            quality_info['error'] = True
            quality_info['total_fields'] = len(expected_fields.get(doc_type, {}))
            return quality_info
            
        # Kontrola, zda obsahuje table_rows
        if 'table_rows' not in result or not result['table_rows']:
            quality_info['error'] = True
            quality_info['total_fields'] = len(expected_fields.get(doc_type, {}))
            return quality_info
        
        # Analyzujeme první řádek (pro metadata a structure) nebo všechny řádky (pro results)
        rows_to_analyze = result['table_rows']
        if doc_type in ["metadata", "structure"]:
            rows_to_analyze = [result['table_rows'][0]] if result['table_rows'] else []
        
        if not rows_to_analyze:
            quality_info['error'] = True
            quality_info['total_fields'] = len(expected_fields.get(doc_type, {}))
            return quality_info
        
        # Analyzujeme kvalitu extrakce
        expected = expected_fields.get(doc_type, {})
        critical = critical_fields.get(doc_type, {})
        
        quality_info['total_fields'] = len(expected)
        
        # Pro results bereme průměr přes všechny řádky
        if doc_type == "results":
            valid_count = 0
            total_possible = len(expected) * len(rows_to_analyze)
            
            for row in rows_to_analyze:
                for field_name, field_idx in expected.items():
                    if field_idx < len(row) and row[field_idx] not in ['NA', '', None]:
                        valid_count += 1
                        if field_name not in quality_info['extracted_fields']:
                            quality_info['extracted_fields'].append(field_name)
            
            quality_info['valid_fields'] = valid_count
            quality_info['total_fields'] = total_possible
            
        else:  # metadata nebo structure
            row = rows_to_analyze[0]
            for field_name, field_idx in expected.items():
                if field_idx < len(row) and row[field_idx] not in ['NA', '', None]:
                    quality_info['valid_fields'] += 1
                    quality_info['extracted_fields'].append(field_name)
                else:
                    quality_info['empty_fields'].append(field_name)
        
        # Kontrola kritických polí
        if doc_type != "results":  # Pro results je složitější
            row = rows_to_analyze[0]
            for field_name, field_idx in critical.items():
                if field_idx < len(row) and row[field_idx] in ['NA', '', None]:
                    quality_info['missing_critical'].append(field_name)
        
        # Výpočet success rate
        if quality_info['total_fields'] > 0:
            quality_info['success_rate'] = (quality_info['valid_fields'] / quality_info['total_fields']) * 100
        
        return quality_info
    
    def _validate_response(self, result: Dict, doc_type: str) -> bool:
        """Validuje odpověď podle typu dokumentu"""
        if result is None or 'error' in result:
            return False
            
        if doc_type == "pre_scan":
            # Pre-scan musí obsahovat číslo
            if 'count' not in result:
                return False
        elif 'table_rows' not in result or not result['table_rows']:
            return False
        
        # Specifická validace podle typu
        if doc_type == "metadata":
            # Musí obsahovat alespoň autora a rok
            if len(result['table_rows']) == 0:
                return False
            row = result['table_rows'][0]
            if len(row) < 8:
                return False
            if row[2] == 'NA' or row[7] == 'NA':  # Author, Year
                return False
                
        elif doc_type == "structure":
            # Musí obsahovat model info
            if len(result['table_rows']) == 0:
                return False
            row = result['table_rows'][0]
            if len(row) < 26:
                return False
                
        elif doc_type == "results":
            # Musí obsahovat inflační výsledky
            for row in result['table_rows']:
                if len(row) < 46:
                    return False
                if row[40] == 'NA':  # Results_Inflation
                    return False
        
        return True
    
    def _parse_response(self, response) -> Dict[str, Any]:
        """Parsuje odpověď s lepším error handling"""
        try:
            if hasattr(response, 'content'):
                text = response.content[0].text if response.content else ""
            else:
                text = str(response)
            
            # Speciální parsing pro pre-scan
            if "This paper contains" in text and "distinct inflation results" in text:
                # Hledáme číslo v textu
                match = re.search(r'This paper contains (\d+) distinct inflation results', text)
                if match:
                    return {'count': int(match.group(1))}
            
            lines = text.strip().split('\n')
            
            # Hledáme začátek tabulky
            table_start = -1
            for i, line in enumerate(lines):
                if 'Idstudy\t' in line or (line.startswith('Idstudy') and '\t' in line):
                    table_start = i
                    break
            
            if table_start >= 0:
                # Extrahujeme řádky tabulky
                table_rows = []
                for line in lines[table_start + 1:]:
                    if '\t' in line:
                        cols = line.split('\t')
                        # Doplníme chybějící sloupce
                        while len(cols) < len(META_ANALYSIS_COLUMNS):
                            cols.append('NA')
                        # Ořežeme přebytečné
                        if len(cols) > len(META_ANALYSIS_COLUMNS):
                            cols = cols[:len(META_ANALYSIS_COLUMNS)]
                        table_rows.append(cols)
                
                if table_rows:
                    return {'table_rows': table_rows}
                else:
                    return {'error': 'No valid table rows found'}
            else:
                # Zkusíme najít strukturovaná data jinak
                logger.warning("Nenalezena standardní tabulka, zkouším alternativní parsing")
                result = self._parse_alternative_format(text)
                if result is None:
                    logger.error("_parse_alternative_format vrátil None")
                    return {'error': 'Could not parse response', 'table_rows': []}
                return result
                
        except Exception as e:
            logger.error(f"Chyba při parsování: {e}")
            return {'error': str(e)}
    
    def _parse_alternative_format(self, text: str) -> Dict[str, Any]:
        """Parsuje alternativní formáty odpovědí"""
        # Zkusíme najít JSON
        try:
            import json
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                if isinstance(data, dict):
                    # Převedeme JSON na řádky tabulky
                    row = ['NA'] * len(META_ANALYSIS_COLUMNS)
                    for i, col in enumerate(META_ANALYSIS_COLUMNS):
                        if col in data:
                            row[i] = str(data[col])
                    return {'table_rows': [row]}
        except Exception as e:
            logger.warning(f"JSON parsing failed: {e}")
            pass
        
        # Zkusíme najít key-value páry
        data = {}
        for line in text.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                # Mapování na sloupce
                for i, col in enumerate(META_ANALYSIS_COLUMNS):
                    if col.lower() in key.lower():
                        data[i] = value
                        break
        
        if data:
            row = ['NA'] * len(META_ANALYSIS_COLUMNS)
            for idx, value in data.items():
                row[idx] = value
            return {'table_rows': [row]}
        
        return {'error': 'Could not parse response', 'table_rows': []}
    
    def analyze_pdf_optimized(self, pdf_path: str) -> pd.DataFrame:
        """Optimalizovaná analýza PDF s novou strukturou"""
        
        doc_name = os.path.basename(pdf_path)  # Definujeme hned na začátku
        
        logger.info(f"\n{'='*60}")
        logger.info(f"📚 Analyzuji PDF: {doc_name}")
        logger.info(f"{'='*60}")
        
        # 1. Vylepšená extrakce PDF
        pdf_content = self.extract_pdf_content_enhanced(pdf_path)
        if not pdf_content['full_text']:
            logger.error(f"❌ Nepodařilo se extrahovat obsah")
            return self._create_empty_dataframe(self.current_study_id)
        
        # 2. Document 0: Pre-scan pro počítání výsledků
        logger.info("\n🔍 Document 0: Pre-scan (Sonnet)")
        system_prompt, user_prompt = self.create_optimized_prompts(pdf_content, "pre_scan")
        pre_scan_result = self.analyze_with_fallback(system_prompt, user_prompt, "pre_scan")
        
        expected_results = 1  # Default
        if 'count' in pre_scan_result:
            expected_results = pre_scan_result['count']
            logger.info(f"📊 Očekávám {expected_results} inflačních výsledků")
        
        # 3. Document 1: Metadata (levný model)
        logger.info("\n📋 Document 1: Metadata (Sonnet)")
        time.sleep(1)
        system_prompt, user_prompt = self.create_optimized_prompts(pdf_content, "metadata")
        results1 = self.analyze_with_fallback(system_prompt, user_prompt, "metadata")
        
        # Debug Document 1
        doc1_quality = self._analyze_document_quality(results1, "metadata", doc_name)
        logger.info(f"📊 Document 1 kvalita: {doc1_quality}")
        if doc1_quality and 'valid_fields' in doc1_quality:
            logger.info(f"📊 Document 1 kvalita: {doc1_quality['valid_fields']}/{doc1_quality['total_fields']} polí ({doc1_quality['success_rate']:.1f}%)")
            if doc1_quality['missing_critical']:
                logger.warning(f"⚠️ Document 1 chybí kritická pole: {', '.join(doc1_quality['missing_critical'])}")
        else:
            logger.error(f"❌ Document 1 kvalita je None nebo neplatná: {doc1_quality}")
        
        if doc1_quality:
            self.document_stats['doc1_results'].append(doc1_quality)
        
        # 4. Document 2: Structure - jen STUDIJNÍ úroveň (levný model)
        logger.info("\n📋 Document 2: Structure - Study Level (Sonnet)")
        time.sleep(1)
        system_prompt, user_prompt = self.create_optimized_prompts(pdf_content, "structure")
        results2 = self.analyze_with_fallback(system_prompt, user_prompt, "structure")
        
        # Debug Document 2
        doc2_quality = self._analyze_document_quality(results2, "structure", doc_name)
        logger.info(f"📊 Document 2 kvalita: {doc2_quality}")
        if doc2_quality and 'valid_fields' in doc2_quality:
            logger.info(f"📊 Document 2 kvalita: {doc2_quality['valid_fields']}/{doc2_quality['total_fields']} polí ({doc2_quality['success_rate']:.1f}%)")
            if doc2_quality['missing_critical']:
                logger.warning(f"⚠️ Document 2 chybí kritická pole: {', '.join(doc2_quality['missing_critical'])}")
        else:
            logger.error(f"❌ Document 2 kvalita je None nebo neplatná: {doc2_quality}")
        
        if doc2_quality:
            self.document_stats['doc2_results'].append(doc2_quality)
        
        # 5. Document 3: Results s moved variables (Opus)
        logger.info("\n📋 Document 3: Results + Parameters (Opus)")
        time.sleep(1)
        system_prompt, user_prompt = self.create_optimized_prompts(pdf_content, "results")
        results3 = self.analyze_with_fallback(system_prompt, user_prompt, "results")
        
        # Zjistíme kolik výsledků Document 3 skutečně extrahoval
        actual_results = 0
        if 'table_rows' in results3 and results3['table_rows']:
            actual_results = len(results3['table_rows'])
            # Filtrujeme prázdné řádky
            valid_results = []
            for row in results3['table_rows']:
                if len(row) > 40 and row[40] != 'NA':  # Results_Inflation není NA
                    valid_results.append(row)
            actual_results = len(valid_results)
            results3['table_rows'] = valid_results  # Aktualizujeme na platné řádky
        
        logger.info(f"📊 Document 3 extrahoval: {actual_results} inflačních výsledků")
        
        # Debug Document 3
        doc3_quality = self._analyze_document_quality(results3, "results", doc_name)
        logger.info(f"📊 Document 3 kvalita: {doc3_quality}")
        if doc3_quality and 'valid_fields' in doc3_quality:
            logger.info(f"📊 Document 3 kvalita: {doc3_quality['valid_fields']}/{doc3_quality['total_fields']} polí ({doc3_quality['success_rate']:.1f}%)")
            if doc3_quality['missing_critical']:
                logger.warning(f"⚠️ Document 3 chybí kritická pole: {', '.join(doc3_quality['missing_critical'])}")
        else:
            logger.error(f"❌ Document 3 kvalita je None nebo neplatná: {doc3_quality}")
        
        # Porovnání Document 0 vs Document 3
        if expected_results != actual_results:
            if actual_results == 0:
                logger.error(f"❌ NESOULAD: Document 0 očekával {expected_results}, Document 3 našel {actual_results} (ŽÁDNÉ!)")
            elif actual_results < expected_results:
                logger.warning(f"⚠️ NESOULAD: Document 0 očekával {expected_results}, Document 3 našel jen {actual_results}")
            else:
                logger.info(f"✅ BONUS: Document 0 očekával {expected_results}, Document 3 našel {actual_results}")
        else:
            logger.info(f"✅ SHODA: Document 0 i Document 3 shodně {actual_results} výsledků")
        
        # Uložíme pro debugging
        if doc3_quality:
            self.document_stats['doc3_actual'].append({
                'file': doc_name,
                'count': actual_results,
                'expected': expected_results,
                'match': expected_results == actual_results,
                'quality': doc3_quality
            })
            
            self.document_stats['doc3_results'].append(doc3_quality)
        
        # Pokud results3 obsahuje error, zkusíme jednodušší přístup
        if 'error' in results3:
            logger.warning("⚠️ Zkouším alternativní extrakci výsledků")
            simplified_prompt = self._create_simplified_results_prompt(pdf_content)
            results3 = self.analyze_with_fallback(system_prompt, simplified_prompt, "results")
        
        # 6. Sloučit výsledky s novou strukturou
        df = self.merge_results_new_structure(results1, results2, results3, 
                                            self.current_study_id, expected_results)
        
        # 7. Post-processing a validace
        df = self.post_process_dataframe(df)
        
        # 8. Pokud stále chybí výsledky, zkusíme manuální extrakci
        if df['Results_Inflation'].eq('NA').all():
            logger.warning("⚠️ Žádné inflační výsledky, zkouším manuální extrakci")
            manual_results = self._extract_results_manually(pdf_content)
            if manual_results:
                df = self._apply_manual_results(df, manual_results)
        
        return df
    
    def _create_simplified_results_prompt(self, pdf_content: Dict) -> str:
        """Vytvoří zjednodušený prompt pro extrakci výsledků"""
        return """
Extract ONLY inflation results from the PDF. Focus on:
1. Find ALL tables with inflation values (π, pi, inflation rate)
2. Extract the numerical inflation values
3. Note which table they come from
4. Include any parameters mentioned
5. Note if prices are flexible/sticky for each result
6. Note if ZLB applies for each result

Create a simple table with columns:
- IdEstimate (1, 2, 3...)
- Results_Table (e.g., "Table 1")
- Results_Inflation (the numerical value)
- Flexible_Price_Assumption (1 for flexible, 0 for sticky)
- Zero_Lower_Bound (1 if ZLB mentioned, 0 if not)
- Results_Inflation_Assumption (brief description)

Fill all 47 columns but focus mainly on extracting the inflation values and per-result assumptions.
Use NA for any missing values.
"""
    
    def merge_results_new_structure(self, results1: Dict, results2: Dict, results3: Dict, 
                                  study_id: int, expected_results: int) -> pd.DataFrame:
        """Sloučení výsledků s novou strukturou dokumentů"""
        
        # Určíme počet řádků na základě results3
        num_rows = expected_results
        if 'table_rows' in results3 and results3['table_rows']:
            num_rows = len(results3['table_rows'])
        
        logger.info(f"📊 Slučuji výsledky: {num_rows} inflačních odhadů")
        
        # Vytvoříme DataFrame
        df = pd.DataFrame(index=range(num_rows), columns=META_ANALYSIS_COLUMNS)
        df.fillna('NA', inplace=True)
        
        # Mapování pro Document 1 (metadata)
        doc1_mapping = {
            0: 'Idstudy', 2: 'Author', 3: 'Author_Affiliation', 
            4: 'DOI', 5: 'Journal_Name', 6: 'Num_Citations',
            7: 'Year', 8: 'Base_Model_Type', 23: 'Country', 
            46: 'Impact_Factor'
        }
        
        # Mapování pro Document 2 (structure - bez moved variables)
        doc2_mapping = {
            9: 'Augmented_base_model', 10: 'Augmentation_Description',
            11: 'Ramsey_Rule', 12: 'HH_Included', 13: 'Firms_Included',
            14: 'Banks_Included', 15: 'Government_Included',
            16: 'HH_Maximization_Type', 17: 'HH_Maximized_Vars',
            18: 'Producer_Type', 19: 'Producer_Assumption',
            20: 'Other_Agent_Included', 21: 'Other_Agent_Assumptions',
            22: 'Empirical_Research'
        }
        
        # Mapování pro Document 3 (results + moved variables)
        doc3_mapping = {
            1: 'IdEstimate', 
            24: 'Flexible_Price_Assumption',  # MOVED FROM DOC2
            25: 'Exogenous_Inflation',        # MOVED FROM DOC2
            26: 'Households_discount_factor',
            27: 'Consumption_curvature_parameter', 28: 'Disutility_of_labor',
            29: 'Inverse_of_labor_supply_elasticity', 30: 'Money_curvature_parameter',
            31: 'Loan_to_value_ratio', 32: 'Labor_share_of_output',
            33: 'Depositors_discount_factor', 34: 'Price_adjustment_cost',
            35: 'Elasticity_of_substitution_between_goods',
            36: 'AR1_coefficient_of_TFP', 37: 'Std_dev_to_TFP_shock',
            38: 'Zero_Lower_Bound',           # MOVED FROM DOC2
            39: 'Results_Table',
            40: 'Results_Inflation', 41: 'Results_Inflation_Assumption',
            42: 'Preferred_Estimate', 43: 'Reason_for_Preferred',
            44: 'Std_Dev_Inflation', 45: 'Interest_Rate'
        }
        
        # Aplikujeme mapování s validací
        if results1 is not None and 'table_rows' in results1 and results1['table_rows']:
            self._apply_mapping(df, results1['table_rows'][0], doc1_mapping, broadcast=True)
        
        if results2 is not None and 'table_rows' in results2 and results2['table_rows']:
            self._apply_mapping(df, results2['table_rows'][0], doc2_mapping, broadcast=True)
        
        if results3 is not None and 'table_rows' in results3 and results3['table_rows']:
            for row_idx, row_data in enumerate(results3['table_rows']):
                if row_idx < num_rows:
                    self._apply_mapping(df, row_data, doc3_mapping, row_idx=row_idx)
        
        # Finální úpravy
        df['Idstudy'] = str(study_id)
        if df['IdEstimate'].eq('NA').all():
            df['IdEstimate'] = range(1, num_rows + 1)
        
        return df
    
    def _apply_mapping(self, df: pd.DataFrame, row_data: List, mapping: Dict, 
                      broadcast: bool = False, row_idx: int = None):
        """Aplikuje mapování s validací"""
        if row_data is None or not isinstance(row_data, list):
            return
            
        for idx, col_name in mapping.items():
            if idx < len(row_data) and row_data[idx] not in ['NA', '', None]:
                value = str(row_data[idx]).strip()
                
                # Validace hodnot
                if col_name in ['Year', 'Num_Citations']:
                    # Musí být číslo
                    if not value.isdigit():
                        continue
                
                if col_name in ['HH_Included', 'Firms_Included', 'Banks_Included', 
                               'Government_Included', 'Empirical_Research', 
                               'Flexible_Price_Assumption', 'Exogenous_Inflation',
                               'Zero_Lower_Bound', 'Preferred_Estimate']:
                    # Musí být 0 nebo 1
                    if value not in ['0', '1']:
                        continue
                
                # Aplikuj hodnotu
                if broadcast:
                    df[col_name] = value
                elif row_idx is not None:
                    df.loc[row_idx, col_name] = value
    
    def _extract_results_manually(self, pdf_content: Dict) -> List[Dict]:
        """Pokusí se manuálně extrahovat inflační výsledky z PDF"""
        results = []
        
        # Hledáme inflační hodnoty v textu
        inflation_pattern = r'(?:inflation|π|pi)\s*[=:]\s*([-]?\d+\.?\d*)\s*%?'
        
        for i, table in enumerate(pdf_content.get('tables', [])):
            matches = re.findall(inflation_pattern, table, re.IGNORECASE)
            for j, match in enumerate(matches):
                try:
                    value = float(match)
                    # Převést na desetinné číslo pokud je v procentech
                    if abs(value) > 1:
                        value = value / 100
                    results.append({
                        'table': f"Table {i+1}",
                        'value': value,
                        'assumption': f"From table {i+1}"
                    })
                except:
                    pass
        
        # Hledat i v hlavním textu
        text_matches = re.findall(inflation_pattern, pdf_content['full_text'][:20000], re.IGNORECASE)
        for match in text_matches[:5]:  # Max 5 z textu
            try:
                value = float(match)
                if abs(value) > 1:
                    value = value / 100
                results.append({
                    'table': "Text",
                    'value': value,
                    'assumption': "From main text"
                })
            except:
                pass
        
        return results
    
    def _apply_manual_results(self, df: pd.DataFrame, manual_results: List[Dict]) -> pd.DataFrame:
        """Aplikuje manuálně extrahované výsledky do DataFrame"""
        if not manual_results:
            return df
        
        # Vytvoříme nový DataFrame s manuálními výsledky
        new_rows = []
        for i, result in enumerate(manual_results):
            row = df.iloc[0].copy() if len(df) > 0 else pd.Series(['NA'] * len(META_ANALYSIS_COLUMNS), index=META_ANALYSIS_COLUMNS)
            row['IdEstimate'] = str(i + 1)
            row['Results_Table'] = result['table']
            row['Results_Inflation'] = str(result['value'])
            row['Results_Inflation_Assumption'] = result['assumption']
            new_rows.append(row)
        
        if new_rows:
            return pd.DataFrame(new_rows)
        return df
    
    def post_process_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Post-processing a validace dat"""
        
        # Konverze datových typů
        numeric_columns = [
            'Households_discount_factor', 'Consumption_curvature_parameter',
            'Disutility_of_labor', 'Inverse_of_labor_supply_elasticity',
            'Money_curvature_parameter', 'Loan_to_value_ratio',
            'Labor_share_of_output', 'Depositors_discount_factor',
            'Price_adjustment_cost', 'Elasticity_of_substitution_between_goods',
            'AR1_coefficient_of_TFP', 'Std_dev_to_TFP_shock',
            'Results_Inflation', 'Std_Dev_Inflation', 'Interest_Rate'
        ]
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                df[col] = df[col].fillna('NA')
        
        # Validace rozsahů
        validations = {
            'Households_discount_factor': (0.9, 1.0),
            'Labor_share_of_output': (0.5, 0.8),
            'AR1_coefficient_of_TFP': (0.8, 1.0),
            'Results_Inflation': (-0.1, 0.1)  # -10% až 10%
        }
        
        for col, (min_val, max_val) in validations.items():
            if col in df.columns:
                mask = pd.to_numeric(df[col], errors='coerce').between(min_val, max_val)
                invalid_count = (~mask).sum()
                if invalid_count > 0:
                    logger.warning(f"⚠️ {col}: {invalid_count} hodnot mimo očekávaný rozsah {min_val}-{max_val}")
        
        return df
    
    def process_folder_optimized(self, folder_path: str, max_workers: int = 2) -> pd.DataFrame:
        """Zpracuje složku s optimalizovaným workflow"""
        
        pdf_files = list(Path(folder_path).glob("*.pdf"))
        
        if not pdf_files:
            logger.warning("Nebyly nalezeny žádné PDF soubory")
            return pd.DataFrame(columns=META_ANALYSIS_COLUMNS)
        
        logger.info(f"📚 Nalezeno {len(pdf_files)} PDF souborů")
        
        # Inicializace progress trackingu
        self.extraction_stats['total_files'] = len(pdf_files)
        
        all_results = []
        
        # Sekvenční zpracování (paralelní by mohlo překročit rate limits)
        for idx, pdf_path in enumerate(pdf_files, 1):
            print(f"\n{'='*80}")
            print(f"📄 Zpracovávám {idx}/{len(pdf_files)}: {pdf_path.name}")
            print(f"💰 Dosavadní náklady: ${self.cost_tracker.calculate_cost():.2f}")
            print(f"{'='*80}")
            
            try:
                # Rate limiting
                if idx > 1:
                    time.sleep(3)
                
                # Analýza
                df_study = self.analyze_pdf_optimized(str(pdf_path))
                
                if not df_study.empty and not (len(df_study) == 1 and all(df_study.iloc[0] == 'NA')):
                    all_results.append(df_study)
                    self.extraction_stats['successful'] += 1
                    
                    # Zobrazit krátkého summary pro tento soubor
                    inflation_results = df_study[df_study['Results_Inflation'] != 'NA']
                    print(f"✅ Úspěch: {len(inflation_results)} inflačních výsledků extrahováno")
                else:
                    self.extraction_stats['failed'] += 1
                    print(f"❌ Selhání: žádné validní inflační výsledky")
                
                self.current_study_id += 1
                
            except Exception as e:
                logger.error(f"❌ Chyba při zpracování {pdf_path.name}: {e}")
                self.extraction_stats['failed'] += 1
                print(f"❌ Kritická chyba: {e}")
                continue
        
        # Finální statistiky
        self._print_final_statistics()
        
        # Spojení výsledků
        if all_results:
            final_df = pd.concat(all_results, ignore_index=True)
            return final_df
        else:
            return pd.DataFrame(columns=META_ANALYSIS_COLUMNS)
    
    def _print_final_statistics(self):
        """Zobrazí finální statistiky včetně detailního debuggingu všech dokumentů"""
        print(f"\n{'='*80}")
        print(" FINÁLNÍ STATISTIKY - KOMPLETNÍ DEBUG ".center(80, "="))
        print(f"{'='*80}")
        
        # Úspěšnost
        print(f"\n📊 Základní úspěšnost:")
        for key, value in self.extraction_stats.items():
            print(f"  • {key}: {value}")
        
        # Document 0 vs Document 3 analýza
        if self.document_stats['doc0_expected'] and self.document_stats['doc3_actual']:
            print(f"\n🔍 Document 0 vs Document 3 analýza:")
            
            total_files = len(self.document_stats['doc0_expected'])
            matches = sum(1 for stat in self.document_stats['doc3_actual'] if stat['match'])
            match_rate = (matches / total_files) * 100 if total_files > 0 else 0
            
            total_expected = sum(stat['count'] for stat in self.document_stats['doc0_expected'])
            total_actual = sum(stat['count'] for stat in self.document_stats['doc3_actual'])
            
            print(f"  • Soubory s perfektní shodou: {matches}/{total_files} ({match_rate:.1f}%)")
            print(f"  • Celkem očekáváno (Doc 0): {total_expected} výsledků")
            print(f"  • Celkem extrahováno (Doc 3): {total_actual} výsledků")
            print(f"  • Míra extrakce: {(total_actual/total_expected)*100:.1f}%" if total_expected > 0 else "  • Míra extrakce: N/A")
        
        # Kvalita jednotlivých dokumentů
        doc_types = [
            ('doc1_results', 'Document 1 (Metadata)', 'metadata'),
            ('doc2_results', 'Document 2 (Structure)', 'structure'), 
            ('doc3_results', 'Document 3 (Results)', 'results')
        ]
        
        for doc_key, doc_name, doc_type in doc_types:
            if doc_key in self.document_stats and self.document_stats[doc_key]:
                results = self.document_stats[doc_key]
                
                # Průměrná kvalita
                avg_success_rate = sum(r['success_rate'] for r in results) / len(results)
                total_valid = sum(r['valid_fields'] for r in results)
                total_possible = sum(r['total_fields'] for r in results)
                error_count = sum(1 for r in results if r['error'])
                
                print(f"\n📋 {doc_name} kvalita:")
                print(f"  • Průměrná úspěšnost: {avg_success_rate:.1f}%")
                print(f"  • Celkem extrahováno: {total_valid}/{total_possible} polí")
                print(f"  • Chyby: {error_count}/{len(results)} souborů")
                
                # Nejčastější chybějící kritická pole
                missing_critical = {}
                for result in results:
                    for field in result.get('missing_critical', []):
                        missing_critical[field] = missing_critical.get(field, 0) + 1
                
                if missing_critical:
                    print(f"  • Nejčastější chybějící kritická pole:")
                    for field, count in sorted(missing_critical.items(), key=lambda x: x[1], reverse=True)[:3]:
                        print(f"    - {field}: {count}/{len(results)} souborů")
                
                # Nejhorší soubory
                worst_files = sorted([r for r in results if not r['error']], 
                                   key=lambda x: x['success_rate'])[:3]
                if worst_files:
                    print(f"  • Nejhorší výsledky:")
                    for result in worst_files:
                        print(f"    - {result['file'][:25]}: {result['success_rate']:.1f}%")
        
        # Detailní nesoulady Document 0 vs 3
        if self.document_stats['doc0_expected'] and self.document_stats['doc3_actual']:
            mismatches = [stat for stat in self.document_stats['doc3_actual'] if not stat['match']]
            if mismatches:
                print(f"\n⚠️ Document 0 vs 3 nesoulady:")
                for stat in mismatches[:5]:  # Zobraz prvních 5
                    print(f"    • {stat['file'][:30]}: očekáváno {stat['expected']}, nalezeno {stat['count']}")
                if len(mismatches) > 5:
                    print(f"    • ... a {len(mismatches)-5} dalších")
        
        # Náklady
        cost = self.cost_tracker.calculate_cost()
        print(f"\n💰 Odhad nákladů:")
        print(f"  • Input tokens: {self.cost_tracker.input_tokens:,}")
        print(f"  • Output tokens: {self.cost_tracker.output_tokens:,}")
        print(f"  • Cache write tokens: {self.cost_tracker.cache_write_tokens:,}")
        print(f"  • Cache read tokens: {self.cost_tracker.cache_read_tokens:,}")
        print(f"  • Celkové náklady: ${cost:.2f}")
        
        if self.extraction_stats.get('successful', 0) > 0:
            cost_per_file = cost / self.extraction_stats['successful']
            print(f"  • Náklady na úspěšný soubor: ${cost_per_file:.2f}")
        
        # Celkové doporučení
        print(f"\n🎯 DEBUGGING DOPORUČENÍ:")
        
        # Document 1 doporučení
        if 'doc1_results' in self.document_stats:
            doc1_avg = sum(r['success_rate'] for r in self.document_stats['doc1_results']) / len(self.document_stats['doc1_results'])
            if doc1_avg < 70:
                print(f"  • Document 1 (Metadata): {doc1_avg:.1f}% - VYLADIT PROMPT pro Author/Year/DOI extrakci")
        
        # Document 2 doporučení
        if 'doc2_results' in self.document_stats:
            doc2_avg = sum(r['success_rate'] for r in self.document_stats['doc2_results']) / len(self.document_stats['doc2_results'])
            if doc2_avg < 60:
                print(f"  • Document 2 (Structure): {doc2_avg:.1f}% - VYLADIT PROMPT pro identifikaci agentů")
        
        # Document 3 doporučení
        if 'doc3_results' in self.document_stats:
            doc3_avg = sum(r['success_rate'] for r in self.document_stats['doc3_results']) / len(self.document_stats['doc3_results'])
            if doc3_avg < 50:
                print(f"  • Document 3 (Results): {doc3_avg:.1f}% - VYLADIT PROMPT pro extrakci výsledků/parametrů")
        
        # Document 0 vs 3 doporučení
        if self.document_stats['doc0_expected'] and self.document_stats['doc3_actual']:
            mismatches = sum(1 for stat in self.document_stats['doc3_actual'] if not stat['match'])
            if mismatches > len(self.document_stats['doc3_actual']) * 0.3:  # > 30% nesouladů
                print(f"  • Document 0 vs 3: {mismatches} nesouladů - VYLADIT buď počítání nebo extrakci")
    
    def _get_pdf_cache_key(self, pdf_path: str) -> str:
        """Generuje cache klíč pro PDF"""
        stat = os.stat(pdf_path)
        key = f"{os.path.basename(pdf_path)}_{stat.st_size}_{stat.st_mtime}"
        return hashlib.md5(key.encode()).hexdigest()
    
    def _load_from_cache(self, cache_key: str) -> Optional[Dict]:
        """Načte data z cache"""
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
            except:
                pass
        return None
    
    def _save_to_cache(self, cache_key: str, data: Dict):
        """Uloží data do cache"""
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)
        except:
            pass
    
    def _create_empty_dataframe(self, study_id: int) -> pd.DataFrame:
        """Vytvoří prázdný DataFrame"""
        empty_row = {col: 'NA' for col in META_ANALYSIS_COLUMNS}
        empty_row['Idstudy'] = str(study_id)
        empty_row['IdEstimate'] = '1'
        return pd.DataFrame([empty_row])


def main():
    """Hlavní funkce"""
    print("=" * 80)
    print(" INFLATION META-ANALYSIS v8.0 - Full Debug System ".center(80, "="))
    print("=" * 80)
    print("\n🔄 Nová struktura dokumentů:")
    print("  Document 0: Pre-scan (rychlé počítání)")
    print("  Document 1: Metadata (nezměněno)")
    print("  Document 2: Structure - pouze studijní úroveň")
    print("  Document 3: Results + moved variables (per result)")
    print("\n🔍 Kompletní debugging systém:")
    print("  • Real-time kvalita každého dokumentu")
    print("  • Detailní Excel sheety pro každý dokument")
    print("  • Debug CSV soubory")
    print("  • Automatická doporučení pro ladění")
    print("\n💰 Optimalizováno pro minimální náklady")
    print("🎯 Sonnet pro jednoduché úlohy, Claude 4 Opus pro složité")
    print("📦 Lokální cache pro opakované zpracování")
    print("✅ Validace a error recovery\n")
    
    # GUI pro výběr složek
    root = tk.Tk()
    root.withdraw()
    
    pdf_folder = filedialog.askdirectory(
        title="Vyberte složku s PDF soubory"
    )
    
    if not pdf_folder:
        print("❌ Nebyla vybrána složka")
        return
    
    print(f"✅ Vybraná složka: {pdf_folder}")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    export_folder = filedialog.askdirectory(
        title="Vyberte složku pro výsledky",
        initialdir=script_dir
    )
    
    root.destroy()
    
    if not export_folder:
        export_folder = os.path.join(script_dir, "AI_export_v8_new_structure")
    
    os.makedirs(export_folder, exist_ok=True)
    
    # Logging
    log_file = os.path.join(export_folder, f"log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)
    
    # Inicializace analyzátoru
    analyzer = OptimizedPDFAnalyzer(CLAUDE_API_KEY, export_folder)
    
    try:
        # Zpracování
        print("\n🚀 Spouštím zpracování s kompletním debug systémem...")
        final_df = analyzer.process_folder_optimized(pdf_folder)
        
        if final_df.empty:
            print("\n❌ Žádné výsledky k uložení")
            return
        
        # Uložení výsledků
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Excel s detaily a kompletním debuggingem
        excel_path = os.path.join(export_folder, f"meta_analysis_v8_{timestamp}.xlsx")
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            final_df.to_excel(writer, sheet_name='Meta-Analysis', index=False)
            
            # Základní statistiky
            stats_df = pd.DataFrame([{
                'Total Studies': final_df['Idstudy'].nunique(),
                'Total Estimates': len(final_df),
                'Total Cost': f"${analyzer.cost_tracker.calculate_cost():.2f}",
                'Cost per Study': f"${analyzer.cost_tracker.calculate_cost() / final_df['Idstudy'].nunique():.2f}",
                'Success Rate': f"{analyzer.extraction_stats.get('successful', 0) / analyzer.extraction_stats.get('total_files', 1) * 100:.1f}%"
            }])
            stats_df.to_excel(writer, sheet_name='Statistics', index=False)
            
            # Document 0 vs Document 3 porovnání
            if analyzer.document_stats['doc0_expected'] and analyzer.document_stats['doc3_actual']:
                comparison_data = []
                for i, (expected, actual) in enumerate(zip(analyzer.document_stats['doc0_expected'], 
                                                         analyzer.document_stats['doc3_actual'])):
                    comparison_data.append({
                        'File': expected['file'],
                        'Doc0_Expected': expected['count'],
                        'Doc3_Actual': actual['count'],
                        'Match': '✅' if actual['match'] else '❌',
                        'Difference': actual['count'] - expected['count'],
                        'Extraction_Rate': f"{(actual['count']/expected['count'])*100:.1f}%" if expected['count'] > 0 else "N/A"
                    })
                
                comparison_df = pd.DataFrame(comparison_data)
                comparison_df.to_excel(writer, sheet_name='Doc0_vs_Doc3_Comparison', index=False)
            
            # Debug sheety pro každý dokument
            doc_debug_info = [
                ('doc1_results', 'Document_1_Debug', 'Document 1 (Metadata)'),
                ('doc2_results', 'Document_2_Debug', 'Document 2 (Structure)'),
                ('doc3_results', 'Document_3_Debug', 'Document 3 (Results)')
            ]
            
            for doc_key, sheet_name, doc_name in doc_debug_info:
                if doc_key in analyzer.document_stats and analyzer.document_stats[doc_key]:
                    debug_data = []
                    for result in analyzer.document_stats[doc_key]:
                        debug_data.append({
                            'File': result['file'],
                            'Success_Rate': f"{result['success_rate']:.1f}%",
                            'Valid_Fields': result['valid_fields'],
                            'Total_Fields': result['total_fields'],
                            'Error': '❌' if result['error'] else '✅',
                            'Missing_Critical': ', '.join(result.get('missing_critical', [])),
                            'Extracted_Fields': ', '.join(result.get('extracted_fields', [])[:10]),  # Max 10 pro čitelnost
                            'Empty_Fields': ', '.join(result.get('empty_fields', [])[:10])
                        })
                    
                    debug_df = pd.DataFrame(debug_data)
                    debug_df.to_excel(writer, sheet_name=sheet_name, index=False)
                    
                print(f"📊 {doc_name} debug uložen do sheet '{sheet_name}'")
        
        # CSV backup
        csv_path = os.path.join(export_folder, f"meta_analysis_v8_{timestamp}.csv")
        final_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        
        # Debug CSV soubory pro všechny dokumenty
        debug_csvs = []
        
        # Document 0 vs Document 3 porovnání
        if analyzer.document_stats['doc0_expected'] and analyzer.document_stats['doc3_actual']:
            debug_data = []
            for expected, actual in zip(analyzer.document_stats['doc0_expected'], 
                                      analyzer.document_stats['doc3_actual']):
                debug_data.append({
                    'File': expected['file'],
                    'Doc0_Expected': expected['count'],
                    'Doc3_Actual': actual['count'],
                    'Match': actual['match'],
                    'Difference': actual['count'] - expected['count'],
                    'Extraction_Rate': (actual['count']/expected['count']) if expected['count'] > 0 else 0
                })
            
            debug_df = pd.DataFrame(debug_data)
            debug_csv_path = os.path.join(export_folder, f"doc0_vs_doc3_debug_{timestamp}.csv")
            debug_df.to_csv(debug_csv_path, index=False, encoding='utf-8-sig')
            debug_csvs.append(debug_csv_path)
        
        # Kompletní kvalita debug pro všechny dokumenty
        all_quality_data = []
        for doc_key, doc_name in [('doc1_results', 'Document_1'), ('doc2_results', 'Document_2'), ('doc3_results', 'Document_3')]:
            if doc_key in analyzer.document_stats:
                for result in analyzer.document_stats[doc_key]:
                    all_quality_data.append({
                        'Document': doc_name,
                        'File': result['file'],
                        'Success_Rate': result['success_rate'],
                        'Valid_Fields': result['valid_fields'],
                        'Total_Fields': result['total_fields'],
                        'Error': result['error'],
                        'Missing_Critical_Count': len(result.get('missing_critical', [])),
                        'Missing_Critical_Fields': '; '.join(result.get('missing_critical', [])),
                        'Extracted_Fields_Count': len(result.get('extracted_fields', [])),
                        'Empty_Fields_Count': len(result.get('empty_fields', []))
                    })
        
        if all_quality_data:
            quality_df = pd.DataFrame(all_quality_data)
            quality_csv_path = os.path.join(export_folder, f"all_documents_quality_{timestamp}.csv")
            quality_df.to_csv(quality_csv_path, index=False, encoding='utf-8-sig')
            debug_csvs.append(quality_csv_path)
        
        if debug_csvs:
            print(f"🔍 Debug CSV soubory vytvořeny: {len(debug_csvs)} souborů")
        
        print(f"\n✅ Hlavní výsledky uloženy: {excel_path}")
        
        print("\n🎉 Zpracování dokončeno!")
        print(f"💰 Celkové náklady: ${analyzer.cost_tracker.calculate_cost():.2f}")
        
        # Kompletní doporučení pro ladění
        print(f"\n🔧 DEBUGGING DASHBOARD:")
        print(f"{'='*50}")
        
        # Průměrné kvality jednotlivých dokumentů
        doc_qualities = {}
        for doc_key, doc_name in [('doc1_results', 'Document 1'), ('doc2_results', 'Document 2'), ('doc3_results', 'Document 3')]:
            if doc_key in analyzer.document_stats and analyzer.document_stats[doc_key]:
                results = analyzer.document_stats[doc_key]
                avg_quality = sum(r['success_rate'] for r in results) / len(results)
                error_rate = sum(1 for r in results if r['error']) / len(results) * 100
                doc_qualities[doc_name] = {'quality': avg_quality, 'errors': error_rate}
                
                status = "🟢 OK" if avg_quality > 70 else "🟡 NEEDS WORK" if avg_quality > 50 else "🔴 CRITICAL"
                print(f"{doc_name}: {avg_quality:.1f}% kvalita, {error_rate:.1f}% chyb {status}")
        
        # Document 0 vs 3 shoda
        if analyzer.document_stats['doc0_expected'] and analyzer.document_stats['doc3_actual']:
            matches = sum(1 for stat in analyzer.document_stats['doc3_actual'] if stat['match'])
            total = len(analyzer.document_stats['doc3_actual'])
            match_rate = (matches / total) * 100
            
            status = "🟢 OK" if match_rate > 80 else "🟡 NEEDS WORK" if match_rate > 60 else "🔴 CRITICAL"
            print(f"Doc 0 vs 3: {match_rate:.1f}% shoda {status}")
        
        print(f"\n📁 Podrobné výsledky:")
        print(f"  • Excel: {os.path.basename(excel_path)}")
        print(f"  • Sheets: Meta-Analysis, Statistics, Doc0_vs_Doc3_Comparison")
        print(f"  • Debug Sheets: Document_1_Debug, Document_2_Debug, Document_3_Debug")
        print(f"  • CSV debug soubory: {len(debug_csvs) if 'debug_csvs' in locals() else 0}")
        
        print(f"\n🎯 PRIORITNÍ AKCE:")
        priority_actions = []
        
        if 'Document 1' in doc_qualities and doc_qualities['Document 1']['quality'] < 70:
            priority_actions.append("1. Vyladit Document 1 prompt (metadata extrakce)")
        if 'Document 2' in doc_qualities and doc_qualities['Document 2']['quality'] < 60:
            priority_actions.append("2. Vyladit Document 2 prompt (struktura modelu)")
        if 'Document 3' in doc_qualities and doc_qualities['Document 3']['quality'] < 50:
            priority_actions.append("3. Vyladit Document 3 prompt (výsledky/parametry)")
        
        if analyzer.document_stats.get('doc0_expected') and analyzer.document_stats.get('doc3_actual'):
            mismatches = sum(1 for stat in analyzer.document_stats['doc3_actual'] if not stat['match'])
            if mismatches > len(analyzer.document_stats['doc3_actual']) * 0.3:
                priority_actions.append("4. Synchronizovat Document 0 a Document 3 prompty")
        
        if priority_actions:
            for action in priority_actions:
                print(f"  {action}")
        else:
            print("  🎉 Všechny dokumenty fungují dobře!")
        
    except Exception as e:
        logger.error(f"Kritická chyba: {e}")
        print(f"❌ Chyba: {e}")


if __name__ == "__main__":
    main()
