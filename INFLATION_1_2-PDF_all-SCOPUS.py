#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
INFLATION_META_ANALYSIS_v4_batch.py - Native PDF Support Batch Version
Zpracuje všechny PDF soubory ve složce a vytvoří jeden souhrnný Excel
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
from pathlib import Path

# Nastavení loggingu
logging.basicConfig(
    level=logging.DEBUG,  # Změněno na DEBUG pro více informací
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
        # FileHandler přidáme až v main() funkci
    ]
)
logger = logging.getLogger(__name__)
# Nastavíme vyšší úroveň pro některé knihovny, aby nezahlcovaly výstup
logging.getLogger('anthropic').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

# Claude API klíč
CLAUDE_API_KEY = ""

# Scopus API klíč
SCOPUS_API_KEY = ""

# Model
CLAUDE_MODEL = "claude-opus-4-20250514"

# Výstupní složka - bude nastavena v main() funkci
EXPORT_FOLDER = None

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

class PDFAnalyzer:
    """Hlavní třída pro analýzu PDF dokumentů s nativní podporou"""
    
    def __init__(self, api_key: str, export_folder: str):
        self.api_key = api_key
        self.export_folder = export_folder
        self.client = anthropic.Anthropic(api_key=api_key)
        self.current_study_id = 1  # Pro správné číslování studií
        
        # Scopus API session
        self.scopus_session = requests.Session()
        self.scopus_session.headers.update({
            'X-ELS-APIKey': SCOPUS_API_KEY,
            'Accept': 'application/json'
        })
        
    def analyze_pdf_native(self, pdf_path: str) -> Dict[str, Any]:
        """Analyzuje PDF pomocí nativní podpory Claude"""
        
        logger.info(f"🤖 Analyzuji: {os.path.basename(pdf_path)}")
        
        # Načteme PDF jako base64
        with open(pdf_path, "rb") as f:
            pdf_data = base64.standard_b64encode(f.read()).decode("utf-8")
        
        # Vytvoříme kompletní prompt
        complete_prompt = self._create_complete_extraction_prompt()
        
        # Vytvoříme nový klient pro každé volání (čistý kontext)
        fresh_client = anthropic.Anthropic(api_key=self.api_key)
        
        # Pošleme request s PDF dokumentem
        try:
            response = fresh_client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=8000,
                temperature=0.1,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "document",
                                "source": {
                                    "type": "base64",
                                    "media_type": "application/pdf",
                                    "data": pdf_data
                                }
                                # Odstranil jsem cache_control pro dávkové zpracování
                            },
                            {
                                "type": "text",
                                "text": complete_prompt
                            }
                        ]
                    }
                ]
            )
            
            text = response.content[0].text
            logger.info(f"✅ Odpověď přijata pro {os.path.basename(pdf_path)}")
            
            # Zpracujeme odpověď
            return self._parse_response(text)
            
        except Exception as e:
            logger.error(f"Chyba při analýze {os.path.basename(pdf_path)}: {e}")
            return {'error': str(e)}
    
    def _parse_response(self, text: str) -> Dict[str, Any]:
        """Parsuje odpověď od Claude"""
        
        # Debug log
        logger.debug(f"Délka odpovědi: {len(text)} znaků")
        
        lines = text.strip().split('\n')
        
        # Hledáme začátek tabulky (header)
        table_start = -1
        for i, line in enumerate(lines):
            if 'Idstudy\t' in line or line.startswith('Idstudy'):
                table_start = i
                logger.debug(f"Nalezen header tabulky na řádku {i}")
                break
        
        if table_start >= 0:
            # Extrahujeme řádky tabulky
            table_rows = []
            for line in lines[table_start + 1:]:
                if '\t' in line:
                    cols = line.split('\t')
                    if len(cols) == len(META_ANALYSIS_COLUMNS):
                        table_rows.append(cols)
                    else:
                        logger.warning(f"Řádek má {len(cols)} sloupců místo {len(META_ANALYSIS_COLUMNS)}")
            
            logger.debug(f"Extrahováno {len(table_rows)} řádků dat")
            return {'table_rows': table_rows}
        else:
            # Pokud nenajdeme tabulku, vrátíme raw text
            logger.warning("Tabulka nebyla nalezena v odpovědi")
            # Zkusíme najít alespoň nějaké strukturované informace
            if len(text) > 100:
                logger.debug(f"První část odpovědi: {text[:500]}...")
            return {'raw_text': text}
    
    def _create_complete_extraction_prompt(self) -> str:
        """Vytvoří kompletní prompt pro extrakci všech dat"""
        return """
 # AI-Optimized Meta-Analysis Research Assistant Instructions (Enhanced v4)

## CRITICAL SYSTEM DIRECTIVES

### MANDATORY COMPLIANCE REQUIREMENTS
- **NEVER leave any cell empty** - use "NA" for missing information
- **NEVER fabricate data** - only report verifiable information from sources
- **ALWAYS use exact column names** as specified below
- **ALWAYS follow the 0/1 coding system** for Yes/No questions (0 = No, 1 = Yes)
- **ALWAYS extract ALL inflation results** found in the paper
- **ALWAYS verify variable identification** using notation sections and context
- **ALWAYS reset assumptions for each new table** - never carry over structure assumptions
- **ALWAYS preserve numerical signs** - negative values must include minus sign

### OUTPUT FORMAT REQUIREMENTS
- Generate a table with exact column headers provided
- Each row = one inflation result from the paper  
- Fill every cell with either data or "NA"
- Use tab-separated format for easy Excel import
- Include header row with all column names

## TASK OVERVIEW
Extract data from academic PDF articles for meta-analysis dataset creation. Process the attached PDF systematically using the numbered questions below. Each question corresponds to a specific Excel column.

## CRITICAL NOTATION GUIDE (READ FIRST)

### ENHANCED VARIABLE IDENTIFICATION PROTOCOL

**Inflation Variables - Extended Recognition:**
- **Standard notations**: π, π*, πe, π̄, phi, φ, Π, π^*, π_t
- **Expected value notation**: E[π], E(π), 𝔼[π], E_t[π] - these ARE inflation values
- **Common labels**: "inflation", "inflation rate", "optimal inflation", "inflation target", "steady-state inflation"
- **Typical range**: -10% to 10% (annualized) - but can be outside this range
- **CRITICAL SIGN PRESERVATION**: 
 - Always check for negative signs (-) before numbers
 - Look for "deflation" which implies negative inflation
 - Check text descriptions: "negative inflation", "below zero"
 - Friedman rule typically implies negative optimal inflation around -4% to -5%
- **Context clues**: Often discussed with price stability, welfare costs, Friedman rule, zero lower bound
- **WARNING - Verify these carefully**:
 - V[π], Var[π], σ²(π) - likely variance, NOT inflation value
 - SD[π], σ(π) - likely standard deviation
 - Cov[π,x] - covariance, not inflation
 
**Verification Protocol for Ambiguous Notation:**
1. **Check surrounding text**: How is this value discussed?
2. **Check units**: Variance would be in (%)², inflation in %
3. **Check magnitude**: Variance typically much smaller than inflation
4. **Check table headers**: Often specify "mean" vs "variance"
5. **When uncertain**: Look for explicit definition in text

**Decision Rule**: 
- E[π] → Extract as inflation
- V[π] → Only extract if explicitly confirmed as inflation estimator, not variance

**Interest Rate Variables:**
- Common symbols: i, r, R, i*, r*, ī, r̄, i^n (nominal), r^r (real)
- Common labels: "interest rate", "nominal rate", "policy rate", "real rate"
- Typical range: -5% to 20% (annualized)
- Context clues: Often discussed with monetary policy, Taylor rule, Fisher equation

**Output Variables:**
- Common symbols: y, Y, ŷ, y*, GDP, y_gap
- Common labels: "output", "output gap", "GDP", "production"
- Context clues: Often discussed with business cycles, welfare

**CRITICAL**: Always check the paper's notation section or variable definitions first!

## DATA EXTRACTION FRAMEWORK

### 1. AUTHOR INFORMATION

**1.1 (INVARIANT)** 
- **Task**: Extract author names in APA format
- **Format**: Last name, First Initial. (Year). Example: "Smith, J. (2023)"
- **Source**: PDF article header/title page
- **Output**: Text string
- **Column**: `Author`

**1.2 (INVARIANT)**
- **Task**: Find author institutional affiliations
- **Process**: Check PDF title page, footnotes, and author information sections
- **Format**: Institution name only, comma-separated for multiple authors
- **If not found**: Write "Cannot find affiliation"
- **Column**: `Author_Affiliation`

**1.3 (INVARIANT)**
- **Task**: Extract DOI (Digital Object Identifier)
- **Process**: 1) Search throughout entire PDF for DOI pattern 2) Look for "DOI:", "doi:", "https://doi.org/", "http://dx.doi.org/" 3) Check title page, first page, abstract, references 4) DOI format: 10.xxxx/xxxxx
- **Format**: Full DOI including "10." prefix
- **If not found**: Write "Cannot find DOI"
- **Column**: `DOI`

### 2. JOURNAL INFORMATION

**2.1 (INVARIANT)**
- **Task**: Extract journal name
- **Source**: PDF header, first page, or citation info
- **Format**: Exact journal name as appears in PDF
- **If not found**: "Cannot find journal name"
- **Column**: `Journal_Name`

**2.2 (INVARIANT)**
- **Task**: External API will provide impact factor
- **Format**: Leave as "NA" - will be filled externally
- **Column**: `Impact_Factor`

### 3. CITATION INFORMATION

**3.1 (INVARIANT)**
- **Task**: Count citation numbers using Scopus API
- **Source**: Scopus Abstract Citations Count API
- **Process**: 1) Use DOI from step 1.3 2) Call Scopus API with DOI 3) Extract citation count from response
- **Format**: Number only
- **If not found**: "Cannot find citation count"
- **Column**: `Num_Citations`

### 4. PUBLICATION DATE

**4.1 (INVARIANT)**
- **Task**: Extract publication year
- **Source**: Search throughout entire PDF - title page, header, footer, reference section, journal information, copyright notice
- **Process**: 1) Check title page first 2) Check headers/footers on multiple pages 3) Check reference section 4) Check journal citation format anywhere in document
- **Format**: 4-digit year only
- **Column**: `Year`

### 5. RESEARCH SPECIFICATIONS

**5.1 (INVARIANT)**
- **Task**: Identify base economic model type
- **Examples**: "DSGE", "New Keynesian", "RBC", "VAR", "OLG", "Cash-in-advance"
- **Source**: PDF abstract, introduction, or methodology section
- **Column**: `Base_Model_Type`

**5.2 (INVARIANT)**
- **Task**: Determine if model has augmentations
- **Process**: Look for model modifications, extensions, or additions beyond standard version
- **Output**: 1 (Yes) or 0 (No)
- **Column**: `Augmented_base_model`

**5.3 (VARIANT)**
- **Task**: Describe model augmentations
- **Condition**: Only if 5.2 = 1, otherwise "NA"
- **Format**: Brief description (2-5 words)
- **Column**: `Augmentation_Description`

**5.4 (VARIANT)**
- **Task**: Check for Ramsey rule consideration
- **Search terms**: "Ramsey", "optimal policy", "welfare maximization", "commitment"
- **Output**: 1 (Yes) or 0 (No)
- **Column**: `Ramsey_Rule`

**5.5 (VARIANT)**
- **Task**: Identify household agents in model
- **Search terms**: "household", "consumers", "families", "representative agent"
- **Output**: 1 (Yes) or 0 (No)
- **Column**: `HH_Included`

**5.6 (VARIANT)**
- **Task**: Identify firm/entrepreneur agents
- **Search terms**: "firms", "entrepreneurs", "producers", "companies"
- **Output**: 1 (Yes) or 0 (No)
- **Column**: `Firms_Included`

**5.7 (VARIANT)**
- **Task**: Identify banking sector in model
- **Search terms**: "banks", "financial intermediaries", "banking sector", "credit"
- **Critical**: Re-read carefully if uncertain
- **Output**: 1 (Yes) or 0 (No)
- **Column**: `Banks_Included`

**5.8 (VARIANT) - GOVERNMENT VERIFICATION**
- **Task**: Identify if government plays ACTIVE ROLE in the model
- **CRITICAL VERIFICATION**: Government must be an active model component, not just mentioned
- **Evidence of ACTIVE government role**:
 - Government budget constraint equation
 - Government spending (G) in resource constraint
 - Fiscal policy rules or instruments
 - Tax rates that affect equilibrium
 - Government debt dynamics
 - Transfer payments that enter household budget
- **NOT sufficient for marking as 1**:
 - Only mentioning "government" in text
 - Discussing government in literature review
 - Government only as policy discussion
- **Search enhanced**: Look for equations with G_t, τ (tax), T (transfers), B^g (gov bonds)
- **Output**: 1 (Yes - active role) or 0 (No - not in model)
- **Column**: `Government_Included`

**5.9 (INVARIANT)**
- **Task**: Identify what households maximize
- **Common answers**: "utility", "welfare", "consumption plus leisure", "expected utility"
- **Format**: Short phrase (2-4 words)
- **Column**: `HH_Maximization_Type`

**5.10 (INVARIANT)**
- **Task**: List variables in household optimization
- **Common answers**: "consumption, labor", "consumption, money, leisure", "consumption, hours worked"
- **Format**: Comma-separated list
- **Column**: `HH_Maximized_Vars`

**5.11 (VARIANT)**
- **Task**: Identify all firm types in model
- **Process**: 1) Look for explicit model equations or mathematical formulations involving firms 2) Check if firms are actual decision-making agents with optimization problems 3) Don't count casual mentions - need evidence of firms as active model components
- **Examples**: "intermediate goods firms, final goods firms", "wholesale firms, retail firms"
- **Format**: Comma-separated list
- **Robustness Check**: Verify firms have optimization problems, production functions, or decision variables
- **Column**: `Producer_Type`

**5.12 (VARIANT)**
- **Task**: Identify market structure assumptions for each firm type
- **Search terms**: "monopolistic competition", "perfect competition", "monopoly", "Dixit-Stiglitz"
- **Format**: "firm type: assumption" format
- **Example**: "intermediate firms: monopolistic competition, final firms: perfect competition"
- **Column**: `Producer_Assumption`

**5.13 (VARIANT)**
- **Task**: Check for other agents beyond households/firms/banks/government
- **Exclusions**: Do not count households, firms, banks, government
- **Examples**: "labor unions", "central bank", "foreign sector"
- **Output**: 1 (Yes) or 0 (No)
- **Column**: `Other_Agent_Included`

**5.14 (VARIANT)**
- **Task**: Describe other agents' assumptions
- **Condition**: Only if 5.13 = 1, otherwise "NA"
- **Format**: Brief description
- **Column**: `Other_Agent_Assumptions`

**5.15 (INVARIANT)**
- **Task**: Determine if research uses empirical data/estimation
- **Process**: Look if the result is model output using calibration (not empirical) or based on regression analysis/data estimation (empirical)
- **Output**: 1 (Yes) or 0 (No)
- **Column**: `Empirical_Research`

**5.16 (INVARIANT)**
- **Task**: Identify country/region of data used
- **Process**: Look for calibration data, empirical data sources, parameter values "calibrated to X economy"
- **Examples**: "US", "Euro Area", "UK", "Japan"
- **If none specified**: "NA"
- **Column**: `Country`

**5.17 (VARIANT)**
- **Task**: Check price flexibility assumption for each inflation result
- **Process**: For each inflation result, determine if prices are flexible or sticky
- **Output**: 1 (flexible prices) or 0 (sticky prices)
- **Column**: `Flexible_Price_Assumption`

**5.18 (VARIANT)**
- **Task**: Check if inflation is exogenous
- **Process**: Determine if inflation is set externally (exogenous) vs. determined by model (endogenous)
- **Search terms**: "exogenous inflation", "inflation target", "inflation assumption", "given inflation rate"
- **Output**: 1 (exogenous) or 0 (endogenous)
- **Column**: `Exogenous_Inflation`

**5.19 (VARIANT)**
- **Task**: Check for growth parameters
- **Search terms**: "growth rate", "trend growth", "g", "productivity growth"
- **Output**: 1 (Yes) or 0 (No)
- **Column**: `Growth_Included`

**5.20 (VARIANT)**
- **Task**: Check zero lower bound environment
- **Process**: Determine if zero lower bound constraint is considered in the model
- **Search terms**: "zero lower bound", "ZLB", "effective lower bound", "ELB"
- **Output**: 1 (Yes) or 0 (No)
- **Column**: `Zero_Lower_Bound`

### CRITICAL SECTION: RESULTS EXTRACTION WITH ENHANCED PROTOCOLS

**5.21 (VARIANT)**
- **Task**: Identify and map all results locations
- **Enhanced Process**: 
 1. Create a mental map of ALL tables, figures, and text sections with numerical results
 2. Specifically note which tables contain inflation, interest rates, and other variables
 3. Check table titles, captions, and column headers carefully
 4. Note section numbers where results are discussed in text
 5. Look for results in: main text, appendices, online appendices, footnotes
- **Format**: "Table 1 (inflation & interest rates), Table 3 (welfare), Text Section 4.2"
- **Column**: `Results_Table`

### ENHANCED INFLATION EXTRACTION PROTOCOL

**5.22 CRITICAL INFLATION EXTRACTION**
- **Task**: Extract ALL inflation values with EXACT precision
- **MANDATORY SIGN CHECK PROTOCOL**:
 1. **Visual Inspection**: Look for minus sign (-) before the number
 2. **Context Verification**: Check surrounding text for words like "negative", "deflation", "below zero"
 3. **Model Type Check**: 
    - Flexible price models often have negative optimal inflation (Friedman rule)
    - New Keynesian models typically have values near zero
    - ZLB models often have positive optimal inflation
 4. **Range Verification**: 
    - Friedman rule: typically -3% to -5%
    - New Keynesian: typically -1% to +1%
    - With ZLB: typically +1% to +4%
    - But can be outside these ranges!
 5. **Format Preservation**: 
    - If source shows "-2.5%", extract as "-2.5"
    - If source shows "negative 2.5 percent", extract as "-2.5"
    - If source shows "deflation of 2.5%", extract as "-2.5"
- **Column**: `Results_Inflation`

**5.40 INTEREST RATE EXTRACTION**
- **Task**: Extract interest rates corresponding to each inflation value
- **Process**: 
 1. Find the interest rate that pairs with each inflation result
 2. Check Fisher equation relationship (nominal = real + inflation)
 3. Preserve signs exactly as shown
- **Column**: `Interest_Rate`

### EXTRACTION VERIFICATION PROTOCOL

After extracting from EACH source:
1. **Sign Double-Check**: Re-verify all negative values are captured with minus signs
2. **Completeness Check**: Count results in source vs. extracted rows
3. **Relationship Check**: Verify economic relationships make sense

**5.23 (INVARIANT)**
- **Task**: Count total distinct inflation results
- **Process**: Count all unique inflation values across ALL sources
- **Output**: Total count
- **Verification**: This number should match your final row count
- **Column**: `Num_Inflation_Results`

**5.24 (VARIANT)**
- **Task**: Identify author's preferred estimate
- **Enhanced identifiers**: 
 - "baseline result"
 - "main specification"  
 - "preferred estimate"
 - "benchmark"
 - Results emphasized in abstract/conclusion
 - Results used for policy implications
- **Output**: 1 (preferred) or 0 (not preferred)
- **Column**: `Preferred_Estimate`

**5.25 (VARIANT)**
- **Task**: Explain why estimate is preferred
- **Condition**: Only for preferred estimates (5.24 = 1)
- **Format**: 1-2 professional sentences
- **Column**: `Reason_for_Preferred`

**5.26 (VARIANT)**
- **Task**: Describe assumptions for each inflation result
- **Process**: Note the specific model variant/calibration/scenario
- **Format**: Brief assumption description
- **Example**: "Baseline calibration with sticky prices", "With ZLB constraint"
- **Column**: `Results_Inflation_Assumption`

### ENHANCED PARAMETER EXTRACTION PROTOCOL

**CRITICAL PARAMETER SEARCH STRATEGY**:
1. **Primary Sources** (Check in this order):
  - Calibration tables (often Table 1 or in appendix)
  - Parameter tables/sections
  - Text descriptions of calibration
  - Footnotes with parameter values
  - Online appendices
  
2. **Search Patterns**:
  - Look for sections titled: "Calibration", "Parameters", "Baseline Values"
  - Search for parameter symbols AND their descriptions
  - Check around equations where parameters first appear
  - Look for phrases like "we set", "calibrated to", "following [citation]"

3. **Common Parameter Locations**:
  - After model description, before results
  - In subsection on calibration/estimation
  - In tables with "Parameter", "Value", "Description" columns
  - In footnotes explaining choices

4. **Zero Value Protocol**:
  - Zero IS a valid parameter value - extract as "0" or "0.0"
  - Common zero parameters: money in utility (cashless), adjustment costs (flexible)
  - Never skip zero values

**5.27 (VARIANT) - Households' discount factor**
- **Common symbols**: β, beta, δ
- **Common values**: 0.96-0.995 (quarterly), 0.98-0.999 (monthly)
- **Search enhanced**: "discount factor", "beta", "β", "time preference"
- **Column**: `Households_discount_factor`

**5.28 (VARIANT) - Consumption curvature parameter**
- **Common symbols**: σ, gamma, CRRA, IES (as 1/σ)
- **Common values**: 1-4 (risk aversion), 0.25-1 (as IES)
- **Search enhanced**: "risk aversion", "CRRA", "intertemporal elasticity", "curvature"
- **Column**: `Consumption_curvature_parameter`

**5.29 (VARIANT) - Disutility of labor**
- **Common symbols**: χ, psi, ψ, xi
- **Context**: Weight on labor/leisure in utility function
- **Search enhanced**: "labor disutility", "labor weight", "preference for leisure"
- **Column**: `Disutility_of_labor`

**5.30 (VARIANT) - Inverse of labor supply elasticity**
- **Common symbols**: φ, phi, ν, nu, η
- **Common values**: 0.5-5 (Frisch elasticity is 1/φ)
- **Search enhanced**: "Frisch elasticity", "labor supply elasticity", "labor curvature"
- **Column**: `Inverse_of_labor_supply_elasticity`

**5.31 (VARIANT) - Money curvature parameter**
- **Common symbols**: ξ, xi, ζ, zeta, b
- **Context**: In money-in-utility or cash-in-advance models
- **Note**: Often 0 in cashless New Keynesian models
- **Search enhanced**: "money demand elasticity", "money in utility"
- **Column**: `Money_curvature_parameter`

**5.32 (VARIANT) - Loan-to-value ratio**
- **Common symbols**: LTV, m, θ
- **Common values**: 0.7-0.9
- **Context**: In models with collateral constraints
- **Search enhanced**: "LTV", "collateral requirement", "borrowing constraint"
- **Column**: `Loan_to_value_ratio`

**5.33 (VARIANT) - Labor share of output**
- **Common symbols**: 1-α, labor share, wage share
- **Common values**: 0.6-0.7
- **Search enhanced**: "labor share", "capital share" (then 1-capital share), "Cobb-Douglas"
- **Column**: `Labor_share_of_output`

**5.34 (VARIANT) - Depositors' discount factor**
- **Common symbols**: β_d, beta_d, β_s (savers)
- **Context**: In models with heterogeneous agents
- **Search enhanced**: "patient households", "savers", "depositors"
- **Column**: `Depositors_discount_factor`

**5.35 (VARIANT) - Price adjustment cost**
- **Common symbols**: κ, kappa, φ_p, Rotemberg parameter
- **Context**: Rotemberg (1982) quadratic adjustment costs
- **Note**: Different from Calvo parameter
- **Search enhanced**: "price adjustment cost", "Rotemberg", "menu cost"
- **Column**: `Price_adjustment_cost`

**5.36 (VARIANT) - Elasticity of substitution between goods**
- **Common symbols**: ε, epsilon, η, theta
- **Common values**: 6-11 (implies markup of 20%-10%)
- **Search enhanced**: "elasticity of substitution", "markup", "market power"
- **Column**: `Elasticity_of_substitution_between_goods`

**5.37 (VARIANT) - AR(1) coefficient of TFP**
- **Common symbols**: ρ_a, rho_a, ρ_z, persistence
- **Common values**: 0.9-0.99
- **Search enhanced**: "TFP persistence", "technology shock", "AR(1)", "autocorrelation"
- **Column**: `AR1_coefficient_of_TFP`

**5.38 (VARIANT) - Standard deviation to TFP shock**
- **Common symbols**: σ_a, sigma_a, σ_z, std(a)
- **Common values**: 0.006-0.02
- **Search enhanced**: "TFP volatility", "technology shock", "standard deviation"
- **Column**: `Std_dev_to_TFP_shock`

**5.39 (VARIANT)**
- **Task**: Extract standard deviation of inflation result
- **Process**: Look for uncertainty measures, confidence intervals, posterior distributions
- **May appear**: In parentheses, brackets, or separate column
- **Column**: `Std_Dev_Inflation`

### 6. STUDY IDENTIFICATION

**6.1 (INVARIANT)** - Assign sequential study ID → **Column**: `Idstudy`
**6.2 (VARIANT)** - Assign sequential estimate ID for each inflation result → **Column**: `IdEstimate`

## EXTRACTION QUALITY CONTROL

**Critical Final Checks**:
1. **Sign Verification**: Re-check ALL negative values have minus signs
2. **Parameter Completeness**: Did you check ALL possible parameter locations?
3. **Count Verification**: Number of rows matches count of inflation results
4. **Zero Values**: Any zeros properly recorded as "0" not "NA"
5. **Government Role**: If Government_Included = 1, verify active model role exists

## ENHANCED VALIDATION CHECKLIST

### Pre-Extraction:
- [ ] Located paper's notation section
- [ ] Identified model type (affects expected parameter ranges)
- [ ] Found calibration/parameter section

### During Extraction:
- [ ] Checked signs on ALL numerical values
- [ ] Searched multiple locations for each parameter
- [ ] Verified economic relationships make sense
- [ ] Preserved exact numerical precision
- [ ] Confirmed government has active model role if marked as 1

### Post-Extraction:
- [ ] All negative inflation values show minus signs
- [ ] Parameter search was exhaustive (tables, text, appendix)
- [ ] Zero values recorded as "0" not "NA"
- [ ] Row count matches inflation result count
- [ ] Government inclusion based on model equations, not just mentions

## CRITICAL REMINDERS

1. **SIGN PRESERVATION IS MANDATORY** - double-check all negative values
2. **PARAMETER SEARCH MUST BE EXHAUSTIVE** - check tables, text, footnotes, appendices
3. **ZEROS ARE VALID** - never skip them
4. **FRIEDMAN RULE IMPLIES NEGATIVE** - typically -3% to -5% inflation
5. **When in doubt about signs** - check context and model type
6. **GOVERNMENT MUST BE IN MODEL** - not just mentioned in text

## REQUIRED OUTPUT FORMAT

### EXACT COLUMN ORDER (MANDATORY)

## REQUIRED OUTPUT FORMAT

### EXACT COLUMN ORDER (MANDATORY)
```
Idstudy	IdEstimate	Author	Author_Affiliation	DOI	Journal_Name	Num_Citations	Year	Base_Model_Type	Augmented_base_model	Augmentation_Description	Ramsey_Rule	HH_Included	Firms_Included	Banks_Included	Government_Included	HH_Maximization_Type	HH_Maximized_Vars	Producer_Type	Producer_Assumption	Other_Agent_Included	Other_Agent_Assumptions	Empirical_Research	Country	Flexible_Price_Assumption	Exogenous_Inflation	Households_discount_factor	Consumption_curvature_parameter	Disutility_of_labor	Inverse_of_labor_supply_elasticity	Money_curvature_parameter	Loan_to_value_ratio	Labor_share_of_output	Depositors_discount_factor	Price_adjustment_cost	Elasticity_of_substitution_between_goods	AR1_coefficient_of_TFP	Std_dev_to_TFP_shock	Zero_Lower_Bound	Results_Table	Results_Inflation	Results_Inflation_Assumption	Preferred_Estimate	Reason_for_Preferred	Std_Dev_Inflation	Interest_Rate	Impact_Factor
```

### PROCESSING WORKFLOW (WITH ENHANCED PROTOCOLS)
1. **Read PDF completely** and identify notation/variable definitions
2. **Map all results locations** (tables, figures, text) including parameter tables
3. **Answer questions 1.1-5.20** systematically
4. **For EACH table: Execute Table Reset Protocol**
5. **For large tables: Execute Extraction Completeness Protocol**
6. **Extract results with anomaly detection active**
7. **Apply Zero Value Protocol for parameters**
8. **Validate using enhanced checklist and quality control**
9. **Search external sources** when required
10. **Create multiple rows** for multiple inflation results
11. **Fill every cell** with data or "NA" (including zeros)
12. **Format as tab-separated table**
"""
    
    def process_results_to_dataframe(self, results: Dict[str, Any], pdf_path: str, study_id: int) -> pd.DataFrame:
        """Zpracuje výsledky do DataFrame s unikátním Idstudy"""
        
        if 'table_rows' in results and results['table_rows']:
            # Máme tabulku - vytvoříme DataFrame
            try:
                df = pd.DataFrame(results['table_rows'], columns=META_ANALYSIS_COLUMNS)
                
                # Nastavíme správné Idstudy pro všechny řádky této studie
                df['Idstudy'] = str(study_id)
                
                # Vyčistíme data
                df = df.replace('', 'NA')
                df = df.fillna('NA')
                
                logger.info(f"✅ Vytvořeno {len(df)} řádků pro studii {study_id}")
                return df
            except Exception as e:
                logger.error(f"Chyba při vytváření DataFrame: {e}")
                logger.debug(f"Počet řádků: {len(results['table_rows'])}")
                if results['table_rows']:
                    logger.debug(f"Počet sloupců v prvním řádku: {len(results['table_rows'][0])}")
                    logger.debug(f"Očekávaný počet sloupců: {len(META_ANALYSIS_COLUMNS)}")
                
                # Pokus o opravu - vytvoříme DataFrame s dostupnými daty
                if results['table_rows']:
                    # Vezmeme jen tolik sloupců, kolik máme
                    min_cols = min(len(results['table_rows'][0]), len(META_ANALYSIS_COLUMNS))
                    truncated_data = [row[:min_cols] for row in results['table_rows']]
                    truncated_cols = META_ANALYSIS_COLUMNS[:min_cols]
                    
                    try:
                        df = pd.DataFrame(truncated_data, columns=truncated_cols)
                        # Doplníme chybějící sloupce
                        for col in META_ANALYSIS_COLUMNS:
                            if col not in df.columns:
                                df[col] = 'NA'
                        
                        df['Idstudy'] = str(study_id)
                        df = df.replace('', 'NA')
                        df = df.fillna('NA')
                        
                        logger.warning(f"⚠️ Částečně úspěšné zpracování - vytvořeno {len(df)} řádků s omezenými daty")
                        return df[META_ANALYSIS_COLUMNS]  # Vrátíme ve správném pořadí
                        
                    except Exception as e2:
                        logger.error(f"Selhala i opravná extrakce: {e2}")
        
        elif 'raw_text' in results:
            logger.info(f"📝 Dostali jsme raw text místo tabulky pro {os.path.basename(pdf_path)}")
            logger.debug(f"Délka textu: {len(results['raw_text'])} znaků")
            
        # Vytvoříme prázdný DataFrame s NA hodnotami
        logger.warning(f"⚠️ Nepodařilo se extrahovat strukturovaná data pro {os.path.basename(pdf_path)}")
        
        empty_row = {col: 'NA' for col in META_ANALYSIS_COLUMNS}
        empty_row['Idstudy'] = str(study_id)
        empty_row['IdEstimate'] = '1'
        
        return pd.DataFrame([empty_row])
    
    def get_scopus_citations(self, doi: str) -> str:
        """Získá počet citací z Scopus API pomocí DOI"""
        try:
            if not doi or doi == "NA" or doi == "Cannot find DOI":
                return "NA"
            
            # Scopus Abstract Citations Count API
            url = "https://api.elsevier.com/content/abstract/citation-count"
            params = {'doi': doi}
            
            # Zvýšený timeout a retry mechanismus
            for attempt in range(3):  # 3 pokusy
                try:
                    response = self.scopus_session.get(url, params=params, timeout=30)  # Zvýšeno na 30s
                    
                    if response.status_code == 200:
                        data = response.json()
                        citation_response = data.get('citation-count-response', {})
                        document = citation_response.get('document', {})
                        citation_count = document.get('citation-count', '0')
                        
                        logger.info(f"✅ Scopus citace pro DOI {doi}: {citation_count}")
                        return str(citation_count)
                    elif response.status_code == 404:
                        logger.warning(f"DOI {doi} nenalezen v Scopus databázi")
                        return "0"
                    else:
                        logger.warning(f"Scopus API chyba {response.status_code} pro DOI {doi}")
                        if attempt < 2:  # Poslední pokus
                            time.sleep(2)  # Pauza před dalším pokusem
                            continue
                        return "NA"
                        
                except requests.exceptions.Timeout:
                    logger.warning(f"Timeout při pokusu {attempt + 1}/3 pro DOI {doi}")
                    if attempt < 2:
                        time.sleep(3)  # Delší pauza před retry
                        continue
                    return "NA"
                except Exception as e:
                    logger.warning(f"Chyba při pokusu {attempt + 1}/3 pro DOI {doi}: {e}")
                    if attempt < 2:
                        time.sleep(2)
                        continue
                    return "NA"
            
            return "NA"
                
        except Exception as e:
            logger.warning(f"Chyba při získávání Scopus citací pro DOI {doi}: {e}")
            return "NA"
    
    def search_google_scholar(self, title: str, authors: str) -> str:
        """Vyhledá počet citací na Google Scholar (fallback)"""
        try:
            search_query = f"{title} {authors}".strip()
            if not search_query:
                return "NA"
                
            url = f"https://scholar.google.com/scholar?q={search_query}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Hledáme citace
                for div in soup.find_all('div', class_='gs_fl'):
                    cited_match = re.search(r'Cited by (\d+)', div.text)
                    if cited_match:
                        return cited_match.group(1)
            
            return "NA"
            
        except Exception as e:
            logger.warning(f"Chyba při hledání citací: {e}")
            return "NA"
    
    def search_impact_factor(self, journal_name: str) -> str:
        """Vyhledá impact factor časopisu"""
        try:
            if not journal_name or journal_name == "NA":
                return "NA"
                
            # Známé impact faktory
            known_factors = {
                "Economic Inquiry": "1.540",
                # Můžete přidat další známé časopisy
            }
            
            for known_journal, factor in known_factors.items():
                if known_journal.lower() in journal_name.lower():
                    return factor
            
            # Obecné hledání
            search_query = f"{journal_name} impact factor"
            url = f"https://www.resurchify.com/search?q={search_query}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                # Hledáme impact factor v textu
                impact_match = re.search(r'Impact\s*[Ff]actor[:\s]+(\d+\.?\d*)', response.text)
                if impact_match:
                    return impact_match.group(1)
            
            return "NA"
            
        except Exception as e:
            logger.warning(f"Chyba při hledání impact faktoru: {e}")
            return "NA"
    
    def process_folder(self, folder_path: str) -> pd.DataFrame:
        """Zpracuje všechny PDF ve složce a vrátí souhrnný DataFrame"""
        
        # Najdeme všechny PDF soubory
        pdf_files = list(Path(folder_path).glob("*.pdf"))
        
        if not pdf_files:
            logger.warning("Ve složce nebyly nalezeny žádné PDF soubory")
            return pd.DataFrame(columns=META_ANALYSIS_COLUMNS)
        
        logger.info(f"📚 Nalezeno {len(pdf_files)} PDF souborů pro zpracování")
        
        all_results = []
        successful_count = 0
        failed_count = 0
        
        for idx, pdf_path in enumerate(pdf_files, 1):
            print(f"\n{'='*60}")
            print(f"📄 Zpracovávám {idx}/{len(pdf_files)}: {pdf_path.name}")
            print(f"{'='*60}")
            
            # Kontrola velikosti
            file_size = pdf_path.stat().st_size / (1024 * 1024)  # MB
            print(f"📏 Velikost: {file_size:.2f} MB")
            
            if file_size > 32:
                logger.warning(f"⚠️ PŘESKAKUJI: {pdf_path.name} je větší než 32 MB limit")
                failed_count += 1
                continue
            
            try:
                # Delší pauza mezi requesty pro stabilitu
                if idx > 1:
                    wait_time = 5  # 5 sekund mezi requesty
                    print(f"⏳ Čekám {wait_time} sekund před dalším requestem...")
                    time.sleep(wait_time)
                
                # Analyzujeme PDF
                results = self.analyze_pdf_native(str(pdf_path))
                
                # Kontrola výsledků
                if 'error' in results:
                    logger.error(f"❌ Chyba API: {results['error']}")
                    failed_count += 1
                    continue
                
                # Zpracujeme výsledky
                df_study = self.process_results_to_dataframe(results, str(pdf_path), self.current_study_id)
                
                # Kontrola, zda máme validní data
                if df_study.empty or (len(df_study) == 1 and all(df_study.iloc[0] == 'NA')):
                    logger.warning(f"⚠️ Žádná data extrahována z {pdf_path.name}")
                    failed_count += 1
                    
                    # Uložíme debug info
                    debug_path = os.path.join(self.export_folder, f"debug_{pdf_path.stem}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
                    with open(debug_path, 'w', encoding='utf-8') as f:
                        json.dump(results, f, ensure_ascii=False, indent=2)
                    logger.info(f"📝 Debug info uloženo: {debug_path}")
                else:
                    # Doplníme impact factor pro první řádek studie
                    first_row = df_study.iloc[0]
                    
                    # Impact factor
                    if first_row['Journal_Name'] != 'NA':
                        impact = self.search_impact_factor(first_row['Journal_Name'])
                        df_study['Impact_Factor'] = impact
                        logger.info(f"  📊 Impact factor: {impact}")
                    
                    # Citace budou zpracovány na konci v batch módu
                    logger.info(f"  📊 DOI nalezeno: {first_row['DOI']} - citace budou zpracovány na konci")
                    
                    # Přidáme k celkovým výsledkům
                    all_results.append(df_study)
                    successful_count += 1
                    
                    print(f"✅ Úspěšně zpracováno: {len(df_study)} inflačních odhadů")
                
                # Zvýšíme ID pro další studii
                self.current_study_id += 1
                
            except Exception as e:
                logger.error(f"❌ Neočekávaná chyba při zpracování {pdf_path.name}: {e}")
                failed_count += 1
                
                # Uložíme error info
                error_info = {
                    'file': pdf_path.name,
                    'error': str(e),
                    'type': type(e).__name__
                }
                error_path = os.path.join(self.export_folder, f"error_{pdf_path.stem}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
                with open(error_path, 'w', encoding='utf-8') as f:
                    json.dump(error_info, f, ensure_ascii=False, indent=2)
                
                continue
        
        # Finální statistiky
        print(f"\n{'='*60}")
        print(f"📊 Zpracování dokončeno:")
        print(f"  ✅ Úspěšně: {successful_count}")
        print(f"  ❌ Neúspěšně: {failed_count}")
        print(f"  📁 Celkem: {len(pdf_files)}")
        print(f"{'='*60}")
        
        # Spojíme všechny výsledky
        if all_results:
            final_df = pd.concat(all_results, ignore_index=True)
            logger.info(f"\n✅ Celkem {successful_count} úspěšných studií s {len(final_df)} řádky")
            return final_df
        else:
            logger.warning("Nebyly získány žádné výsledky")
            return pd.DataFrame(columns=META_ANALYSIS_COLUMNS)

    def process_citations_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        """Zpracuje citace pro všechny DOI najednou na konci"""
        
        logger.info("📊 Zpracovávám citace pro všechny DOI...")
        
        # Najdeme unikátní DOI
        unique_dois = df[df['DOI'] != 'NA'][df['DOI'] != 'Cannot find DOI']['DOI'].unique()
        
        if len(unique_dois) == 0:
            logger.warning("Žádné validní DOI k zpracování")
            return df
        
        logger.info(f"Našel jsem {len(unique_dois)} unikátních DOI pro zpracování")
        
        # Zpracujeme citace pro každé DOI
        citation_results = {}
        for doi in unique_dois:
            logger.info(f"Získávám citace pro DOI: {doi}")
            citations = self.get_scopus_citations(doi)
            citation_results[doi] = citations
            time.sleep(1)  # Krátká pauza mezi requesty
        
        # Aktualizujeme DataFrame
        for doi, citations in citation_results.items():
            df.loc[df['DOI'] == doi, 'Num_Citations'] = citations
        
        logger.info("✅ Citace zpracovány pro všechny DOI")
        return df

def main():
    """Hlavní funkce"""
    print("=" * 80)
    print(" INFLATION META-ANALYSIS v4.0 BATCH - Native PDF + Scopus API ".center(80, "="))
    print("=" * 80)
    print("\nDávkové zpracování PDF souborů s nativní podporou Claude Opus 4")
    print("Citace získávány z Scopus API pomocí DOI")
    print("Všechny výsledky budou uloženy do jednoho Excel souboru\n")
    
    # Výběr složky s PDF soubory
    print("📁 Vyberte složku obsahující PDF soubory...")
    root = tk.Tk()
    root.withdraw()
    
    pdf_folder = filedialog.askdirectory(
        title="Vyberte složku s PDF soubory pro analýzu"
    )
    
    if not pdf_folder:
        print("❌ Nebyla vybrána složka")
        root.destroy()
        return
    
    print(f"✅ Vybraná složka: {pdf_folder}")
    
    # Výběr složky pro uložení výsledků
    print("\n📁 Vyberte složku pro uložení výsledků...")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_export = os.path.join(script_dir, "AI_export_batch")
    
    export_folder = filedialog.askdirectory(
        title="Vyberte složku pro uložení výsledků",
        initialdir=script_dir
    )
    
    root.destroy()
    
    if not export_folder:
        export_folder = default_export
        print(f"💾 Použiji výchozí složku: {export_folder}")
    else:
        print(f"💾 Vybraná složka: {export_folder}")
    
    # Vytvoříme složku pokud neexistuje
    os.makedirs(export_folder, exist_ok=True)
    
    # Inicializace
    analyzer = PDFAnalyzer(CLAUDE_API_KEY, export_folder)
    
    try:
        # Zpracování všech PDF ve složce
        print("\n🚀 Spouštím dávkové zpracování...")
        final_df = analyzer.process_folder(pdf_folder)
        
        if final_df.empty:
            print("\n❌ Nebyly získány žádné výsledky k uložení")
            return
        
        # Zpracování citací pro všechny DOI
        final_df = analyzer.process_citations_batch(final_df)

        # Zobrazení souhrnu výsledků
        print("\n" + "=" * 80)
        print(" SOUHRN VÝSLEDKŮ ".center(80, "="))
        print("=" * 80)
        
        # Statistiky
        unique_studies = final_df['Idstudy'].nunique()
        total_estimates = len(final_df)
        
        print(f"\n📊 Statistiky:")
        print(f"  • Počet studií: {unique_studies}")
        print(f"  • Celkem inflačních odhadů: {total_estimates}")
        print(f"  • Průměr odhadů na studii: {total_estimates/unique_studies:.1f}")
        
        # Přehled studií
        print(f"\n📚 Přehled studií:")
        for study_id in sorted(final_df['Idstudy'].unique()):
            study_data = final_df[final_df['Idstudy'] == study_id].iloc[0]
            study_count = len(final_df[final_df['Idstudy'] == study_id])
            author = study_data['Author'] if study_data['Author'] != 'NA' else 'Neznámý autor'
            year = study_data['Year'] if study_data['Year'] != 'NA' else '????'
            print(f"  {study_id}. {author} ({year}) - {study_count} odhadů")
        
        # Uložení výsledků
        print("\n💾 Ukládám souhrnné výsledky...")
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Excel export
        excel_path = os.path.join(export_folder, f"meta_analysis_batch_{timestamp}.xlsx")
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            # Hlavní data
            final_df.to_excel(writer, sheet_name='Meta-Analysis', index=False)
            
            # Souhrn
            summary_df = pd.DataFrame({
                'Metric': ['Total Studies', 'Total Estimates', 'Average per Study', 'Processing Date'],
                'Value': [unique_studies, total_estimates, f"{total_estimates/unique_studies:.1f}", timestamp]
            })
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Validace
            validation_df = pd.DataFrame({
                'Study_ID': final_df['Idstudy'].unique(),
                'Author': [final_df[final_df['Idstudy']==sid]['Author'].iloc[0] for sid in final_df['Idstudy'].unique()],
                'Estimates': [len(final_df[final_df['Idstudy']==sid]) for sid in final_df['Idstudy'].unique()],
                'Has_Parameters': [
                    'Yes' if final_df[final_df['Idstudy']==sid]['Households_discount_factor'].iloc[0] != 'NA' else 'No' 
                    for sid in final_df['Idstudy'].unique()
                ]
            })
            validation_df.to_excel(writer, sheet_name='Validation', index=False)
        
        print(f"✅ Excel uložen: {excel_path}")
        
        # CSV backup
        csv_path = os.path.join(export_folder, f"meta_analysis_batch_{timestamp}.csv")
        final_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"✅ CSV backup: {csv_path}")
        
        print("\n🎉 Dávkové zpracování dokončeno!")
        print("✨ Použita nativní PDF podpora Claude Opus 4")
        
    except Exception as e:
        logger.error(f"Kritická chyba: {e}")
        print(f"❌ Chyba: {e}")

if __name__ == "__main__":
    main()
