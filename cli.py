from dotenv import dotenv_values
import json
import requests
import subprocess


class CLI:

    def __init__(self):
        env_variables = dotenv_values('.env')
        self.api_token = env_variables.get('HS_API_TOKEN')
        self.headers = headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_token}'
        }
        self.contact_url = "https://api.hubapi.com/crm/v3/objects/contacts"
        self.company_url = "https://api.hubapi.com/crm/v3/objects/companies"

    @staticmethod
    def process(gum_output):
        return gum_output.stdout.strip().split("\n")

    def prompt(self, input_placehoder):
        value = self.process(subprocess.run(["gum", "input", "--placeholder", input_placehoder], stdout=subprocess.PIPE, text=True))
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
        response = requests.get(self.company_url, headers=self.headers)
        companies = [ f'{c.get("properties").get("name")} - {c.get("properties").get("domain")} - {c.get("id")}' for c in response.json().get("results")]
        items_string = "\\n".join(companies)
        command = f"echo '{items_string}' | gum filter"
        process = subprocess.run(command, shell=True, stdout=subprocess.PIPE, text=True)
        return process.stdout.split("-")[-1].strip()

    def get_contact(self):
        response = requests.get(self.contact_url, headers=self.headers)
        contacts = [ f'{c.get("properties").get("firstname")} - {c.get("properties").get("lastname")} - {c.get("properties").get("email")} - {c.get("id")}' for c in response.json().get("results")]
        items_string = "\\n".join(contacts)
        command = f"echo '{items_string}' | gum filter"
        process = subprocess.run(command, shell=True, stdout=subprocess.PIPE, text=True)
        return process.stdout.split("-")[-1].strip()

    def create_deal(self):
        command = 'gum confirm "Do you want to create a company first?"'
        process = subprocess.run(command, shell=True, stdout=subprocess.PIPE, text=True)
        if process.returncode == 0:
            company = self.create_company()
        else:
            company = self.get_company()
        
        command = 'gum confirm "Do you want to create a contact?"'
        process = subprocess.run(command, shell=True, stdout=subprocess.PIPE, text=True)
        if process.returncode == 0:
            contact = self.create_contact()
        else:
            contact = self.get_contact()

        command = 'gum input --placeholder "Deal name"'
        deal_name = self.process(subprocess.run(command, shell=True, stdout=subprocess.PIPE, text=True))[0]
        print(deal_name, company, contact)
        

    def launch_menu(self):
        command = 'gum choose --cursor="👉 " "0. Create Deal" "1. Create Company" "2. Create Contact" "3. Get Company" "4. Get Contact"'
        process = subprocess.run(command, shell=True, stdout=subprocess.PIPE, text=True)
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
    cli = CLI()
    cli.launch_menu()

