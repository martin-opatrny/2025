#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
INFLATION_META_ANALYSIS_v6_hybrid_caching.py
Hybridní architektura využívající Prompt Caching + Extended Thinking
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

# Importuj prompty ze starého skriptu
from paste import DOCUMENT_1_PROMPT, DOCUMENT_2_PROMPT, DOCUMENT_3_PROMPT


class HybridPDFAnalyzer:
    """Hybridní analyzátor využívající Prompt Caching a Extended Thinking"""
    
    def __init__(self, api_key: str, export_folder: str):
        self.api_key = api_key
        self.export_folder = export_folder
        self.client = anthropic.Anthropic(api_key=api_key)
        self.current_study_id = 1
        
        # Cache pro session data
        self.session_cache = {}
        self.cache_stats = {
            'cache_writes': 0,
            'cache_hits': 0,
            'total_saved_tokens': 0
        }
        
    def extract_pdf_content(self, pdf_path: str) -> str:
        """Extrahuje text z PDF souboru"""
        logger.info(f"📄 Extrahuji text z PDF: {os.path.basename(pdf_path)}")
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text()
                
                logger.info(f"✅ Extrahováno {len(text)} znaků z {len(pdf_reader.pages)} stran")
                return text
                
        except Exception as e:
            logger.error(f"❌ Chyba při čtení PDF: {e}")
            return ""
    
    def create_cached_system_prompt(self, pdf_content: str, doc_name: str) -> List[Dict]:
        """Vytvoří system prompt s cache_control pro PDF obsah"""
        return [
            {
                "type": "text",
                "text": f"You are analyzing the academic paper: {doc_name}\n\n"
                       "Follow the extraction instructions precisely and extract data "
                       "for meta-analysis from the PDF content below."
            },
            {
                "type": "text",
                "text": f"PDF CONTENT:\n\n{pdf_content}",
                "cache_control": {"type": "ephemeral"}
            }
        ]
    
    def analyze_with_caching(self, system_prompt: List[Dict], user_prompt: str, 
                           query_name: str, use_thinking: bool = False,
                           thinking_budget: int = 4000) -> Dict[str, Any]:
        """
        Analyzuje s využitím Prompt Caching a volitelně Extended Thinking
        
        Args:
            system_prompt: System prompt s PDF obsahem (s cache_control)
            user_prompt: Uživatelský dotaz (Document 1, 2, nebo 3 prompt)
            query_name: Název dotazu pro logging
            use_thinking: Zda použít Extended Thinking
            thinking_budget: Budget tokenů pro thinking
        """
        
        logger.info(f"🤖 Spouštím {query_name} analýzu...")
        
        if use_thinking:
            logger.info(f"🧠 Extended Thinking aktivováno (budget: {thinking_budget} tokenů)")
        
        try:
            # Nastavení modelů - snadno měnitelné
            STANDARD_MODEL = CLAUDE_MODEL  # Claude 4 Opus pro standardní dotazy
            THINKING_MODEL = CLAUDE_MODEL  # Claude 4 Opus i pro Extended Thinking
            
            # Připrav parametry
            params = {
                "model": THINKING_MODEL if use_thinking else STANDARD_MODEL,
                "max_tokens": thinking_budget + 2000 if use_thinking else 8000,  # Musí být větší než thinking_budget
                "temperature": 1.0 if use_thinking else 0.1,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_prompt}]
            }
            
            # Přidej thinking pokud je požadováno
            if use_thinking:
                params["thinking"] = {
                    "type": "enabled",
                    "budget_tokens": thinking_budget
                }
            
            # Zavolej API s streaming pro dlouhé operace
            if use_thinking:
                # Pro Extended Thinking použij streaming
                response = self.client.messages.create(**params, stream=True)
                # Zpracuj streamovanou odpověď
                full_response = self._process_stream_response(response)
            else:
                # Pro standardní dotazy použij normální volání
                response = self.client.messages.create(**params)
            
            # Loguj cache statistiky
            usage = response.usage
            if hasattr(usage, 'cache_creation_input_tokens') and usage.cache_creation_input_tokens:
                self.cache_stats['cache_writes'] += usage.cache_creation_input_tokens
                logger.info(f"📝 Cache write: {usage.cache_creation_input_tokens} tokenů")
            
            if hasattr(usage, 'cache_read_input_tokens') and usage.cache_read_input_tokens:
                self.cache_stats['cache_hits'] += usage.cache_read_input_tokens
                saved = usage.cache_read_input_tokens * 0.9  # 90% úspora
                self.cache_stats['total_saved_tokens'] += saved
                logger.info(f"💰 Cache hit: {usage.cache_read_input_tokens} tokenů (ušetřeno ~{saved:.0f})")
            
            # Zpracuj odpověď
            if use_thinking:
                return self._parse_thinking_response(full_response)
            else:
                return self._parse_standard_response(response)
                
        except Exception as e:
            logger.error(f"❌ Chyba při {query_name} analýze: {e}")
            return {'error': str(e)}
    
    def _process_stream_response(self, stream) -> Any:
        """Zpracuje streamovanou odpověď z Extended Thinking"""
        thinking_content = []
        final_answer = ""
        
        for chunk in stream:
            if chunk.type == "content_block_delta":
                if chunk.delta.type == "thinking":
                    thinking_content.append(chunk.delta.thinking)
                elif chunk.delta.type == "text_delta":
                    final_answer += chunk.delta.text
        
        # Vytvoříme mock response objekt pro kompatibilitu
        class MockResponse:
            def __init__(self, content):
                self.content = content
        
        return MockResponse([type('obj', (object,), {'type': 'text', 'text': final_answer})()])
    
    def _parse_thinking_response(self, response) -> Dict[str, Any]:
        """Parsuje odpověď s thinking blocks"""
        thinking_content = []
        final_answer = ""
        
        for block in response.content:
            if block.type == "thinking":
                thinking_content.append(block.thinking)
            elif block.type == "text":
                final_answer += block.text
        
        return self._parse_response(final_answer)
    
    def _parse_standard_response(self, response) -> Dict[str, Any]:
        """Parsuje standardní odpověď"""
        text = response.content[0].text if response.content else ""
        return self._parse_response(text)
    
    def _parse_response(self, text: str) -> Dict[str, Any]:
        """Parsuje textovou odpověď na tabulková data"""
        lines = text.strip().split('\n')
        
        # Hledáme začátek tabulky
        table_start = -1
        for i, line in enumerate(lines):
            if 'Idstudy\t' in line or line.startswith('Idstudy'):
                table_start = i
                break
        
        if table_start >= 0:
            # Extrahujeme řádky tabulky
            table_rows = []
            for line in lines[table_start + 1:]:
                if '\t' in line:
                    cols = line.split('\t')
                    if len(cols) == len(META_ANALYSIS_COLUMNS):
                        table_rows.append(cols)
            
            return {'table_rows': table_rows}
        else:
            return {'raw_text': text}
    
    def analyze_pdf_hybrid(self, pdf_path: str) -> pd.DataFrame:
        """
        Hybridní analýza PDF s optimalizací pomocí Prompt Caching
        
        Strategie:
        1. První dotaz (metadata) - ustanoví cache
        2. Druhý dotaz (model structure) - využije cache hit
        3. Třetí dotaz (results) - využije cache hit + Extended Thinking pro složitou extrakci
        """
        
        logger.info(f"\n{'='*60}")
        logger.info(f"📚 Analyzuji PDF: {os.path.basename(pdf_path)}")
        logger.info(f"{'='*60}")
        
        # 1. Extrahuj obsah PDF
        pdf_content = self.extract_pdf_content(pdf_path)
        if not pdf_content:
            logger.error(f"❌ Nepodařilo se extrahovat obsah z {os.path.basename(pdf_path)}")
            return self._create_empty_dataframe(self.current_study_id)
        
        # 2. Vytvoř cached system prompt
        doc_name = os.path.basename(pdf_path)
        system_prompt = self.create_cached_system_prompt(pdf_content, doc_name)
        
        # 3. Document 1: Metadata (ustanoví cache)
        logger.info("\n📋 Document 1: Extrakce metadat (ustanovení cache)")
        results1 = self.analyze_with_caching(
            system_prompt=system_prompt,
            user_prompt=DOCUMENT_1_PROMPT,
            query_name="Document 1 (Metadata)",
            use_thinking=False  # Jednoduché, nepotřebuje thinking
        )
        
        # 4. Document 2: Model Structure (využije cache)
        logger.info("\n📋 Document 2: Struktura modelu (cache hit)")
        time.sleep(2)  # Krátká pauza
        results2 = self.analyze_with_caching(
            system_prompt=system_prompt,
            user_prompt=DOCUMENT_2_PROMPT,
            query_name="Document 2 (Model Structure)",
            use_thinking=False  # Strukturované, ale ne příliš složité
        )
        
        # 5. Document 3: Results & Parameters (cache hit + thinking)
        logger.info("\n📋 Document 3: Výsledky a parametry (cache hit + extended thinking)")
        time.sleep(2)
        results3 = self.analyze_with_caching(
            system_prompt=system_prompt,
            user_prompt=DOCUMENT_3_PROMPT,
            query_name="Document 3 (Results)",
            use_thinking=True,  # Složité - extrakce všech inflačních výsledků
            thinking_budget=8000  # Vyšší budget pro důkladnou analýzu
        )
        
        # 6. Sloučit výsledky
        df = self.merge_results(results1, results2, results3, self.current_study_id)
        
        # 7. Zobrazit statistiky cache
        self._print_cache_statistics()
        
        return df
    
    def merge_results(self, results1: Dict, results2: Dict, results3: Dict, study_id: int) -> pd.DataFrame:
        """Sloučí výsledky ze 3 dotazů do jednoho DataFrame"""
        
        # Získáme počet řádků z třetího dotazu
        if 'table_rows' in results3 and results3['table_rows']:
            num_rows = len(results3['table_rows'])
        else:
            num_rows = 1
        
        logger.info(f"📊 Slučuji výsledky: {num_rows} inflačních odhadů")
        
        # Vytvoříme prázdný DataFrame
        df = pd.DataFrame(index=range(num_rows), columns=META_ANALYSIS_COLUMNS)
        df.fillna('NA', inplace=True)
        
        # Naplníme data z jednotlivých dotazů
        # Document 1 - metadata (stejná pro všechny řádky)
        if 'table_rows' in results1 and results1['table_rows']:
            doc1_data = results1['table_rows'][0]
            doc1_cols = ['Idstudy', 'Author', 'Author_Affiliation', 'DOI', 'Journal_Name', 
                        'Num_Citations', 'Year', 'Base_Model_Type', 'Country', 'Impact_Factor']
            
            for col_idx, col_name in enumerate(doc1_cols):
                if col_idx < len(doc1_data):
                    df[col_name] = doc1_data[col_idx]
        
        # Document 2 - model structure
        if 'table_rows' in results2 and results2['table_rows']:
            doc2_data = results2['table_rows'][0]
            doc2_mapping = {
                'Augmented_base_model': 9,
                'Augmentation_Description': 10,
                'Ramsey_Rule': 11,
                'HH_Included': 12,
                'Firms_Included': 13,
                'Banks_Included': 14,
                'Government_Included': 15,
                'HH_Maximization_Type': 16,
                'HH_Maximized_Vars': 17,
                'Producer_Type': 18,
                'Producer_Assumption': 19,
                'Other_Agent_Included': 20,
                'Other_Agent_Assumptions': 21,
                'Empirical_Research': 22,
                'Flexible_Price_Assumption': 24,
                'Exogenous_Inflation': 25,
                'Zero_Lower_Bound': 38
            }
            
            for col_name, col_idx in doc2_mapping.items():
                if col_idx < len(doc2_data):
                    df[col_name] = doc2_data[col_idx]
        
        # Document 3 - results & parameters (různé pro každý řádek)
        if 'table_rows' in results3 and results3['table_rows']:
            for row_idx, row_data in enumerate(results3['table_rows']):
                if row_idx < num_rows:
                    doc3_mapping = {
                        'IdEstimate': 1,
                        'Households_discount_factor': 26,
                        'Consumption_curvature_parameter': 27,
                        'Disutility_of_labor': 28,
                        'Inverse_of_labor_supply_elasticity': 29,
                        'Money_curvature_parameter': 30,
                        'Loan_to_value_ratio': 31,
                        'Labor_share_of_output': 32,
                        'Depositors_discount_factor': 33,
                        'Price_adjustment_cost': 34,
                        'Elasticity_of_substitution_between_goods': 35,
                        'AR1_coefficient_of_TFP': 36,
                        'Std_dev_to_TFP_shock': 37,
                        'Zero_Lower_Bound': 38,
                        'Results_Table': 39,
                        'Results_Inflation': 40,
                        'Results_Inflation_Assumption': 41,
                        'Preferred_Estimate': 42,
                        'Reason_for_Preferred': 43,
                        'Std_Dev_Inflation': 44,
                        'Interest_Rate': 45
                    }
                    
                    for col_name, col_idx in doc3_mapping.items():
                        if col_idx < len(row_data):
                            df.loc[row_idx, col_name] = row_data[col_idx]
        
        # Nastavíme správné Idstudy
        df['Idstudy'] = str(study_id)
        
        # Vyčistíme data
        df = df.replace('', 'NA')
        df = df.fillna('NA')
        
        return df
    
    def _create_empty_dataframe(self, study_id: int) -> pd.DataFrame:
        """Vytvoří prázdný DataFrame s NA hodnotami"""
        empty_row = {col: 'NA' for col in META_ANALYSIS_COLUMNS}
        empty_row['Idstudy'] = str(study_id)
        empty_row['IdEstimate'] = '1'
        return pd.DataFrame([empty_row])
    
    def _print_cache_statistics(self):
        """Zobrazí statistiky využití cache"""
        logger.info("\n💰 Cache statistiky:")
        logger.info(f"  • Cache writes: {self.cache_stats['cache_writes']} tokenů")
        logger.info(f"  • Cache hits: {self.cache_stats['cache_hits']} tokenů")
        logger.info(f"  • Ušetřeno tokenů: ~{self.cache_stats['total_saved_tokens']:.0f}")
        
        if self.cache_stats['cache_hits'] > 0:
            efficiency = (self.cache_stats['total_saved_tokens'] / 
                         (self.cache_stats['cache_writes'] + self.cache_stats['cache_hits'])) * 100
            logger.info(f"  • Efektivita cache: {efficiency:.1f}%")
    
    def process_folder_hybrid(self, folder_path: str) -> pd.DataFrame:
        """Zpracuje všechny PDF ve složce s hybridní optimalizací"""
        
        pdf_files = list(Path(folder_path).glob("*.pdf"))
        
        if not pdf_files:
            logger.warning("Ve složce nebyly nalezeny žádné PDF soubory")
            return pd.DataFrame(columns=META_ANALYSIS_COLUMNS)
        
        logger.info(f"📚 Nalezeno {len(pdf_files)} PDF souborů pro zpracování")
        
        all_results = []
        successful_count = 0
        failed_count = 0
        
        for idx, pdf_path in enumerate(pdf_files, 1):
            print(f"\n{'='*80}")
            print(f"📄 Zpracovávám {idx}/{len(pdf_files)}: {pdf_path.name}")
            print(f"{'='*80}")
            
            try:
                # Pauza mezi soubory
                if idx > 1:
                    wait_time = 5
                    print(f"⏳ Čekám {wait_time} sekund před dalším souborem...")
                    time.sleep(wait_time)
                
                # Analyzuj PDF s hybridní metodou
                df_study = self.analyze_pdf_hybrid(str(pdf_path))
                
                # Kontrola výsledků
                if df_study.empty or (len(df_study) == 1 and all(df_study.iloc[0] == 'NA')):
                    logger.warning(f"⚠️ Žádná data extrahována z {pdf_path.name}")
                    failed_count += 1
                else:
                    all_results.append(df_study)
                    successful_count += 1
                    print(f"✅ Úspěšně zpracováno: {len(df_study)} inflačních odhadů")
                
                # Zvýšíme ID pro další studii
                self.current_study_id += 1
                
            except Exception as e:
                logger.error(f"❌ Neočekávaná chyba při zpracování {pdf_path.name}: {e}")
                failed_count += 1
                continue
        
        # Finální statistiky
        print(f"\n{'='*80}")
        print(f"📊 Zpracování dokončeno:")
        print(f"  ✅ Úspěšně: {successful_count}")
        print(f"  ❌ Neúspěšně: {failed_count}")
        print(f"  📁 Celkem: {len(pdf_files)}")
        print(f"{'='*80}")
        
        # Celkové cache statistiky
        self._print_cache_statistics()
        
        # Spojíme všechny výsledky
        if all_results:
            final_df = pd.concat(all_results, ignore_index=True)
            logger.info(f"\n✅ Celkem {successful_count} úspěšných studií s {len(final_df)} řádky")
            return final_df
        else:
            logger.warning("Nebyly získány žádné výsledky")
            return pd.DataFrame(columns=META_ANALYSIS_COLUMNS)


