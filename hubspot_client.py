import requests
import json


class HubSpotClient:

    def __init__(self, api_token, account_id):
        self.api_token = api_token
        self.account_id = account_id
        self.contact_url = "https://api.hubapi.com/crm/v3/objects/contacts?count=100"
        self.company_url = "https://api.hubapi.com/crm/v3/objects/companies?count=100"
        self.deal_url = "https://api.hubapi.com/deals/v1/deal"
        self.pipeline_url = "https://api.hubapi.com/crm-pipelines/v1/pipelines/deals"
        self.headers = headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_token}'
        }

    def create_contact(self, email, firstname, lastname):
        data = { 
            "properties": {
                "email": email,
                "firstname": firstname,
                "lastname": lastname
            }
        }

        response = requests.post(self.contact_url, headers=self.headers, json=data)
        if response.json().get("id"):
            return response.json().get("id")
        else:
            raise Exception(response.content)

    def create_company(self, name, domain):
        data = { 
            "properties": {
                "name": name,
                "domain": domain
            }
        }
        response = requests.post(self.company_url, headers=self.headers, json=data)
        if response.json().get("id"):
            return response.json().get("id")
        else:
            raise Exception(response.content)

    def create_deal(self, deal_name, deal_stage, pipeline_id, company_id, contact_id):
        data = { 
            "properties": [
                    {
                        "name": "dealname",
                        "value": deal_name
                    },
                    {
                        "name": "dealstage",
                        "value": deal_stage
                    },
                    {
                        "name": "pipeline",
                        "value": pipeline_id
                    }
            ],
            "associations": {
                "associatedCompanyIds": [int(company_id)],
                "associatedVids": [int(contact_id)]
            }
        }
        response = requests.post(self.deal_url, headers=self.headers, json=data)
        deal_id = response.json().get("dealId")
        if deal_id:
            return deal_id
        else:
            raise Exception(response.content)

    def get_contact(self):
        response = requests.get(self.contact_url, headers=self.headers)
        results = response.json().get("results")
        next_page = response.json().get("paging")
        while next_page:
            response = requests.get(next_page.get("next").get("link"), headers=self.headers)
            results.extend(response.json().get("results"))
            next_page = response.json().get("paging")
        return results

    def get_company(self):
        response = requests.get(self.company_url, headers=self.headers)
        results = response.json().get("results")
        next_page = response.json().get("paging")
        while next_page:
            response = requests.get(next_page.get("next").get("link"), headers=self.headers)
            results.extend(response.json().get("results"))
            next_page = response.json().get("paging")
        return results

    def get_pipeline(self):
        response = requests.get(self.pipeline_url, headers=self.headers)
        data = response.json().get("results")[2]
        pipeline_id = data.get("pipelineId")
        stages = [{"stage_id": s.get("stageId"), "label": s.get("label")} for s in data.get("stages")]
        return {
            "pipeline_id": pipeline_id,
            "stages": stages
        }