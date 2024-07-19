from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.cluster import KMeans

from data_fetch import get_corporates, fetch_corporate_details
from celery import Celery, chord
from celery import group
import logging
from mongo import mongo_client
from fastapi.encoders import jsonable_encoder
from bson import ObjectId
import requests

celery = Celery('tasks')
celery.config_from_object('celery_config')

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
hf_token = "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"
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


@celery.task
def initialize_task():
    corporates = get_corporates(API_URL, HEADERS)
    detail_tasks = group(fetch_details_task.s(corporate['id']) for corporate in corporates)
    workflow = chord(detail_tasks, analysis_task.s())
    workflow.apply_async()


@celery.task
def fetch_details_task(corporate_id):
    # logging.info(f"Fetching details for corporate ID: {corporate_id}")
    details = fetch_corporate_details(API_URL, HEADERS, corporate_id)
    inserted = mongo_client["db"]["corporates"].insert_one(jsonable_encoder(details))
    return str(inserted.inserted_id)


@celery.task
def analysis_task(corporate_ids):
    corporates = list(mongo_client["db"]["corporates"].find(
        {'_id': {'$in': [ObjectId(_id) for _id in corporate_ids]}}
    ))
    descriptions = [corporate['description'] for corporate in corporates]
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
    #print(f"Embeddings: {final_embeddings[:10]} Length: {len(final_embeddings[0])}")

    # Clustering
    range_n_clusters = range(10, 30)
    best_n_clusters = None
    best_silhouette_score = -1

    for n_clusters in range_n_clusters:
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        cluster_labels = kmeans.fit_predict(final_embeddings)

        silhouette_avg = silhouette_score(final_embeddings, cluster_labels)
        if silhouette_avg > best_silhouette_score:
            best_silhouette_score = silhouette_avg
            best_n_clusters = n_clusters

    if best_n_clusters is None:
        return "No optimal clustering found."

    # Apply the best clustering
    kmeans = KMeans(n_clusters=best_n_clusters, random_state=42)
    cluster_labels = kmeans.fit_predict(final_embeddings)
    print(f"Best cluster number:{best_n_clusters} Cluster labels:{cluster_labels}")

    for corporate, label in zip(corporates, cluster_labels):
        mongo_client["db"]["corporates"].update_one(
            {'_id': corporate['_id']},
            {'$set': {'cluster_label': int(label)}}
        )
    return f"Corporates Length {len(corporates)}"
