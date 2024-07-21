import json

from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.cluster import KMeans
import os
from dotenv import load_dotenv

from data_fetch import get_corporates, fetch_corporate_details
from celery import Celery, chord
from celery import group
import logging
from mongo import mongo_client
from fastapi.encoders import jsonable_encoder
from bson import ObjectId
import requests
import google.generativeai as genai

load_dotenv()

celery = Celery('tasks')
celery.config_from_object('celery_config')

hf_token = os.getenv('HUGGINGFACE_API_KEY')
gemini_token = os.getenv('GEMINI_API_KEY')

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
logging.basicConfig(level=logging.INFO)

model_id = "sentence-transformers/all-MiniLM-L6-v2"
api_url_huggingface = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{model_id}"
headers_huggingface = {"Authorization": f"Bearer {hf_token}"}


def query_vectors(texts):
    try:
        response = requests.post(api_url_huggingface, headers=headers_huggingface,
                                 json={"inputs": texts, "options": {"wait_for_model": True}})
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error couldn't fetch the vectors: {e}")
        return None


def initialize_task():
    corporates = get_corporates(API_URL, HEADERS)
    detail_tasks = group(fetch_details_task.s(corporate['id']) for corporate in corporates)

    initial_doc = {
        "clusters": [],
        "status": "PENDING"
    }
    inserted_doc = mongo_client["results_db"]["results"].insert_one(initial_doc)
    analysis_id = str(inserted_doc.inserted_id)

    workflow = chord(detail_tasks, analysis_task.s(analysis_id))
    workflow.apply_async()
    return analysis_id


@celery.task
def fetch_details_task(corporate_id):
    details = fetch_corporate_details(API_URL, HEADERS, corporate_id)
    inserted = mongo_client["db"]["corporates"].insert_one(jsonable_encoder(details))
    return str(inserted.inserted_id)


@celery.task
def analysis_task(corporate_ids, analysis_id):
    corporates = list(mongo_client["db"]["corporates"].find(
        {'_id': {'$in': [ObjectId(_id) for _id in corporate_ids]}}
    ))

    descriptions = []
    for corporate in corporates:
        if 'description' in corporate:
            descriptions.append(corporate['description'])

    embeddings = query_vectors(descriptions)

    if embeddings is None:
        return "Could not fetch embeddings."

    # Dimensionality reduction for my vector-size (initially 384 dimensions)
    pca = PCA()
    reduced_embeddings = pca.fit_transform(embeddings)

    explained_variance_ratio = pca.explained_variance_ratio_
    cumulative_variance = explained_variance_ratio.cumsum()
    ideal_components = next(x[0] for x in enumerate(cumulative_variance) if x[1] >= 0.90)
    print("Ideal vector size: ", ideal_components)
    pca = PCA(n_components=ideal_components)
    final_embeddings = pca.fit_transform(embeddings)


    # Clustering
    n_clusters = range(10, 30)
    best_n_clusters = None
    best_silhouette_score = -1

    for n_clusters in n_clusters:
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        cluster_labels = kmeans.fit_predict(final_embeddings)

        silhouette = silhouette_score(final_embeddings, cluster_labels)
        if silhouette > best_silhouette_score:
            best_silhouette_score = silhouette
            best_n_clusters = n_clusters

    if best_n_clusters is None:
        return "No optimal clustering found."

    kmeans = KMeans(n_clusters=best_n_clusters, random_state=42)
    cluster_labels = kmeans.fit_predict(final_embeddings)
    print(f"Best cluster number:{best_n_clusters}")

    for corporate, label in zip(corporates, cluster_labels):
        mongo_client["db"]["corporates"].update_one(
            {'_id': corporate['_id']},
            {'$set': {'cluster_label': int(label)}}
        )

    clusters = {}
    for corporate, label in zip(corporates, cluster_labels):
        if label not in clusters:
            clusters[label] = []
        clusters[label].append({
            "name": corporate['name'],
            "description": corporate['description']
        })

    formatted_clusters = [{"cluster": int(key), "companies": value} for key, value in clusters.items()]
    titles = generate_cluster_title(formatted_clusters)
    title_dict = {item["cluster"]: item["cluster_title"] for item in titles}

    final_result = []
    for cluster in formatted_clusters:
        cluster_label = cluster["cluster"]
        title = title_dict.get(cluster_label, "Unknown Title")
        final_result.append({
            "cluster_label": cluster_label,
            "cluster_title": title,
            "companies": cluster["companies"]
        })

    mongo_client["results_db"]["results"].update_one(
        {
            "_id": ObjectId(analysis_id)
        },
        {"$set":{
            "clusters": final_result,
            "status": "SUCCESS"
        }}
    )

    return analysis_id


def generate_cluster_title(clusters):
    try:
        genai.configure(api_key=gemini_token)
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content([
            """I am giving you some clusters and their contents. Find exactly one title for each cluster, and return a list of dictionary which includes cluster label and it's cluster_title for each cluster. Here is list format that I want, do not return something different from that: [{"cluster": 0, "cluster_title": "Title0"},{"cluster": 1, "cluster_title": "Title1"}]).""",
            json.dumps(clusters, default=int)])

        print("Response text: ", response.text)
        response_text = response.text.strip()

        if response_text.startswith("```json"):
            response_text = response_text[len("```json"):].strip()
        if response_text.endswith("```"):
            response_text = response_text[:-len("```")].strip()

        response_text = response_text.replace("\n", "").replace("\r", "")
        json_data = json.loads(response_text)
        return json_data

    except Exception as e:
        logging.error(f"Error in generate_cluster_title: {e}")
        return []
