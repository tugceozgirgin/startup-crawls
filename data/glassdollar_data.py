# This class is for fetching the list of enterprises
# and their details for each enterprise from the
# Glassdollar website using the  GraphQL API (https://ranking.glassdollar.com/graphql).

import requests
import json

class DataFetch:
    def __init__(self, api_url, headers):
        self.api_url = api_url
        self.headers = headers

    def get_corporates(self):
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
            response = requests.post(self.api_url, json=list_page_query, headers=self.headers)
            corporates = response.json()['data']['topRankedCorporates'];
        except (requests.exceptions.RequestException, ValueError) as e:
            print(f"An error occurred: {e}")

        return corporates

    def get_corporate_details(self):
        result = []
        corporates = self.get_corporates()

        detail_query = {
            'operationName': 'CorporateDetails',
            'variables': {
                'id': None  # Placeholder for corporate ID
            },
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

        for corporate in corporates:
            detail_query['variables']['id'] = corporate['id']
            try:
                response = requests.post(self.api_url, json=detail_query, headers=self.headers)
                details = response.json()['data']['corporate']
                result.append(details)
            except (requests.exceptions.RequestException, ValueError) as e:
                print(f"An error occurred: {e}")

        with open("corporate_details.json", "w") as file:
            json.dump(result, file, indent=4)

        return result


api_url = 'https://ranking.glassdollar.com/graphql'

headers = {
    'Content-Type': 'application/json',
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Accept-Language': 'en-US,en;q=0.9,tr;q=0.8',
    'User-Agent': 'Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.188 Safari/537.36 CrKey/1.54.250320',
    'Origin': 'https://ranking.glassdollar.com',
    'Referer': 'https://ranking.glassdollar.com/',
}

fetcher = DataFetch(api_url, headers)
data = fetcher.get_corporate_details()
print(data)
