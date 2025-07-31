# Prompty pro meta-analýzu inflace
# Vyplňte obsah podle vašich potřeb

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
Idstudy	IdEstimate	Author	Author_Affiliation	DOI	Journal_Name	Num_Citations	Year	Base_Model_Type	Augmented_base_model	Augmentation_Description	Ramsey_Rule	HH_Included	Firms_Included	Banks_Included	Government_Included	HH_Maximization_Type	HH_Maximized_Vars	Producer_Type	Producer_Assumption	Other_Agent_Included	Other_Agent_Assumptions	Empirical_Research	Country	Flexible_Price_Assumption	Exogenous_Inflation	Households_discount_factor	Consumption_curvature_parameter	Disutility_of_labor	Inverse_of_labor_supply_elasticity	Money_curvature_parameter	Loan_to_value_ratio	Labor_share_of_output	Depositors_discount_factor	Price_adjustment_cost	Elasticity_of_substitution_between_goods	AR1_coefficient_of_TFP	Std_dev_to_TFP_shock	Zero_Lower_Bound	Results_Table	Results_Inflation	Results_Inflation_Assumption	Preferred_Estimate	Reason_for_Preferred	Std_Dev_Inflation	Interest_Rate	Impact_Factor
1	NA	Smith, J. (2023)	MIT	10.1234/example	Journal of Monetary Economics	45	2023	DSGE	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	US	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA
```

---
"""

DOCUMENT_2_PROMPT = """
# Document 2: Model Structure & Assumptions Instructions

## CRITICAL SYSTEM DIRECTIVES

## TASK OVERVIEW
Extract data from academic PDF articles for meta-analysis dataset creation. Process the attached PDF systematically using the numbered questions below. Each question corresponds to a specific Excel column.

### MANDATORY COMPLIANCE REQUIREMENTS
- **NEVER leave any cell empty** - use "NA" for missing information
- **NEVER fabricate data** - only report verifiable information from sources
- **ALWAYS use exact column names** as specified in the complete output format
- **ALWAYS follow the 0/1 coding system** for Yes/No questions (0 = No, 1 = Yes)
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

## DOCUMENT 2 ASSIGNED COLUMNS
This document extracts the following columns:
- Idstudy (copy from Document 1 or assign if working independently)
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
- Flexible_Price_Assumption
- Exogenous_Inflation
- Growth_Included
- Zero_Lower_Bound

All other columns must be filled with "NA".

## EXTRACTION INSTRUCTIONS

### 1. STUDY IDENTIFICATION
- **Column**: `Idstudy`
- **Task**: Use same ID as Document 1 (or assign starting from 1 if working independently)

### 2. MODEL AUGMENTATION

**Task 5.2 - Augmented Model Check**
- **Column**: `Augmented_base_model`
- **Task**: Determine if model has augmentations
- **Process**: Look for model modifications, extensions, or additions beyond standard version
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
  - The central bank minimizes an "ad-hoc" or "quadratic loss function" (e.g., stabilizing inflation around a given target and an output gap) that is not derived from a government financing problem
  - Optimal inflation is determined solely by monetary frictions without fiscal considerations
  - The paper focuses only on monetary policy without fiscal policy integration
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

### 5. AGENT CHARACTERISTICS

**Task 5.9 - Household Maximization Type**
- **Column**: `HH_Maximization_Type`
- **Task**: Identify what households maximize
- **Common answers**: "utility", "welfare", "consumption plus leisure", "expected utility"
- **Format**: Short phrase (2-4 words)

**Task 5.10 - Household Maximized Variables**
- **Column**: `HH_Maximized_Vars`
- **Task**: List variables in household optimization
- **Common answers**: "consumption, labor", "consumption, money, leisure", "consumption, hours worked"
- **Format**: Comma-separated list

**Task 5.11 - Producer Types**
- **Column**: `Producer_Type`
- **Task**: Identify all firm types in model
- **Process**: 
  1. Look for explicit model equations or mathematical formulations involving firms
  2. Check if firms are actual decision-making agents with optimization problems
  3. Don't count casual mentions - need evidence of firms as active model components
- **Examples**: "intermediate goods firms, final goods firms", "wholesale firms, retail firms"
- **Format**: Comma-separated list
- **Robustness Check**: Verify firms have optimization problems, production functions, or decision variables

**Task 5.12 - Producer Assumptions**
- **Column**: `Producer_Assumption`
- **Task**: Identify market structure assumptions for each firm type
- **Search terms**: "monopolistic competition", "perfect competition", "monopoly", "Dixit-Stiglitz"
- **Format**: "firm type: assumption" format
- **Example**: "intermediate firms: monopolistic competition, final firms: perfect competition"

**Task 5.13 - Other Agents Check**
- **Column**: `Other_Agent_Included`
- **Task**: Check for other agents beyond households/firms/banks/government
- **Exclusions**: Do not count households, firms, banks, government
- **Examples**: "labor unions", "central bank", "foreign sector"
- **Output**: 1 (Yes) or 0 (No)

**Task 5.14 - Other Agent Assumptions**
- **Column**: `Other_Agent_Assumptions`
- **Task**: Describe other agents' assumptions
- **Condition**: Only if Task 5.13 = 1, otherwise "NA"
- **Format**: Brief description

### 6. RESEARCH TYPE

**Task 5.15 - Empirical Research Check**
- **Column**: `Empirical_Research`
- **Task**: Determine if research uses empirical data/estimation
- **Process**: Look if the result is model output using calibration (not empirical) or based on regression analysis/data estimation (empirical)
- **Output**: 1 (Yes) or 0 (No)

### 7. MODEL ASSUMPTIONS (PER RESULT)

**Task 5.17 - Price Flexibility**
- **Column**: `Flexible_Price_Assumption`
- **Task**: Check price flexibility assumption for each inflation result
- **Process**: For each inflation result, determine if prices are flexible or sticky
- **Output**: 1 (flexible prices) or 0 (sticky prices)
- **Note**: May vary across different results in same paper

**Task 5.18 - Exogenous Inflation**
- **Column**: `Exogenous_Inflation`
- **Task**: Check if inflation is exogenous
- **Process**: Determine if inflation is set externally (exogenous) vs. determined by model (endogenous)
- **Search terms**: "exogenous inflation", "inflation target", "inflation assumption", "given inflation rate"
- **Output**: 1 (exogenous) or 0 (endogenous)

**Task 5.19 - Growth Parameters**
- **Column**: `Growth_Included`
- **Task**: Check for growth parameters
- **Search terms**: "growth rate", "trend growth", "g", "productivity growth"
- **Output**: 1 (Yes) or 0 (No)
- **Note**: Not a column in final output but needed for extraction process

**Task 5.20 - Zero Lower Bound**
- **Column**: `Zero_Lower_Bound`
- **Task**: Check zero lower bound environment
- **Process**: Determine if zero lower bound constraint is considered in the model
- **Search terms**: "zero lower bound", "ZLB", "effective lower bound", "ELB"
- **Output**: 1 (Yes) or 0 (No)

## CRITICAL REMINDERS

1. **RAMSEY RULE REQUIRES FISCAL COMPONENT** - not just "optimal policy"
2. **GOVERNMENT MUST BE ACTIVE** - not just mentioned in text
3. **BINARY VALUES ARE CRITICAL** - always 0 or 1, never blank
4. **PRICE FLEXIBILITY MAY VARY** - check for each result scenario

## VALIDATION CHECKLIST

### Pre-Extraction:
- [ ] Located model description section
- [ ] Found agent descriptions
- [ ] Identified methodology

### During Extraction:
- [ ] Verified Ramsey Rule has fiscal-monetary joint optimization
- [ ] Confirmed government has active model role
- [ ] Checked all agent types systematically

### Post-Extraction:
- [ ] All binary columns have 0 or 1 values
- [ ] All text columns have appropriate descriptions or "NA"
- [ ] No columns left empty

## OUTPUT EXAMPLE
```
Idstudy	IdEstimate	Author	Author_Affiliation	DOI	Journal_Name	Num_Citations	Year	Base_Model_Type	Augmented_base_model	Augmentation_Description	Ramsey_Rule	HH_Included	Firms_Included	Banks_Included	Government_Included	HH_Maximization_Type	HH_Maximized_Vars	Producer_Type	Producer_Assumption	Other_Agent_Included	Other_Agent_Assumptions	Empirical_Research	Country	Flexible_Price_Assumption	Exogenous_Inflation	Households_discount_factor	Consumption_curvature_parameter	Disutility_of_labor	Inverse_of_labor_supply_elasticity	Money_curvature_parameter	Loan_to_value_ratio	Labor_share_of_output	Depositors_discount_factor	Price_adjustment_cost	Elasticity_of_substitution_between_goods	AR1_coefficient_of_TFP	Std_dev_to_TFP_shock	Zero_Lower_Bound	Results_Table	Results_Inflation	Results_Inflation_Assumption	Preferred_Estimate	Reason_for_Preferred	Std_Dev_Inflation	Interest_Rate	Impact_Factor
1	NA	NA	NA	NA	NA	NA	NA	NA	1	Financial frictions	0	1	1	1	1	utility	consumption, labor	intermediate firms, final firms	intermediate firms: monopolistic competition, final firms: perfect competition	0	NA	0	NA	0	0	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	1	NA	NA	NA	NA	NA	NA	NA	NA
```
"""

DOCUMENT_3_PROMPT = """
# Document 3: Results & Parameters Instructions

## TASK OVERVIEW
Extract data from academic PDF articles for meta-analysis dataset creation. Process the attached PDF systematically using the numbered questions below. Each question corresponds to a specific Excel column.

## CRITICAL SYSTEM DIRECTIVES

### MANDATORY COMPLIANCE REQUIREMENTS
- **NEVER leave any cell empty** - use "NA" for missing information
- **NEVER fabricate data** - only report verifiable information from sources
- **ALWAYS use exact column names** as specified in the complete output format
- **ALWAYS extract ALL inflation results** from ALL tables, figures, and text
- **ALWAYS verify variable identification** using notation sections and context
- **ALWAYS reset assumptions for each new table** - never carry over structure assumptions
- **ALWAYS preserve numerical signs** - negative values must include minus sign
- **ALWAYS cross-verify results** when similar tables appear
- **ALWAYS fill only assigned columns** - use "NA" for all other columns

### OUTPUT FORMAT REQUIREMENTS
- Generate a table with ALL 47 column headers (complete list at end of document)
- Fill ONLY the columns specified in this document
- Mark all other columns as "NA"
- Each row = one inflation result from the paper
- Use tab-separated format for easy Excel import
- Include header row with all column names

## COMPLETE COLUMN LIST (47 COLUMNS)
```
Idstudy	IdEstimate	Author	Author_Affiliation	DOI	Journal_Name	Num_Citations	Year	Base_Model_Type	Augmented_base_model	Augmentation_Description	Ramsey_Rule	HH_Included	Firms_Included	Banks_Included	Government_Included	HH_Maximization_Type	HH_Maximized_Vars	Producer_Type	Producer_Assumption	Other_Agent_Included	Other_Agent_Assumptions	Empirical_Research	Country	Flexible_Price_Assumption	Exogenous_Inflation	Households_discount_factor	Consumption_curvature_parameter	Disutility_of_labor	Inverse_of_labor_supply_elasticity	Money_curvature_parameter	Loan_to_value_ratio	Labor_share_of_output	Depositors_discount_factor	Price_adjustment_cost	Elasticity_of_substitution_between_goods	AR1_coefficient_of_TFP	Std_dev_to_TFP_shock	Zero_Lower_Bound	Results_Table	Results_Inflation	Results_Inflation_Assumption	Preferred_Estimate	Reason_for_Preferred	Std_Dev_Inflation	Interest_Rate	Impact_Factor
```

## DOCUMENT 3 ASSIGNED COLUMNS
This document extracts the following columns:
- Idstudy (copy from Document 1 or assign if working independently)
- IdEstimate
- Households_discount_factor through Zero_Lower_Bound (all parameters)
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

## EXTRACTION INSTRUCTIONS

### 1. STUDY IDENTIFICATION
- **Column**: `Idstudy`
- **Task**: Use same ID as Document 1 (or assign starting from 1 if working independently)

- **Column**: `IdEstimate`
- **Task**: Assign sequential estimate ID for each inflation result
- **Format**: Integer starting from 1 for each study

### 2. CRITICAL RESULTS EXTRACTION

**Task 5.21 - COMPREHENSIVE RESULTS MAPPING**
- **Column**: `Results_Table`
- **Task**: Identify and map ALL results locations
- **MANDATORY SCANNING PROTOCOL**: 
  1. **Create exhaustive inventory**: List EVERY table, figure, and text section with numerical results
  2. **Never skip tables**: Even if a table appears to show only welfare costs, it may contain optimal inflation values
  3. **Check all locations**:
     - Main body tables (Tables 1, 2, 3, etc.)
     - Figures with numerical values
     - Text sections with inline results
     - Footnotes with numerical results
     - Appendices (including online appendices)
     - Robustness check sections
  4. **For each location, note**:
     - What variables are shown (inflation, interest rates, welfare, output)
     - How many distinct inflation values appear
     - Any parameter variations between results
- **Cross-verification**: When similar tables appear, note differences
- **Format**: "Table 1, Table 2, Figure 3, Text Section 4.2"

**Task 5.22 - CRITICAL INFLATION EXTRACTION - COMPLETE SCANNING REQUIRED**
- **Column**: `Results_Inflation`
- **Task**: Extract ALL inflation values with EXACT precision from ALL sources
- **MANDATORY COMPLETE EXTRACTION PROTOCOL**:
  1. **NEVER STOP AFTER ONE TABLE** - Extract from ALL tables identified in 5.21
  2. **COMPARE SIMILAR TABLES**: When tables have similar structure:
     - Extract ALL rows from BOTH tables
     - Note differences (e.g., row 9 might differ between tables)
     - Do NOT assume identical results - verify each value
  3. **SIGN VERIFICATION PROTOCOL**:
     - **Visual inspection**: Look for minus sign (-) before the number
     - **Cross-table verification**: If same parameter appears in multiple tables, verify sign consistency
     - **Context verification**: Check surrounding text for "negative", "deflation", "below zero"
     - **Model consistency**: Flexible price models → expect negative; New Keynesian → expect near zero
  4. **EXTRACTION RULES**:
     - Extract EVERY inflation value, even if it appears redundant
     - Preserve exact decimal places as shown
     - If value appears in multiple tables with different signs → flag for verification
  5. **COMPLETENESS CHECK**:
     - Count inflation values in source
     - Count extracted rows
     - These MUST match

**Task 5.23 - Total Count Verification**
- **Task**: Count total distinct inflation results across ALL sources
- **Process**: 
  1. Count results in each table
  2. Count results in each figure
  3. Count results mentioned in text
  4. Count results in appendices
  5. Sum total from all sources
- **Critical**: This MUST equal your final row count
- **Note**: Not a final column but verification step

### 3. RESULT CHARACTERISTICS

**Task 5.24 - Preferred Estimate**
- **Column**: `Preferred_Estimate`
- **Task**: Identify author's preferred estimate
- **Enhanced identifiers**: 
  - "baseline result"
  - "main specification"  
  - "preferred estimate"
  - "benchmark"
  - Results emphasized in abstract/conclusion
  - Results used for policy implications
- **Output**: 1 (preferred) or 0 (not preferred)

**Task 5.25 - Reason for Preferred**
- **Column**: `Reason_for_Preferred`
- **Task**: Explain why estimate is preferred
- **Condition**: Only for preferred estimates (Task 5.24 = 1), otherwise "NA"
- **Format**: 1-2 professional sentences

**Task 5.26 - Results Assumptions**
- **Column**: `Results_Inflation_Assumption`
- **Task**: Describe assumptions for each inflation result
- **Process**: Note the specific model variant/calibration/scenario
- **Format**: Brief assumption description
- **Example**: "Baseline calibration with sticky prices", "With ZLB constraint", "No growth (g = 0)"

**Task 5.39 - Standard Deviation of Inflation**
- **Column**: `Std_Dev_Inflation`
- **Task**: Extract standard deviation of inflation result
- **Process**: Look for uncertainty measures, confidence intervals, posterior distributions
- **May appear**: In parentheses, brackets, or separate column

**Task 5.40 - Interest Rate**
- **Column**: `Interest_Rate`
- **Task**: Extract interest rates corresponding to each inflation value
- **Process**: 
  1. Find the interest rate that pairs with each inflation result
  2. Check Fisher equation relationship (nominal = real + inflation)
  3. Preserve signs exactly as shown

### 4. PARAMETER EXTRACTION

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
   - Do NOT calculate any parameters, extract only stated values

3. **Common Parameter Locations**:
   - After model description, before results
   - In subsection on calibration/estimation
   - In tables with "Parameter", "Value", "Description" columns
   - In footnotes explaining choices

4. **Zero Value Protocol**:
   - Zero IS a valid parameter value - extract as "0" or "0.0"
   - Common zero parameters: money in utility (cashless), adjustment costs (flexible)
   - Never skip zero values

**Task 5.27 - Households' discount factor**
- **Column**: `Households_discount_factor`
- **Common symbols**: β, beta, δ
- **Common values**: 0.96-0.995 (quarterly), 0.98-0.999 (monthly)
- **Search enhanced**: "discount factor", "beta", "β", "time preference"

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

**Task 5.20 - Zero Lower Bound** (Note: Also appears in Document 2)
- **Column**: `Zero_Lower_Bound`
- **Task**: Check zero lower bound environment for each result
- **Process**: Determine if zero lower bound constraint is considered
- **Search terms**: "zero lower bound", "ZLB", "effective lower bound", "ELB"
- **Output**: 1 (Yes) or 0 (No)

## EXTRACTION VERIFICATION PROTOCOL

After extracting from EACH source:
1. **Completeness Double-Check**: 
   - Did I extract from ALL tables listed in Task 5.21?
   - Does my row count match the total inflation results count?
2. **Sign Triple-Check**: 
   - Re-verify all negative values have minus signs
   - Cross-verify between similar tables
3. **Consistency Check**: 
   - When same scenario appears in multiple tables, are values consistent?
   - If not, extract both and note the difference

## CRITICAL REMINDERS

1. **COMPLETE EXTRACTION IS MANDATORY** - extract from ALL tables, not just first one
2. **SIGN PRESERVATION IS CRITICAL** - Double-check every negative value
3. **CROSS-VERIFY SIMILAR TABLES** - They may have subtle differences
4. **PARAMETER SEARCH MUST BE EXHAUSTIVE** - check everywhere
5. **ZEROS ARE VALID** - never skip them
6. **When similar tables appear** - extract from BOTH and verify consistency
7. **Create one row per inflation result** - multiple rows from same paper

## VALIDATION CHECKLIST

### Pre-Extraction:
- [ ] Located paper's notation section
- [ ] Identified model type (affects expected parameter ranges)
- [ ] Found calibration/parameter section
- [ ] Mapped ALL tables with results (not just first one found)

### During Extraction:
- [ ] Extracted from ALL tables, not just one
- [ ] Compared similar tables for differences
- [ ] Verified signs match source exactly
- [ ] Searched exhaustively for parameters

### Post-Extraction:
- [ ] Row count matches total inflation results
- [ ] All similar scenarios have consistent signs across tables
- [ ] No tables were skipped
- [ ] Each inflation result has its own row

## OUTPUT EXAMPLE (Multiple rows for multiple results)
```
Idstudy	IdEstimate	Author	Author_Affiliation	DOI	Journal_Name	Num_Citations	Year	Base_Model_Type	Augmented_base_model	Augmentation_Description	Ramsey_Rule	HH_Included	Firms_Included	Banks_Included	Government_Included	HH_Maximization_Type	HH_Maximized_Vars	Producer_Type	Producer_Assumption	Other_Agent_Included	Other_Agent_Assumptions	Empirical_Research	Country	Flexible_Price_Assumption	Exogenous_Inflation	Households_discount_factor	Consumption_curvature_parameter	Disutility_of_labor	Inverse_of_labor_supply_elasticity	Money_curvature_parameter	Loan_to_value_ratio	Labor_share_of_output	Depositors_discount_factor	Price_adjustment_cost	Elasticity_of_substitution_between_goods	AR1_coefficient_of_TFP	Std_dev_to_TFP_shock	Zero_Lower_Bound	Results_Table	Results_Inflation	Results_Inflation_Assumption	Preferred_Estimate	Reason_for_Preferred	Std_Dev_Inflation	Interest_Rate	Impact_Factor
1	1	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	0.99	2	0.5	1	0	NA	0.67	NA	NA	6	0.95	0.007	0	Table 1	-0.02	Baseline calibration	1	Main specification with standard parameters	NA	0.02	NA
1	2	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	0.99	2	0.5	1	0	NA	0.67	NA	NA	6	0.95	0.007	1	Table 1	0.00	With ZLB constraint	0	NA	NA	0.04	NA
1	3	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	0.99	1	0.5	1	0	NA	0.67	NA	NA	6	0.95	0.007	0	Table 2	-0.03	Low risk aversion	0	NA	NA	0.01	NA
```
""" 
