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