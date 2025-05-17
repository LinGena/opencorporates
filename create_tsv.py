from utils.func import *
import pandas as pd
import json
from datetime import datetime
from db.db_companies import DbCompanies
import csv


def create_tsv():
    # с лимитом надо разобраться
    result = DbCompanies().get_results_data()
    data_list = []
    for row in result:
        data = json.loads(row[0]) 
        data_list.append(data)

    column_order = [
        "company_number", "company_name", "company_category", "previous_company_numbers", "other_identifiers",
        "status", "incorporation_date", "dissolution_date", "company_type",
        "jurisdiction", "branch", "registered_street", "registered_city",
        "registered_zip", "registered_state", "registered_country", "agent_name",
        "agent_address", "industry_codes", "number_of_employees",
        "alternative_names", "business_classification_text", "latest_accounts_date",
        "annual_return_last_made", "previous_names", "directors_officers",
        "inactive_directors_officers", "company_addresses", "official_register_entries",
        "website", "branches", "statements_of_control", "filings", "recent_filings",
        "identifiers", "industry_codes_json", "subsidiaries", "trademark_registrations",
        "last_update_from_source", "last_change_recorded", "next_update_from_source",
        "source", "source_url", "url", "cache_time"
    ]

    # for row in data_list:
    #     for key, value in row.items():
    #         if isinstance(value, list):
    #             row[key] = "" if not value else json.dumps(value, ensure_ascii=False)  # Пустой список → ""
    #         elif isinstance(value, dict):
    #             row[key] = "" if not value else json.dumps(value, ensure_ascii=False)  # Словарь → JSON строка
    df = pd.DataFrame(data_list, columns=column_order)
    now = datetime.now().strftime("%Y%m%d")
    df.to_csv(f"opencorporates_{now}.tsv", sep='\t', index=False, quoting=csv.QUOTE_NONE)

    # from utils.func import write_to_file_json
    # write_to_file_json('result.json', df.to_dict(orient='records'))
create_tsv()