import os
import pandas as pd
from urllib.parse import urlparse
from flask import Flask, render_template, request, redirect, url_for
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

app = Flask(__name__)
app.static_folder = 'static'

def process_user_data(input_folder, output_folder, user_id):
    user_csv = os.path.join(input_folder, f'user{user_id}.csv')
    output_file = os.path.join(output_folder, f'product_counts_user{user_id}.csv')
    df = pd.read_csv(user_csv)

    # Add a column named user_id to the data
    df['User_id'] = user_id

    # Function to extract domain from URL
    def extract_domain(url):
        try:
            parsed_url = urlparse(url)
            return parsed_url.netloc
        except:
            return None

    # Apply function to extract domain from Links column
    df['Domain'] = df['Links'].apply(extract_domain)

    # Filter out searches (Here searches are filtered from google.com)
    google_searches_df = df[df['Domain'].str.contains('google.com')]

    # Extract search queries (Here the search queries are extracted from the link)
    google_searches_df['Search_Query'] = google_searches_df['Links'].str.extract(r'q=([^&]+)')

    # Drop rows with None values in Search_Query column
    google_searches_df = google_searches_df.dropna(subset=['Search_Query'])

    # Define the search terms
    search_terms = [
        'shoes', 'shirt', 'jeans', 'pants', 'kurta', 'salwar', 'dress', 'mobile', 'earbuds', 'cars', 'charger',
        'mouse', 'laptop', 'OLED', 'LCD', 'USB', 'engines', 'mileage', 'interior', 'airbags', 'diesel', 'petrol',
        'electric', 'brake', 'classic', 'vintage', 'sports', 'keyboard'
    ]

    # Initialize dictionary to store term counts
    search_term_counts = {term: 0 for term in search_terms}

    # Count frequency of each search term in search queries
    for term in search_terms:
        term_count = google_searches_df['Search_Query'].str.lower().str.replace(' ', '').str.contains(term.lower()).sum()
        search_term_counts[term] = term_count

    # Convert the search_term_counts dictionary to a DataFrame
    result_df = pd.DataFrame(list(search_term_counts.items()), columns=['Product', 'Count'])

    # Add 'User_id' column as the first column
    result_df.insert(0, 'User_id', user_id)

    # Create the output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    # Save the results to a CSV file with 'User_id' column as the first column
    result_df.to_csv(output_file, index=False)
#Client Federation
def client_federation():
    category_mapping = {
        'shirt': 'Clothing', 'jeans': 'Clothing', 'pants': 'Clothing', 'kurta': 'Clothing', 'salwar': 'Clothing',
        'dress': 'Clothing', 'mobile': 'Electronics', 'earbuds': 'Electronics', 'cars': 'Vehicles', 'charger': 'Electronics',
        'mouse': 'Electronics', 'laptop': 'Electronics', 'OLED': 'Electronics', 'LCD': 'Electronics', 'USB': 'Electronics',
        'engines': 'Vehicles', 'mileage': 'Vehicles', 'interior': 'Vehicles', 'airbags': 'Vehicles', 'diesel': 'Vehicles',
        'petrol': 'Vehicles', 'electric': 'Vehicles', 'brake': 'Vehicles', 'classic': 'Vehicles', 'vintage': 'Vehicles',
        'sports': 'Vehicles', 'keyboard': 'Electronics',
    }

    final_output_folder = 'static'
    os.makedirs(final_output_folder, exist_ok=True)

    user_files = [f'output/product_counts_user{user_number}.csv' for user_number in range(1, 8)]
    combined_category_df = pd.DataFrame(columns=['User_id', 'Category', 'Count'])

    for user_file in user_files:
        user_df = pd.read_csv(user_file)

        # Replace 'Product' column values with categories
        user_df['Category'] = user_df['Product'].map(category_mapping)

        # Group by 'Category' and sum the counts for each category
        category_sum_df = user_df.groupby('Category')['Count'].sum().reset_index()

        # Add 'User_id' column
        user_id = int(user_file.split('_user')[1].split('.')[0])
        category_sum_df.insert(0, 'User_id', user_id)

        # Append to the combined DataFrame
        combined_category_df = pd.concat([combined_category_df, category_sum_df], ignore_index=True)

    output_file_path = os.path.join(final_output_folder, 'category_counts_net.csv')

    # Save the files
    combined_category_df.to_csv(output_file_path, index=False)

def cluster(num_clusters):
    df = pd.read_csv("static/category_counts_net.csv")

    # Pivot the DataFrame to have categories as columns
    pivot_df = df.pivot_table(index='User_id', columns='Category', values='Count', fill_value=0)

    # Normalize the data
    scaler = StandardScaler()
    normalized_data = scaler.fit_transform(pivot_df)

    # Perform K-means clustering
    kmeans = KMeans(n_clusters=num_clusters, random_state=42)
    kmeans.fit(normalized_data)

    # Assign cluster labels to users
    pivot_df['Cluster'] = kmeans.labels_

    # Reset index to get 'User_id' as a column
    pivot_df.reset_index(inplace=True)

    # Extract 'User_id' and 'Cluster' columns
    final_output = pivot_df[['User_id', 'Cluster']]

    # Save the final output as a CSV file
    output_csv_path = 'static/clustering_result.csv'
    final_output.to_csv(output_csv_path, index=False)

input_folder = 'inputs'
output_folder = 'output'

# Process user data for each user
for user_id in range(1, 8):
    process_user_data(input_folder, output_folder, user_id)

# Client federation process
client_federation()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/report')
def report():
    return render_template('report.html')

@app.route('/users-profile')
def users_profile():
    return render_template('users-profile.html')

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        num_clusters = int(request.form['clusters'])
        cluster(num_clusters)
        return redirect(url_for('settings'))
    return render_template('settings.html')

if __name__ == '__main__':
    app.run(debug=True)
