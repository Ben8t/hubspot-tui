from dotenv import dotenv_values
import json
import os
import requests
import subprocess
import threading


def run_command(command):
    process = subprocess.run(command, shell=True, stdout=subprocess.PIPE, text=True)
    return process

class CLI:

    def __init__(self):
        env_variables = dotenv_values('.env')
        self.api_token = env_variables.get('HS_API_TOKEN')
        self.hs_account_id = env_variables.get("HS_ACCOUNT_ID")
        self.headers = headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_token}'
        }
        self.contact_url = "https://api.hubapi.com/crm/v3/objects/contacts?count=100"
        self.company_url = "https://api.hubapi.com/crm/v3/objects/companies?count=100"
        self.deal_url = "https://api.hubapi.com/deals/v1/deal"
        self.pipeline_url = "https://api.hubapi.com/crm-pipelines/v1/pipelines/deals"

    @staticmethod
    def process(gum_output):
        return gum_output.stdout.strip().split("\n")

    def prompt(self, input_placehoder):
        command = f'gum input --placeholder "{input_placehoder}"'
        value = self.process(subprocess.run(command, shell=True, stdout=subprocess.PIPE, text=True))
        return value[0]
    


    def create_contact(self):
        data = { 
            "properties": {
                "email": self.prompt("email"),
                "firstname": self.prompt("firstname"),
                "lastname": self.prompt("lastname")
            }
        }

        response = requests.post(self.contact_url, headers=self.headers, json=data)
        if response.json().get("id"):
            return response.json().get("id")
        else:
            raise Exception(response.content)


    def create_company(self):
        data = { 
            "properties": {
                "name": self.prompt("name"),
                "domain": self.prompt("domain")
            }
        }
        response = requests.post(self.company_url, headers=self.headers, json=data)
        if response.json().get("id"):
            return response.json().get("id")
        else:
            raise Exception(response.content)

    def get_company(self):
        command = 'gum spin --spinner meter --title "Loading company..." -- sleep 15'
        command_thread = threading.Thread(target=run_command, args=(command,))
        command_thread.start()
        response = requests.get(self.company_url, headers=self.headers)
        results = response.json().get("results")
        next_page = response.json().get("paging")
        while next_page:
            response = requests.get(next_page.get("next").get("link"), headers=self.headers)
            results.extend(response.json().get("results"))
            next_page = response.json().get("paging")

        for c in results:
            c["properties"]["name"] = c["properties"]["name"].replace("'", "")
    
        command_thread.join()
        companies = [ f'{c.get("properties").get("name")} - {c.get("properties").get("domain")} - {c.get("id")}' for c in results]
        items_string = "\\n".join(companies)
        command = f"echo '{items_string}' | gum filter"
        process = run_command(command)
        company_id = process.stdout.split("-")[-1].strip()
        print(f"🖇️ https://app-eu1.hubspot.com/contacts/{self.hs_account_id}/record/0-2/{company_id}")
        return company_id

    def get_contact(self):
        command = 'gum spin --spinner meter --title "Loading contact..." -- sleep 15'
        command_thread = threading.Thread(target=run_command, args=(command,))
        command_thread.start()
        response = requests.get(self.contact_url, headers=self.headers)
        results = response.json().get("results")
        next_page = response.json().get("paging")
        while next_page:
            response = requests.get(next_page.get("next").get("link"), headers=self.headers)
            results.extend(response.json().get("results"))
            next_page = response.json().get("paging")

        for c in results:
            try:
                c["properties"]["firstname"] = c["properties"]["firstname"].replace("'", "")
                c["properties"]["lastname"] = c["properties"]["lastname"].replace("'", "")
            except:
                pass

        command_thread.join()
        contacts = [ f'{c.get("properties").get("firstname")} - {c.get("properties").get("lastname")} - {c.get("properties").get("email")} - {c.get("id")}' for c in results]
        items_string = "\\n".join(contacts)
        command = f"echo '{items_string}' | gum filter"
        process = run_command(command)
        contact_id = process.stdout.split("-")[-1].strip()
        print(f"🖇️ https://app-eu1.hubspot.com/contacts/{self.hs_account_id}/record/0-1/{contact_id}")
        return contact_id

    def get_pipeline(self):
        response = requests.get(self.pipeline_url, headers=self.headers)
        data = response.json().get("results")[0]
        pipeline_id = data.get("pipelineId")
        stages = [{"stage_id": s.get("stageId"), "label": s.get("label")} for s in data.get("stages")]
        return {
            "pipeline_id": pipeline_id,
            "stages": stages
        }

    def choose_stage(self):
        stages = [ f'{s.get("stage_id")} - {s.get("label")}' for s in self.get_pipeline().get("stages")]
        items_string = "\\n".join(stages)
        command = f"echo '{items_string}' | gum filter"
        process = run_command(command)
        return process.stdout.split("-")[0].strip()


    def create_deal(self):
        command = 'gum confirm "Do you want to create a company first?"'
        process = run_command(command)
        if process.returncode == 0:
            company = self.create_company()
        else:
            company = self.get_company()
        
        command = 'gum confirm "Do you want to create a contact?"'
        process = run_command(command)
        if process.returncode == 0:
            contact = self.create_contact()
        else:
            contact = self.get_contact()

        deal_name = self.prompt("Deal name")
        data = { 
            "properties": [
                    {
                        "name": "dealname",
                        "value": deal_name
                    },
                    {
                        "name": "dealstage",
                        "value": self.choose_stage()
                    },
                    {
                        "name": "pipeline",
                        "value": self.get_pipeline().get("pipeline_id")
                    }
            ],
            "associations": {
                "associatedCompanyIds": [int(company)],
                "associatedVids": [int(contact)]
            }
        }

        response = requests.post(self.deal_url, headers=self.headers, json=data)
        deal_id = response.json().get("dealId")
        if deal_id:
            print(f"🖇️ https://app-eu1.hubspot.com/contacts/{self.hs_account_id}/record/0-3/{deal_id}")
            return deal_id
        else:
            raise Exception(response.content)
        

    def launch_menu(self):
        command = 'gum style --border double --margin "1" --padding "1 2" --border-foreground "#FF7A59" "👋 Welcome to $(gum style --foreground "#FF7A59" \'HubSpot CLI\')"'
        process = run_command(command)
        print(process.stdout)
        command = 'gum choose --cursor="> " "0. Create Deal 🤝" "1. Create Company 🏢" "2. Create Contact 📞" "3. Get Company" "4. Get Contact"'
        process = run_command(command)
        id = process.stdout.split(".")[0].strip()
        if id == "0":
            self.create_deal()
        if id == "1":
            self.create_company()
        if id == "2":
            self.create_contact()
        if id == "3":
            self.get_company()
        if id == "4":
            self.get_contact()
        

if __name__ == "__main__":
    os.environ['GUM_INPUT_PROMPT_FOREGROUND'] = "#FF7A59"
    os.environ['GUM_CHOOSE_PROMPT_FOREGROUND'] = "#FF7A59"
    os.environ['GUM_CHOOSE_CURSOR_FOREGROUND'] = "#FF7A59"
    os.environ['GUM_FILTER_PROMPT_FOREGROUND'] = "#FF7A59"
    os.environ['GUM_FILTER_MATCH_FOREGROUND'] = "#FF7A59"
    cli = CLI()
    cli.launch_menu()

