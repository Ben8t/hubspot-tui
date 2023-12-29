from hubspot_client import HubSpotClient
import os
from dotenv import dotenv_values
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import time

class CLI:

    def __init__(self, hs_client):
        self.hs_client = hs_client
        command = 'gum style --border double --margin "1" --padding "1 2" --border-foreground "#FF7A59" "👋 Welcome to $(gum style --foreground "#FF7A59" \'HubSpot CLI\')"'
        process = self.run_command(command)
        print(process.stdout)
        self.contacts, self.companies = self.get_assets()

    @staticmethod
    def parse_output(gum_output):
        return gum_output.stdout.strip().split("\n")
    
    @staticmethod
    def run_command(command):
        process = subprocess.run(command, shell=True, stdout=subprocess.PIPE, text=True)
        return process

    def prompt(self, input_placehoder):
        command = f'gum input --placeholder "{input_placehoder}"'
        value = self.parse_output(self.run_command(command))
        return value[0]

    def create_contact(self):
        email = self.prompt("email")
        firstname = self.prompt("firstname")
        lastname = self.prompt("lastname")
        self.hs_client.create_contact(email, firstname, lastname)

    def create_company(self):
        name = self.prompt("name")
        domain = self.prompt("domain")
        self.hs_client.create_company(self, name, domain)

    def get_assets(self):
        command = 'gum spin --spinner meter --title "Loading assets (companies, contacts)..." -- sleep 15'
        command_thread = threading.Thread(target=self.run_command, args=(command,))
        command_thread.start()

        with ThreadPoolExecutor(max_workers=2) as executor:
            future_contact = executor.submit(self.hs_client.get_contact)
            future_company = executor.submit(self.hs_client.get_company)

            # Retrieve the results once they're available
            contacts = future_contact.result()
            companies = future_company.result()

        command_thread.join()
        return contacts, companies

    def get_company(self):
        display_companies = []
        for c in self.companies:
            try:
                item = {
                        "name": c.get("properties").get("name").replace("'", ""),
                        "domain": c.get("properties").get("domain"),
                        "id": c.get("id")
                    }
                display_companies.append(
                    f'{item.get("name")} - {item.get("domain")} - {item.get("id")}'
                )
            except:
                pass
            
        items_string = "\\n".join(display_companies)
        print(display_companies)
        command = f"echo '{items_string}' | gum filter"
        process = self.run_command(command)
        company_id = process.stdout.split("-")[-1].strip()
        print(f"🖇️ https://app-eu1.hubspot.com/contacts/{self.hs_client.account_id}/record/0-2/{company_id}")
        return company_id

    def get_contact(self):
        display_contacts = []
        for c in self.contacts:
            try:
                item = {
                        "firstname": c.get("properties").get("firstname").replace("'", ""),
                        "lastname": c.get("properties").get("lastname").replace("'", ""),
                        "email": c.get("properties").get("email"),
                        "id": c.get("id")
                    }
                display_contacts.append(
                    f'{item.get("firstname")} - {item.get("lastname")} - {item.get("email")} - {item.get("id")}'
                )
            except:
                pass
            
        items_string = "\\n".join(display_contacts)
        command = f"echo '{items_string}' | gum filter"
        process = self.run_command(command)
        contact_id = process.stdout.split("-")[-1].strip()
        print(f"🖇️ https://app-eu1.hubspot.com/contacts/{self.hs_client.account_id}/record/0-1/{contact_id}")
        return contact_id

    def launch_menu(self):
        command = 'gum choose --cursor="> " "0. Create Deal 🤝" "1. Create Company 🏢" "2. Create Contact 📞" "3. Get Company" "4. Get Contact" "5. Refresh data 🆕"'
        process = self.run_command(command)
        id = process.stdout.split(".")[0].strip()
        if id == "0":
            pass
            #self.create_deal()
        if id == "1":
            self.create_company()
        if id == "2":
            self.create_contact()
        if id == "3":
            self.get_company()
        if id == "4":
            self.get_contact()
        if id == "5":
            self.get_assets()
        
        command = 'gum confirm "Do you want to stay in the CLI?"'
        process = self.run_command(command)
        if process.returncode == 0:
            self.launch_menu()
        else:
            exit(0)

if __name__ == "__main__":
    os.environ['GUM_INPUT_PROMPT_FOREGROUND'] = "#FF7A59"
    os.environ['GUM_CHOOSE_PROMPT_FOREGROUND'] = "#FF7A59"
    os.environ['GUM_CHOOSE_CURSOR_FOREGROUND'] = "#FF7A59"
    os.environ['GUM_FILTER_PROMPT_FOREGROUND'] = "#FF7A59"
    os.environ['GUM_FILTER_MATCH_FOREGROUND'] = "#FF7A59"
    os.environ['GUM_SPIN_SPINNER_FOREGROUND'] = "#FF7A59"
    env_variables = dotenv_values('.env')
    
    hs_client = HubSpotClient(env_variables.get('HS_API_TOKEN'), env_variables.get("HS_ACCOUNT_ID"))
    
    cli = CLI(hs_client)
    cli.launch_menu()