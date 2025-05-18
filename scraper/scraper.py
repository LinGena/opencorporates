from bs4 import BeautifulSoup
from datetime import datetime
from scraper.session import GetSession
# from scraper.session_requests import GetSession
from db.db_companies import DbCompanies
from utils.func import *


class Scraper(GetSession, DbCompanies):
    def __init__(self, first_start: bool = False):
        GetSession.__init__(self, first_start)
        DbCompanies.__init__(self)
        
    def run(self, urls: list = None) -> None:
        try:
            tasks = self.get_urls(urls=urls)
            for task in tasks:
                id = task[0]
                url = task[1]
            # id = 2
            # urls = [
            #    'https://opencorporates.com/companies/us_ca/0806592'
            # ]
            # i = 2
            # for url in urls:
                print('-----', url)
                self.subsidiaries_link_companies = set()
                src = self.get_page_content(url)
                if not src:
                    self.update_status(id)
                datas = self.get_page_datas(src, url)
                self.update_datas(id, datas)
                if self.subsidiaries_link_companies:
                    self.check_urls_in_table(list(self.subsidiaries_link_companies))
                    return self.run(urls=list(self.subsidiaries_link_companies))
                # write_to_file_json(f'result_{i}.json', datas)
                # i+=1
        except Exception as ex:
            self.logger.error(ex)
            if src:
                write_to_file('error.html', src)
        self.worker_close()

    def get_page_datas(self, src : str, url: str) -> dict:
        self.soup = BeautifulSoup(src, 'lxml')
        self.company_category = ''
        company_schema = {
            "company_number": self.get_dd("company_number"),
            "company_name": self.get_company_name(),
            "company_category":self.company_category,
            "previous_company_numbers": self.get_list("previous_company_numbers","attribute_item"),
            "other_identifiers": self.get_other_identifiers(),
            "status": self.get_dd("status"),
            "incorporation_date": self.get_dd("incorporation_date"),
            "dissolution_date": self.get_dd("dissolution date"),
            "company_type": self.get_dd("company_type"),
            "jurisdiction": self.get_dd("jurisdiction"),
            "branch": self.get_dd("branch"), 
            "registered_street": "",
            "registered_city": "",
            "registered_zip": "",
            "registered_state": "",
            "registered_country": "",
            "agent_name": self.get_dd("agent_name"),
            "agent_address": self.get_dd("agent_address"),
            "industry_codes": self.get_list("industry_codes", "attribute_item"),
            "number_of_employees": self.get_dd("number_of_employees"),
            "alternative_names": self.get_alternative_names(),
            "business_classification_text": self.get_dd("business_classification_text"),
            "latest_accounts_date": self.get_dd("latest_accounts_date"),
            "annual_return_last_made": self.get_dd("annual_return_last_made_up_date"),
            "previous_names": self.get_list("previous_names", "name_line"),
            "directors_officers": self.get_inactive_directors_officers("officers"),
            "inactive_directors_officers": self.get_inactive_directors_officers("inactive_officers"),
            "company_addresses": self.get_company_addresses(),
            "official_register_entries": self.get_official_register_entries(),
            "website": self.get_websites(),
            "branches": self.get_branches(),
            "statements_of_control": self.get_statements_of_control(),
            "filings": self.get_filings(),
            "recent_filings": self.get_recent_filings(),
            "identifiers": self.get_identifiers(),
            "industry_codes_json": self.get_industry_codes_json(),
            "subsidiaries": self.get_subsidiaries(),
            "trademark_registrations": self.get_trademark_registrations(),
            "last_update_from_source": self.get_dd("last_update_from_source"),
            "last_change_recorded": self.get_dd("last_change_recorded"),
            "next_update_from_source": self.get_dd("next_update_from_source"),
            "source": self.get_dd("source"),
            "source_url": self.get_source_url(),
            "url": url,
            "cache_time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        }
        company_schema.update(self.get_address())
        return company_schema

    def get_company_name(self) -> str:
        company_name = ""
        company_name_block = self.soup.find('h1',{"itemprop":"name"})
        if company_name_block:
            company_name = company_name_block.text.strip()
        if 'branch' in company_name:
            self.company_category = 'branch'
            company_name = company_name.replace('branch','')
        elif 'nonprofit' in company_name:
            self.company_category = 'nonprofit'
            company_name = company_name.replace('nonprofit','')
        company_name = company_name.replace('\n',' ').strip()
        return company_name

    def get_dd(self, dd_class: str, soup: BeautifulSoup = None) -> str:
        value = ""
        if soup:
            dd_value = soup.find('dd', class_=dd_class)
        else:
            dd_value = self.soup.find('dd', class_=dd_class)
        if dd_value:
            value = dd_value.text.strip()
        return value
    
    def get_list(self, dd_name: str, li_name: str) -> list:
        value = []
        if self.get_dd(dd_name):
            try:
                for li in self.soup.select(f".{dd_name} .{li_name}"):
                    value.append(li.text.strip())
            except Exception as ex:
                self.logger.debug(ex)
        return value
    
    def get_address(self) -> str:
        value = {
            "registered_street": "",
            "registered_city": "",
            "registered_zip": "",
            "registered_state": "",
            "registered_country": ""
        }
        if self.get_dd("registered_address adr"):
            try:
                address_lines = [li.get_text(separator=", ", strip=True) for li in self.soup.select(".address_lines .address_line")]
                address = ', '.join(address_lines)
                if len(address_lines) == 5:
                    for i, field in enumerate(value):
                        value[field] = address_lines[i]
                else:
                    value.update({'address_scraped':address})
                    location = self.geolocator.geocode(address, language="en")
                    if location:
                        lat, lon = location.latitude, location.longitude
                        reversed_location = self.geolocator.reverse((lat, lon))
                        if reversed_location and "address" in reversed_location.raw:
                            address_data = reversed_location.raw["address"]
                            value['registered_street'] = address_data.get("house_number", "") + ' ' + address_data.get("road", "")
                            value['registered_city'] = address_data.get("city", address_data.get("town", address_data.get("village", "")))
                            value['registered_zip'] = address_data.get("postcode", "")
                            value['registered_state'] = address_data.get("state", "")
                            value['registered_country'] = address_data.get("country", "")
            except Exception as ex:
                self.logger.debug(ex)
        return value
    
    def get_alternative_names(self) -> str:
        value = ""
        if self.get_dd("alternative_names"):
            try:
                alternative_names_list = [li.text.strip() for li in self.soup.select(".alternative_names .name_line")]
                if alternative_names_list:
                    value = ", ".join(alternative_names_list)
            except Exception as ex:
                self.logger.debug(ex)
        return value
    
    def get_other_identifiers(self) -> list:
        value = []
        if self.get_dd("other_identifiers"):
            try:
                for li in self.soup.select(".other_identifiers .attribute_item"):
                    a_teg = li.find("a", class_="identifier")
                    if not a_teg:
                        continue
                    link = a_teg.get("href")
                    name = a_teg.text.strip()
                    identifier_link = f"{self.domain_name}{link}"
                    src = self.get_page_content(identifier_link)
                    if src:
                        soup = BeautifulSoup(src,'lxml')
                        res = {name:{
                            "Identifying System" : self.get_dd("identifying_system", soup),
                            "Identifying System Shortcode" : self.get_dd("identifying_system_shortcode", soup),
                            "Identifying System Website" : self.get_dd("identifying_system_website", soup),
                            "Identifying System Wikipedia Page" : self.get_dd("identifying_system_wikipedia_page", soup),
                        }}
                        value.append(res)
            except Exception as ex:
                self.logger.debug(ex)
        return value

    def get_inactive_directors_officers(self, dd_name: str) -> list:
        value = []
        if self.get_dd(dd_name):
            try:
                for li in self.soup.select(f".{dd_name} .attribute_item"):
                    a_teg = li.find("a")
                    if not a_teg:
                        continue
                    link = a_teg.get("href")
                    name = a_teg.text.strip()
                    profile_link = f"{self.domain_name}{link}"
                    src = self.get_page_content(profile_link)
                    if src:
                        soup = BeautifulSoup(src,'lxml')
                        res = {name:{
                            "Company" : self.get_dd("company", soup).replace("inactive","").strip(),
                            "Name" : self.get_dd("name", soup),
                            "Address" : self.get_dd("address", soup).replace('\n',', '),
                            "Position" : self.get_dd("position", soup),
                            "Occupation" : self.get_dd("occupation", soup),
                            "Nationality" : self.get_dd("nationality", soup),
                            "Start Date" : self.get_dd("start_date", soup),
                            "End Date" : self.get_dd("end_date", soup)
                        }}
                        value.append(res)
            except Exception as ex:
                self.logger.debug(ex)
        return value
    
    def get_value(self, soup: BeautifulSoup, name: str) -> str:
        block = soup.find("a", {"name": name})
        if block:
            return block.find_next("td").text.strip()
        return ""
    
    def get_statements_of_control(self) -> list:
        self.statements_of_control_result= []
        try:
            def get_data(main_soup: BeautifulSoup) -> None:
                div = main_soup.find('div', id="data-table-control_statement_subject")
                if div:
                    rows = div.select("table tbody tr")
                    for row in rows:
                        tds = row.find_all('td')
                        link_tag = row.find("a", href=lambda x: x and x.startswith("/statements/"), text="details")
                        statements_link = f"{self.domain_name}{link_tag.get('href')}"
                        data = {
                            "Date": self.get_td_text(tds,0),
                            "Description": self.get_td_text(tds,1),
                            "Mechanisms": self.get_td_text(tds,2),
                            "details": statements_link
                        }
                        self.statements_of_control_result.append(data)

            all_links = self.soup.find('a', href=lambda x: x and '/control_statement_subject' in x)
            if all_links:
                page = 0
                while True:
                    page += 1
                    if page == 500:
                        break
                    filings_link = f"{self.domain_name}{all_links.get('href')}"
                    src = self.get_page_content(filings_link)
                    soup = BeautifulSoup(src, 'lxml')
                    get_data(soup)
                    pagination = soup.find('div', class_='pagination')
                    if pagination:
                        next_page = pagination.find('li', class_='next next_page')
                        if next_page:
                            next_link = next_page.find('a')
                            if next_link and next_link.get('href') != "#": 
                                all_links = {"href": next_link.get('href')}
                                continue 
                    break
            else:
                get_data(self.soup)
        except Exception as ex:
            self.logger.debug(ex)
        return self.statements_of_control_result
    
    def get_td_text(self, tds: list[BeautifulSoup], number: int) -> str:
        value = ''
        try:
            if len(tds) > number:
                value = tds[number].text.strip()
        except Exception as ex:
            self.logger.debug(ex)
        return value

    def get_filings(self) -> list:
        self.filings_result= []
        try:
            def get_data(main_soup: BeautifulSoup) -> None:
                div = main_soup.find('div', id="data-table-filing_delegate")
                if div:
                    rows = div.select("table tbody tr")
                    for row in rows:
                        tds = row.find_all('td')
                        link_tag = row.find("a", href=lambda x: x and x.startswith("/statements/"), text="details")
                        filings_link = None
                        if link_tag:
                            filings_link = f"{self.domain_name}{link_tag.get('href')}"
                        data = {
                            "Filing Date":self.get_td_text(tds,0),
                            "Title":self.get_td_text(tds,1),
                            "Description":self.get_td_text(tds,2),
                            "Details":filings_link
                        }
                        self.filings_result.append(data)

            all_links = self.soup.find('a', href=lambda x: x and '/filing_delegate' in x)
            if all_links:
                page = 0
                while True:
                    page += 1
                    if page == 500:
                        break
                    filings_link = f"{self.domain_name}{all_links.get('href')}"
                    src = self.get_page_content(filings_link)
                    soup = BeautifulSoup(src, 'lxml')
                    get_data(soup)
                    pagination = soup.find('div', class_='pagination')
                    if pagination:
                        next_page = pagination.find('li', class_='next next_page')
                        if next_page:
                            next_link = next_page.find('a')
                            if next_link and next_link.get('href') != "#": 
                                all_links = {"href": next_link.get('href')}
                                continue 
                    break
            else:
                get_data(self.soup)
        except Exception as ex:
            self.logger.debug(ex)
        return self.filings_result
    
    def get_trademark_registrations(self) -> list:
        self.trademark_registrations = []
        try:
            def get_data(main_soup: BeautifulSoup) -> None:
                div = main_soup.find('div', id="data-table-trademark_registration")
                if div:
                    rows = div.select("table tbody tr")
                    for row in rows:
                        tds = row.find_all('td')
                        link_tag = row.find("a", href=lambda x: x and x.startswith("/statements/"), text="details")
                        trademark_link = None
                        if link_tag:
                            trademark_link = f"{self.domain_name}{link_tag.get('href')}"
                        image_link = ''
                        if len(tds)>1:
                            block_imge = tds[1].find('img')
                            if block_imge:
                                image_link = block_imge.get('src')
                        data = {
                            "Mark Text":self.get_td_text(tds,0),
                            "Image":image_link,
                            "Register":self.get_td_text(tds,2),
                            "Nice classifications":self.get_td_text(tds,3),
                            "Registration Date":self.get_td_text(tds,4),
                            "Expiry Date":self.get_td_text(tds,5),
                            "Details":trademark_link
                        }
                        self.trademark_registrations.append(data)

            all_links = self.soup.find('a', href=lambda x: x and '/trademark_registration' in x)
            if all_links:
                page = 0
                while True:
                    page += 1
                    if page == 500:
                        break
                    trademark_link = f"{self.domain_name}{all_links.get('href')}"
                    src = self.get_page_content(trademark_link)
                    soup = BeautifulSoup(src, 'lxml')
                    get_data(soup)
                    pagination = soup.find('div', class_='pagination')
                    if pagination:
                        next_page = pagination.find('li', class_='next next_page')
                        if next_page:
                            next_link = next_page.find('a')
                            if next_link and next_link.get('href') != "#": 
                                all_links = {"href": next_link.get('href')}
                                continue 
                    break
            else:
                get_data(self.soup)
        except Exception as ex:
            self.logger.debug(ex)
        return self.trademark_registrations
    
    def get_subsidiaries(self) -> list:
        self.subsidiaries_result = []
        try:
            def get_data(main_soup: BeautifulSoup) -> None:
                div = main_soup.find('div', id="data-table-subsidiary_relationship_subject")
                if div:
                    trs = div.find_all("tr")
                    for tr in trs:
                        name_tag = tr.find('a',class_="company")
                        if not name_tag:
                            continue
                        name = name_tag.text.strip()
                        link_company = f"{self.domain_name}{name_tag.get('href')}"
                        link_tag = tr.find("a", href=lambda x: x and x.startswith("/statements/"), text="details")
                        if not link_tag:
                            continue
                        subsidiaries_link = f"{self.domain_name}{link_tag.get('href')}"
                        data = {
                            "Company": name,
                            "Company_Url": link_company,
                            "Details": subsidiaries_link
                        }
                        self.subsidiaries_link_companies.add(link_company)
                        self.subsidiaries_result.append({name:data})

            all_links = self.soup.find('a', href=lambda x: x and '/subsidiary_relationship_subject' in x)
            if all_links:
                page = 0
                while True:
                    page += 1
                    if page == 500:
                        break
                    subsidiaries_link = f"{self.domain_name}{all_links.get('href')}"
                    src = self.get_page_content(subsidiaries_link)
                    soup = BeautifulSoup(src, 'lxml')
                    get_data(soup)
                    pagination = soup.find('div', class_='pagination')
                    if pagination:
                        next_page = pagination.find('li', class_='next next_page')
                        if next_page:
                            next_link = next_page.find('a')
                            if next_link and next_link.get('href') != "#": 
                                all_links = {"href": next_link.get('href')}
                                continue 
                    break
            else:
                get_data(self.soup)
        except Exception as ex:
            self.logger.debug(ex)
        return self.subsidiaries_result

    def get_company_addresses(self) -> list:
        value = set()
        lower_value = set()
        try:
            div = self.soup.find('div', id="company_addresses")
            if div:
                for p in div.find_all('p',class_="description"):
                    address = p.text.strip()
                    if str(address).lower() not in lower_value:
                        lower_value.add(str(address).lower())
                        value.add(address)
        except Exception as ex:
            self.logger.debug(ex)
        return list(value)
    
    def get_recent_filings(self) -> list:
        value = []
        try: 
            div = self.soup.find('div', id="filings")
            if div:
                all_links = div.find_all('a', class_='filing')
                if all_links:
                    for link in all_links:
                        name = link.text.strip()
                        filing_link = f"{self.domain_name}{link.get('href')}"
                        src = self.get_page_content(filing_link)
                        if not src:
                            continue
                        soup = BeautifulSoup(src,'lxml')
                        filing_url = ""
                        filing_url_line = soup.find('dd', class_="filing_url")
                        if filing_url_line:
                            filing_url_a = filing_url_line.find('a')
                            if filing_url_a:
                               filing_url = filing_url_a.get('href')
                        data = {
                            "Company": self.get_dd("company", soup),
                            "Filing Date": self.get_dd("filing_date", soup),
                            "Filing Url": filing_url,
                            "Filing Number": self.get_dd("filing_number truncate", soup),
                            "Filing Type": self.get_dd("filing_type", soup),
                            "Filing Code": self.get_dd("filing_code", soup)
                        }
                        value.append({name:data})
        except Exception as ex:
            self.logger.debug(ex)
        return value
    
    def get_official_register_entries(self) -> dict:
        value = {}
        try:
            div = self.soup.find('div', id="official_register_entries")
            if div:
                entries = div.find_all("div", class_="assertion official_register_entry")
                for entry in entries:
                    name = entry.find("a").text.strip()
                    register_id = entry.find("p", class_="description").text.strip().replace("register id: ", "")
                    value[name] = register_id
        except Exception as ex:
            self.logger.debug(ex)
        return value
    
    def get_websites(self) -> list:
        value = set()
        try:
            div = self.soup.find('div', id="websites")
            if div:
                a_tegs = div.find_all("a", class_="external")
                for a_teg in a_tegs:
                    link = a_teg.get('href')
                    if link:
                        value.add(link)
        except Exception as ex:
            self.logger.debug(ex)
        return list(value)
    
    def get_source_url(self) -> str:
        value = ""
        dd_value = self.soup.find('dd', class_="source")
        if dd_value:
            a_teg = dd_value.find('a')
            if a_teg:
                value = a_teg.get('href',"")
        return value
    
    def get_identifiers(self) -> dict:
        value = {}
        try:
            div = self.soup.find('div', id="data-table-identifier_delegate")
            if div:
                rows = div.select("table tbody tr")
                for row in rows:
                    tds = row.find_all("td")
                    system = tds[0].text.strip() if tds[0] else ""
                    identifier = tds[1].text.strip() if tds[0] else ""
                    if identifier:
                        value[identifier] = system
        except Exception as ex:
            self.logger.debug(ex)
        return value

    def get_industry_codes_json(self) -> list:
        value = []
        try:
            div = self.soup.find('div', id="data-table-industry_code")
            if div:
                rows = div.select("table tbody tr")
                for row in rows:
                    name = row.find('td').text.strip()
                    link_tag = row.find("a", href=lambda x: x and x.startswith("/statements/"), text="details")
                    if not link_tag:
                        continue
                    industry_codes_link = f"{self.domain_name}{link_tag.get('href')}"
                    src = self.get_page_content(industry_codes_link)
                    if not src:
                        continue
                    soup = BeautifulSoup(src,'lxml')
                    data = {
                        "codeScheme": self.get_dd("code_scheme", soup),
                        "codeSchemeWebsite": self.get_dd("code_scheme_website", soup),
                        "parentCode": self.get_dd("parent_code", soup),
                        "mapsTo": self.get_dd("maps_to", soup)
                    }
                    value.append({name:data})
        except Exception as ex:
            self.logger.debug(ex)
        return value
    
    def get_branches(self) -> list:
        value = []
        try:
            div = self.soup.find('div', id="data-table-branch_relationship_subject")
            if div:
                rows = div.select("table tbody tr")
                for row in rows:
                    link_tag = row.find("a", class_='company branch actif')
                    if not link_tag:
                        continue
                    name = link_tag.text.strip()
                    branches_link = f"{self.domain_name}{link_tag.get('href')}"
                    src = self.get_page_content(branches_link)
                    if not src:
                        continue
                    soup = BeautifulSoup(src,'lxml')
                    data = {
                        "Company_Number": self.get_dd("company_number", soup),
                        "Status": self.get_dd("status", soup),
                        "Incorporation_Date": self.get_dd("incorporation_date", soup)
                    }
                    value.append({name:data})
        except Exception as ex:
            self.logger.debug(ex)
        return value