# startup-crawls

##Installation

1) Clone the repository:

git clone https://github.com/tugceozgirgin/startup-crawls.git
cd your-repo

2) Get your API keys from Gemini and HuggingFace:

Related Links:

  Gemini: https://ai.google.dev/gemini-api/docs/api-key?authuser=1
  
  HuggingFace: http://hf.co/settings/tokens (IMPORTANT: Give all the accesses)

Then open the .env file and put your API keys to the corresponding places:

![image](https://github.com/user-attachments/assets/f8dc1394-4240-48f6-a8f3-4b74170b0d00)


3) Now it is ready to build
docker-compose up --build

#Running

1) After the build has been completed and the celery ready log appeared, go to http://localhost:8000/docs#/

![image](https://github.com/user-attachments/assets/8d93ebf1-8c2c-4423-84b7-bcd2839a21f2)


![image](https://github.com/user-attachments/assets/826d1587-2007-4611-bf8e-997b54c8595b)

2) First post crawl-corporates to initiate the corporate fetching and analysis processes.
   
   ![image](https://github.com/user-attachments/assets/44b2f9a0-f245-4b60-bdd1-edf7c95a59e0)

It will return you an analysis_id. With that ID, you can get the clustering and analysis results from the database. It will return a pending message if the initialization process if the initialization step has not ended yet. 

    a)Pending Status:
    
![image](https://github.com/user-attachments/assets/ec329bb7-a903-46ec-bfe6-179c79e8719b)

    b) Success Status & Results:

![image](https://github.com/user-attachments/assets/7a398e3e-3a66-4bf4-bf67-77d2da9ab8fc)


#Database After Successful Runs

a) Fetched Corporate Data from https://ranking.glassdollar.com

![fetched_data](https://github.com/user-attachments/assets/f1167eb2-a956-40d9-8c66-2d04c470eb25)

b) Clustering/Analysis Results

![image](https://github.com/user-attachments/assets/b07dedab-3e0b-4a35-887a-fb022f102719)

#Analysis Explanation

1)Retrieve Corporate Details:

The function starts by retrieving detailed information for a list of corporate IDs from the MongoDB database. It collects the descriptions of these companies for further analysis.

2)Vector Embedding:

The descriptions are converted into vector embeddings using a pre-trained model from Hugging Face's API.

3)Dimensionality Reduction:

Given that the initial vector size is 384 dimensions, Principal Component Analysis (PCA) is used to reduce the dimensionality of the embeddings while retaining 90% of the variance.

4)Clustering:

The function attempts to find the optimal number of clusters by iterating over a range of possible values (10 to 30) and calculating the silhouette score for each. The number of clusters with the highest silhouette score is selected as the best. KMeans clustering is then performed using this optimal number of clusters. Each corporate is assigned a cluster label based on its vector representation.

5)Generate Cluster Titles:

Using the Gemini API, the function generates a title for each cluster. This is done by passing the clusters' data to the model and requesting a suitable title for each cluster.

7)Store Final Results:

The final clustering results, including cluster labels and titles, are updated in the MongoDB database under a specified analysis ID. 


