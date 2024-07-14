# This class is for fetching the list of enterprises
# and their details for each enterprise from the
# Glassdollar website using the  GraphQL API (https://ranking.glassdollar.com/graphql).

import requests
from celery import Celery

app = Celery('tasks', broker='redis://redis:6379/0', backend='redis://redis:6379/0')
API_URL = 'https://ranking.glassdollar.com/graphql'

HEADERS = {
    'Content-Type': 'application/json',
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Accept-Language': 'en-US,en;q=0.9,tr;q=0.8',
    'User-Agent': 'Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.188 Safari/537.36 CrKey/1.54.250320',
    'Origin': 'https://ranking.glassdollar.com',
    'Referer': 'https://ranking.glassdollar.com/',
}
def get_corporates(api_url, headers):
        list_page_query = {
            'operationName': 'TopRankedCorporates',
            'variables': {},
            'query': '''
            query TopRankedCorporates {
              topRankedCorporates {
                id
                name
                logo_url
                industry
                hq_city
                startup_partners {
                  company_name
                  logo_url: logo
                  __typename
                }
                startup_friendly_badge
                __typename
              }
            }
            '''
        }
        try:
            response = requests.post(api_url, json=list_page_query, headers=headers)
            corporates = response.json()['data']['topRankedCorporates'];
        except (requests.exceptions.RequestException, ValueError) as e:
            print(f"An error occurred: {e}")
            corporates = []

        return corporates

def fetch_corporate_details(api_url, headers, corporate_id):
        detail_query = {
            'operationName': 'CorporateDetails',
            'variables': {'id': corporate_id},
            'query': '''
            query CorporateDetails($id: String!) {
              corporate(id: $id) {
                name
                description
                logo_url
                hq_city
                hq_country
                website_url
                linkedin_url
                twitter_url
                startup_partners_count
                startup_partners {
                  company_name
                  logo_url: logo
                  city
                  website
                  country
                  theme_gd
                }
                startup_themes
              }
            }
            '''
        }
        try:
            response = requests.post(api_url, json=detail_query, headers=headers)
            details = response.json()['data']['corporate']
        except (requests.exceptions.RequestException, ValueError) as e:
            print(f"An error occurred: {e}")
            details = {}

        return details

@app.task(bind=True)
def fetch_all_corporates(self):
    corporates = get_corporates(API_URL, HEADERS)
    details_list = []

    for corporate in corporates:
        corporate_id = corporate['id']
        details = fetch_corporate_details(API_URL, HEADERS, corporate_id)
        details_list.append(details)
        self.update_state(state='PROGRESS', meta={'current': len(details_list), 'total': len(corporates)})

    return details_list