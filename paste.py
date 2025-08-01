# Prompty pro meta-analýzu inflace
# Vyplňte obsah podle vašich potřeb

DOCUMENT_0_PROMPT = """
# Document 0: Inflation Results Pre-Scanner

## PURPOSE
This document performs a rapid scan to count the total number of inflation results in the paper. This count will be used by all subsequent documents to ensure consistent row generation.

## CRITICAL DIRECTIVE
- **ONLY count inflation results** - do not extract any other information
- **Be exhaustive** - scan ALL tables, figures, and text sections
- **Report one number** - the total count of distinct inflation results

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
State clearly: "This paper contains [X] distinct inflation results. All subsequent documents should create [X] rows."

## EXAMPLES
- Table with 5 rows, each showing optimal inflation under different parameters = 5 results
- Figure comparing 3 different model specifications = 3 results  
- Text mentioning "baseline inflation of 2% and robustness check of 0%" = 2 results

## VALIDATION
After counting, verify by asking:
- Did I check all tables?
- Did I check all figures?
- Did I check the appendices?
- Did I count each distinct scenario?



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

---


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
- [ ] Created exactly ONE row
- [ ] All binary columns have 0 or 1 values
- [ ] All text columns have appropriate descriptions or "NA"

## OUTPUT EXAMPLE (ONE ROW ONLY)

Idstudy  IdEstimate  Author	Author_Affiliation	DOI	Journal_Name	Num_Citations	Year	Base_Model_Type  Augmented_base_model  Augmentation_Description  Ramsey_Rule	HH_Included  Firms_Included  Banks_Included  Government_Included  HH_Maximization_Type	HH_Maximized_Vars	Producer_Type	Producer_Assumption	Other_Agent_Included	Other_Agent_Assumptions	Empirical_Research	Country	Flexible_Price_Assumption	Exogenous_Inflation	Households_discount_factor	Consumption_curvature_parameter	Disutility_of_labor	Inverse_of_labor_supply_elasticity	Money_curvature_parameter	Loan_to_value_ratio	Labor_share_of_output	Depositors_discount_factor	Price_adjustment_cost	Elasticity_of_substitution_between_goods	AR1_coefficient_of_TFP	Std_dev_to_TFP_shock	Zero_Lower_Bound	Results_Table	Results_Inflation	Results_Inflation_Assumption	Preferred_Estimate	Reason_for_Preferred	Std_Dev_Inflation	Interest_Rate	Impact_Factor
1  NA  NA  NA  NA  NA  NA  NA  NA  1  Financial frictions  0  1  1  1  1  utility	consumption, labor	intermediate firms, final firms	intermediate firms: monopolistic competition, final firms: perfect competition	0  NA  0  NA  NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA

```
---

DOCUMENT_3_PROMPT = """
# Document 3: Results & Parameters Instructions

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
- Idstudy (copy from Document 1)
- IdEstimate
- Flexible_Price_Assumption
- Exogenous_Inflation 
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

[Continue with Tasks 5.28-5.38 for all other parameters, each noting to extract the value specific to this result]

## EXTRACTION VERIFICATION PROTOCOL

1. **Row Count Verification**: 
   - Confirm total rows match Document 0's count
   
2. **Assumption Matching**:
   - Verify Flexible_Price_Assumption matches the scenario description
   - Verify Zero_Lower_Bound matches the result context
   
3. **Sign Verification**:
   - Double-check all negative inflation values

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