def main():
    """Hlavní funkce"""
    print("=" * 80)
    print(" INFLATION META-ANALYSIS v6.0 - Hybrid Caching Architecture ".center(80, "="))
    print("=" * 80)
    print("\n🚀 Hybridní architektura: Prompt Caching + Extended Thinking")
    print("📊 Dramatické snížení nákladů díky cache hits")
    print("🧠 Inteligentní analýza s Extended Thinking pro složité extrakce")
    print("💰 90% úspora tokenů při opakovaných dotazech\n")
    
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
    default_export = os.path.join(script_dir, "AI_export_v6_hybrid")
    
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
    
    # Přidáme file handler pro logging
    log_file = os.path.join(export_folder, f"processing_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)
    
    # Inicializace
    analyzer = HybridPDFAnalyzer(CLAUDE_API_KEY, export_folder)
    
    try:
        # Zpracování všech PDF ve složce
        print("\n🚀 Spouštím hybridní zpracování s Prompt Caching...")
        final_df = analyzer.process_folder_hybrid(pdf_folder)
        
        if final_df.empty:
            print("\n❌ Nebyly získány žádné výsledky k uložení")
            return
        
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
        
        # Excel export s detailními listy
        excel_path = os.path.join(export_folder, f"meta_analysis_v6_hybrid_{timestamp}.xlsx")
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            # Hlavní data
            final_df.to_excel(writer, sheet_name='Meta-Analysis', index=False)
            
            # Souhrn
            summary_df = pd.DataFrame({
                'Metric': ['Total Studies', 'Total Estimates', 'Average per Study', 
                          'Processing Date', 'Architecture'],
                'Value': [unique_studies, total_estimates, f"{total_estimates/unique_studies:.1f}", 
                         timestamp, 'Hybrid Caching v6.0']
            })
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Cache statistiky
            cache_df = pd.DataFrame({
                'Metric': ['Cache Writes (tokens)', 'Cache Hits (tokens)', 
                          'Tokens Saved', 'Cache Efficiency'],
                'Value': [
                    analyzer.cache_stats['cache_writes'],
                    analyzer.cache_stats['cache_hits'],
                    f"~{analyzer.cache_stats['total_saved_tokens']:.0f}",
                    f"{(analyzer.cache_stats['total_saved_tokens'] / (analyzer.cache_stats['cache_writes'] + analyzer.cache_stats['cache_hits']) * 100):.1f}%" if analyzer.cache_stats['cache_hits'] > 0 else "N/A"
                ]
            })
            cache_df.to_excel(writer, sheet_name='Cache_Statistics', index=False)
        
        print(f"✅ Excel uložen: {excel_path}")
        
        # CSV backup
        csv_path = os.path.join(export_folder, f"meta_analysis_v6_hybrid_{timestamp}.csv")
        final_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"✅ CSV backup: {csv_path}")
        
        print("\n🎉 Hybridní zpracování dokončeno!")
        print("✨ Použita kombinace Prompt Caching + Extended Thinking")
        print(f"💰 Ušetřeno ~{analyzer.cache_stats['total_saved_tokens']:.0f} tokenů díky cache hits")
        
    except Exception as e:
        logger.error(f"Kritická chyba: {e}")
        print(f"❌ Chyba: {e}")


if __name__ == "__main__":
    main()
