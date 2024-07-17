# This class is for fetching the list of enterprises
# and their details for each enterprise from the
# Glassdollar website using the  GraphQL API (https://ranking.glassdollar.com/graphql).

import requests

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
    corporates = []
    page = 1
    has_more = True

    while has_more:
        corporates_json_data = {
            "operationName": "Corporates",
            "variables": {
                "filters": {
                    "hq_city": [],
                    "industry": []
                },
                "page": page
            },
            "query": "query Corporates($filters: CorporateFilters, $page: Int) {\n  corporates(filters: $filters, page: $page) {\n    rows {\n      id\n      name\n    }\n    count\n  }\n}\n"
        }
        try:
            response = requests.post(api_url, json=corporates_json_data, headers=headers)
            response_json = response.json()

            if 'data' in response_json and 'corporates' in response_json['data']:
                data = response_json['data']['corporates']
                rows = data['rows']
                count = data['count']

                if rows:
                    corporates.extend(rows)
                    page += 1
                else:
                    has_more = False

                if len(corporates) >= count:
                    has_more = False
            else:
                print(f"Response format is not correct.")
                break

        except (requests.exceptions.RequestException, ValueError) as e:
            print(f"Error: {e}")
            break
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


corporates = get_corporates(API_URL, HEADERS)
print(corporates)
# # for corporate in corporates:
# #     corporate_id = corporate['id']
# #     details = fetch_corporate_details(API_URL, HEADERS, corporate_id)
# #     print(details)

