import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import numpy as np
import matplotlib.pyplot as plt

def preprocess_text(text: str) -> str:
    # Базовая предобработка текста
    text = text.lower()
    # Здесь можно добавить стемминг/лемматизацию
    return text

def find_optimal_clusters(tfidf_matrix, max_clusters=10):
    silhouette_scores = []
    for n_clusters in range(2, max_clusters + 1):
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        cluster_labels = kmeans.fit_predict(tfidf_matrix)
        silhouette_avg = silhouette_score(tfidf_matrix, cluster_labels)
        silhouette_scores.append(silhouette_avg)
    
    # Визуализация результатов
    plt.plot(range(2, max_clusters + 1), silhouette_scores)
    plt.xlabel('Number of clusters')
    plt.ylabel('Silhouette Score')
    plt.title('Silhouette Score for Different Numbers of Clusters')
    plt.savefig('silhouette_scores.png')
    
    return np.argmax(silhouette_scores) + 2  # +2 потому что начинаем с 2 кластеров

def cluster_qa_pairs(csv_file: str, output_file: str):
    # Загрузка данных
    df = pd.read_csv(csv_file)
    
    # Объединение вопросов и ответов для лучшей кластеризации
    combined_text = df['question'] + ' ' + df['answer']
    combined_text = combined_text.apply(preprocess_text)
    
    # Векторизация текста
    vectorizer = TfidfVectorizer(max_features=1000)
    tfidf_matrix = vectorizer.fit_transform(combined_text)
    
    # Определение оптимального количества кластеров
    optimal_clusters = find_optimal_clusters(tfidf_matrix)
    
    # Кластеризация
    kmeans = KMeans(n_clusters=optimal_clusters, random_state=42)
    df['cluster'] = kmeans.fit_predict(tfidf_matrix)
    
    # Сохранение результатов
    df.to_csv(output_file, index=False, encoding='utf-8')
    
    # Вывод статистики по кластерам
    print(f"\nОптимальное количество кластеров: {optimal_clusters}")
    print("\nРазмеры кластеров:")
    print(df['cluster'].value_counts().sort_index())
    
    # Вывод примеров из каждого кластера
    print("\nПримеры из каждого кластера:")
    for cluster in range(optimal_clusters):
        print(f"\nКластер {cluster}:")
        cluster_samples = df[df['cluster'] == cluster].head(2)
        for _, row in cluster_samples.iterrows():
            print(f"Вопрос: {row['question'][:100]}...")
            print(f"Ответ: {row['answer'][:100]}...")
            print("---")

if __name__ == "__main__":
    cluster_qa_pairs('2021_qa.csv', '2021_clustered.csv') 